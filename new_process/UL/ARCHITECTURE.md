# Architecture Documentation

## System Overview

The VPI UL Monthly Report Generator is a single-script Python application that performs ETL (Extract, Transform, Load) operations from a PostgreSQL database and generates interactive HTML reports for data quality monitoring and trend analysis for Uplink (UL) carrier data.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ vpi.vpi_data_n5l_waiv_stage_ul (Current Month)        │  │
│  │ vpi.vpi_data_n5l_ul (Reference M-1, M-2)              │  │
│  │ vpi_temp.rehome_market_info (Rehome mappings)         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ psycopg2
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              vpi_ul_monthly_report.py                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Configuration & Date Setup                        │  │
│  │ 2. SQL Query Execution (9 queries)                   │  │
│  │ 3. Data Transformation & KPI Calculation             │  │
│  │ 4. HTML Rendering (9 sections)                       │  │
│  │ 5. File Output                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTML generation
                             ▼
┌─────────────────────────────────────────────────────────────┐
│           vpi_ul_report_Month_YYYY.html                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ • Executive Summary                                   │  │
│  │ • KPI Cards (6 metrics)                              │  │
│  │ • Detailed Analysis Tables (A1-A9)                   │  │
│  │ • Color-coded Insights & Flags                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Configuration Layer (Lines 17-45)

**Purpose**: Centralized configuration and date handling

**Components**:
- Database connection string (PostgreSQL)
- Table name constants (STAGE, REF)
- Date calculation logic (current month, M-1, M-2)
- Output file path generation

**Key Configuration**:
```python
CONN  = "postgresql://npanalytics_ro:verizon24@..."
STAGE = "vpi.vpi_data_n5l_waiv_stage_ul"
REF   = "vpi.vpi_data_n5l_ul"
```

**Key Logic**:
- Default: First day of previous month
- Override: Command-line argument for custom snapshot date
- Date format: YYYY-MM-DD

### 2. Query Layer (Lines 47-209)

**Purpose**: Execute SQL queries to extract data from PostgreSQL

**Query Types**:

| Query Key | Purpose | Tables Used | UL-Specific |
|-----------|---------|-------------|-------------|
| `avail` | Data availability and row counts | STAGE, REF | _ul table names |
| `market` | Market-level volume trends | STAGE, REF | _ul table names |
| `bandvend` | Band/vendor by projected year | STAGE, REF | trgprjd_ul field |
| `bss_curr` | BSS classification analysis | STAGE, REF | _ul table names |
| `movement` | Carrier movement tracking | STAGE, REF | _ul table names |
| `trgdist` | Target flag distribution | STAGE | trgprjd_ul field |
| `cec` | CEC classification distribution | STAGE, REF | _ul table names |
| `rehome` | Market rehome mappings | vpi_temp.rehome_market_info | Shared |
| `lost_by_band` | Lost carriers by band group | STAGE, REF, vpi_temp | 5% threshold |
| `dq` | Data quality checks | STAGE | cec_prjd expected null |

**UL-Specific Query Differences**:

1. **Table Names**: All queries use `_ul` suffix
   - `vpi.vpi_data_n5l_waiv_stage_ul` instead of `vpi.vpi_data_n5l_waiv_stage`
   - `vpi.vpi_data_n5l_ul` instead of `vpi.vpi_data_n5l`

2. **Target Flag Field**: Uses `trgprjd_ul` instead of `trgprjd`
   ```sql
   WHERE cptmonth=%s AND trgprjd_ul='y'
   ```

3. **Lost_by_band Threshold**: Uses 5% instead of 10%
   ```sql
   AND ROUND(((m0.cnt - m1.cnt)::numeric / NULLIF(m1.cnt,0))*100,2) <= -5
   ```

4. **Availability Query**: Different filtering logic
   ```sql
   WHERE cptmonth = %s  -- Stage (exact match)
   WHERE cptmonth IN (%s, %s)  -- Reference (multiple months)
   ```

**Error Handling**:
- Try-catch blocks for each query
- Rollback on failure
- Empty result set fallback
- Console logging of query status

### 3. Transformation Layer (Lines 230-536)

**Purpose**: Transform raw query results into KPIs and derived metrics

**Helper Functions**:

- `fmt(n)`: Number formatting with comma separators
- `pct_class(v)`: CSS class assignment based on percentage thresholds
- `delta_class(v)`: CSS class for positive/negative deltas
- `flag_html(flag)`: HTML rendering for status flags
- `kpi_delta_class(v)`: KPI delta direction classification

**KPI Calculations**:

- Current carrier count (from stage table)
- M-1 carrier count (from reference table)
- Net change (current - M-1)
- Lost carriers (in M-1, not in current)
- New carriers (in current, not in M-1)
- Data quality status (null checks)

**Derived Insights**:

- Market movers (rehome vs unexplained declines)
- Band/vendor flagging (consistent decreases across years)
- MMW-specific analysis (hardcoded MMW band highlighting)
- BSS vs NOT BSS carrier movement

**UL-Specific Transformations**:

1. **MMW Band Highlighting**: Hardcoded logic to identify MMW losses
   ```python
   bcls = 'text-red' if r['bandgrp'] == 'MMW' else ''
   bold = 'font-weight:600;' if r['bandgrp'] == 'MMW' else ''
   ```

2. **Data Quality Status**: Excludes `cec_prjd` from null checks
   ```python
   dq_status = 'Clean' if all(
       (dq.get(c) or 0) == 0
       for c in ['null_agg_id','null_market','null_bandgrp','null_vendor',
                 'null_projdate','null_trgprjd','null_cec_curr']
   ) else 'Issues Found'
   ```

3. **Market Movers**: Different threshold logic for unexplained declines
   ```python
   big_drop = [(r['market'], r['var_curr_m1'], r['curr_cnt'], r['m1_cnt'])
               for r in rows if r.get('var_curr_m1') is not None 
               and float(r['var_curr_m1']) <= -10]
   ```

### 4. Rendering Layer (Lines 284-515)

**Purpose**: Generate HTML tables and sections

**Render Functions**:

| Function | Section | Output | UL-Specific |
|----------|---------|--------|-------------|
| `render_avail_table()` | A1 | Data availability table | _ul table names |
| `render_market_table()` | A2 | Market volume trends | _ul table names |
| `market_movers_html()` | A2 | Market movement insights | No rehome separation |
| `render_bandvend_table()` | A3 | Band/vendor by year | trgprjd_ul field |
| `render_bss_table()` | A4 | BSS classification | _ul table names |
| `render_trgdist_table()` | A7 | Target flag distribution | trgprjd_ul field |
| `render_cec_table()` | A8 | CEC classification | _ul table names |
| `render_lost_by_band_table()` | A6b | Lost carriers by band | MMW highlighting |
| `render_dq_table()` | A9 | Data quality metrics | cec_prjd expected null |

**UL-Specific Rendering**:

1. **Lost_by_band Table**: MMW band hardcoded highlighting
   ```python
   bcls = 'text-red' if r['bandgrp'] == 'MMW' else ''
   bold = 'font-weight:600;' if r['bandgrp'] == 'MMW' else ''
   ```

2. **Data Quality Table**: Special handling for cec_prjd
   ```python
   if check is None and label.startswith('Null cec_prjd'):
       status = '<span class="text-muted">&#9642; Expected — not populated for UL</span>'
   ```

3. **Market Movers**: Different rehome handling
   - Separates rehome drops from unexplained drops
   - Shows rehome destination mapping

**HTML Structure**:
- Dark theme CSS variables
- Responsive grid layout
- Color-coded status indicators
- Collapsible details sections
- Visual bar charts for percentages

### 5. Template Layer (Lines 537-804)

**Purpose**: Assemble final HTML document

**Components**:
- CSS stylesheet (embedded)
- Header with metadata
- KPI cards row
- Analysis sections (A1-A9)
- Executive summary
- Footer with generation info

**Dynamic Content**:
- Month labels (h0, h1, h2)
- Query results injection
- KPI value formatting
- Insight generation
- Badge counts and colors

**UL-Specific Template Elements**:

1. **Section Titles**: Uses UL-specific field names
   ```html
   A3 — trgprjd_ul='y' Band/Vendor by Projected Year
   A7 — trgprjd_ul Flag Distribution by Projected Year
   ```

2. **A6b Badge**: MMW-specific percentage calculation
   ```html
   MMW {round(...)}%% of Loss
   ```

3. **A6b Insight**: MMW-specific messaging
   ```html
   <b>MMW dominates the loss</b> — confirming that unexplained market 
   declines are almost entirely a MMW carrier drop.
   ```

4. **Executive Summary**: UL-specific action messages
   ```html
   Ericsson mid-band UL projected-target carriers dropped ~50-58%% across 
   every projection year (2026–2030).
   ```

5. **A8 Insight**: CEC field note
   ```html
   <b>Note: cec_prjd is 100%% null</b> in both UL tables — excluded from this report.
   ```

6. **Footer**: UL table names
   ```html
   Stage: vpi.vpi_data_n5l_waiv_stage_ul (Jul 2026)
   Ref: vpi.vpi_data_n5l_ul (Jun 2026 / May 2026)
   ```

## Data Flow

```
1. Script Execution
   ↓
2. Date Calculation (CURR, M1, M2)
   ↓
3. Database Connection (psycopg2)
   ↓
4. Query Execution (parallel queries with UL-specific fields)
   ↓
5. Result Storage (dictionary)
   ↓
6. KPI Calculation (derived metrics with MMW logic)
   ↓
7. HTML Rendering (section by section with UL highlighting)
   ↓
8. Template Assembly (final HTML with UL messaging)
   ↓
9. File Output (HTML report)
```

## Design Patterns

### 1. Dictionary-Based Query Management
- Queries stored as dictionary with SQL and parameters
- Easy to add/modify queries
- Consistent execution pattern

### 2. Functional Rendering
- Each table has dedicated render function
- Modular and testable
- Reusable HTML patterns

### 3. CSS Variable Theming
- Centralized color scheme
- Easy theme customization
- Consistent visual language

### 4. Progressive Enhancement
- Core data first
- Insights derived from data
- Executive summary last

### 5. UL-Specific Hardcoding
- MMW band hardcoded in multiple places
- cec_prjd null handling throughout
- trgprjd_ul field references

## Error Handling Strategy

1. **Query Level**: Individual query failures don't stop execution
2. **Data Level**: Null checks and fallback values throughout
3. **Display Level**: Graceful degradation with "—" for missing data
4. **File Level**: UTF-8 encoding for special characters
5. **UL-Specific**: Expected null handling for cec_prjd

## Performance Considerations

- **Connection**: Single database connection for all queries
- **Cursor**: RealDictCursor for named column access
- **Queries**: Optimized SQL with proper indexing assumptions
- **Memory**: Results stored in memory (suitable for dataset size)
- **Output**: Single file write operation

## Security Considerations

- **Credentials**: Embedded in script (production environment)
- **Database**: Read-only access (npanalytics_ro user)
- **Network**: SSL connection to AWS RDS
- **Input**: Date parameter validation via datetime parsing
- **Output**: Local file system write only

## Extension Points

### Adding New Analysis Sections

1. Add query to `QUERIES` dictionary with UL table names
2. Execute query and store results
3. Create render function for table
4. Add section to HTML template
5. Update executive summary if needed

### Modifying Thresholds

Key thresholds are defined in helper functions:
- `pct_class()`: -10%, -5%, +5%, +10%
- Flag logic in queries: >5% decrease
- Market decline: >10% unexplained
- Lost_by_band: 5% threshold (UL-specific)

### Custom Styling

Edit CSS variables in `CSS` constant:
- Colors: `--bg`, `--surface`, `--accent`, `--green`, `--red`
- Spacing: Grid gaps, padding
- Typography: Font sizes, weights

### UL-Specific Customizations

1. **MMW Band**: Change hardcoded 'MMW' references if needed
2. **Target Field**: Update `trgprjd_ul` references if field name changes
3. **CEC Fields**: Modify null handling logic if cec_prjd becomes populated
4. **Thresholds**: Adjust 5% lost_by_band threshold if needed

## Comparison with DL Architecture

| Aspect | DL | UL |
|--------|-----|-----|
| Table Names | `vpi.vpi_data_n5l_waiv_stage` | `vpi.vpi_data_n5l_waiv_stage_ul` |
| Target Flag | `trgprjd` | `trgprjd_ul` |
| CEC Fields | Both populated | cec_prjd expected null |
| Lost_by_band | Dynamic top band | Hardcoded MMW |
| Market Threshold | 10% | 5% (lost_by_band) |
| Insight Messages | Generic | MMW-specific |
| Availability Query | Range filter | Exact + range filter |
