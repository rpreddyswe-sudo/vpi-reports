# Report Sections Documentation

## Overview

The VPI DL Monthly Report generates a comprehensive HTML report with 9 main analysis sections (A1-A9) plus an Executive Summary. Each section provides specific insights into data quality, trends, and anomalies in the carrier telecommunications data.

## Section A1: Data Availability & Volume Trend

**Purpose**: Sanity check for data availability and overall volume trends

**Badge**: `Sanity Check` (blue informational)

**Key Metrics**:
- Total rows per table
- Distinct carrier counts per table
- Month-over-month comparison

**Tables Displayed**:
- Stage table (current month)
- Reference table (M-1, M-2)

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi.vpi_data_n5l` (historical)

**Insights Provided**:
- Data availability for current and historical months
- Overall volume growth/decline trends
- Row count vs carrier count ratios

**Typical Use Cases**:
- Verify data loaded successfully for current month
- Check historical data availability
- Identify major volume changes

**Example Output**:
```
Table                    | Month       | Total Rows | Distinct Carriers
-------------------------|-------------|-------------|------------------
vpi.vpi_data_n5l         | 2026-05-01  | 5,915,505   | 1,183,098
vpi.vpi_data_n5l         | 2026-06-01  | 5,967,830   | 1,193,565
vpi.vpi_data_n5l_waiv_stage | 2026-07-01 | 6,004,665   | 1,200,902
```

---

## Section A2: Market Volume: 3-Month Trend

**Purpose**: Analyze market-level volume changes and identify anomalies

**Badges**:
- `X Unexplained >-10%` (red - critical)
- `Y Confirmed Rehome` (green - acceptable)

**Key Metrics**:
- Row counts per market
- Current month (M0) vs M-1 percentage change
- M-1 vs M-2 percentage change

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi.vpi_data_n5l` (M-1, M-2)
- `vpi_temp.rehome_market_info` (rehome mappings)

**Insights Provided**:
- **Confirmed Rehome Markets**: Source → destination mappings with expected volume changes
- **Unexplained Declines**: Markets with >10% decline not due to rehome
- **Notable Gains**: Markets with >10% growth

**Thresholds**:
- >10% decline: Flagged as unexplained (if not rehome)
- >10% growth: Highlighted as notable gain
- Rehome markets: Expected volume changes

**Color Coding**:
- Red: Negative percentage changes
- Green: Positive percentage changes
- Orange: Moderate negative changes (-5% to -10%)

**Typical Use Cases**:
- Identify markets requiring investigation
- Validate rehome activities
- Track market growth patterns

**Example Insights**:
```
Confirmed Rehome Markets (source -> destination):
• Mkt 36 → Mkt 39 (rehome): -5.56% (53,015 → 50,065)
• Mkt 43 → Mkt 5 (rehome): -0.86% (18,055 → 17,900)

Unexplained Declines >-10% — Investigate:
• Mkt 236: -15.2% (9,090 → 7,710) — investigate

Notable Gains (Jul 2026 vs Jun 2026 >+10%):
• Mkt 236: +49.39% (9,090 → 13,580)
• Mkt 39 ← rehome from Mkt 36: +32.51% (8,120 → 10,760)
```

---

## Section A3: trgprjd='y' Band/Vendor by Projected Year

**Purpose**: Monitor carriers with target project flag across projection years

**Badge**: `X Combo(s) Flagged Across All Years` (red - critical)

**Key Metrics**:
- Carrier counts by band, vendor, and projected year
- Percentage change from M-1 to current
- Flag for >5% decreases

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi.vpi_data_n5l` (M-1)
- Filter: `trgprjd='y'` and `projecteddate BETWEEN 2026 AND 2030`

**Projected Years**: 2026, 2027, 2028, 2029, 2030

**Insights Provided**:
- Band/vendor combinations with consistent decreases across all years
- Year-by-year breakdown of carrier counts
- Flagged combinations requiring investigation

**Thresholds**:
- >5% decrease: Flagged as "Decrease >5%"
- Consistent across all years: Listed in critical insight

**Color Coding**:
- Red background: Flagged rows
- Red text: Negative percentages
- Green text: Positive percentages

**Typical Use Cases**:
- Identify band/vendor combinations with systematic issues
- Validate target project carrier counts
- Monitor year-based projection trends

**Example Insights**:
```
Consistently flagged across all projection years:
• SUB1-13/NOK: -14.31% across all proj years
• SUB1-5/NOK: -14.29% across all proj years
• SUB3/NOK: -13.95% across all proj years
```

---

## Section A4: BSS cec_curr Band/Vendor

**Purpose**: Analyze BSS (Base Station Subsystem) carriers by band and vendor

**Badge**: `X Flag(s)` (yellow - warning if >0, green if 0)

**Key Metrics**:
- BSS carrier counts by band and vendor
- Percentage change from M-1 to current
- Flag for >5% decreases

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi.vpi_data_n5l` (M-1)
- Filter: `cec_curr='BSS'`

**Insights Provided**:
- BSS carrier distribution across bands/vendors
- Significant decreases in BSS carriers
- Vendor-specific BSS trends

**Thresholds**:
- >5% decrease: Flagged as requiring attention

**Color Coding**:
- Red background: Flagged rows
- Red text: Negative percentages
- Green text: Positive percentages

**Typical Use Cases**:
- Monitor BSS equipment changes
- Validate vendor BSS deployments
- Track BSS carrier movement

**Example Output**:
```
BandGrp | Vendor | Jun 2026 (Prev) | Jul 2026 (Curr) | Pct Diff | Flag
--------|--------|-----------------|-----------------|----------|--------
MB      | ERC    | 241             | 276             | +14.52%  | ✓ Acceptable
MB      | SAM    | 132             | 74              | -43.94%  | ⚠ Decrease >5%
SUB1-13 | NOK    | 322             | 263             | -18.32%  | ⚠ Decrease >5%
```

---

## Section A6: Net Carrier Movement

**Purpose**: Track carrier additions and removals between months

**Badge**: `Net +X` or `Net -X` (yellow - warning, red - critical if <-20,000)

**Key Metrics**:
- Lost carriers (in M-1, not in current)
- New carriers (in current, not in M-1)
- Net change

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi.vpi_data_n5l` (M-1)

**Calculation Method**:
- Lost: `agg_unique_id` in M-1 but not in current
- New: `agg_unique_id` in current but not in M-1
- Net: New - Lost

**Insights Provided**:
- Overall carrier churn rate
- Net growth/decline
- Balance of additions vs removals

**Thresholds**:
- Net change <-20,000: Critical flag
- Net change >0: Green (growth)
- Net change <0: Red (decline)

**Color Coding**:
- Red: Lost carriers, negative net change
- Green: New carriers, positive net change

**Typical Use Cases**:
- Monitor overall carrier portfolio health
- Identify abnormal churn
- Validate data completeness

**Example Output**:
```
Category                              | Carrier Count
--------------------------------------|--------------
Lost from Jun 2026 (not in Jul 2026)  | 6,876
New in Jul 2026 (not in Jun 2026)     | 14,213
Net Change                            | +7,337
```

---

## Section A6b: Lost Carriers by BandGrp (Unexplained Markets Only)

**Purpose**: Analyze band group distribution of lost carriers from unexplained declining markets

**Badge**: `BAND_NAME X% of Loss` (red - critical)

**Key Metrics**:
- Lost carriers per band group
- Percentage of total lost carriers
- Visual bar chart

**Data Sources**:
- `vpi.vpi_data_n5l` (M-1)
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi_temp.rehome_market_info` (to exclude rehome markets)

**Filter Criteria**:
- Markets with >5% decline
- Not in rehome mappings
- Lost carriers (in M-1, not in current)

**Insights Provided**:
- Which band groups are most affected by losses
- Top contributing band to investigate
- Visual representation of distribution

**Thresholds**:
- Top band highlighted in red
- Percentage calculated of total lost carriers

**Color Coding**:
- Red background: Top contributing band
- Red text: Top band count and percentage
- Blue bars: Visual representation

**Typical Use Cases**:
- Identify band-specific pipeline issues
- Prioritize investigation by band
- Understand loss distribution

**Example Output**:
```
BandGrp | Lost Carriers | % of Total | Visual
--------|---------------|------------|--------
SUB1-5  | 8             | 25.8%      | ████████████
MB      | 6             | 19.4%      | ████████
MMW     | 6             | 19.4%      | ████████
SUB3    | 6             | 19.4%      | ████████
```

---

## Section A7: trgprjd Flag Distribution by Projected Year

**Purpose**: Analyze distribution of target flag across projected years

**Badge**: `Stable` (green - informational)

**Key Metrics**:
- Carrier counts by projected year and flag
- Percentage of year total
- Flag distribution ('y' vs 'n')

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)

**Projected Years**: 2026, 2027, 2028, 2029, 2030

**Insights Provided**:
- Year-over-year target flag trends
- Percentage of targeted carriers per year
- Overall target flag distribution

**Color Coding**:
- Green text: 'y' flag values
- Normal text: 'n' flag values
- Bold: 'y' flag indicators

**Typical Use Cases**:
- Monitor target project progression
- Validate year-based target allocation
- Track target flag adoption

**Example Output**:
```
Projected Year | Flag | Carriers | % of Year Total
---------------|------|----------|----------------
2026           | n    | 1,141,430| 95.1%
2026           | y    | 59,295   | 4.9%
2027           | n    | 1,123,739| 93.6%
2027           | y    | 76,987   | 6.4%
```

---

## Section A8: cec_curr Distribution

**Purpose**: Analyze CEC (Current Equipment Classification) distribution changes

**Badge**: `BSS +/-X` (blue - informational)

**Key Metrics**:
- Carrier counts by CEC classification
- Delta between current and M-1
- BSS vs NOT BSS movement

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)
- `vpi.vpi_data_n5l` (M-1)

**CEC Classifications**:
- BSS: Base Station Subsystem
- NOT BSS: Non-BSS equipment
- NONE: No classification
- -: Missing/unknown

**Insights Provided**:
- Overall CEC distribution changes
- BSS-specific carrier movement
- Classification trend analysis

**Color Coding**:
- Green text: Positive deltas
- Red text: Negative deltas
- Bold: Total row

**Typical Use Cases**:
- Monitor CEC classification changes
- Validate BSS equipment trends
- Track classification completeness

**Example Output**:
```
cec_curr | Jun 2026 Count | Jul 2026 Count | Delta
---------|----------------|----------------|-------
BSS      | 6,067          | 5,763          | -304
NOT BSS  | 1,187,328      | 1,194,944      | +7,616
NONE     | 166            | 184            | +18
-        | 9              | 12             | +3
Total    | 1,193,570      | 1,200,903      | +7,333
```

---

## Section A9: Data Quality

**Purpose**: Validate data quality through null checks on key columns

**Badge**: `Clean` (green) or `Issues Found` (red)

**Key Metrics**:
- Total rows
- Total distinct carriers
- Null counts for each key column

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage` (current)

**Columns Checked**:
- `agg_unique_id`
- `market`
- `bandgrp`
- `vendor`
- `projecteddate`
- `trgprjd`
- `cec_curr`
- `cec_prjd`

**Insights Provided**:
- Overall data completeness
- Specific columns with null values
- Data quality status

**Thresholds**:
- 0 nulls: "Clean" status
- Any nulls: "Issues Found" status

**Color Coding**:
- Green checkmark: Clean columns
- Red warning: Columns with nulls
- Green badge: Overall clean status
- Red badge: Overall issues found

**Typical Use Cases**:
- Validate data loading completeness
- Identify data quality issues
- Monitor ETL process health

**Example Output**:
```
Metric                  | Value     | Status
-------------------------|-----------|--------
Total Rows               | 6,004,665 |
Total Distinct Carriers  | 1,200,902 |
Null agg_unique_id       | 0         | ✓ Clean
Null market              | 0         | ✓ Clean
Null bandgrp             | 0         | ✓ Clean
Null vendor              | 0         | ✓ Clean
```

---

## Executive Summary

**Purpose**: Consolidate key findings and action items

**Location**: Bottom of report, after all analysis sections

**Components**:

### 1. Action Required - Band/Vendor Flags
- Lists band/vendor combinations with consistent decreases across all projection years
- Requires investigation before publishing
- Based on Section A3 findings

### 2. Confirmed Rehome
- Lists all market rehome mappings
- Explains expected volume changes
- Based on Section A2 findings

### 3. Monitor - Unexplained Market Declines
- Count of markets with >10% unexplained declines
- Top band group for lost carriers
- Net carrier movement summary
- Based on Sections A2 and A6b findings

### 4. Monitor - BSS cec_curr
- Count of flagged BSS band/vendor combinations
- Based on Section A4 findings

### 5. Data Quality
- Overall data quality status
- Null check summary
- Based on Section A9 findings

**Color Coding**:
- Red background: Critical action items
- Yellow background: Monitoring items
- Green background: Positive status

**Typical Use Cases**:
- Quick review of report findings
- Prioritize investigation items
- Communicate status to stakeholders

---

## KPI Cards

**Purpose**: Provide at-a-glance summary of key metrics

**Location**: Top of report, below header

**Cards Displayed**:

1. **Current Month Stage Carriers**
   - Value: Carrier count for current month
   - Delta: Net change vs M-1
   - Color: Green if positive, red if negative

2. **M-1 Ref Carriers**
   - Value: Carrier count for reference month
   - Delta: Baseline indicator
   - Color: Neutral

3. **New in Current Month**
   - Value: New carriers not in M-1
   - Delta: "not in M-1 ref"
   - Color: Green

4. **Lost from M-1**
   - Value: Lost carriers not in current
   - Delta: "not in current stage"
   - Color: Red

5. **Current Month Total Rows**
   - Value: Total row count
   - Delta: Percentage change vs M-1
   - Color: Green if positive, red if negative

6. **Data Quality**
   - Value: "Clean" or "Issues Found"
   - Delta: Null count summary
   - Color: Green if clean, red if issues

**Layout**: Responsive grid (auto-fit, min 175px per card)

**Typical Use Cases**:
- Quick status check
- Identify major changes
- Prioritize report review

---

## Color Legend

| Color | Meaning | Usage |
|-------|---------|-------|
| Green | Positive, acceptable, clean | Growth, clean data, acceptable values |
| Red | Negative, critical, issues | Declines, flags, null values, critical issues |
| Yellow | Warning, monitor | Moderate declines, monitoring items |
| Blue | Informational | Neutral information, badges |
| Orange | Moderate negative | -5% to -10% changes |

---

## Badge Types

| Badge | Color | Meaning |
|-------|-------|---------|
| `Sanity Check` | Blue | Informational section |
| `X Unexplained >-10%` | Red | Critical market declines |
| `Y Confirmed Rehome` | Green | Expected volume changes |
| `X Combo(s) Flagged` | Red | Critical band/vendor issues |
| `X Flag(s)` | Yellow/Red | Warnings or critical flags |
| `Net +/-X` | Yellow/Red | Carrier movement status |
| `BAND X% of Loss` | Red | Top contributing band |
| `Stable` | Green | Normal distribution |
| `BSS +/-X` | Blue | CEC classification change |
| `Clean` / `Issues Found` | Green/Red | Data quality status |

---

## Report Navigation

### Recommended Review Order

1. **Executive Summary** (bottom) - Quick overview of action items
2. **KPI Cards** (top) - High-level metrics
3. **A9 - Data Quality** - Validate data completeness
4. **A2 - Market Volume** - Identify market-level issues
5. **A3 - Band/Vendor** - Check band/vendor anomalies
6. **A6/A6b - Carrier Movement** - Understand carrier churn
7. **A4 - BSS** - Validate BSS-specific changes
8. **A7/A8 - Distributions** - Review flag/CEC trends
9. **A1 - Availability** - Confirm data loaded

### Collapsible Sections

- **A2 Market Table**: Click "Show full market table" to expand
- Collapsed by default to reduce visual clutter
- Shows all markets with detailed metrics

### Interactive Features

- Hover effects on table rows
- Clickable summary elements
- Responsive design for different screen sizes
