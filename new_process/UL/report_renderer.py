"""
Report Renderer for VPI UL Monthly Report
Handles HTML rendering functions and formatting utilities
"""

def fmt(n):
    """Format number with commas"""
    try:
        return "{:,}".format(int(n))
    except (ValueError, TypeError):
        return str(n) if n is not None else "0"

def pct_class(v):
    """Return CSS class for percentage values"""
    try:
        return 'text-green' if float(v) >= 0 else 'text-red'
    except: return ''

def delta_class(d):
    """Return CSS class for delta values"""
    try:
        if d > 0: return 'text-green'
        if d < 0: return 'text-red'
        return ''
    except: return ''

def flag_html(flag):
    """Return HTML for flag status"""
    if flag and 'Decrease' in str(flag):
        return '<span class="flag-bad">&#x26A0; Decrease &gt;5%%</span>'
    return '<span class="flag-ok">&#10003; Acceptable</span>'

def kpi_delta_class(v):
    """Return CSS class for KPI delta"""
    try: return 'up' if float(v) >= 0 else 'down'
    except: return 'neutral'

def render_avail_table(results, h0, h1, m2_dt, stage_table):
    """Render availability table"""
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

def render_market_table(results, h0, h1, m2_dt):
    """Render market table"""
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

def render_bandvend_table(results, h0, h1):
    """Render band/vendor table"""
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

def render_bss_table(results, h0, h1):
    """Render BSS table"""
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

def render_trgdist_table(results):
    """Render target distribution table"""
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

def render_cec_table(results, h0, h1):
    """Render CEC table"""
    rows = results.get('cec', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>cec_curr</th><th>{h1} Count</th><th>{h0} Count</th><th>Delta</th>'
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
    html += f'<td class="num">{fmt(total_m1)}</td>'
    html += f'<td class="num">{fmt(total_curr)}</td>'
    html += f'<td class="num {tdc}">{tdstr}</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_lost_by_band_table(results):
    """Render lost by band table"""
    rows = results.get('lost_by_band', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += '<th>BandGrp</th><th>Lost Carriers</th><th>%% of Total Lost</th>'
    html += '</tr></thead><tbody>'
    total_lost = sum(int(r['lost_carriers']) for r in rows)
    for r in rows:
        lost = int(r['lost_carriers'])
        pct = round(lost / total_lost * 100, 1) if total_lost else 0
        html += f'<tr><td>{r["bandgrp"]}</td>'
        html += f'<td class="num">{fmt(lost)}</td>'
        html += f'<td class="num text-muted">{pct}%%</td></tr>'
    html += '</tbody></table></div>'
    return html

def render_dq_table(results):
    """Render data quality table"""
    rows = results.get('dq', [])
    if not rows:
        return '<div class="tbl-wrap"><p>No data quality information available</p></div>'
    
    r = rows[0]
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += '<th>Metric</th><th>Count</th>'
    html += '</tr></thead><tbody>'
    
    metrics = [
        ('Total Rows', r.get('total_rows')),
        ('Distinct Carriers', r.get('total_carriers')),
        ('Null agg_unique_id', r.get('null_agg_id')),
        ('Null market', r.get('null_market')),
        ('Null bandgrp', r.get('null_bandgrp')),
        ('Null vendor', r.get('null_vendor')),
        ('Null projecteddate', r.get('null_projdate')),
        ('Null trgprjd', r.get('null_trgprjd')),
        ('Null cec_curr', r.get('null_cec_curr')),
        ('Null cec_prjd', r.get('null_cec_prjd'))
    ]
    
    for label, value in metrics:
        html += f'<tr><td>{label}</td><td class="num">{fmt(value)}</td></tr>'
    
    html += '</tbody></table></div>'
    return html

def render_market_band_carrier_change_table(results, h0, h1):
    """Render market/band carrier change table"""
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

def render_trgcurr_market_band_table(results, trgcurr):
    """Render target current market/band table"""
    rows = results.get('trgcurr_market_band', [])
    html = '<div class="tbl-wrap"><table><thead><tr>'
    html += f'<th>Market</th><th>BandGrp</th><th>{trgcurr} Flag</th><th>Carriers</th><th>%% of Market/Band</th>'
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