"""
Data Processor for VPI UL Monthly Report
Handles data analysis and insight generation functions
"""

def market_movers_html(results, h0, h1):
    """Generate market movement analysis HTML"""
    rows = results.get('market', [])
    rehome_src = {int(r['old_market']): int(r['new_market']) for r in results.get('rehome', []) 
                  if r.get('old_market') and r.get('new_market') and str(r['old_market']).strip() and str(r['new_market']).strip()}
    rehome_dst = {v: k for k, v in rehome_src.items()}
    rows_by_mkt = {int(r['market']): r for r in rows}

    # Always show all rehome source markets regardless of decline %
    rehome_drop_html = ''
    for old_mkt, new_mkt in sorted(rehome_src.items()):
        r = rows_by_mkt.get(old_mkt, {})
        v  = r.get('var_curr_m1')
        c  = r.get('curr_cnt')
        m1 = r.get('m1_cnt')
        vstr = f'{v}%%' if v is not None else '—'
        rehome_drop_html += (
            f'<li>Mkt {old_mkt} &#8594; Mkt {new_mkt} (rehome): '
            f'<span class="text-red">{vstr}</span> ({m1} &#8594; {c})</li>'
        )

    # Unexplained: non-rehome markets with >= 10% decline
    big_drop = [(r['market'], r['var_curr_m1'], r['curr_cnt'], r['m1_cnt'])
                for r in rows if r.get('var_curr_m1') is not None
                and float(r['var_curr_m1']) <= -10
                and int(r['market']) not in rehome_src]
    big_gain = [(r['market'], r['var_curr_m1'], r['curr_cnt'], r['m1_cnt'])
                for r in rows if r.get('var_curr_m1') is not None and float(r['var_curr_m1']) >= 10]
    big_drop.sort(key=lambda x: float(x[1]))
    big_gain.sort(key=lambda x: -float(x[1]))

    unexplained_drop_html = ''
    for m, v, c, m1 in big_drop:
        unexplained_drop_html += (
            f'<li>Mkt {m}: <span class="text-red">{v}%%</span> '
            f'({m1} &#8594; {c}) — <b>investigate</b></li>'
        )

    gain_html = ''.join(
        f'<li>Mkt {m}'
        f'{"  &#8592; rehome from Mkt " + str(rehome_dst[int(m)]) if int(m) in rehome_dst else ""}'
        f': <span class="text-green">+{v}%%</span> ({m1} &#8594; {c})</li>'
        for m, v, c, m1 in big_gain
    ) or '<li>None</li>'

    return rehome_drop_html, unexplained_drop_html, gain_html, len(big_drop), len(big_gain)

def bandvend_flags(results):
    """Get band/vendor flags for consistent decreases"""
    flagged = [(r['projecteddate'], r['bandgrp'], r['vendor'], r['pct_diff'])
               for r in results.get('bandvend',[]) if 'Decrease' in str(r.get('flag',''))]
    seen = set()
    uniq = []
    for yr, bg, v, pc in flagged:
        if (bg, v) not in seen:
            seen.add((bg, v))
            uniq.append((bg, v, pc))
    return uniq

def bss_flags_count(results):
    """Count BSS flags"""
    return sum(1 for r in results.get('bss_curr',[]) if 'Decrease' in str(r.get('flag','')))

def market_band_flags_count(results):
    """Count market/band carrier change flags"""
    return sum(1 for r in results.get('market_band_carrier_change',[]) if 'Decrease' in str(r.get('flag','')))