# Report Sections Documentation

## Overview

The VPI UL Monthly Report generates a comprehensive HTML report with 9 main analysis sections (A1-A9) plus an Executive Summary. Each section provides specific insights into data quality, trends, and anomalies in the carrier telecommunications data for Uplink (UL) deployments.

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
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi.vpi_data_n5l_ul` (historical)

**Insights Provided**:
- Data availability for current and historical months
- Overall volume growth/decline trends
- Row count vs carrier count ratios

**UL-Specific Notes**:
- Uses `_ul` suffix table names
- Stage table uses exact date match
- Reference table uses IN clause for multiple months

**Typical Use Cases**:
- Verify data loaded successfully for current month
- Check historical data availability
- Identify major volume changes

**Example Output**:
```
Table                          | Month       | Total Rows | Distinct Carriers
-------------------------------|-------------|-------------|------------------
vpi.vpi_data_n5l_ul            | 2026-05-01  | 5,406,490   | 1,081,406
vpi.vpi_data_n5l_ul            | 2026-06-01  | 5,465,470   | 1,093,212
vpi.vpi_data_n5l_waiv_stage_ul| 2026-07-01  | 5,520,550   | 1,104,198
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
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi.vpi_data_n5l_ul` (M-1, M-2)
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

**UL-Specific Notes**:
- Uses `_ul` suffix table names
- Same threshold logic as DL (>10%)
- Rehome detection shared with DL

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
• Mkt 236: +57.10% (7,425 → 11,665)
• Mkt 39 ← rehome from Mkt 36: +22.83% (7,950 → 9,765)
```

---

## Section A3: trgprjd_ul='y' Band/Vendor by Projected Year

**Purpose**: Monitor carriers with UL target project flag across projection years

**Badge**: `X Combo(s) Flagged Across All Years` (red - critical)

**Key Metrics**:
- Carrier counts by band, vendor, and projected year
- Percentage change from M-1 to current
- Flag for >5% decreases

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi.vpi_data_n5l_ul` (M-1)
- Filter: `trgprjd_ul='y'` and `projecteddate BETWEEN 2026 AND 2030`

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

**UL-Specific Notes**:
- Uses `trgprjd_ul` field instead of `trgprjd`
- Same logic as DL A3 but with UL field
- Executive summary mentions UL-specific context

**Typical Use Cases**:
- Identify band/vendor combinations with systematic issues
- Validate UL target project carrier counts
- Monitor year-based projection trends

**Example Insights**:
```
Consistently flagged across all projection years:
• SUB3/SAM: -6.09% across all proj years
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
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi.vpi_data_n5l_ul` (M-1)
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

**UL-Specific Notes**:
- Uses `_ul` suffix table names
- Same logic as DL A4
- cec_curr populated (only cec_prjd is null)

**Typical Use Cases**:
- Monitor BSS equipment changes
- Validate vendor BSS deployments
- Track BSS carrier movement

**Example Output**:
```
BandGrp | Vendor | Jun 2026 (Prev) | Jul 2026 (Curr) | Pct Diff | Flag
--------|--------|-----------------|-----------------|----------|--------
MB      | ERC    | 78              | 114             | +46.15%  | ✓ Acceptable
SUB1-13 | SAM    | 4,672           | 4,261           | -8.80%   | ⚠ Decrease >5%
SUB3    | SAM    | 56              | 52              | -7.14%   | ⚠ Decrease >5%
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
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi.vpi_data_n5l_ul` (M-1)

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

**UL-Specific Notes**:
- Uses `_ul` suffix table names
- Same logic as DL A6

**Typical Use Cases**:
- Monitor overall carrier portfolio health
- Identify abnormal churn
- Validate data completeness

**Example Output**:
```
Category                              | Carrier Count
--------------------------------------|--------------
Lost from Jun 2026 (not in Jul 2026)  | 7,280
New in Jul 2026 (not in Jun 2026)     | 18,266
Net Change                            | +10,986
```

---

## Section A6b: Lost Carriers by BandGrp (Unexplained Markets Only)

**Purpose**: Analyze band group distribution of lost carriers from unexplained declining markets

**Badge**: `MMW X% of Loss` (red - critical)

**Key Metrics**:
- Lost carriers per band group
- Percentage of total lost carriers
- Visual bar chart

**Data Sources**:
- `vpi.vpi_data_n5l_ul` (M-1)
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi_temp.rehome_market_info` (to exclude rehome markets)

**Filter Criteria**:
- Markets with >5% decline (UL-specific: 5% vs DL's 10%)
- Not in rehome mappings
- Lost carriers (in M-1, not in current)

**Insights Provided**:
- Which band groups are most affected by losses
- **MMW band specifically highlighted** (UL-specific)
- Visual representation of distribution

**Thresholds**:
- **MMW band hardcoded as top band** (UL-specific)
- Percentage calculated of total lost carriers
- 5% market decline threshold (UL-specific)

**Color Coding**:
- **Red background: MMW band (hardcoded)** (UL-specific)
- Red text: MMW band count and percentage
- Blue bars: Visual representation

**UL-Specific Notes**:
- **MMW band hardcoded as top band** (vs dynamic top band in DL)
- **5% market decline threshold** (vs 10% in DL)
- **Specific MMW-focused insight messaging**
- **Hardcoded MMW highlighting in table**

**Typical Use Cases**:
- Identify MMW-specific pipeline issues
- Prioritize MMW band investigation
- Understand loss distribution

**Example Output**:
```
BandGrp | Lost Carriers | % of Total | Visual
--------|---------------|------------|--------
MMW     | 0             | 0.0%       | 
SUB1-5  | 0             | 0.0%       | 
SUB3    | 0             | 0.0%       | 
TOTAL   | 0             | 100.0%     |
```

**UL-Specific Insight**:
```
MMW dominates the loss — confirming that unexplained market declines are 
almost entirely a MMW carrier drop. The small losses in SUB1-5, SUB3, 
SUB1-13 and MB are likely collateral from markets that have mixed bands 
but are MMW-heavy. Investigate whether MMW carriers are being excluded or 
dropped upstream in the Jul 2026 staging pipeline.
```

---

## Section A7: trgprjd_ul Flag Distribution by Projected Year

**Purpose**: Analyze distribution of UL target flag across projected years

**Badge**: `Stable` (green - informational)

**Key Metrics**:
- Carrier counts by projected year and flag
- Percentage of year total
- Flag distribution ('y' vs 'n')

**Data Sources**:
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)

**Projected Years**: 2026, 2027, 2028, 2029, 2030

**Insights Provided**:
- Year-over-year UL target flag trends
- Percentage of targeted carriers per year
- Overall target flag distribution

**Color Coding**:
- Green text: 'y' flag values
- Normal text: 'n' flag values
- Bold: 'y' flag indicators

**UL-Specific Notes**:
- Uses `trgprjd_ul` field instead of `trgprjd`
- Same logic as DL A7 but with UL field

**Typical Use Cases**:
- Monitor UL target project progression
- Validate year-based UL target allocation
- Track UL target flag adoption

**Example Output**:
```
Projected Year | Flag | Carriers | % of Year Total
---------------|------|----------|----------------
2026           | n    | 1,041,936| 94.4%
2026           | y    | 62,075   | 5.6%
2027           | n    | 1,045,157| 94.7%
2027           | y    | 58,853   | 5.3%
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
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)
- `vpi.vpi_data_n5l_ul` (M-1)

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

**UL-Specific Notes**:
- **Note in insight: cec_prjd is 100% null** (UL-specific)
- Uses `_ul` suffix table names
- Same logic as DL A8 but with null note

**Typical Use Cases**:
- Monitor CEC classification changes
- Validate BSS equipment trends
- Track classification completeness

**Example Output**:
```
cec_curr | Jun 2026 Count | Jul 2026 Count | Delta
---------|----------------|----------------|-------
BSS      | 8,704          | 8,978          | +274
NOT BSS  | 1,084,332      | 1,095,031      | +10,699
NONE     | 176            | 189            | +13
-        | 0              | 0              | 0
Total    | 1,093,212      | 1,104,198      | +10,986
```

**UL-Specific Insight**:
```
The overall carrier movement is primarily in NOT BSS (+10,699).
BSS carriers changed by +274.
Note: cec_prjd is 100% null in both UL tables — excluded from this report.
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
- `vpi.vpi_data_n5l_waiv_stage_ul` (current)

**Columns Checked**:
- `agg_unique_id`
- `market`
- `bandgrp`
- `vendor`
- `projecteddate`
- `trgprjd_ul` (UL-specific)
- `cec_curr`
- `cec_prjd` (Expected null for UL)

**Insights Provided**:
- Overall data completeness
- Specific columns with null values
- **cec_prjd expected null note** (UL-specific)

**Thresholds**:
- 0 nulls: "Clean" status
- Any nulls: "Issues Found" status
- **cec_prjd null: Expected** (UL-specific)

**Color Coding**:
- Green checkmark: Clean columns
- Red warning: Columns with nulls
- **Muted text: Expected null (cec_prjd)** (UL-specific)
- Green badge: Overall clean status
- Red badge: Overall issues found

**UL-Specific Notes**:
- **cec_prjd expected to be 100% null**
- **cec_prjd excluded from data quality status**
- **Uses `trgprjd_ul` field instead of `trgprjd`**
- **Special status message for cec_prjd**

**Typical Use Cases**:
- Validate data loading completeness
- Identify data quality issues
- Monitor ETL process health
- **Confirm cec_prjd null behavior** (UL-specific)

**Example Output**:
```
Metric                  | Value     | Status
-------------------------|-----------|--------
Total Rows               | 5,520,550 |
Total Distinct Carriers  | 1,104,198 |
Null agg_unique_id       | 0         | ✓ Clean
Null market              | 0         | ✓ Clean
Null bandgrp             | 0         | ✓ Clean
Null vendor              | 0         | ✓ Clean
Null projecteddate       | 0         | ✓ Clean
Null trgprjd_ul          | 0         | ✓ Clean
Null cec_curr            | 0         | ✓ Clean
Null cec_prjd            | 5,520,550 | • Expected — not populated for UL
```

---

## Executive Summary

**Purpose**: Consolidate key findings and action items

**Location**: Bottom of report, after all analysis sections

**Components**:

### 1. Action Required - Band/Vendor Flags
- Lists band/vendor combinations with consistent decreases across all projection years
- **UL-specific context: Ericsson mid-band UL projected-target carriers** (UL-specific)
- Requires investigation before publishing
- Based on Section A3 findings

### 2. Confirmed Rehome
- Lists all market rehome mappings
- Explains expected volume changes
- Based on Section A2 findings
- Shared with DL report

### 3. Monitor - Unexplained Market Declines
- Count of markets with >10% unexplained declines
- **MMW band percentage of lost carriers** (UL-specific)
- **MMW-specific pipeline issue messaging** (UL-specific)
- Net carrier movement summary
- Based on Sections A2 and A6b findings

### 4. Monitor - BSS cec_curr
- Count of flagged BSS band/vendor combinations
- Based on Section A4 findings

### 5. Data Quality
- Overall data quality status
- Null check summary
- **cec_prjd expected null note** (UL-specific)
- Based on Section A9 findings

**Color Coding**:
- Red background: Critical action items
- Yellow background: Monitoring items
- Green background: Positive status

**UL-Specific Elements**:
- **MMW band percentage calculation in badge**
- **MMW-specific insight messaging**
- **UL target flag context in action items**
- **cec_prjd expected null note**

**Typical Use Cases**:
- Quick review of report findings
- Prioritize investigation items
- Communicate status to stakeholders
- **Focus on MMW and UL target flag issues** (UL-specific)

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

**UL-Specific Notes**:
- Same structure as DL
- Uses UL table data
- Data quality accounts for cec_prjd expected null

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
| `MMW X% of Loss` | Red | MMW band loss percentage (UL-specific) |
| `Stable` | Green | Normal distribution |
| `BSS +/-X` | Blue | CEC classification change |
| `Clean` / `Issues Found` | Green/Red | Data quality status |

---

## Report Navigation

### Recommended Review Order

1. **Executive Summary** (bottom) - Quick overview of action items
2. **KPI Cards** (top) - High-level metrics
3. **A9 - Data Quality** - Validate data completeness (note cec_prjd expected null)
4. **A2 - Market Volume** - Identify market-level issues
5. **A3 - Band/Vendor** - Check UL target flag anomalies
6. **A6/A6b - Carrier Movement** - Understand carrier churn (focus on MMW)
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

---

## UL-Specific Report Features

### MMW Band Focus

- **Hardcoded MMW highlighting** in A6b section
- **MMW percentage in badge**
- **MMW-specific insight messaging**
- **5% threshold for lost_by_band analysis** (vs 10% in DL)

### UL Target Flag (trgprjd_ul)

- **Uses trgprjd_ul field** throughout report
- **Section titles reference UL target flag**
- **Executive summary mentions UL context**
- **Same logic as DL but with UL field**

### CEC Field Behavior

- **cec_prjd expected to be 100% null**
- **Noted in A8 insight**
- **Special handling in A9 data quality**
- **Excluded from data quality status**

### Market Decline Thresholds

- **General market: >10%** (same as DL)
- **Lost_by_band: >5%** (UL-specific, vs 10% in DL)
- **Focus on MMW pipeline issues**

### Executive Summary Messaging

- **UL-specific action item context**
- **MMW pipeline issue emphasis**
- **UL target flag investigation guidance**
- **cec_prjd expected null note**

---

## Comparison with DL Report Sections

| Section | DL | UL |
|---------|-----|-----|
| A1 | trgprjd field | trgprjd_ul field |
| A2 | Same thresholds | Same thresholds |
| A3 | trgprjd field | trgprjd_ul field |
| A4 | Same logic | Same logic |
| A6 | Same logic | Same logic |
| A6b | Dynamic top band | **Hardcoded MMW** |
| A6b | 10% threshold | **5% threshold** |
| A7 | trgprjd field | trgprjd_ul field |
| A8 | Both CEC populated | **cec_prjd expected null** |
| A9 | All columns checked | **cec_prjd expected null** |
| Exec Summary | Generic messaging | **MMW/UL-specific messaging** |
