# Data Model Documentation

## Database Overview

The VPI DL Monthly Report Generator queries a PostgreSQL database containing telecommunications carrier data. The data is organized across multiple tables within the `vpi` schema.

## Database Connection

- **Host**: `nts-gydv-fuze-planning-prd-01-cluster.cluster-cl9vgbtolm5s.us-east-1.rds.amazonaws.com`
- **Port**: `5432`
- **Database**: `fuzenppprod`
- **Schema**: `vpi`
- **User**: `npanalytics_ro` (read-only access)

## Tables

### 1. vpi.vpi_data_n5l_waiv_stage (STAGE)

**Purpose**: Current month staging table for analysis

**Key Columns**:

| Column | Type | Description | Usage |
|--------|------|-------------|-------|
| `agg_unique_id` | string | Unique carrier identifier | Primary key for carrier tracking |
| `cptmonth` | date | Completion month | Snapshot date filtering |
| `market` | integer | Market identifier | Market-level analysis |
| `bandgrp` | string | Band group (e.g., MB, SUB1-5, SUB3) | Frequency band analysis |
| `vendor` | string | Vendor code (e.g., NOK, SAM, ERC) | Vendor analysis |
| `projecteddate` | integer | Projected year (2026-2030) | Year-based projections |
| `trgprjd` | string | Target project flag ('y'/'n') | Target flag distribution |
| `cec_curr` | string | Current CEC classification | CEC analysis (BSS/NOT BSS) |
| `cec_prjd` | string | Projected CEC classification | Future CEC classification |

**Sample Data Structure**:
```
agg_unique_id | cptmonth  | market | bandgrp | vendor | projecteddate | trgprjd | cec_curr | cec_prjd
--------------|-----------|--------|---------|--------|---------------|---------|----------|----------
CAR12345      | 2026-07-01| 5      | MB      | NOK    | 2026          | y       | BSS      | BSS
CAR67890      | 2026-07-01| 10     | SUB1-5  | SAM    | 2027          | n       | NOT BSS  | NOT BSS
```

**Relationships**:
- One carrier can have multiple rows (one per projected year)
- `agg_unique_id` is unique per carrier but not per row
- `cptmonth` partitions data by snapshot date

### 2. vpi.vpi_data_n5l (REF)

**Purpose**: Reference table containing historical data (M-1, M-2)

**Schema**: Identical to `vpi.vpi_data_n5l_waiv_stage`

**Usage**:
- Serves as baseline for month-over-month comparisons
- Contains multiple months of historical data
- Used for trend analysis (3-month trends)

**Key Differences from Stage**:
- Historical data only (no current month)
- Used as reference point for comparisons
- May contain additional historical months

### 3. vpi_temp.rehome_market_info

**Purpose**: Stores market rehome mappings for expected volume changes

**Schema**:

| Column | Type | Description |
|--------|------|-------------|
| `old_market` | integer | Source market being rehomed |
| `new_market` | integer | Destination market receiving rehome |

**Sample Data**:
```
old_market | new_market
-----------|-----------
36         | 39
43         | 5
53         | 46
```

**Usage**:
- Identifies expected volume decreases in source markets
- Identifies expected volume increases in destination markets
- Used to separate explained vs unexplained market changes
- Critical for accurate anomaly detection

## Data Relationships

### Carrier Movement

```
┌─────────────────┐
│  M-1 Reference  │
│  (vpi.vpi_data │
│   _n5l)        │
└────────┬────────┘
         │
         │ agg_unique_id comparison
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│  Lost   │ │   New    │
│ Carriers│ │ Carriers │
└─────────┘ └──────────┘
```

### Market Rehome Flow

```
┌──────────────┐
│ Old Market   │
│ (Source)     │
└──────┬───────┘
       │
       │ Volume Decrease
       │ (Expected)
       ▼
┌──────────────┐
│ New Market   │
│ (Destination)│
└──────────────┘
```

## Data Quality Rules

### Required Fields (Null Checks)

The following columns must be non-null for data quality validation:

1. **agg_unique_id** - Carrier identifier (critical for tracking)
2. **market** - Market identifier (required for market analysis)
3. **bandgrp** - Band group (required for frequency analysis)
4. **vendor** - Vendor code (required for vendor analysis)
5. **projecteddate** - Projected year (required for year-based analysis)
6. **trgprjd** - Target flag (required for target analysis)
7. **cec_curr** - Current CEC classification (required for CEC analysis)
8. **cec_prjd** - Projected CEC classification (required for future analysis)

### Data Validation Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Null values in key columns | 0 | Flag as data quality issue |
| Market volume decrease | >10% | Flag as unexplained decline |
| Band/vendor decrease | >5% | Flag as significant decrease |
| Carrier net change | <-20,000 | Critical flag |

## Domain Values

### Band Groups (bandgrp)

- **MB**: Mid-band
- **MB-OTHER**: Mid-band other
- **SUB1-5**: Sub-6 GHz 1.5 GHz
- **SUB1-13**: Sub-6 GHz 1.3 GHz
- **SUB3**: Sub-6 GHz 3 GHz
- **MMW**: Millimeter wave

### Vendor Codes (vendor)

- **NOK**: Nokia
- **SAM**: Samsung
- **ERC**: Ericsson
- (Additional vendors as needed)

### CEC Classifications (cec_curr, cec_prjd)

- **BSS**: Base Station Subsystem
- **NOT BSS**: Non-BSS equipment
- **NONE**: No classification
- **-**: Missing/unknown

### Target Flag (trgprjd)

- **y**: Targeted for project
- **n**: Not targeted
- **null**: Missing flag

## Query Patterns

### Time-Based Filtering

All queries use `cptmonth` for time-based filtering:

```sql
WHERE cptmonth = '2026-07-01'  -- Current month
WHERE cptmonth >= '2026-05-01' -- Range query
```

### Carrier Uniqueness

Carrier-level analysis uses `COUNT(DISTINCT agg_unique_id)`:

```sql
COUNT(DISTINCT agg_unique_id) AS carriers
```

### Market-Level Aggregation

Market analysis groups by market:

```sql
SELECT market, COUNT(*) AS cnt
FROM table
WHERE cptmonth = %s
GROUP BY market
```

### Band/Vendor Cross-Analysis

Combined band and vendor analysis:

```sql
SELECT bandgrp, vendor, COUNT(DISTINCT agg_unique_id) AS cnt
FROM table
WHERE cptmonth = %s
GROUP BY bandgrp, vendor
```

## Data Volume Characteristics

Based on sample report (July 2026):
- **Total Rows**: ~6 million
- **Distinct Carriers**: ~1.2 million
- **Markets**: ~200+
- **Projected Years**: 2026-2030 (5 years)
- **Rows per Carrier**: ~5 (one per projected year)

## Index Assumptions

For optimal query performance, the following indexes are assumed:

```sql
-- Primary filtering
CREATE INDEX idx_cptmonth ON vpi.vpi_data_n5l_waiv_stage(cptmonth);
CREATE INDEX idx_cptmonth ON vpi.vpi_data_n5l(cptmonth);

-- Carrier tracking
CREATE INDEX idx_agg_unique_id ON vpi.vpi_data_n5l_waiv_stage(agg_unique_id);
CREATE INDEX idx_agg_unique_id ON vpi.vpi_data_n5l(agg_unique_id);

-- Market analysis
CREATE INDEX idx_market ON vpi.vpi_data_n5l_waiv_stage(market);
CREATE INDEX idx_market ON vpi.vpi_data_n5l(market);

-- Combined queries
CREATE INDEX idx_market_cptmonth ON vpi.vpi_data_n5l_waiv_stage(market, cptmonth);
```

## Data Lifecycle

1. **Ingestion**: Data loaded into stage table monthly
2. **Validation**: Data quality checks performed
3. **Analysis**: Monthly report generated comparing stage vs reference
4. **Archival**: Stage data becomes reference for next month
5. **Retention**: Historical data maintained for trend analysis

## Security Considerations

- **Access**: Read-only database user (npanalytics_ro)
- **Network**: SSL connection to AWS RDS
- **Data Scope**: Production data (fuzenppprod)
- **PII**: Carrier identifiers may be sensitive
- **Compliance**: Follow Verizon data handling policies
