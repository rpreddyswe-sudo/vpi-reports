# VPI DL Monthly Report Generator

## Overview

This project is a Python-based reporting tool that generates monthly HTML reports for Verizon's VPI DL (Data Layer) staging analysis. The tool compares current month staging data against previous month reference data to identify trends, anomalies, and data quality issues in carrier telecommunications data.

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

## Project Structure

```
/Users/raygapu/VZ/27533/DL/
├── vpi_dl_monthly_report.py    # Main Python script
└── vpi_dl_report_Month_YYYY.html  # Generated HTML reports
```

## Database Connection

The tool connects to a PostgreSQL database:
- **Database**: `fuzenppprod`
- **Schema**: `vpi`
- **Stage Table**: `vpi.vpi_data_n5l_waiv_stage`
- **Reference Table**: `vpi.vpi_data_n5l`
- **Rehome Table**: `vpi_temp.rehome_market_info`

## Output

The script generates an HTML report file named `vpi_dl_report_Month_YYYY.html` in the same directory as the script. The report includes:
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
python vpi_dl_monthly_report.py

# Run with specific snapshot date
python vpi_dl_monthly_report.py 2026-05-01
```

## Report Sections

The generated report includes the following sections:
- **A1**: Data Availability & Volume Trend
- **A2**: Market Volume: 3-Month Trend
- **A3**: trgprjd='y' Band/Vendor by Projected Year
- **A4**: BSS cec_curr Band/Vendor
- **A6**: Net Carrier Movement
- **A6b**: Lost Carriers by BandGrp (Unexplained Markets)
- **A7**: trgprjd Flag Distribution by Projected Year
- **A8**: cec_curr Distribution
- **A9**: Data Quality

See [REPORT_SECTIONS.md](REPORT_SECTIONS.md) for detailed documentation of each section.

## Security Notes

- Database credentials are embedded in the script (production read-only access)
- Connection string uses SSL-secured AWS RDS endpoint
- Read-only database access prevents data modification
