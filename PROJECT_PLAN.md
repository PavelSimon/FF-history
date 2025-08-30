# Firefox History Daily Journal Generator

## Project Overview

This project creates an automated system to generate daily journals from Firefox browser history, storing data in SQLite and exporting to Markdown files. Additionally, it includes a Solara-based web dashboard for interactive data visualization and analysis.

## Architecture

### Core Components

1. **Firefox History Parser** (`firefox_parser.py`)
   - Locates Firefox profile directories
   - Reads `places.sqlite` database
   - Extracts browsing history with metadata

2. **Journal Generator** (`journal_generator.py`)
   - Processes browsing data into meaningful insights
   - Categorizes websites and activities
   - Generates daily summaries

3. **Database Manager** (`database.py`)
   - Manages local SQLite database for journal entries
   - Handles daily data partitioning
   - Provides data access layer

4. **Markdown Exporter** (`markdown_exporter.py`)
   - Creates formatted daily journal files
   - Uses customizable templates
   - Organizes files by date

5. **Scheduler** (`scheduler.py`)
   - Automates daily journal generation
   - Handles background processing
   - Manages execution timing

6. **Solara Dashboard** (`dashboard/`)
   - Interactive web-based visualization
   - Real-time data analysis
   - Customizable charts and reports

## Technical Stack

### Core Dependencies
```toml
dependencies = [
    "sqlite3",  # Database operations (built-in)
    "pathlib",  # File path handling (built-in)
    "datetime", # Date/time operations (built-in)
    "json",     # Configuration handling (built-in)
    "logging",  # Error handling (built-in)
    "schedule", # Task scheduling
    "typing",   # Type hints (built-in)
    "solara",   # Web dashboard framework
    "plotly",   # Interactive charts
    "pandas",   # Data manipulation
    "numpy",    # Numerical operations
]
```

## Data Flow

### 1. Data Collection
```
Firefox places.sqlite → History Parser → Raw browsing data
```

### 2. Processing Pipeline
```
Raw data → Journal Generator → Structured insights → SQLite Database
                            ↓
                      Daily Markdown Files
```

### 3. Visualization Pipeline
```
SQLite Database → Solara Dashboard → Interactive Web Interface
```

## Database Schema

### Journal Entries Table
```sql
CREATE TABLE journal_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL UNIQUE,
    total_sites_visited INTEGER,
    total_time_spent INTEGER,  -- minutes
    top_categories TEXT,       -- JSON array
    productivity_score REAL,
    summary TEXT,
    raw_data TEXT,            -- JSON with detailed history
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Site Categories Table
```sql
CREATE TABLE site_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    productivity_weight REAL DEFAULT 0.0
);
```

### Daily Statistics Table
```sql
CREATE TABLE daily_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    sites_visited INTEGER,
    time_spent INTEGER,
    PRIMARY KEY (date, hour)
);
```

## Firefox History Data Structure

### Firefox `places.sqlite` Tables Used
- `moz_places`: URL information (url, title, visit_count)
- `moz_historyvisits`: Visit timestamps and duration
- `moz_bookmarks`: Bookmarked sites (optional)

### Profile Location by OS
- **Windows**: `%APPDATA%\Mozilla\Firefox\Profiles\`
- **macOS**: `~/Library/Application Support/Firefox/Profiles/`
- **Linux**: `~/.mozilla/firefox/`

## Solara Dashboard Visualization Plan

### 1. Main Dashboard Components

#### Overview Page
```python
# Components to implement:
- Daily activity timeline (24-hour heatmap)
- Top visited sites (bar chart)
- Category breakdown (pie chart)
- Productivity score trend (line chart)
- Weekly/monthly summaries
```

#### Analytics Page
```python
# Advanced visualizations:
- Time spent by category (stacked area chart)
- Browsing pattern analysis (scatter plot)
- Site visit frequency (treemap)
- Hourly activity patterns (polar chart)
- Productivity correlation analysis
```

#### Historical View
```python
# Time-series analysis:
- Calendar heatmap of daily activity
- Long-term trend analysis
- Comparative monthly/yearly views
- Search and filter capabilities
- Export functionality
```

### 2. Interactive Features

#### Filters and Controls
- Date range picker
- Category filter checkboxes  
- Productivity score slider
- Search functionality
- Time granularity selector (hourly/daily/weekly)

#### Data Exploration
- Drill-down capabilities
- Hover tooltips with detailed info
- Clickable elements for detailed views
- Real-time data updates
- Custom date comparisons

### 3. Solara Component Structure

```
dashboard/
├── app.py                 # Main Solara application
├── components/
│   ├── __init__.py
│   ├── overview.py        # Overview dashboard page
│   ├── analytics.py       # Analytics page
│   ├── historical.py      # Historical data view
│   ├── filters.py         # Filter components
│   └── charts.py          # Reusable chart components
├── utils/
│   ├── __init__.py
│   ├── data_loader.py     # Data loading utilities
│   ├── chart_helpers.py   # Chart creation helpers
│   └── date_utils.py      # Date manipulation utilities
└── assets/
    ├── style.css          # Custom CSS styles
    └── config.json        # Dashboard configuration
```

### 4. Chart Types and Data Visualization

#### Time-based Charts
```python
# Daily Timeline (Plotly Timeline)
- Horizontal timeline showing browsing sessions
- Color-coded by category
- Interactive zoom and pan

# Activity Heatmap (Plotly Heatmap)
- 24x7 grid showing activity intensity
- Tooltips with detailed statistics
- Custom color scales

# Trend Lines (Plotly Line)
- Productivity scores over time
- Time spent trends
- Visit count patterns
```

#### Category Analysis
```python
# Category Breakdown (Plotly Pie/Sunburst)
- Hierarchical category visualization
- Interactive selection
- Percentage and absolute values

# Time Distribution (Plotly Bar/Stacked Bar)
- Time spent per category
- Comparative analysis
- Sortable and filterable
```

#### Advanced Analytics
```python
# Correlation Matrix (Plotly Heatmap)
- Relationships between metrics
- Statistical significance indicators
- Interactive exploration

# Distribution Analysis (Plotly Histogram/Box)
- Session duration distributions
- Visit frequency patterns
- Statistical outlier detection
```

## Configuration System

### Configuration File (`config.json`)
```json
{
    "firefox": {
        "profile_path": "auto",
        "exclude_private": true,
        "excluded_domains": ["localhost", "127.0.0.1"]
    },
    "journal": {
        "output_directory": "./journals",
        "template_path": "./templates/daily_template.md",
        "include_statistics": true,
        "minimum_visit_duration": 30
    },
    "database": {
        "path": "./data/journal.db",
        "backup_enabled": true,
        "retention_days": 365
    },
    "scheduler": {
        "enabled": true,
        "time": "23:30",
        "timezone": "local"
    },
    "dashboard": {
        "host": "localhost",
        "port": 8765,
        "theme": "light",
        "auto_refresh": 300
    }
}
```

## Implementation Phases

### Phase 1: Core Functionality
1. Firefox history parser
2. Basic journal generation
3. SQLite database setup
4. Markdown export

### Phase 2: Automation
1. Scheduling system
2. Configuration management
3. Error handling and logging
4. Data validation

### Phase 3: Visualization
1. Solara dashboard setup
2. Basic charts implementation
3. Interactive components
4. Data filtering and search

### Phase 4: Advanced Features
1. Advanced analytics
2. Custom categories and rules
3. Export functionality
4. Performance optimization

## File Structure

```
ff-history/
├── pyproject.toml
├── README.md
├── config.json
├── main.py                    # Entry point
├── src/
│   ├── __init__.py
│   ├── firefox_parser.py      # Firefox history parsing
│   ├── journal_generator.py   # Journal content generation
│   ├── database.py           # Database operations
│   ├── markdown_exporter.py  # Markdown file generation
│   ├── scheduler.py          # Task scheduling
│   └── config.py             # Configuration management
├── dashboard/                 # Solara web interface
│   ├── app.py
│   ├── components/
│   ├── utils/
│   └── assets/
├── templates/
│   └── daily_template.md      # Markdown template
├── data/                      # SQLite database storage
├── journals/                  # Generated markdown files
├── logs/                      # Application logs
└── tests/
    ├── __init__.py
    ├── test_firefox_parser.py
    ├── test_journal_generator.py
    ├── test_database.py
    └── test_dashboard.py
```

## Usage Examples

### Command Line Interface
```bash
# Generate today's journal
uv run python main.py generate --date today

# Generate journal for specific date
uv run python main.py generate --date 2024-03-15

# Start scheduler daemon
uv run python main.py schedule --start

# Launch dashboard (method 1)
uv run python main.py dashboard --port 8765

# Launch dashboard (method 2 - recommended)
uv run solara run dashboard/app.py:Page --port 8765

# Export data
uv run python main.py export --format csv --date-range "2024-03-01,2024-03-31"
```

### Dashboard Access
```bash
# Start dashboard server (recommended)
uv run solara run dashboard/app.py:Page --port 8765

# Access via browser
http://localhost:8765
```

## Performance Considerations

### Optimization Strategies
1. **Database Indexing**: Index frequently queried date columns
2. **Data Caching**: Cache processed data for dashboard
3. **Lazy Loading**: Load dashboard components on demand
4. **Background Processing**: Process large datasets asynchronously
5. **Memory Management**: Stream large Firefox history files

### Scalability
- Handle large Firefox history databases (100k+ entries)
- Efficient date-range queries
- Responsive dashboard with large datasets
- Configurable data retention policies

## Security and Privacy

### Data Protection
- Local-only data storage
- No external API calls
- Configurable data exclusion rules
- Automatic private browsing exclusion
- Optional data encryption

### Privacy Features
- Domain blacklisting
- Time-based filtering
- Anonymization options
- Data retention controls

## Testing Strategy

### Unit Tests
- Firefox parser functionality
- Journal generation logic
- Database operations
- Date/time handling

### Integration Tests
- End-to-end journal generation
- Dashboard data loading
- Configuration management
- Scheduler reliability

### Performance Tests
- Large dataset handling
- Dashboard responsiveness
- Memory usage optimization
- Query performance

This comprehensive plan provides a roadmap for building a robust Firefox history journal generator with advanced visualization capabilities using Solara.