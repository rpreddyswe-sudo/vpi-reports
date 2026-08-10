"""
VPI UL Monthly Report Generator
Usage:
    python vpi_ul_monthly_report.py                    # uses first day of current month
    python vpi_ul_monthly_report.py 2026-05-01         # explicit snapshot date
Output:
    vpi_ul_report_May_2026.html  (in same directory as this script)
"""

import sys
import os
from datetime import datetime

# Import from UL-specific modules
from utils import add_months
from csv_handler import load_csv_data, detect_csv_dates, execute_query_on_csv
from report_renderer import *
from data_processor import market_movers_html, bandvend_flags, bss_flags_count, market_band_flags_count

# ─── Config ────────────────────────────────────────────────────────────────
# Environment mode: 'csv' for development (local files), 'db' for production (PostgreSQL)
DATA_MODE = os.environ.get('DATA_MODE', 'csv').lower()  # Default to CSV for development

# Conditional imports based on data mode
if DATA_MODE == 'db':
    import psycopg2
    from psycopg2.extras import RealDictCursor

# Database configuration (for production/UAT)
CONN  = "postgresql://npanalytics_ro:verizon24@nts-gydv-fuze-planning-prd-01-cluster.cluster-cl9vgbtolm5s.us-east-1.rds.amazonaws.com:5432/fuzenppprod"
STAGE = "vpi.vpi_data_n5l_waiv_stage_ul"
REF   = "vpi.vpi_data_n5l_ul"
TRGPRJD_UL = "trgprjd_ul"
TRGCURR_UL = "trgcurr_ul"

# CSV data directory (for development)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

# ─── Date Setup ────────────────────────────────────────────────────────────
if len(sys.argv) > 1:
    snapshot_date = sys.argv[1]
else:
    snapshot_date = add_months(datetime.today().replace(day=1), -1).strftime('%Y-%m-%d')

curr_dt = datetime.strptime(snapshot_date, '%Y-%m-%d')
m1_dt   = add_months(curr_dt, -1)
m2_dt   = add_months(curr_dt, -2)

CURR = curr_dt.strftime('%Y-%m-%d')
M1   = m1_dt.strftime('%Y-%m-%d')
M2   = m2_dt.strftime('%Y-%m-%d')

h0 = curr_dt.strftime('%b %Y')
h1 = m1_dt.strftime('%b %Y')
h2 = m2_dt.strftime('%Y-%m-%d')   # used only in query, not label

today_str = datetime.today().strftime('%Y-%m-%d')
out_file  = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         f"vpi_ul_report_{curr_dt.strftime('%b_%Y')}.html")

print(f"Data Mode: {DATA_MODE.upper()}")
print(f"Snapshot : {CURR}  |  Ref M-1 : {M1}  |  Ref M-2 : {M2}")
print(f"Output   : {out_file}\n")

# ─── Queries ───────────────────────────────────────────────────────────────
QUERIES = {

"avail": (f"""
SELECT '{STAGE}' AS tbl, cptmonth::date AS cptmonth,
       COUNT(*) AS rows, COUNT(DISTINCT agg_unique_id) AS carriers
FROM {STAGE} WHERE cptmonth = %s GROUP BY cptmonth
UNION ALL
SELECT '{REF}', cptmonth::date,
       COUNT(*), COUNT(DISTINCT agg_unique_id)
FROM {REF} WHERE cptmonth IN (%s, %s) GROUP BY cptmonth
ORDER BY 1, 2
""", (CURR, M1, M2)),

"market": (f"""
WITH m0 AS (SELECT market, COUNT(*) AS cnt FROM {STAGE} WHERE cptmonth=%s GROUP BY 1),
     m1 AS (SELECT market, COUNT(*) AS cnt FROM {REF}   WHERE cptmonth=%s GROUP BY 1),
     m2 AS (SELECT market, COUNT(*) AS cnt FROM {REF}   WHERE cptmonth=%s GROUP BY 1)
SELECT m0.market,
       m0.cnt  AS curr_cnt,
       m1.cnt  AS m1_cnt,
       m2.cnt  AS m2_cnt,
       ROUND(((m0.cnt - m1.cnt)::numeric / NULLIF(m1.cnt,0))*100,2) AS var_curr_m1,
       ROUND(((m1.cnt - m2.cnt)::numeric / NULLIF(m2.cnt,0))*100,2) AS var_m1_m2
FROM m0
LEFT JOIN m1 ON m0.market=m1.market
LEFT JOIN m2 ON m0.market=m2.market
ORDER BY 1
""", (CURR, M1, M2)),

"bandvend": (f"""
WITH prev AS (
   SELECT projecteddate, bandgrp, vendor,
          COUNT(DISTINCT agg_unique_id) AS cnt
   FROM {REF}
   WHERE cptmonth=%s AND {TRGPRJD_UL}='y' AND projecteddate BETWEEN 2026 AND 2030
   GROUP BY 1,2,3
),
curr AS (
   SELECT projecteddate, bandgrp, vendor,
          COUNT(DISTINCT agg_unique_id) AS cnt
   FROM {STAGE}
   WHERE cptmonth=%s AND {TRGPRJD_UL}='y' AND projecteddate BETWEEN 2026 AND 2030
   GROUP BY 1,2,3
)
SELECT a.projecteddate, a.bandgrp, a.vendor,
       a.cnt AS prev_count, COALESCE(b.cnt,0) AS curr_count,
       CASE WHEN a.cnt=0 THEN NULL
            ELSE ROUND((((COALESCE(b.cnt,0)-a.cnt)::float/a.cnt)*100)::numeric,2)
       END AS pct_diff,
       CASE WHEN a.cnt>0 AND ((COALESCE(b.cnt,0)-a.cnt)::decimal/a.cnt)<-0.05
            THEN 'Decrease >5%%' ELSE 'Acceptable' END AS flag
FROM prev a
LEFT JOIN curr b ON a.projecteddate=b.projecteddate
                AND a.bandgrp=b.bandgrp AND a.vendor=b.vendor
ORDER BY 1,2,3
""", (M1, CURR)),

"bss_curr": (f"""
WITH prev AS (
   SELECT bandgrp, vendor, COUNT(DISTINCT agg_unique_id) AS cnt
   FROM {REF} WHERE cptmonth=%s AND cec_curr='BSS' GROUP BY 1,2
),
curr AS (
   SELECT bandgrp, vendor, COUNT(DISTINCT agg_unique_id) AS cnt
   FROM {STAGE} WHERE cptmonth=%s AND cec_curr='BSS' GROUP BY 1,2
)
SELECT a.bandgrp, a.vendor,
       a.cnt AS prev_count, COALESCE(b.cnt,0) AS curr_count,
       CASE WHEN a.cnt=0 THEN NULL
            ELSE ROUND((((COALESCE(b.cnt,0)-a.cnt)::float/a.cnt)*100)::numeric,2)
       END AS pct_diff,
       CASE WHEN a.cnt>0 AND ((COALESCE(b.cnt,0)-a.cnt)::decimal/a.cnt)<-0.05
            THEN 'Decrease >5%%' ELSE 'Acceptable' END AS flag
FROM prev a
LEFT JOIN curr b ON a.bandgrp=b.bandgrp AND a.vendor=b.vendor
ORDER BY 1,2
""", (M1, CURR)),

"movement": (f"""
SELECT 'Lost from {h1} (not in {h0} stage)' AS category,
       COUNT(DISTINCT r.agg_unique_id) AS carrier_count
FROM {REF} r WHERE r.cptmonth=%s
  AND NOT EXISTS (SELECT 1 FROM {STAGE} s WHERE s.cptmonth=%s AND s.agg_unique_id=r.agg_unique_id)
UNION ALL
SELECT 'New in {h0} (not in {h1} ref)',
       COUNT(DISTINCT s.agg_unique_id)
FROM {STAGE} s WHERE s.cptmonth=%s
  AND NOT EXISTS (SELECT 1 FROM {REF} r WHERE r.cptmonth=%s AND r.agg_unique_id=s.agg_unique_id)
""", (M1, CURR, CURR, M1)),

"trgdist": (f"""
SELECT projecteddate,
       COALESCE({TRGPRJD_UL},'null') AS flag,
       COUNT(DISTINCT agg_unique_id) AS carriers
FROM {STAGE} WHERE cptmonth=%s
GROUP BY 1,2 ORDER BY 1,2
""", (CURR,)),

"cec": (f"""
WITH stage AS (
  SELECT COALESCE(cec_curr,'-') AS cec_curr,
         COUNT(DISTINCT agg_unique_id) AS stage_cnt
  FROM {STAGE} WHERE cptmonth=%s GROUP BY 1
),
ref AS (
  SELECT COALESCE(cec_curr,'-') AS cec_curr,
         COUNT(DISTINCT agg_unique_id) AS ref_cnt
  FROM {REF} WHERE cptmonth=%s GROUP BY 1
)
SELECT COALESCE(s.cec_curr, r.cec_curr) AS cec_curr,
       COALESCE(r.ref_cnt,0) AS m1_count,
       COALESCE(s.stage_cnt,0) AS curr_count,
       COALESCE(s.stage_cnt,0) - COALESCE(r.ref_cnt,0) AS delta
FROM stage s FULL OUTER JOIN ref r ON s.cec_curr=r.cec_curr
ORDER BY 1
""", (CURR, M1)),

"rehome": ("""
SELECT DISTINCT old_market, new_market
FROM vpi_temp.rehome_market_info
ORDER BY 1
""", ()),

"lost_by_band": (f"""
WITH rh AS (SELECT DISTINCT old_market FROM vpi_temp.rehome_market_info),
unexplained AS (
    SELECT m0.market
    FROM (SELECT market, COUNT(*) AS cnt FROM {STAGE} WHERE cptmonth=%s GROUP BY 1) m0
    JOIN (SELECT market, COUNT(*) AS cnt FROM {REF}   WHERE cptmonth=%s GROUP BY 1) m1
      ON m0.market = m1.market
    LEFT JOIN rh ON m0.market = rh.old_market
    WHERE rh.old_market IS NULL
      AND ROUND(((m0.cnt - m1.cnt)::numeric / NULLIF(m1.cnt,0))*100,2) <= -5
)
SELECT r.bandgrp,
       COUNT(DISTINCT r.agg_unique_id) AS lost_carriers
FROM {REF} r
JOIN unexplained u ON r.market = u.market
WHERE r.cptmonth = %s
  AND NOT EXISTS (
      SELECT 1 FROM {STAGE} s
      WHERE s.cptmonth = %s AND s.agg_unique_id = r.agg_unique_id
  )
GROUP BY 1
ORDER BY 2 DESC
""", (CURR, M1, M1, CURR)),

"dq": (f"""
SELECT COUNT(*) AS total_rows,
       COUNT(DISTINCT agg_unique_id) AS total_carriers,
       SUM(CASE WHEN agg_unique_id IS NULL THEN 1 ELSE 0 END) AS null_agg_id,
       SUM(CASE WHEN market      IS NULL THEN 1 ELSE 0 END) AS null_market,
       SUM(CASE WHEN bandgrp     IS NULL THEN 1 ELSE 0 END) AS null_bandgrp,
       SUM(CASE WHEN vendor      IS NULL THEN 1 ELSE 0 END) AS null_vendor,
       SUM(CASE WHEN projecteddate IS NULL THEN 1 ELSE 0 END) AS null_projdate,
       SUM(CASE WHEN {TRGPRJD_UL}   IS NULL THEN 1 ELSE 0 END) AS null_trgprjd,
       SUM(CASE WHEN cec_curr    IS NULL THEN 1 ELSE 0 END) AS null_cec_curr,
       SUM(CASE WHEN cec_prjd    IS NULL THEN 1 ELSE 0 END) AS null_cec_prjd
FROM {STAGE} WHERE cptmonth=%s
""", (CURR,)),

"market_band_carrier_change": (f"""
WITH prev AS (
   SELECT market, bandgrp, COUNT(DISTINCT agg_unique_id) AS cnt
   FROM {REF} WHERE cptmonth=%s GROUP BY 1,2
),
curr AS (
   SELECT market, bandgrp, COUNT(DISTINCT agg_unique_id) AS cnt
   FROM {STAGE} WHERE cptmonth=%s GROUP BY 1,2
)
SELECT COALESCE(a.market, b.market) AS market,
       COALESCE(a.bandgrp, b.bandgrp) AS bandgrp,
       a.cnt AS prev_count,
       COALESCE(b.cnt,0) AS curr_count,
       CASE WHEN a.cnt=0 THEN NULL
            ELSE ROUND((((COALESCE(b.cnt,0)-a.cnt)::float/a.cnt)*100)::numeric,2)
       END AS pct_diff,
       CASE WHEN a.cnt>0 AND ((COALESCE(b.cnt,0)-a.cnt)::decimal/a.cnt)<-0.05
            THEN 'Decrease >5%%' ELSE 'Acceptable' END AS flag
FROM prev a
FULL OUTER JOIN curr b ON a.market=b.market AND a.bandgrp=b.bandgrp
ORDER BY 1,2
""", (M1, CURR)),

"trgcurr_market_band": (f"""
SELECT market,
       bandgrp,
       COALESCE({TRGCURR_UL},'null') AS trgcurr_flag,
       COUNT(DISTINCT agg_unique_id) AS carriers
FROM {STAGE} WHERE cptmonth=%s
GROUP BY 1,2,3 ORDER BY 1,2,4 DESC
""", (CURR,)),

}

# ─── Run Queries ───────────────────────────────────────────────────────────
# Total queries: 11 (added 2 new queries for market/band analysis)
results = {}

if DATA_MODE == 'csv':
    # Development mode: Use CSV files
    csv_files = load_csv_data(DATA_DIR)
    detected_curr, detected_m1, detected_m2 = detect_csv_dates(csv_files, STAGE, REF)
    
    # Only use detected dates if no specific snapshot date was provided
    # If user provided a specific date, try to use that instead
    if len(sys.argv) <= 1 and detected_curr:
        # No command-line date provided, use detected dates from CSV
        CURR = detected_curr
        M1 = detected_m1 if detected_m1 else M1
        M2 = detected_m2 if detected_m2 else M2
        
        # Update datetime objects and labels
        curr_dt = datetime.strptime(CURR, '%Y-%m-%d')
        m1_dt = datetime.strptime(M1, '%Y-%m-%d')
        m2_dt = datetime.strptime(M2, '%Y-%m-%d')
        h0 = curr_dt.strftime('%b %Y')
        h1 = m1_dt.strftime('%b %Y')
        
        # Update output filename
        out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             f"vpi_ul_report_{curr_dt.strftime('%b_%Y')}.html")
        print(f"Using detected dates from CSV files: {CURR} (current), {M1} (M-1), {M2} (M-2)")
    else:
        # User provided specific date or detection failed, use that date
        # but warn if CSV files don't contain the requested date
        if detected_curr and detected_curr != CURR:
            print(f"Warning: CSV files contain {detected_curr}, but analyzing {CURR} as requested")
        print(f"Using requested date: {CURR} (current), {M1} (M-1), {M2} (M-2)")
    
    print()
    
    for key, (sql, params) in QUERIES.items():
        # Update params with detected dates for CSV mode
        from csv_handler import update_params_for_csv_mode
        updated_params = update_params_for_csv_mode(key, params, CURR, M1, M2)
        results[key] = execute_query_on_csv(key, updated_params, csv_files, STAGE, REF, TRGPRJD_UL, TRGCURR_UL, h0, h1)
    
    print()
    
else:
    # Production mode: Use PostgreSQL database
    print("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(CONN)
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    
    for key, (sql, params) in QUERIES.items():
        try:
            cur.execute(sql, params)
            results[key] = [dict(r) for r in cur.fetchall()]
            print(f"  [ok] {key} — {len(results[key])} rows")
        except Exception as e:
            print(f"  [ERR] {key}: {e}")
            results[key] = []
            conn.rollback()
    
    cur.close()
    conn.close()
    print()

# ─── Derived KPIs ──────────────────────────────────────────────────────────
avail = results.get('avail', [])
stage_row = next((r for r in avail if 'stage' in str(r.get('tbl',''))), {})
ref_row   = next((r for r in avail if 'stage' not in str(r.get('tbl','')) and
                  str(r.get('cptmonth','')).startswith(M1[:7])), {})

curr_carriers = stage_row.get('carriers', 0) or 0
m1_carriers   = ref_row.get('carriers', 0) or 0
net_change    = int(curr_carriers) - int(m1_carriers)
curr_rows     = stage_row.get('rows', 0) or 0

mov = results.get('movement', [])
lost_row = next((r for r in mov if 'Lost' in str(r.get('category',''))), {})
new_row  = next((r for r in mov if 'New'  in str(r.get('category',''))), {})
lost_cnt = lost_row.get('carrier_count', 0) or 0
new_cnt  = new_row.get('carrier_count', 0) or 0

dq = results.get('dq', [{}])[0] if results.get('dq') else {}
dq_status = 'Clean' if all(
    (dq.get(c) or 0) == 0
    for c in ['null_agg_id','null_market','null_bandgrp','null_vendor','null_projdate','null_trgprjd','null_cec_curr']
) else 'Issues Found'

# ─── HTML Renderers ────────────────────────────────────────────────────────
def render_avail_table():
    rows = results.get('avail', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += '<th>Table</th><th>Month</th><th>Total Rows</th><th>Distinct Carriers</th>'
    html += '</tr></thead><tbody>'
    for r in rows:
        hi = 'style="background:rgba(79,142,247,0.07)"' if 'stage' in str(r.get('tbl','')) else ''
        html += f'<tr {hi}><td>{r["tbl"]}</td>'
        html += f'<td class="num">{str(r["cptmonth"])[:10]}</td>'
        html += f'<td class="num">{fmt(r["rows"])}</td>'
        html += f'<td class="num">{fmt(r["carriers"])}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_market_table():
    rows = results.get('market', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>Market</th><th>{h0}</th><th>{h1} (Ref)</th>'
    html += f'<th>{m2_dt.strftime("%b %Y")} (Ref)</th>'
    html += f'<th>{h0} vs {h1} %%</th><th>{h1} vs {m2_dt.strftime("%b %Y")} %%</th>'
    html += '</tr></thead><tbody>'
    for r in rows:
        c1 = pct_class(r.get('var_curr_m1'))
        c2 = pct_class(r.get('var_m1_m2'))
        v1 = r.get('var_curr_m1')
        v2 = r.get('var_m1_m2')
        html += f'<tr><td>{r["market"]}</td>'
        html += f'<td class="num">{fmt(r["curr_cnt"])}</td>'
        html += f'<td class="num">{fmt(r["m1_cnt"])}</td>'
        html += f'<td class="num">{fmt(r["m2_cnt"])}</td>'
        html += f'<td class="num {c1}">{("+" if v1 and float(v1)>0 else "") + str(v1) if v1 is not None else "—"}</td>'
        html += f'<td class="num {c2}">{("+" if v2 and float(v2)>0 else "") + str(v2) if v2 is not None else "—"}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html



def render_bandvend_table():
    rows = results.get('bandvend', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>Proj Year</th><th>BandGrp</th><th>Vendor</th>'
    html += f'<th>{h1} (Prev)</th><th>{h0} (Curr)</th><th>Pct Diff</th><th>Flag</th>'
    html += '</tr></thead><tbody>'
    for r in rows:
        flagged = r.get('flag','') and 'Decrease' in str(r.get('flag',''))
        hi = ' style="background:rgba(248,113,113,0.05)"' if flagged else ''
        pc = r.get('pct_diff')
        pcls = 'text-red' if pc is not None and float(pc) < 0 else ('text-green' if pc is not None and float(pc) > 0 else '')
        pstr = (("+" if float(pc) > 0 else "") + str(pc) + "%%") if pc is not None else "—"
        html += f'<tr{hi}><td>{r["projecteddate"]}</td><td>{r["bandgrp"]}</td><td>{r["vendor"]}</td>'
        html += f'<td class="num">{fmt(r["prev_count"])}</td>'
        html += f'<td class="num">{fmt(r["curr_count"])}</td>'
        html += f'<td class="num {pcls}">{pstr}</td>'
        html += f'<td>{flag_html(r.get("flag"))}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_bss_table():
    rows = results.get('bss_curr', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>BandGrp</th><th>Vendor</th><th>{h1} (Prev)</th><th>{h0} (Curr)</th><th>Pct Diff</th><th>Flag</th>'
    html += '</tr></thead><tbody>'
    for r in rows:
        flagged = r.get('flag','') and 'Decrease' in str(r.get('flag',''))
        hi = ' style="background:rgba(248,113,113,0.05)"' if flagged else ''
        pc = r.get('pct_diff')
        pcls = 'text-red' if pc is not None and float(pc) < 0 else ('text-green' if pc is not None and float(pc) > 0 else '')
        pstr = (("+" if float(pc) > 0 else "") + str(pc) + "%%") if pc is not None else "—"
        html += f'<tr{hi}><td>{r["bandgrp"]}</td><td>{r["vendor"]}</td>'
        html += f'<td class="num">{fmt(r["prev_count"])}</td>'
        html += f'<td class="num">{fmt(r["curr_count"])}</td>'
        html += f'<td class="num {pcls}">{pstr}</td>'
        html += f'<td>{flag_html(r.get("flag"))}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_trgdist_table():
    rows = results.get('trgdist', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += '<th>Projected Year</th><th>Flag</th><th>Carriers</th><th>%% of Year Total</th>'
    html += '</tr></thead><tbody>'
    totals = {}
    for r in rows:
        yr = r['projecteddate']
        totals[yr] = totals.get(yr, 0) + int(r['carriers'] or 0)
    for r in rows:
        yr    = r['projecteddate']
        tot   = totals.get(yr, 1)
        pct   = round(int(r['carriers'] or 0) / tot * 100, 1) if tot else 0
        flagv = str(r['flag'])
        html += f'<tr><td>{yr}</td>'
        html += f'<td style="font-weight:{"600" if flagv=="y" else "normal"};color:{"var(--green)" if flagv=="y" else "inherit"}">{flagv}</td>'
        html += f'<td class="num {"text-green" if flagv=="y" else ""}">{fmt(r["carriers"])}</td>'
        html += f'<td class="num text-muted">{pct}%%</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_cec_table():
    rows = results.get('cec', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>cec_curr</th><th>{h1} (Ref)</th><th>{h0} (Stage)</th><th>Delta</th>'
    html += '</tr></thead><tbody>'
    total_m1 = total_curr = total_delta = 0
    for r in rows:
        d  = int(r.get('delta') or 0)
        dc = delta_class(d)
        dstr = ("+" if d > 0 else "") + fmt(d)
        total_m1   += int(r.get('m1_count') or 0)
        total_curr += int(r.get('curr_count') or 0)
        total_delta += d
        html += f'<tr><td>{r["cec_curr"]}</td>'
        html += f'<td class="num">{fmt(r["m1_count"])}</td>'
        html += f'<td class="num">{fmt(r["curr_count"])}</td>'
        html += f'<td class="num {dc}">{dstr}</td></tr>'
    tdc = delta_class(total_delta)
    tdstr = ("+" if total_delta > 0 else "") + fmt(total_delta)
    html += f'<tr style="font-weight:600;border-top:2px solid var(--border)"><td>Total</td>'
    html += f'<td class="num">{fmt(total_m1)}</td><td class="num">{fmt(total_curr)}</td>'
    html += f'<td class="num {tdc}">{tdstr}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_lost_by_band_table():
    rows  = results.get('lost_by_band', [])
    total = sum(int(r['lost_carriers']) for r in rows)
    html  = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>BandGrp</th><th>Lost Carriers ({h1} not in {h0})</th><th>%% of Total</th><th>Visual</th>'
    html += '</tr></thead><tbody>'
    top_band = rows[0]['bandgrp'] if rows else None
    for r in rows:
        cnt  = int(r['lost_carriers'])
        pct  = round(cnt / total * 100, 1) if total else 0
        bar  = int(pct)
        is_top = r['bandgrp'] == top_band
        bcls = 'text-red' if is_top else ''
        bold = 'font-weight:600;' if is_top else ''
        html += f'<tr style="{bold}background:{"rgba(248,113,113,0.07)" if is_top else "inherit"}">'
        html += f'<td>{r["bandgrp"]}</td>'
        html += f'<td class="num {bcls}">{cnt:,}</td>'
        html += f'<td class="num {bcls}">{pct}%%</td>'
        html += f'<td><div style="background:{"var(--red)" if is_top else "var(--accent)"};height:10px;width:{bar}%%;border-radius:3px;min-width:2px"></div></td>'
        html += '</tr>'
    html += f'<tr style="font-weight:600;border-top:2px solid var(--border)">'
    html += f'<td>TOTAL</td><td class="num">{total:,}</td><td class="num">100.0%%</td><td></td></tr>'
    html += '</tbody></table></div>'
    return html

def render_dq_table():
    r = dq
    rows_data = [
        ('Total Rows',              fmt(r.get('total_rows')),       None),
        ('Total Distinct Carriers', fmt(r.get('total_carriers')),   None),
        ('Null agg_unique_id',      fmt(r.get('null_agg_id')),      r.get('null_agg_id')),
        ('Null market',             fmt(r.get('null_market')),       r.get('null_market')),
        ('Null bandgrp',            fmt(r.get('null_bandgrp')),      r.get('null_bandgrp')),
        ('Null vendor',             fmt(r.get('null_vendor')),       r.get('null_vendor')),
        ('Null projecteddate',      fmt(r.get('null_projdate')),     r.get('null_projdate')),
        (f'Null {TRGPRJD_UL}',      fmt(r.get('null_trgprjd')),      r.get('null_trgprjd')),
        ('Null cec_curr',           fmt(r.get('null_cec_curr')),     r.get('null_cec_curr')),
        ('Null cec_prjd',           fmt(r.get('null_cec_prjd')),     None),  # expected null
    ]
    html = '<div class="tbl-wrap"><table><thead><tr><th>Metric</th><th>Value</th><th>Status</th></tr></thead><tbody>'
    for label, val, check in rows_data:
        if check is None and label.startswith('Null cec_prjd'):
            status = '<span class="text-muted">&#9642; Expected — not populated for UL</span>'
        elif check is None:
            status = ''
        elif int(check or 0) == 0:
            status = '<span class="flag-ok">&#10003; Clean</span>'
        else:
            status = f'<span class="flag-bad">&#x26A0; {fmt(check)} nulls</span>'
        html += f'<tr><td>{label}</td><td class="num">{val}</td><td>{status}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_market_band_carrier_change_table():
    rows = results.get('market_band_carrier_change', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>Market</th><th>BandGrp</th><th>{h1} (Prev)</th><th>{h0} (Curr)</th><th>Pct Diff</th><th>Flag</th>'
    html += '</tr></thead><tbody>'
    for r in rows:
        flagged = r.get('flag','') and 'Decrease' in str(r.get('flag',''))
        hi = ' style="background:rgba(248,113,113,0.05)"' if flagged else ''
        pc = r.get('pct_diff')
        pcls = 'text-red' if pc is not None and float(pc) < 0 else ('text-green' if pc is not None and float(pc) > 0 else '')
        pstr = (("+" if float(pc) > 0 else "") + str(pc) + "%%") if pc is not None else "—"
        html += f'<tr{hi}><td>{r["market"]}</td><td>{r["bandgrp"]}</td>'
        html += f'<td class="num">{fmt(r["prev_count"])}</td>'
        html += f'<td class="num">{fmt(r["curr_count"])}</td>'
        html += f'<td class="num {pcls}">{pstr}</td>'
        html += f'<td>{flag_html(r.get("flag"))}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_trgcurr_market_band_table():
    rows = results.get('trgcurr_market_band', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>Market</th><th>BandGrp</th><th>{TRGCURR_UL} Flag</th><th>Carriers</th><th>%% of Market/Band</th>'
    html += '</tr></thead><tbody>'
    
    # Calculate totals per market/band for percentage calculation
    market_band_totals = {}
    for r in rows:
        key = (r['market'], r['bandgrp'])
        market_band_totals[key] = market_band_totals.get(key, 0) + int(r['carriers'] or 0)
    
    for r in rows:
        key = (r['market'], r['bandgrp'])
        total = market_band_totals.get(key, 1)
        pct = round(int(r['carriers'] or 0) / total * 100, 1) if total else 0
        flagv = str(r.get('trgcurr_flag', 'null'))
        html += f'<tr><td>{r["market"]}</td><td>{r["bandgrp"]}</td>'
        html += f'<td style="font-weight:{"600" if flagv=="y" else "normal"};color:{"var(--green)" if flagv=="y" else "inherit"}">{flagv}</td>'
        html += f'<td class="num {"text-green" if flagv=="y" else ""}">{fmt(r["carriers"])}</td>'
        html += f'<td class="num text-muted">{pct}%%</td></tr>'
    html += '</tbody></table></div>'
    return html

# ─── Build summary insights ────────────────────────────────────────────────
rehome_drop_html, unexplained_drop_html, gain_html, ndrop, ngain = market_movers_html(results, h0, h1)

# Get unique rehome source markets for counting (already deduplicated in query results)
unique_rehome_src = {int(x['old_market']) for x in results.get('rehome', []) if x.get('old_market')}

n_unexplained = sum(1 for r in results.get('market', [])
                    if r.get('var_curr_m1') is not None
                    and float(r['var_curr_m1']) <= -10
                    and int(r['market']) not in unique_rehome_src)
bvf = bandvend_flags(results)
bvf_html = ''.join(f'<li>{bg}/{v}: <span class="text-red">{pc}%%</span> across all proj years</li>' for bg, v, pc in bvf) or '<li>None</li>'
n_bss_flags = bss_flags_count(results)
cec_rows = results.get('cec', [])
bss_delta = next((r.get('delta',0) for r in cec_rows if r.get('cec_curr')=='BSS'), 0)
notbss_delta = next((r.get('delta',0) for r in cec_rows if r.get('cec_curr')=='NOT BSS'), 0)

# Top band for lost_by_band insight (dynamic, not hardcoded)
lost_by_band_rows = results.get('lost_by_band', [])
top_band_total = sum(int(r['lost_carriers']) for r in lost_by_band_rows)
top_band_row   = lost_by_band_rows[0] if lost_by_band_rows else None
top_band_name  = top_band_row['bandgrp'] if top_band_row else ''
top_band_cnt   = int(top_band_row['lost_carriers']) if top_band_row else 0
top_band_pct   = round(top_band_cnt / top_band_total * 100, 1) if top_band_total else 0

# Market/Band carrier change flags
n_market_band_flags = market_band_flags_count(results)

# Data quality message
dq_message = "All key columns 100%% populated — zero nulls." if dq_status=="Clean" else "Issues detected — see A9."

# Lost by band insight text
lost_by_band_insight = (
    f'<b>{top_band_pct}%% of the lost carriers are {top_band_name}</b> ({fmt(top_band_cnt)} carriers) — '
    f'investigate {top_band_name} pipeline/ingestion for {h0}.'
) if top_band_row else ''

# ─── HTML Template ─────────────────────────────────────────────────────────
CSS = """
:root{--bg:#0f1117;--surface:#1a1d27;--surface2:#222535;--border:#2e3347;--text:#e2e8f0;--muted:#8892a4;--accent:#4f8ef7;--green:#34d399;--red:#f87171;--yellow:#fbbf24;--purple:#a78bfa;--orange:#fb923c}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;line-height:1.6}
.page{max-width:1400px;margin:0 auto;padding:32px 24px}
.header{border-bottom:1px solid var(--border);padding-bottom:24px;margin-bottom:32px}
.header h1{font-size:24px;font-weight:700;color:#fff}
.header .sub{color:var(--muted);font-size:13px;margin-top:4px}
.header .meta{display:flex;gap:12px;margin-top:16px;flex-wrap:wrap}
.header .meta span{background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:4px 12px;font-size:12px;color:var(--muted)}
.header .meta span b{color:var(--text)}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:16px;margin-bottom:40px}
.kpi{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 18px}
.kpi .label{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-bottom:8px}
.kpi .value{font-size:26px;font-weight:700;color:#fff}
.kpi .delta{font-size:12px;margin-top:4px}
.kpi .delta.up{color:var(--green)}.kpi .delta.down{color:var(--red)}.kpi .delta.neutral{color:var(--muted)}
.section{margin-bottom:48px}
.section-title{font-size:16px;font-weight:600;color:#fff;margin-bottom:4px;padding-bottom:10px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px}
.badge{font-size:11px;font-weight:500;padding:2px 8px;border-radius:4px}
.badge-info{background:rgba(79,142,247,.15);color:var(--accent)}
.badge-warn{background:rgba(251,191,36,.15);color:var(--yellow)}
.badge-ok{background:rgba(52,211,153,.15);color:var(--green)}
.badge-crit{background:rgba(248,113,113,.15);color:var(--red)}
.section-desc{color:var(--muted);font-size:13px;margin:10px 0 16px}
.insight{background:var(--surface2);border-left:3px solid var(--accent);border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:16px;font-size:13px;color:var(--text)}
.insight.warn{border-left-color:var(--yellow)}.insight.crit{border-left-color:var(--red)}.insight.good{border-left-color:var(--green)}
.insight ul{margin-top:6px;padding-left:18px}.insight li{margin-bottom:3px}.insight b{color:#fff}
.tbl-wrap{overflow-x:auto;border-radius:8px;border:1px solid var(--border);margin-bottom:16px}
table{width:100%;border-collapse:collapse}
thead th{background:var(--surface2);color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em;font-weight:600;padding:10px 14px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}
thead th:first-child{text-align:left}
tbody tr{border-bottom:1px solid var(--border);transition:background .1s}
tbody tr:last-child{border-bottom:none}
tbody tr:hover{background:var(--surface2)}
tbody td{padding:9px 14px;text-align:right;font-size:13px}
tbody td:first-child{text-align:left}
.num{font-variant-numeric:tabular-nums}
.text-red{color:var(--red);font-weight:600}.text-green{color:var(--green);font-weight:600}
.text-yellow{color:var(--yellow)}.text-muted{color:var(--muted)}.text-orange{color:var(--orange)}
.flag-bad{color:var(--red);font-size:12px}.flag-ok{color:var(--green);font-size:12px}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.two-col{grid-template-columns:1fr}}
details summary{cursor:pointer;color:var(--accent);font-size:13px;padding:8px 0;user-select:none}
details summary:hover{text-decoration:underline}
.divider{height:1px;background:var(--border);margin:32px 0}
.footer{color:var(--muted);font-size:12px;text-align:center;padding-top:24px;border-top:1px solid var(--border)}
"""

rehome_pairs = results.get('rehome', [])
rehome_summary_box = (
    '<div class="insight good"><b>Confirmed Rehome:</b> '
    + '  |  '.join(f"Mkt {r['old_market']} -&gt; Mkt {r['new_market']}" for r in rehome_pairs)
    + ' &mdash; volume drop in these markets is expected.</div>'
) if rehome_pairs else ''

net_dir   = 'down' if net_change < 0 else 'up'
net_str   = fmt(abs(net_change))
net_arrow = '&#9660;' if net_change < 0 else '&#9650;'

rows_dir  = ''
try:
    ref_rows_row = next((r for r in avail if 'stage' not in str(r.get('tbl','')) and
                         str(r.get('cptmonth','')).startswith(M1[:7])), {})
    ref_rows = int(ref_rows_row.get('rows', curr_rows) or curr_rows)
    rows_pct = round((int(curr_rows) - ref_rows) / ref_rows * 100, 1) if ref_rows else 0
    rows_dir = 'down' if rows_pct < 0 else 'up'
    rows_delta_str = f"{'&#9660;' if rows_pct<0 else '&#9650;'} {abs(rows_pct)}%% vs {h1}"
except:
    rows_delta_str = ""

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>VPI UL Staging Analysis — {h0}</title>
<style>{CSS}</style>
</head>
<body>
<div class="page">

<div class="header">
  <h1>VPI UL Staging Analysis — {h0}</h1>
  <div class="sub">Monthly comparison: <b>{STAGE}</b> ({h0}) vs <b>{REF}</b> ({h1} / {m2_dt.strftime('%b %Y')})</div>
  <div class="meta">
    <span>Stage: <b>{STAGE}</b></span>
    <span>Reference: <b>{REF}</b></span>
    <span>Snapshot Month: <b>{h0}</b></span>
    <span>M-1 Ref: <b>{h1}</b></span>
    <span>M-2 Ref: <b>{m2_dt.strftime('%b %Y')}</b></span>
    <span>Report Generated: <b>{today_str}</b></span>
  </div>
</div>

<div class="kpi-row">
  <div class="kpi">
    <div class="label">{h0} Stage Carriers</div>
    <div class="value">{fmt(curr_carriers)}</div>
    <div class="delta {net_dir}">{net_arrow} {net_str} vs {h1}</div>
  </div>
  <div class="kpi">
    <div class="label">{h1} Ref Carriers</div>
    <div class="value">{fmt(m1_carriers)}</div>
    <div class="delta neutral">&#9642; baseline</div>
  </div>
  <div class="kpi">
    <div class="label">New in {h0}</div>
    <div class="value" style="color:var(--green)">{fmt(new_cnt)}</div>
    <div class="delta up">not in {h1} ref</div>
  </div>
  <div class="kpi">
    <div class="label">Lost from {h1}</div>
    <div class="value" style="color:var(--red)">{fmt(lost_cnt)}</div>
    <div class="delta down">not in {h0} stage</div>
  </div>
  <div class="kpi">
    <div class="label">{h0} Total Rows</div>
    <div class="value">{fmt(curr_rows)}</div>
    <div class="delta {rows_dir}">{rows_delta_str}</div>
  </div>
  <div class="kpi">
    <div class="label">Data Quality</div>
    <div class="value" style="color:var({'--green' if dq_status=='Clean' else '--red'})">{dq_status}</div>
    <div class="delta {'up' if dq_status=='Clean' else 'down'}">{'0 nulls on key cols' if dq_status=='Clean' else 'See A9'}</div>
  </div>
</div>

<!-- A1 -->
<div class="section">
  <div class="section-title">A1 — Data Availability &amp; Volume Trend <span class="badge badge-info">Sanity Check</span></div>
  <div class="section-desc">Row counts and distinct carrier counts. Stage table shows {h0} snapshot; reference shows prior months.</div>
  {render_avail_table()}
</div>

<!-- A2 -->
<div class="section">
  <div class="section-title">A2 — Market Volume: 3-Month Trend
    <span class="badge badge-crit">{n_unexplained} Unexplained &gt;-10%%</span>
    <span class="badge badge-ok">{len({int(r['old_market']) for r in results.get('rehome',[])})} Confirmed Rehome</span>
  </div>
  <div class="section-desc">Row counts per market, {h0} stage vs {h1}/{m2_dt.strftime('%b %Y')} ref. Declines split into confirmed rehome vs unexplained.</div>
  {'<div class="insight good"><b>Confirmed Rehome Markets (source -> destination):</b><ul>' + rehome_drop_html + '</ul></div>' if rehome_drop_html else ''}
  {'<div class="insight crit"><b>Unexplained Declines &gt;-10%% — Investigate:</b><ul>' + unexplained_drop_html + '</ul></div>' if unexplained_drop_html else ''}
  <div class="insight good">
    <b>Notable Gains ({h0} vs {h1} &gt;+10%%):</b>
    <ul>{gain_html}</ul>
  </div>
  <details>
    <summary>Show full market table ({len(results.get('market',[]))} markets)</summary>
    {render_market_table()}
  </details>
</div>

<!-- A3 -->
<div class="section">
  <div class="section-title">A3 — {TRGPRJD_UL}='y' Band/Vendor by Projected Year (2026–2030)
    <span class="badge badge-crit">{len(bvf)} Combo(s) Flagged Across All Years</span>
  </div>
  <div class="section-desc">Carriers with UL projected target flag, {h1} ref &#8594; {h0} stage, all projection years (2026–2030).</div>
  {'<div class="insight crit"><b>Consistently flagged across all projection years:</b><ul>' + bvf_html + '</ul></div>' if bvf else '<div class="insight good">No band/vendor combinations flagged across any projection year.</div>'}
  {render_bandvend_table()}
</div>

<!-- A4 -->
<div class="section">
  <div class="section-title">A4 — BSS cec_curr Band/Vendor
    <span class="badge {'badge-warn' if n_bss_flags > 0 else 'badge-ok'}">{n_bss_flags} Flag(s)</span>
  </div>
  <div class="section-desc">Carriers where cec_curr='BSS', grouped by band group and vendor, {h1} ref → {h0} stage.</div>
  {render_bss_table()}
</div>

<!-- A6 -->
<div class="section">
  <div class="section-title">A6 — Net Carrier Movement ({h0} Stage vs {h1} Ref)
    <span class="badge {'badge-crit' if net_change < -20000 else 'badge-warn'}">Net {('+' if net_change>0 else '') + fmt(net_change)}</span>
  </div>
  <div class="section-desc">Distinct agg_unique_id present in one month but absent from the other.</div>
  <div class="two-col">
    <div class="insight crit">
      <b>{fmt(lost_cnt)} carriers lost</b> — in {h1} ref, absent from {h0} stage.
    </div>
    <div class="insight good">
      <b>{fmt(new_cnt)} new carriers</b> — in {h0} stage, absent from {h1} ref.
    </div>
  </div>
  <div class="tbl-wrap"><table>
    <thead><tr><th>Category</th><th>Carrier Count</th></tr></thead>
    <tbody>
      <tr><td class="text-red">Lost from {h1} (not in {h0} stage)</td><td class="num text-red">{fmt(lost_cnt)}</td></tr>
      <tr><td class="text-green">New in {h0} (not in {h1} ref)</td><td class="num text-green">{fmt(new_cnt)}</td></tr>
      <tr style="font-weight:600"><td>Net Change</td><td class="num {'text-red' if net_change<0 else 'text-green'}">{('+' if net_change>0 else '') + fmt(net_change)}</td></tr>
    </tbody>
  </table></div>
</div>

<!-- A6b -->
<div class="section">
  <div class="section-title">A6b — Lost Carriers by BandGrp (Unexplained Markets Only)
    <span class="badge badge-crit">{top_band_name} {top_band_pct}%% of Loss</span>
  </div>
  <div class="section-desc">
    Of the carriers lost in unexplained declining markets, how much came from each band group (based on {h1} ref).
    Rehome markets excluded.
  </div>
  {lost_by_band_insight}
  {render_lost_by_band_table()}
</div>

<!-- A7 -->
<div class="section">
  <div class="section-title">A7 — {TRGPRJD_UL} Flag Distribution by Projected Year ({h0} Stage)
    <span class="badge badge-ok">Stable</span>
  </div>
  <div class="section-desc">How {TRGPRJD_UL} ('y'/'n') distributes across each projected year in the {h0} staging table.</div>
  {render_trgdist_table()}
</div>

<!-- A8 -->
<div class="section">
  <div class="section-title">A8 — cec_curr Distribution ({h0} Stage vs {h1} Ref)
    <span class="badge badge-info">BSS {('+' if int(bss_delta or 0)>=0 else '') + fmt(bss_delta)}</span>
  </div>
  <div class="section-desc">Distinct carrier counts by cec_curr classification.</div>
  <div class="insight">
    The overall carrier movement is primarily in <b>NOT BSS</b> ({('+' if int(notbss_delta or 0)>=0 else '') + fmt(notbss_delta)}).
    BSS carriers changed by {('+' if int(bss_delta or 0)>=0 else '') + fmt(bss_delta)}.
    <b>Note: cec_prjd is 100%% null</b> in both UL tables — excluded from this report.
  </div>
  {render_cec_table()}
</div>

<!-- A9 -->
<div class="section">
  <div class="section-title">A9 — Data Quality ({h0} Stage)
    <span class="badge {'badge-ok' if dq_status=='Clean' else 'badge-crit'}">{dq_status}</span>
  </div>
  <div class="section-desc">Null checks on all key columns in {STAGE} for {h0}.</div>
  {render_dq_table()}
</div>

<!-- A10 -->
<div class="section">
  <div class="section-title">A10 — Per Market, Per Band Group Carrier Count Change
    <span class="badge {'badge-crit' if n_market_band_flags > 0 else 'badge-ok'}">{n_market_band_flags} Decrease(s) &gt;5%%</span>
  </div>
  <div class="section-desc">Carrier count changes broken down by market and band group, {h1} ref &#8594; {h0} stage. Identifies specific market/band combinations with significant decreases.</div>
  {render_market_band_carrier_change_table()}
</div>

<!-- A11 -->
<div class="section">
  <div class="section-title">A11 — {TRGCURR_UL} Distribution Per Market, Per Band Group ({h0} Stage)
    <span class="badge badge-info">Detailed Breakdown</span>
  </div>
  <div class="section-desc">Target current flag distribution broken down by market and band group for the {h0} staging table. Shows carrier counts and percentages within each market/band combination.</div>
  {render_trgcurr_market_band_table()}
</div>

<div class="divider"></div>

<!-- Executive Summary -->
<div class="section">
  <div class="section-title">Executive Summary</div>
  {'<div class="insight crit"><b>Action Required — ' + ', '.join(f"{bg}/{v}" for bg,v,_ in bvf) + f' ({TRGPRJD_UL}=y):</b> These band/vendor combinations declined consistently across all projection years (2026–2030). Investigate pipeline/classification before publishing.</div>' if bvf else ''}
  {rehome_summary_box}
  <div class="insight {'crit' if n_unexplained > 0 else 'warn'}">
    <b>{'Action Required' if n_unexplained > 0 else 'Monitor'} — Unexplained Market Declines (&gt;-10%%):</b>
    {n_unexplained} market(s) dropped &gt;10%% with no rehome mapping ({h0} vs {h1}).
    {lost_by_band_insight}
    Net carrier movement: {fmt(lost_cnt)} lost, {fmt(new_cnt)} new, net {('+' if net_change>=0 else '') + fmt(net_change)}.
  </div>
  {f'<div class="insight warn"><b>Monitor — BSS cec_curr:</b> {n_bss_flags} band/vendor combination(s) flagged (&gt;5%% decrease in BSS carriers).</div>' if n_bss_flags > 0 else ''}
  {f'<div class="insight crit"><b>Action Required — Market/Band Carrier Changes:</b> {n_market_band_flags} market/band combination(s) flagged (&gt;5%% decrease). See A10 for detailed breakdown.</div>' if n_market_band_flags > 0 else ''}
  <div class="insight good">
    <b>Data Quality:</b> {dq_message}
    cec_prjd is expected to be null for UL tables.
  </div>
</div>

<div class="footer">
  Generated: {today_str} &nbsp;|&nbsp; Schema: vpi &nbsp;|&nbsp; DB: fuzenppprod<br>
  Stage: {STAGE} ({h0}) &nbsp;|&nbsp; Ref: {REF} ({h1} / {m2_dt.strftime('%b %Y')})
</div>

</div>
</body>
</html>"""

with open(out_file, 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"Report written: {out_file}")
