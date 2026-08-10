# Architecture Documentation

## System Overview

The VPI DL Monthly Report Generator is a single-script Python application that performs ETL (Extract, Transform, Load) operations from a PostgreSQL database and generates interactive HTML reports for data quality monitoring and trend analysis.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ vpi.vpi_data_n5l_waiv_stage (Current Month)          │  │
│  │ vpi.vpi_data_n5l (Reference M-1, M-2)                │  │
│  │ vpi_temp.rehome_market_info (Rehome mappings)        │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ psycopg2
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              vpi_dl_monthly_report.py                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Configuration & Date Setup                        │  │
│  │ 2. SQL Query Execution (9 queries)                   │  │
│  │ 3. Data Transformation & KPI Calculation             │  │
│  │ 4. HTML Rendering (10 sections)                      │  │
│  │ 5. File Output                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTML generation
                             ▼
┌─────────────────────────────────────────────────────────────┐
│           vpi_dl_report_Month_YYYY.html                     │
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
- Table name constants (STAGE, REF, TRGPRJD)
- Date calculation logic (current month, M-1, M-2)
- Output file path generation

**Key Logic**:
- Default: First day of previous month
- Override: Command-line argument for custom snapshot date
- Date format: YYYY-MM-DD

### 2. Query Layer (Lines 47-209)

**Purpose**: Execute SQL queries to extract data from PostgreSQL

**Query Types**:

| Query Key | Purpose | Tables Used |
|-----------|---------|-------------|
| `avail` | Data availability and row counts | STAGE, REF |
| `market` | Market-level volume trends | STAGE, REF |
| `bandvend` | Band/vendor by projected year | STAGE, REF |
| `bss_curr` | BSS classification analysis | STAGE, REF |
| `movement` | Carrier movement tracking | STAGE, REF |
| `trgdist` | Target flag distribution | STAGE |
| `cec` | CEC classification distribution | STAGE, REF |
| `rehome` | Market rehome mappings | vpi_temp.rehome_market_info |
| `lost_by_band` | Lost carriers by band group | STAGE, REF, vpi_temp |
| `dq` | Data quality checks | STAGE |

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
- Top band for lost carriers analysis
- BSS vs NOT BSS carrier movement

### 4. Rendering Layer (Lines 284-515)

**Purpose**: Generate HTML tables and sections

**Render Functions**:

| Function | Section | Output |
|----------|---------|--------|
| `render_avail_table()` | A1 | Data availability table |
| `render_market_table()` | A2 | Market volume trends |
| `market_movers_html()` | A2 | Market movement insights |
| `render_bandvend_table()` | A3 | Band/vendor by year |
| `render_bss_table()` | A4 | BSS classification |
| `render_trgdist_table()` | A7 | Target flag distribution |
| `render_cec_table()` | A8 | CEC classification |
| `render_lost_by_band_table()` | A6b | Lost carriers by band |
| `render_dq_table()` | A9 | Data quality metrics |

**HTML Structure**:
- Dark theme CSS variables
- Responsive grid layout
- Color-coded status indicators
- Collapsible details sections
- Visual bar charts for percentages

### 5. Template Layer (Lines 537-816)

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

## Data Flow

```
1. Script Execution
   ↓
2. Date Calculation (CURR, M1, M2)
   ↓
3. Database Connection (psycopg2)
   ↓
4. Query Execution (parallel queries)
   ↓
5. Result Storage (dictionary)
   ↓
6. KPI Calculation (derived metrics)
   ↓
7. HTML Rendering (section by section)
   ↓
8. Template Assembly (final HTML)
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

## Error Handling Strategy

1. **Query Level**: Individual query failures don't stop execution
2. **Data Level**: Null checks and fallback values throughout
3. **Display Level**: Graceful degradation with "—" for missing data
4. **File Level**: UTF-8 encoding for special characters

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

1. Add query to `QUERIES` dictionary
2. Execute query and store results
3. Create render function for table
4. Add section to HTML template
5. Update executive summary if needed

### Modifying Thresholds

Key thresholds are defined in helper functions:
- `pct_class()`: -10%, -5%, +5%, +10%
- Flag logic in queries: >5% decrease
- Market decline: >10% unexplained

### Custom Styling

CSS variables in `CSS` constant:
- Colors: `--bg`, `--surface`, `--accent`, `--green`, `--red`
- Spacing: Grid gaps, padding
- Typography: Font sizes, weights
