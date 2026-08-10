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
python vpi_dl_monthly_report.py
```

**Example Output**:
```
Snapshot : 2026-07-01  |  Ref M-1 : 2026-06-01  |  Ref M-2 : 2026-05-01
Output   : /Users/raygapu/VZ/27533/DL/vpi_dl_report_Jul_2026.html

  [ok] avail — 3 rows
  [ok] market — 206 rows
  [ok] bandvend — 145 rows
  [ok] bss_curr — 18 rows
  [ok] movement — 2 rows
  [ok] trgdist — 10 rows
  [ok] cec — 4 rows
  [ok] rehome — 3 rows
  [ok] lost_by_band — 6 rows
  [ok] dq — 1 rows

Report written: /Users/raygapu/VZ/27533/DL/vpi_dl_report_Jul_2026.html
```

### Custom Date Execution

Specify a custom snapshot date as the first argument:

```bash
python vpi_dl_monthly_report.py 2026-05-01
```

**Date Format**: YYYY-MM-DD (must be first day of month)

**Example Output**:
```
Snapshot : 2026-05-01  |  Ref M-1 : 2026-04-01  |  Ref M-2 : 2026-03-01
Output   : /Users/raygapu/VZ/27533/DL/vpi_dl_report_May_2026.html
```

## Command-Line Arguments

| Argument | Required | Description | Format |
|----------|----------|-------------|--------|
| `snapshot_date` | No | Custom snapshot date | YYYY-MM-DD |

## Output Files

### File Naming Convention

Output files follow the pattern: `vpi_dl_report_Month_YYYY.html`

- **Month**: Three-letter abbreviation (Jan, Feb, Mar, etc.)
- **YYYY**: Four-digit year
- **Location**: Same directory as the script

### Examples

| Command | Output File |
|---------|--------------|
| `python vpi_dl_monthly_report.py` (run in Aug 2026) | `vpi_dl_report_Jul_2026.html` |
| `python vpi_dl_monthly_report.py 2026-05-01` | `vpi_dl_report_May_2026.html` |
| `python vpi_dl_monthly_report.py 2026-12-01` | `vpi_dl_report_Dec_2026.html` |

## Viewing the Report

### Open in Browser

```bash
# macOS
open vpi_dl_report_Jul_2026.html

# Linux
xdg-open vpi_dl_report_Jul_2026.html

# Windows
start vpi_dl_report_Jul_2026.html
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

## Common Use Cases

### Monthly Monitoring

Run on the first business day of each month to review previous month's data:

```bash
# Run on August 1st to review July data
python vpi_dl_monthly_report.py
```

### Historical Analysis

Generate reports for specific historical months:

```bash
# Analyze May 2026 data
python vpi_dl_monthly_report.py 2026-05-01

# Analyze December 2025 data
python vpi_dl_monthly_report.py 2025-12-01
```

### Data Quality Validation

Quick check of data quality for a specific month:

```bash
python vpi_dl_monthly_report.py 2026-07-01
# Then check Section A9 for data quality status
```

### Investigation

When anomalies are detected, generate report to investigate:

```bash
# Generate report for the month in question
python vpi_dl_monthly_report.py 2026-07-01

# Review:
# - Executive Summary for action items
# - A2 for market-level changes
# - A3 for band/vendor issues
# - A6b for lost carrier analysis
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
python vpi_dl_monthly_report.py 2026-07-01

# Incorrect
python vpi_dl_monthly_report.py 2026/07/01
python vpi_dl_monthly_report.py 07-01-2026
```

### Missing Dependencies

**Error**: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**: Install required packages

```bash
pip install psycopg2-binary python-dateutil
```

### Query Failures

**Error**: `[ERR] market: relation "vpi.vpi_data_n5l_waiv_stage" does not exist`

**Solutions**:
1. Verify table names in configuration section
2. Check database schema permissions
3. Ensure tables exist for the specified month

### Empty Report

**Symptom**: Report generates but shows no data

**Solutions**:
1. Verify data exists for the specified month
2. Check `cptmonth` values in database
3. Review query execution logs in console output

## Automation

### Cron Job (Linux/macOS)

Add to crontab for automated monthly execution:

```bash
# Edit crontab
crontab -e

# Add entry (runs on 2nd day of each month at 9 AM)
0 9 2 * * cd /Users/raygapu/VZ/27533/DL && python vpi_dl_monthly_report.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to monthly on day 2
4. Action: Start a program
5. Program: `python.exe`
6. Arguments: `C:\path\to\vpi_dl_monthly_report.py`
7. Start in: `C:\path\to\DL\`

### Shell Script Wrapper

Create `run_report.sh`:

```bash
#!/bin/bash
cd /Users/raygapu/VZ/27533/DL
DATE=${1:-$(date -d "last month" +%Y-%m-01)}
python vpi_dl_monthly_report.py $DATE
echo "Report generated for $DATE"
```

Usage:
```bash
./run_report.sh              # Previous month
./run_report.sh 2026-05-01   # Specific date
```

## Configuration

### Modifying Database Connection

Edit lines 17-21 in `vpi_dl_monthly_report.py`:

```python
CONN  = "postgresql://user:password@host:port/database"
STAGE = "vpi.vpi_data_n5l_waiv_stage"
REF   = "vpi.vpi_data_n5l"
TRGPRJD = "trgprjd"
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

### Custom Styling

Edit CSS variables (lines 538-539):

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
4. **Track Trends**: Compare month-over-month changes
5. **Archive Reports**: Keep historical reports for trend analysis
6. **Monitor Data Quality**: Check Section A9 for null values
7. **Validate Rehomes**: Confirm rehome mappings are current

## Support

For issues or questions:
1. Check this documentation
2. Review error messages in console output
3. Verify database connectivity
4. Check data availability in source tables
5. Contact database administrator if needed
