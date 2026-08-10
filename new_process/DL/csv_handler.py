"""
CSV Handler for VPI DL Monthly Report
Handles CSV data loading, processing, and query simulation
"""

import os
import csv
from collections import defaultdict
from datetime import datetime

def load_csv_data(data_dir):
    """Load CSV data files for development mode"""
    print("Loading CSV data files...")
    
    # Find the most recent CSV files
    csv_files = {
        'stage': None,
        'ref': None,
        'rehome': None
    }
    
    # List all CSV files in data directory
    if os.path.exists(data_dir):
        all_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        
        # Find stage file (vpi_data_n5l_waiv_stage)
        stage_files = [f for f in all_files if 'vpi_data_n5l_waiv_stage' in f and 'ul' not in f]
        if stage_files:
            csv_files['stage'] = os.path.join(data_dir, max(stage_files))
            print(f"  Stage file: {csv_files['stage']}")
        
        # Find ref file (vpi_data_n5l)
        ref_files = [f for f in all_files if 'vpi_data_n5l' in f and 'waiv_stage' not in f and 'ul' not in f]
        if ref_files:
            csv_files['ref'] = os.path.join(data_dir, max(ref_files))
            print(f"  Ref file: {csv_files['ref']}")
        
        # Find rehome file
        rehome_files = [f for f in all_files if 'rehome' in f]
        if rehome_files:
            csv_files['rehome'] = os.path.join(data_dir, max(rehome_files))
            print(f"  Rehome file: {csv_files['rehome']}")
    
    return csv_files

def detect_csv_dates(csv_files, stage_table, ref_table):
    """Detect available dates from CSV files and return date variables"""
    print("Detecting available dates from CSV files...")
    
    curr, m1, m2 = None, None, None
    
    # Read stage file to get current month
    if csv_files['stage']:
        try:
            with open(csv_files['stage'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                dates = set()
                for row in reader:
                    cptmonth = row.get('cptmonth', '')[:10]  # Get YYYY-MM-DD part
                    if cptmonth:
                        dates.add(cptmonth)
                    if len(dates) > 5:  # Only need first few rows
                        break
                
                if dates:
                    curr = max(dates)  # Use the most recent date as current
                    print(f"  Detected current month from stage: {curr}")
        except Exception as e:
            print(f"  Error reading stage dates: {e}")
    
    # Read ref file to get previous months
    if csv_files['ref']:
        try:
            with open(csv_files['ref'], 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                dates = set()
                for row in reader:
                    cptmonth = row.get('cptmonth', '')[:10]
                    if cptmonth:
                        dates.add(cptmonth)
                    if len(dates) > 10:  # Sample more rows for ref
                        break
                
                if dates and len(dates) >= 1:
                    sorted_dates = sorted(dates)
                    m1 = sorted_dates[-1]  # Most recent as M-1
                    if len(sorted_dates) >= 2:
                        m2 = sorted_dates[-2]  # Second most recent as M-2
                    else:
                        m2 = m1  # Fallback to same as M-1
                    print(f"  Detected M-1 from ref: {m1}")
                    print(f"  Detected M-2 from ref: {m2}")
        except Exception as e:
            print(f"  Error reading ref dates: {e}")
    
    return curr, m1, m2

def read_csv_to_dict(filepath):
    """Read CSV file and return list of dictionaries"""
    data = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"    Error reading {filepath}: {e}")
    return data

def filter_by_month(data, month, month_field='cptmonth'):
    """Filter data by month field - handles both YYYY-MM-DD and YYYY-MM-DD HH:MM:SS formats"""
    filtered = []
    for row in data:
        date_val = row.get(month_field, '')
        # Extract just the date part (YYYY-MM-DD)
        date_part = date_val.split(' ')[0] if ' ' in date_val else date_val
        if date_part == month or date_part.startswith(month):
            filtered.append(row)
    return filtered

def update_params_for_csv_mode(query_key, original_params, curr, m1, m2):
    """Update query parameters to use detected CSV dates instead of hardcoded dates"""
    # Map of parameter positions to date variables for each query
    param_mappings = {
        'avail': [m2, m2],  # Both parameters are M2
        'market': [curr, m1, m2],  # CURR, M1, M2
        'bandvend': [m1, curr],  # M1, CURR
        'bss_curr': [m1, curr],  # M1, CURR
        'movement': [m1, curr],  # M1 for ref (lost), CURR for stage (new)
        'trgdist': [curr],  # CURR
        'cec': [curr, m1],  # CURR, M1
        'lost_by_band': [curr, m1, m1, curr],  # CURR, M1, M1, CURR
        'dq': [curr],  # CURR
        'market_band_carrier_change': [m1, curr],  # M1, CURR
        'trgcurr_market_band': [curr],  # CURR
        'rehome': []  # No date parameters
    }
    
    if query_key in param_mappings:
        return param_mappings[query_key]
    return original_params

def execute_query_on_csv(query_key, params, csv_files, stage_table, ref_table, trgprjd, trgcurr, h0, h1):
    """Execute query logic on CSV data (simulating SQL queries)"""
    print(f"  [CSV] Executing {query_key}...")
    
    try:
        # Load necessary CSV files based on query
        data = {}
        
        if query_key in ['avail', 'market', 'bandvend', 'bss_curr', 'movement', 'trgdist', 'cec', 'dq', 'market_band_carrier_change', 'trgcurr_market_band']:
            if csv_files['stage']:
                data['stage'] = read_csv_to_dict(csv_files['stage'])
                print(f"    Loaded stage: {len(data['stage'])} rows")
        
        if query_key in ['avail', 'market', 'bandvend', 'bss_curr', 'movement', 'cec', 'lost_by_band', 'market_band_carrier_change']:
            if csv_files['ref']:
                data['ref'] = read_csv_to_dict(csv_files['ref'])
                print(f"    Loaded ref: {len(data['ref'])} rows")
        
        if query_key == 'rehome':
            if csv_files['rehome']:
                data['rehome'] = read_csv_to_dict(csv_files['rehome'])
                print(f"    Loaded rehome: {len(data['rehome'])} rows")
        
        # Execute query-specific logic
        result = execute_csv_query_logic(query_key, params, data, stage_table, ref_table, trgprjd, trgcurr, h0, h1)
        print(f"  [ok] {query_key} — {len(result)} rows")
        return result
        
    except Exception as e:
        print(f"  [ERR] {query_key}: {e}")
        return []

def execute_csv_query_logic(query_key, params, data, stage_table, ref_table, trgprjd, trgcurr, h0, h1):
    """Simulate SQL queries on CSV data using standard Python"""
    
    if query_key == 'avail':
        result = []
        # Stage table availability
        if 'stage' in data:
            stage_data = data['stage']
            month_counts = defaultdict(lambda: {'rows': 0, 'carriers': set()})
            for row in stage_data:
                month = row.get('cptmonth', '')[:10]
                if month >= params[0]:  # M2 or later
                    month_counts[month]['rows'] += 1
                    month_counts[month]['carriers'].add(row.get('agg_unique_id', ''))
            
            for month in sorted(month_counts.keys()):
                result.append({
                    'tbl': stage_table,
                    'cptmonth': month,
                    'rows': month_counts[month]['rows'],
                    'carriers': len(month_counts[month]['carriers'])
                })
        
        # Ref table availability
        if 'ref' in data:
            ref_data = data['ref']
            month_counts = defaultdict(lambda: {'rows': 0, 'carriers': set()})
            for row in ref_data:
                month = row.get('cptmonth', '')[:10]
                if month >= params[1]:  # M2 or later
                    month_counts[month]['rows'] += 1
                    month_counts[month]['carriers'].add(row.get('agg_unique_id', ''))
            
            for month in sorted(month_counts.keys()):
                result.append({
                    'tbl': ref_table,
                    'cptmonth': month,
                    'rows': month_counts[month]['rows'],
                    'carriers': len(month_counts[month]['carriers'])
                })
        
        return sorted(result, key=lambda x: (x['tbl'], x['cptmonth']))
    
    elif query_key == 'market':
        if 'stage' not in data or 'ref' not in data:
            return []
        
        stage_data = filter_by_month(data['stage'], params[0])  # CURR
        ref_data = filter_by_month(data['ref'], params[1])  # M1
        ref_data_m2 = filter_by_month(data['ref'], params[2])  # M2
        
        # Count by market
        def count_by_market(rows):
            counts = defaultdict(int)
            for row in rows:
                market = row.get('market', '')
                if market:
                    counts[market] += 1
            return counts
        
        curr_counts = count_by_market(stage_data)
        m1_counts = count_by_market(ref_data)
        m2_counts = count_by_market(ref_data_m2)
        
        # Get all markets
        all_markets = set(curr_counts.keys()) | set(m1_counts.keys()) | set(m2_counts.keys())
        
        result = []
        for market in sorted(all_markets):
            curr_cnt = curr_counts.get(market, 0)
            m1_cnt = m1_counts.get(market, 0)
            m2_cnt = m2_counts.get(market, 0)
            
            var_curr_m1 = round(((curr_cnt - m1_cnt) / m1_cnt * 100), 2) if m1_cnt > 0 else None
            var_m1_m2 = round(((m1_cnt - m2_cnt) / m2_cnt * 100), 2) if m2_cnt > 0 else None
            
            result.append({
                'market': market,
                'curr_cnt': curr_cnt,
                'm1_cnt': m1_cnt,
                'm2_cnt': m2_cnt,
                'var_curr_m1': var_curr_m1,
                'var_m1_m2': var_m1_m2
            })
        
        return sorted(result, key=lambda x: x['market'])
    
    elif query_key == 'movement':
        if 'stage' not in data or 'ref' not in data:
            return []
        
        stage_data = filter_by_month(data['stage'], params[1])  # CURR
        ref_data = filter_by_month(data['ref'], params[0])  # M1
        
        stage_ids = set(row.get('agg_unique_id', '') for row in stage_data)
        ref_ids = set(row.get('agg_unique_id', '') for row in ref_data)
        
        lost = ref_ids - stage_ids
        new = stage_ids - ref_ids
        
        return [
            {'category': f'Lost from {h1} (not in {h0} stage)', 'carrier_count': len(lost)},
            {'category': f'New in {h0} (not in {h1} ref)', 'carrier_count': len(new)}
        ]
    
    elif query_key == 'trgdist':
        if 'stage' not in data:
            return []
        
        stage_data = filter_by_month(data['stage'], params[0])  # CURR
        
        # Count by year and flag
        year_flag_counts = defaultdict(lambda: defaultdict(set))
        for row in stage_data:
            year = row.get('projecteddate', '')
            flag = row.get(trgprjd, 'null')
            if year:
                year_flag_counts[year][flag].add(row.get('agg_unique_id', ''))
        
        result = []
        for year in sorted(year_flag_counts.keys()):
            for flag in ['y', 'n', 'null']:
                carriers = year_flag_counts[year].get(flag, set())
                result.append({
                    'projecteddate': year,
                    'flag': flag,
                    'carriers': len(carriers)
                })
        
        return sorted(result, key=lambda x: (x['projecteddate'], x['flag']))
    
    elif query_key == 'cec':
        if 'stage' not in data or 'ref' not in data:
            return []
        
        stage_data = filter_by_month(data['stage'], params[0])  # CURR
        ref_data = filter_by_month(data['ref'], params[1])  # M1
        
        # Count by CEC
        def count_by_cec(rows):
            counts = defaultdict(set)
            for row in rows:
                cec = row.get('cec_curr', '-') or '-'
                counts[cec].add(row.get('agg_unique_id', ''))
            return {k: len(v) for k, v in counts.items()}
        
        stage_counts = count_by_cec(stage_data)
        ref_counts = count_by_cec(ref_data)
        
        all_cec = set(stage_counts.keys()) | set(ref_counts.keys())
        
        result = []
        for cec in sorted(all_cec):
            stage_cnt = stage_counts.get(cec, 0)
            ref_cnt = ref_counts.get(cec, 0)
            
            result.append({
                'cec_curr': cec,
                'm1_count': ref_cnt,
                'curr_count': stage_cnt,
                'delta': stage_cnt - ref_cnt
            })
        
        return sorted(result, key=lambda x: x['cec_curr'])
    
    elif query_key == 'rehome':
        if 'rehome' not in data:
            return []
        
        # Deduplicate rehome mappings
        seen = set()
        unique_rehome = []
        for row in data['rehome']:
            old_mkt = row.get('old_market', '') or ''
            new_mkt = row.get('new_market', '') or ''
            if old_mkt.strip() and new_mkt.strip():
                key = (old_mkt, new_mkt)
                if key not in seen:
                    seen.add(key)
                    unique_rehome.append({'old_market': old_mkt, 'new_market': new_mkt})
        
        return unique_rehome
    
    elif query_key == 'dq':
        if 'stage' not in data:
            return [{}]
        
        stage_data = filter_by_month(data['stage'], params[0])  # CURR
        
        total_rows = len(stage_data)
        unique_carriers = set(row.get('agg_unique_id', '') for row in stage_data)
        
        null_counts = {
            'null_agg_id': sum(1 for row in stage_data if not row.get('agg_unique_id', '')),
            'null_market': sum(1 for row in stage_data if not row.get('market', '')),
            'null_bandgrp': sum(1 for row in stage_data if not row.get('bandgrp', '')),
            'null_vendor': sum(1 for row in stage_data if not row.get('vendor', '')),
            'null_projdate': sum(1 for row in stage_data if not row.get('projecteddate', '')),
            'null_trgprjd': sum(1 for row in stage_data if not row.get(trgprjd, '')),
            'null_cec_curr': sum(1 for row in stage_data if not row.get('cec_curr', '')),
            'null_cec_prjd': sum(1 for row in stage_data if not row.get('cec_prjd', ''))
        }
        
        return [{
            'total_rows': total_rows,
            'total_carriers': len(unique_carriers),
            **null_counts
        }]
    
    elif query_key == 'market_band_carrier_change':
        if 'stage' not in data or 'ref' not in data:
            return []
        
        stage_data = filter_by_month(data['stage'], params[1])  # CURR
        ref_data = filter_by_month(data['ref'], params[0])  # M1
        
        # Count by market/band
        def count_by_market_band(rows):
            counts = defaultdict(set)
            for row in rows:
                key = (row.get('market', ''), row.get('bandgrp', ''))
                if key[0] and key[1]:
                    counts[key].add(row.get('agg_unique_id', ''))
            return {k: len(v) for k, v in counts.items()}
        
        curr_counts = count_by_market_band(stage_data)
        prev_counts = count_by_market_band(ref_data)
        
        # Get all combinations
        all_combos = set(curr_counts.keys()) | set(prev_counts.keys())
        
        result = []
        for market, bandgrp in sorted(all_combos):
            prev_count = prev_counts.get((market, bandgrp), 0)
            curr_count = curr_counts.get((market, bandgrp), 0)
            
            if prev_count > 0:
                pct_diff = round(((curr_count - prev_count) / prev_count * 100), 2)
                flag = 'Decrease >5%' if pct_diff < -5 else 'Acceptable'
            else:
                pct_diff = None
                flag = 'Acceptable'
            
            result.append({
                'market': market,
                'bandgrp': bandgrp,
                'prev_count': prev_count,
                'curr_count': curr_count,
                'pct_diff': pct_diff,
                'flag': flag
            })
        
        return result
    
    elif query_key == 'trgcurr_market_band':
        if 'stage' not in data:
            return []
        
        stage_data = filter_by_month(data['stage'], params[0])  # CURR
        
        if not stage_data:
            print(f"    [WARN] No stage data found for date {params[0]}")
            return []
        
        # Count by market/band/flag
        counts = defaultdict(lambda: defaultdict(set))
        for row in stage_data:
            key = (row.get('market', ''), row.get('bandgrp', ''))
            flag = row.get(trgcurr, 'null') or 'null'
            if key[0] and key[1]:
                counts[key][flag].add(row.get('agg_unique_id', ''))
        
        result = []
        for (market, bandgrp), flag_counts in sorted(counts.items()):
            for flag, carriers in flag_counts.items():
                result.append({
                    'market': market,
                    'bandgrp': bandgrp,
                    'trgcurr_flag': flag,
                    'carriers': len(carriers)
                })
        
        return sorted(result, key=lambda x: (x['market'], x['bandgrp'], -x['carriers']))
    
    # Simplified versions for complex queries
    elif query_key in ['bandvend', 'bss_curr', 'lost_by_band']:
        # Return empty for these complex queries in CSV mode for now
        # These would require more complex logic to implement fully
        print(f"    [WARN] {query_key} not fully implemented in CSV mode, returning empty")
        return []
    
    return []