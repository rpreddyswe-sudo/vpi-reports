# Usage Guide

## Prerequisites

### Required Software

- **Python**: 3.6 or higher
- **PostgreSQL Client**: For database connectivity
- **Python Packages**:
  - `psycopg2-binary` (or `psycopg2`)
  - `python-dateutil`

### Installation

```bash
# Install required packages
pip install psycopg2-binary python-dateutil

# Or using requirements.txt (if available)
pip install -r requirements.txt
```

### Database Access

- Must have network access to AWS RDS endpoint
- Database credentials are embedded in the script (production environment)
- Read-only access only (no data modification)

## Basic Usage

### Default Execution (Previous Month)

Run the script without arguments to generate a report for the first day of the previous month:

```bash
python vpi_ul_monthly_report.py
```

**Example Output**:
```
Snapshot : 2026-07-01  |  Ref M-1 : 2026-06-01  |  Ref M-2 : 2026-05-01
Output   : /Users/raygapu/VZ/27533/UL/vpi_ul_report_Jul_2026.html

  [ok] avail — 3 rows
  [ok] market — 206 rows
  [ok] bandvend — 45 rows
  [ok] bss_curr — 8 rows
  [ok] movement — 2 rows
  [ok] trgdist — 10 rows
  [ok] cec — 4 rows
  [ok] rehome — 3 rows
  [ok] lost_by_band — 0 rows
  [ok] dq — 1 rows

Report written: /Users/raygapu/VZ/27533/UL/vpi_ul_report_Jul_2026.html
```

### Custom Date Execution

Specify a custom snapshot date as the first argument:

```bash
python vpi_ul_monthly_report.py 2026-05-01
```

**Date Format**: YYYY-MM-DD (must be first day of month)

**Example Output**:
```
Snapshot : 2026-05-01  |  Ref M-1 : 2026-04-01  |  Ref M-2 : 2026-03-01
Output   : /Users/raygapu/VZ/27533/UL/vpi_ul_report_May_2026.html
```

## Command-Line Arguments

| Argument | Required | Description | Format |
|----------|----------|-------------|--------|
| `snapshot_date` | No | Custom snapshot date | YYYY-MM-DD |

## Output Files

### File Naming Convention

Output files follow the pattern: `vpi_ul_report_Month_YYYY.html`

- **Month**: Three-letter abbreviation (Jan, Feb, Mar, etc.)
- **YYYY**: Four-digit year
- **Location**: Same directory as the script

### Examples

| Command | Output File |
|---------|--------------|
| `python vpi_ul_monthly_report.py` (run in Aug 2026) | `vpi_ul_report_Jul_2026.html` |
| `python vpi_ul_monthly_report.py 2026-05-01` | `vpi_ul_report_May_2026.html` |
| `python vpi_ul_monthly_report.py 2026-12-01` | `vpi_ul_report_Dec_2026.html` |

## Viewing the Report

### Open in Browser

```bash
# macOS
open vpi_ul_report_Jul_2026.html

# Linux
xdg-open vpi_ul_report_Jul_2026.html

# Windows
start vpi_ul_report_Jul_2026.html
```

### Report Features

- **Responsive Design**: Adapts to different screen sizes
- **Dark Theme**: Optimized for extended viewing
- **Collapsible Sections**: Click to expand/collapse detailed tables
- **Color Coding**: 
  - Green: Positive changes, acceptable values
  - Red: Negative changes, flags, critical issues
  - Yellow: Warnings
  - Blue: Informational
- **KPI Cards**: Quick summary of key metrics
- **Executive Summary**: Action items and insights at the bottom
- **UL-Specific Insights**: MMW band analysis and UL target flag monitoring

## Common Use Cases

### Monthly Monitoring

Run on the first business day of each month to review previous month's data:

```bash
# Run on August 1st to review July data
python vpi_ul_monthly_report.py
```

### Historical Analysis

Generate reports for specific historical months:

```bash
# Analyze May 2026 data
python vpi_ul_monthly_report.py 2026-05-01

# Analyze December 2025 data
python vpi_ul_monthly_report.py 2025-12-01
```

### Data Quality Validation

Quick check of data quality for a specific month:

```bash
python vpi_ul_monthly_report.py 2026-07-01
# Then check Section A9 for data quality status
# Note: cec_prjd is expected to be null for UL
```

### MMW Band Investigation

When MMW carrier losses are suspected:

```bash
python vpi_ul_monthly_report.py 2026-07-01

# Review:
# - Executive Summary for MMW-specific insights
# - A2 for market-level changes
# - A6b for MMW band analysis (hardcoded MMW highlighting)
# - A3 for UL target flag issues
```

### UL Target Flag Analysis

Monitor UL target flag distribution:

```bash
python vpi_ul_monthly_report.py 2026-07-01

# Review:
# - A3 for trgprjd_ul band/vendor analysis
# - A7 for trgprjd_ul distribution by year
# - Executive Summary for UL-specific action items
```

## Troubleshooting

### Database Connection Issues

**Error**: `could not connect to server`

**Solutions**:
1. Check network connectivity to AWS RDS
2. Verify VPN connection if required
3. Check firewall settings
4. Verify database credentials in script

### Date Format Errors

**Error**: `time data '2026/07/01' does not match format '%Y-%m-%d'`

**Solution**: Use correct date format (YYYY-MM-DD with hyphens)

```bash
# Correct
python vpi_ul_monthly_report.py 2026-07-01

# Incorrect
python vpi_ul_monthly_report.py 2026/07/01
python vpi_ul_monthly_report.py 07-01-2026
```

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**: Install required packages

```bash
pip install psycopg2-binary python-dateutil
```

### Query Failures

**Error**: `[ERR] market: relation "vpi.vpi_data_n5l_waiv_stage_ul" does not exist`

**Solutions**:
1. Verify table names in configuration section
2. Check database schema permissions
3. Ensure tables exist for the specified month
4. Verify `_ul` suffix in table names

### Empty Report

**Symptom**: Report generates but shows no data

**Solutions**:
1. Verify data exists for the specified month
2. Check `cptmonth` values in database
3. Review query execution logs in console output
4. Ensure UL tables are populated

### MMW Band Not Highlighted

**Symptom**: MMW band not showing as highlighted in A6b section

**Solutions**:
1. Verify MMW band exists in data
2. Check lost_by_band query results
3. Ensure market decline threshold (5%) is met
4. Review hardcoded MMW logic in script

## Automation

### Cron Job (Linux/macOS)

Add to crontab for automated monthly execution:

```bash
# Edit crontab
crontab -e

# Add entry (runs on 2nd day of each month at 9 AM)
0 9 2 * * cd /Users/raygapu/VZ/27533/UL && python vpi_ul_monthly_report.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to monthly on day 2
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `C:\path\to\vpi_ul_monthly_report.py`
7. Start in: `C:\path\to\UL\`

### Shell Script Wrapper

Create `run_ul_report.sh`:

```bash
#!/bin/bash
cd /Users/raygapu/VZ/27533/UL
DATE=${1:-$(date -d "last month" +%Y-%m-01)}
python vpi_ul_monthly_report.py $DATE
echo "UL Report generated for $DATE"
```

Usage:
```bash
./run_ul_report.sh              # Previous month
./run_ul_report.sh 2026-05-01   # Specific date
```

## Configuration

### Modifying Database Connection

Edit lines 17-20 in `vpi_ul_monthly_report.py`:

```python
CONN  = "postgresql://user:password@host:port/database"
STAGE = "vpi.vpi_data_n5l_waiv_stage_ul"
REF   = "vpi.vpi_data_n5l_ul"
```

### Changing Thresholds

Edit helper functions (lines 236-260):

```python
def pct_class(v):
    if v is None: return ''
    try:
        f = float(v)
        if f <= -10:  return 'text-red'    # Change threshold
        if f <= -5:   return 'text-orange'  # Change threshold
        if f >= 10:   return 'text-green'  # Change threshold
        if f >= 5:    return 'text-green'   # Change threshold
        return ''
    except: return ''
```

### UL-Specific Configuration

**MMW Band Name**: If MMW band name changes, update hardcoded references:
```python
# Line 454, 456, 460
if r['bandgrp'] == 'MMW'  # Change band name if needed
```

**Lost_by_band Threshold**: Modify 5% threshold in query (line 180):
```sql
AND ROUND(((m0.cnt - m1.cnt)::numeric / NULLIF(m1.cnt,0))*100,2) <= -5
```

**Target Field Name**: If `trgprjd_ul` field name changes:
- Update all query references (lines 82, 89, 140)
- Update data quality check (line 203)
- Update section titles in HTML template

### Custom Styling

Edit CSS variables (lines 524-525):

```python
CSS = """
:root{
    --bg:#0f1117;
    --surface:#1a1d27;
    --accent:#4f8ef7;
    --green:#34d399;
    --red:#f87171;
    # Add custom colors
}
"""
```

## Performance Tips

### Execution Time

Typical execution time: 30-60 seconds
- Database queries: 20-40 seconds
- HTML generation: 5-10 seconds
- File write: <1 second

### Optimizing for Large Datasets

If execution is slow:
1. Ensure database indexes exist on `cptmonth` and `agg_unique_id`
2. Run during off-peak hours
3. Consider limiting date range for historical analysis

### Memory Usage

Typical memory usage: 100-200 MB
- Results stored in memory
- Suitable for standard workstations
- No disk caching required

## Best Practices

1. **Monthly Routine**: Run on the first business day of each month
2. **Review Executive Summary**: Check action items first
3. **Investigate Flags**: Prioritize red-flagged items
4. **Monitor MMW Band**: Pay special attention to MMW carrier losses
5. **Track UL Target Flags**: Monitor trgprjd_ul distribution changes
6. **Validate Rehomes**: Confirm rehome mappings are current
7. **Check Data Quality**: Verify Section A9 (note cec_prjd expected null)
8. **Archive Reports**: Keep historical reports for trend analysis

## UL-Specific Considerations

### cec_prjd Null Handling

- **Expected Behavior**: cec_prjd is 100% null for UL tables
- **Data Quality**: Excluded from null checks
- **Reporting**: Noted as expected null in A9 section
- **Investigation**: No action needed if null

### MMW Band Monitoring

- **Priority**: MMW band is critical for UL deployments
- **Threshold**: 5% market decline triggers analysis
- **Highlighting**: Hardcoded red highlighting in A6b section
- **Insights**: Specific messaging for MMW pipeline issues

### UL Target Flag (trgprjd_ul)

- **Field**: Uses trgprjd_ul instead of trgprjd
- **Analysis**: Monitored across projection years
- **Flagging**: Consistent decreases flagged across all years
- **Action**: Investigate pipeline/classification issues

### Market Decline Thresholds

- **General**: >10% decline flagged in A2
- **Lost_by_band**: >5% decline used for MMW analysis
- **Rehome**: Excluded from unexplained analysis
- **Context**: Different from DL thresholds

## Comparison with DL Usage

| Aspect | DL | UL |
|--------|-----|-----|
| Script Name | `vpi_dl_monthly_report.py` | `vpi_ul_monthly_report.py` |
| Output File | `vpi_dl_report_Month_YYYY.html` | `vpi_ul_report_Month_YYYY.html` |
| Target Flag | trgprjd | trgprjd_ul |
| CEC Field | Both populated | cec_prjd expected null |
| MMW Focus | Dynamic top band | Hardcoded MMW |
| Thresholds | 10% market, 10% lost_by_band | 10% market, 5% lost_by_band |

## Support

For issues or questions:
1. Check this documentation
2. Review error messages in console output
3. Verify database connectivity
4. Check data availability in source tables
5. Contact database administrator if needed
6. Review UL-specific configuration if MMW/trgprjd_ul issues
