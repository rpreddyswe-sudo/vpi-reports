# VPI UL Monthly Report Generator

## Overview

This project is a Python-based reporting tool that generates monthly HTML reports for Verizon's VPI UL (Uplink) staging analysis. The tool compares current month staging data against previous month reference data to identify trends, anomalies, and data quality issues in carrier telecommunications data for uplink deployments.

## Purpose

The report generator provides:
- **Data Quality Monitoring**: Validates key columns for null values and completeness
- **Volume Trend Analysis**: Tracks carrier counts and row counts across months
- **Market Movement Tracking**: Identifies market-level changes and rehome activities
- **Band/Vendor Analysis**: Monitors carrier distribution across frequency bands and vendors
- **Carrier Movement Analysis**: Tracks new and lost carriers between snapshots
- **Executive Insights**: Summarizes key findings and action items

## Key Features

- **Automated Date Handling**: Defaults to first day of previous month, supports custom dates
- **Multi-Month Comparison**: Compares current month (M0) with M-1 and M-2 reference periods
- **Intelligent Flagging**: Automatically flags significant changes (>5% decreases, >10% market declines)
- **Rehome Detection**: Identifies expected volume changes due to market rehomes
- **Interactive HTML Output**: Generates styled, responsive HTML reports with collapsible sections
- **Data Quality Checks**: Comprehensive null checks on all critical columns
- **UL-Specific Logic**: Handles UL-specific fields like `trgprjd_ul` and expected null `cec_prjd`

## Project Structure

```
/Users/raygapu/VZ/27533/UL/
├── vpi_ul_monthly_report.py    # Main Python script
└── vpi_ul_report_Month_YYYY.html  # Generated HTML reports
```

## Database Connection

The tool connects to a PostgreSQL database:
- **Database**: `fuzenppprod`
- **Schema**: `vpi`
- **Stage Table**: `vpi.vpi_data_n5l_waiv_stage_ul`
- **Reference Table**: `vpi.vpi_data_n5l_ul`
- **Rehome Table**: `vpi_temp.rehome_market_info`

## Key Differences from DL Report

The UL report differs from the DL report in several important ways:

1. **Table Names**: Uses `_ul` suffix for all tables
2. **Target Flag**: Uses `trgprjd_ul` instead of `trgprjd`
3. **CEC Fields**: `cec_prjd` is expected to be null for UL (not populated)
4. **Market Decline Threshold**: Uses 5% threshold for unexplained market declines in lost_by_band analysis
5. **MMW Focus**: Hardcoded highlighting of MMW band in lost carrier analysis
6. **Insight Messages**: UL-specific messaging for MMW pipeline issues

## Output

The script generates an HTML report file named `vpi_ul_report_Month_YYYY.html` in the same directory as the script. The report includes:
- Executive summary with action items
- KPI cards showing key metrics
- Detailed tables for each analysis section
- Color-coded insights and flags
- Responsive design for viewing in browsers

## Dependencies

- Python 3.x
- `psycopg2` - PostgreSQL database adapter
- `python-dateutil` - Date manipulation utilities

## Quick Start

```bash
# Run with default date (first day of previous month)
python vpi_ul_monthly_report.py

# Run with specific snapshot date
python vpi_ul_monthly_report.py 2026-05-01
```

## Report Sections

The generated report includes the following sections:
- **A1**: Data Availability & Volume Trend
- **A2**: Market Volume: 3-Month Trend
- **A3**: trgprjd_ul='y' Band/Vendor by Projected Year
- **A4**: BSS cec_curr Band/Vendor
- **A6**: Net Carrier Movement
- **A6b**: Lost Carriers by BandGrp (Unexplained Markets)
- **A7**: trgprjd_ul Flag Distribution by Projected Year
- **A8**: cec_curr Distribution
- **A9**: Data Quality

See [REPORT_SECTIONS.md](REPORT_SECTIONS.md) for detailed documentation of each section.

## UL-Specific Considerations

### Target Flag Field
- Uses `trgprjd_ul` instead of `trgprjd`
- Same logic for flagging carriers with UL projected targets

### CEC Fields
- `cec_curr`: Populated and analyzed (BSS/NOT BSS classification)
- `cec_prjd`: Expected to be 100% null for UL tables
- Data quality checks account for this expected null

### MMW Band Analysis
- Lost carrier analysis specifically highlights MMW (Millimeter Wave) band
- Hardcoded logic to identify MMW-dominated losses
- Specific insight messaging for MMW pipeline issues

### Market Decline Thresholds
- Lost_by_band analysis uses 5% threshold (vs 10% in some DL analyses)
- Focus on identifying MMW-specific carrier drops

## Security Notes

- Database credentials are embedded in the script (production read-only access)
- Connection string uses SSL-secured AWS RDS endpoint
- Read-only database access prevents data modification
