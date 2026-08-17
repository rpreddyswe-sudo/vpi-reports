# A10 and A11 Implementation Explanation

## Overview
A10 and A11 are **new enhanced analysis sections** added to the VPI DL (Data Layer) and UL (Uplink) Monthly Reports to provide more granular insights into carrier distribution and target classification. These sections complement the existing analysis by breaking down data at a more detailed market/band level.

**Implementation Status:**
- ✅ **DL**: Production-ready with `trgcurr` field
- ✅ **UL**: Production-ready with `trgcurr_ul` field
- ✅ **Both**: Identical business logic and use cases

---

## A10 — Per Market, Per Band Group Carrier Count Change

### Purpose
Identifies specific market and band group combinations that show significant carrier count changes between the reference month (M-1) and current staging month. This provides **granular visibility** into where carrier gains or losses are occurring.

### Business Value
- **Targeted Investigation**: Instead of looking at overall market changes, we can pinpoint exact market/band combinations that need attention
- **Band-Level Analysis**: Different frequency bands (MB, MMW, SUB1-13, etc.) may have different deployment patterns and issues
- **Early Warning**: Identifies specific band groups within markets that are declining >5%, allowing proactive investigation

### How It Works

#### SQL Query Logic
```sql
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
```

#### Key Features
- **Full Outer Join**: Captures both new and disappearing market/band combinations
- **Percentage Calculation**: Computes the percentage change between reference and current counts
- **Flagging Logic**: Flags combinations with >5% decrease for investigation
- **Null Handling**: Gracefully handles cases where market/band combinations appear/disappear

### Example Output Interpretation
| Market | BandGrp | May 2025 (Prev) | Jan 2026 (Curr) | Pct Diff | Flag |
|--------|---------|------------------|-----------------|----------|------|
| 25     | MB      | 10               | 0               | -100.0%  | ⚠️ Decrease >5% |
| 100    | MB      | 0                | 739             | —        | ✅ Acceptable |

**Interpretation**: Market 25 lost all MB band carriers, while Market 100 gained new MB band carriers.

---

## A11 — trgcurr Distribution Per Market, Per Band Group

### Purpose
Provides a detailed breakdown of the **target current flag** distribution across markets and band groups. This shows which carriers are currently classified as having targets versus those without targets at a granular level.

**Field Names:**
- **DL**: Uses `trgcurr` field
- **UL**: Uses `trgcurr_ul` field

### Business Value
- **Target Penetration Analysis**: Shows how well targets are set within each market/band combination
- **Classification Validation**: Identifies markets/bands where target classification may be missing or over-represented
- **Deployment Planning**: Helps understand which market/band combinations have active target classifications for capacity planning

### How It Works

#### SQL Query Logic
```sql
SELECT market,
       bandgrp,
       COALESCE({TRGCURR},'null') AS trgcurr_flag,
       COUNT(DISTINCT agg_unique_id) AS carriers
FROM {STAGE} WHERE cptmonth=%s
GROUP BY 1,2,3 ORDER BY 1,2,4 DESC
```

**Note for UL Implementation:**
- UL uses `trgcurr_ul` instead of `trgcurr`
- The query structure is identical, only the field name changes

#### Key Features
- **Flag Distribution**: Breaks down carriers by target current flag (y/n/null) within each market/band
- **Percentage Calculation**: Computes the percentage of carriers with each flag within the market/band combination
- **Current Snapshot**: Reflects the state of the current staging table only
- **Color Coding**: Highlights carriers with targets (y flag) for easy identification
- **UL Compatibility**: UL implementation uses `trgcurr_ul` field with identical logic

### Example Output Interpretation
| Market | BandGrp | trgcurr Flag | Carriers | % of Market/Band |
|--------|---------|--------------|----------|------------------|
| 100    | MB      | n            | 732      | 99.1%            |
| 100    | MB      | y            | 7        | 0.9%             |
| 100    | MMW     | n            | 597      | 99.8%            |
| 100    | MMW     | y            | 1        | 0.2%             |

**Interpretation**: In Market 100, MB band has 99.1% of carriers without targets and only 0.9% with targets, indicating very low target penetration in this band.

**Note**: UL reports will show `trgcurr_ul Flag` in the header instead of `trgcurr Flag`, but the interpretation remains identical.

---

## Integration with Existing Analysis

### Relationship to Other Sections
- **A2 (Market Volume)**: Provides market-level overview, A10 drills down to market/band level
- **A3 (Band/Vendor Analysis)**: Focuses on vendors by year, A10 focuses on raw counts by market/band
- **A7 (trgprjd Distribution)**: Shows projected target distribution, A11 shows current target distribution

### Enhanced Insights
- **Correlation Analysis**: Can correlate market/band declines (A10) with target classification (A11)
- **Gap Identification**: Identify market/band combinations with low target penetration that may need attention
- **Trend Analysis**: Track how target classification evolves within specific market/band combinations over time

---

## Technical Implementation Details

### Data Sources
- **A10**: Uses both Reference (M-1) and Stage (current) tables
- **A11**: Uses only Stage (current) table

### Performance Considerations
- **Grouping Operations**: Both queries use GROUP BY on market and bandgrp, which is efficient with proper indexing
- **FULL OUTER JOIN**: A10 uses full outer join to capture all combinations, which may be slightly more expensive but provides complete coverage
- **Row Counts**: Typical results range from 10-50 rows depending on market/band diversity

### CSV Mode Implementation
Both sections are fully implemented in CSV mode with identical logic to database mode:
- **A10**: Uses Python defaultdict and set operations to replicate SQL aggregation
- **A11**: Uses Python grouping to replicate SQL GROUP BY functionality

**UL CSV Mode**: The UL implementation includes identical CSV mode support with proper handling of `trgcurr_ul` field names.

---

## UL-Specific Implementation Details

### Field Name Differences
The UL implementation uses UL-specific field names while maintaining identical business logic and SQL patterns:

| Aspect | DL Field | UL Field |
|--------|----------|----------|
| Target Current | `trgcurr` | `trgcurr_ul` |
| Target Projected | `trgprjd` | `trgprjd_ul` |
| Stage Table | `vpi.vpi_data_n5l_waiv_stage` | `vpi.vpi_data_n5l_waiv_stage_ul` |
| Reference Table | `vpi.vpi_data_n5l` | `vpi.vpi_data_n5l_ul` |

### Implementation Consistency
- **SQL Logic**: Identical query structure with field name substitutions
- **CSV Mode**: Identical Python logic with proper parameter passing
- **HTML Rendering**: Identical table structure and styling
- **Business Value**: Same operational insights and use cases apply

### UL-Specific Configuration
```python
# UL Configuration in vpi_ul_monthly_report.py
TRGPRJD_UL = "trgprjd_ul"
TRGCURR_UL = "trgcurr_ul"
STAGE = "vpi.vpi_data_n5l_waiv_stage_ul"
REF = "vpi.vpi_data_n5l_ul"
```

### Implementation Status
- ✅ **SQL Queries**: Production-ready with UL-specific field names
- ✅ **CSV Mode**: Fully functional with proper `trgcurr_ul` handling
- ✅ **HTML Rendering**: Complete with UL-specific table headers
- ✅ **Integration**: Well-integrated into UL report structure
- ✅ **Testing**: Consistent behavior with DL implementation

### Code Examples
**UL A10 Query (identical structure to DL):**
```python
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
```

**UL A11 Query (identical structure to DL):**
```python
"trgcurr_market_band": (f"""
SELECT market,
       bandgrp,
       COALESCE({TRGCURR_UL},'null') AS trgcurr_flag,
       COUNT(DISTINCT agg_unique_id) AS carriers
FROM {STAGE} WHERE cptmonth=%s
GROUP BY 1,2,3 ORDER BY 1,2,4 DESC
""", (CURR,)),
```

---

## Use Cases for Team Lead

### 1. Operational Monitoring
- **Daily**: Check A10 for any new market/band combinations showing >5% decline
- **Weekly**: Review A11 to track target classification penetration trends
- **Monthly**: Use both sections as part of the regular VPI staging analysis

### 2. Data Quality Validation
- **Target Coverage**: Use A11 to identify markets/bands with insufficient target classification
- **Anomaly Detection**: Use A10 to find unexpected carrier losses in specific bands
- **Classification Audit**: Validate that target classification aligns with deployment priorities

### 3. Strategic Planning
- **Band Strategy**: Analyze which bands have high/low target penetration across markets
- **Market Prioritization**: Focus attention on market/band combinations with concerning trends
- **Resource Allocation**: Direct investigation resources to problematic market/band combinations

---

## Summary

**A10 and A11 provide granular, actionable insights** that complement the existing VPI analysis by:

1. **Drilling down** from market-level to market/band-level analysis
2. **Identifying specific problem areas** rather than broad trends
3. **Enabling targeted investigation** and resource allocation
4. **Supporting data quality validation** at a more detailed level

**Implementation Coverage:**
- **DL Reports**: Production-ready with `trgcurr` field implementation
- **UL Reports**: Production-ready with `trgcurr_ul` field implementation
- **Consistency**: Identical business logic, SQL patterns, and operational value
- **Maintenance**: Unified documentation simplifies updates and consistency

These sections represent an enhancement to both VPI DL and UL analysis, providing deeper visibility into carrier distribution and target classification patterns that support better operational decision-making across both uplink and data layer domains.