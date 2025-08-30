# Firefox History Daily Journal Generator

Automatically generate daily journals from your Firefox browsing history with SQLite storage, Markdown export, and interactive Solara dashboard visualization.

## Features

### Core Functionality
- **Automated Journal Generation**: Parse Firefox history and create meaningful daily summaries
- **SQLite Storage**: Persistent local database with daily entries and statistics
- **Markdown Export**: Beautiful daily journal files with insights and analytics
- **Scheduling**: Automated daily journal generation at configurable times
- **Multi-OS Support**: Works on Windows, macOS, and Linux

### Interactive Dashboard
- **Real-time Visualization**: Solara-based web dashboard with interactive charts
- **Productivity Tracking**: Monitor productivity scores and browsing patterns
- **Category Analysis**: Automatic website categorization and time tracking
- **Historical Views**: Analyze trends over days, weeks, and months
- **Export Functionality**: Export data in JSON/CSV formats

### Analytics Features
- **Activity Heatmaps**: Visualize browsing patterns by hour and day
- **Productivity Scoring**: Intelligent scoring based on website categories
- **Domain Analysis**: Track time spent on different websites
- **Weekly Summaries**: Aggregate insights across longer periods

## Installation

### Prerequisites
- Python 3.13+
- Firefox browser with browsing history
- UV package manager (recommended)

### Setup
```bash
# Clone or download the project
cd ff-history

# Install dependencies with UV (recommended)
uv sync

# Or install manually with UV
uv add schedule streamlit plotly pandas numpy

# Alternative: use pip
pip install schedule streamlit plotly pandas numpy
```

## Configuration

The application uses a `config.json` file for configuration:

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

## Usage

### Command Line Interface

#### Generate Daily Journal
```bash
# Generate journal for today
uv run python main.py generate

# Generate journal for specific date
uv run python main.py generate --date 2024-03-15
```

#### Start Scheduler
```bash
# Start automated daily journal generation
uv run python main.py schedule --start
```

#### Launch Dashboard
```bash
# Method 1: Auto-detect best dashboard (recommended)
uv run python main.py dashboard

# Method 2: Simple HTML dashboard (always works)
uv run python simple_dashboard.py

# Method 3: Interactive Streamlit dashboard
uv run streamlit run streamlit_dashboard.py --server.port 8765

# Start on custom host/port
uv run python main.py dashboard --host 0.0.0.0 --port 8080
```

#### Export Data
```bash
# Export last 30 days as JSON
uv run python main.py export --format json

# Export specific date range as CSV
uv run python main.py export --format csv --date-range "2024-03-01,2024-03-31"
```

### Web Dashboard

The application provides two dashboard options:

#### Simple HTML Dashboard (Recommended)
- Generates a static HTML file with your data
- Always works, no server required
- Opens automatically in your browser
- Shows weekly summaries and recent entries
- Perfect for quick data overview

#### Interactive Streamlit Dashboard
- Modern web server on `http://localhost:8765`
- Interactive Plotly charts and visualizations
- Real-time data filtering and analysis
- Stable and reliable Python framework

**Dashboard Features:**
- Daily productivity trends and statistics
- **Visited sites breakdown** with time spent and visit counts
- Category analysis and time distribution
- **Interactive charts** with hover details and filtering
- **Page titles sampling** from visited sites
- Historical data view and export
- Responsive design for all devices

## Project Structure

```
ff-history/
├── src/                      # Core application modules
│   ├── firefox_parser.py     # Firefox history parsing
│   ├── journal_generator.py  # Journal content generation
│   ├── database.py          # SQLite database operations
│   ├── markdown_exporter.py # Markdown file generation
│   ├── scheduler.py         # Task scheduling
│   └── config.py           # Configuration management
├── dashboard/               # Solara web interface
│   ├── app.py              # Main dashboard application
│   ├── components/         # UI components
│   └── utils/             # Dashboard utilities
├── templates/              # Markdown templates
├── data/                  # SQLite database storage
├── journals/             # Generated markdown files
├── logs/                # Application logs
├── config.json          # Configuration file
├── main.py             # CLI entry point
└── README.md          # This file
```

## Data Privacy & Security

**Local-Only Processing**
- All data stays on your machine
- No external API calls or data transmission
- Firefox history accessed read-only
- Configurable data exclusion rules

**Privacy Controls**
- Exclude private browsing sessions
- Domain blacklisting support
- Automatic sensitive data filtering
- Configurable data retention

## Example Output

### Daily Journal Entry
```markdown
# Daily Journal - March 15, 2024

## Summary
Visited 45 unique websites, spent approximately 4h 23m browsing. This was a moderately productive day with balanced activities. Primary focus areas: Development (2h 15m), Research (1h 8m), Entertainment (58min).

## Statistics
- **Total Sites Visited**: 45
- **Total Time Spent**: 263 minutes (4 hours 23 minutes)
- **Productivity Score**: 6.8/10

## Activity Breakdown
### Top Categories by Time
1. **Development** - 2 hours 15 minutes (18 visits)
2. **Research** - 1 hour 8 minutes (12 visits)
3. **Entertainment** - 58 minutes (8 visits)

### Most Visited Domains
1. **github.com** (Development) - 1 hour 32 minutes (8 visits)
2. **stackoverflow.com** (Development) - 43 minutes (6 visits)
3. **youtube.com** (Entertainment) - 58 minutes (8 visits)
```

### Dashboard Features
- **Overview**: Productivity trends and category breakdowns
- **Analytics**: Heatmaps and domain analysis
- **Historical**: Data tables and export options

## Troubleshooting

### Common Issues

**Firefox Profile Not Found**
```bash
# Check if Firefox is installed and has been used
# Manual profile path configuration in config.json
"firefox": {
    "profile_path": "/path/to/firefox/profile"
}
```

**Database Permissions**
```bash
# Ensure write permissions to data directory
mkdir -p data logs journals
```

**Missing Dependencies**
```bash
# Install all dependencies with UV
uv sync

# Or install specific packages
uv add schedule streamlit plotly pandas numpy
```

**Dashboard Not Loading**
```bash
# Try direct Streamlit command
uv run streamlit run streamlit_dashboard.py --server.port 8765

# Check if Streamlit is installed
uv add streamlit
```

**Scheduler Issues**
```bash
# Make sure schedule package is installed
uv add schedule
```

## Development

### Adding Custom Categories
Modify the site categorization in `src/journal_generator.py`:

```python
def _categorize_domain(self, domain: str) -> Dict[str, Any]:
    # Add custom domain patterns
    if 'mycustomsite.com' in domain:
        category = "Custom Category"
        productivity_weight = 0.5
```

### Custom Dashboard Charts
Add new visualizations in `dashboard/components/charts.py`:

```python
def create_custom_chart(data: pd.DataFrame) -> go.Figure:
    # Your custom Plotly chart implementation
    pass
```

### Running Tests
```bash
# Run tests (when implemented)
uv run python -m pytest tests/

# Check code style
uv run python -m flake8 src/
```

## Quick Start Guide

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Generate your first journal**:
   ```bash
   uv run python main.py generate
   ```

3. **View the generated journal**:
   ```bash
   # Check the journals/ directory for the markdown file
   ls journals/
   ```

4. **Start the dashboard**:
   ```bash
   uv run streamlit run streamlit_dashboard.py --server.port 8765
   ```

5. **Open your browser** to `http://localhost:8765`

6. **Set up automation** (optional):
   ```bash
   uv run python main.py schedule --start
   ```

## Performance Notes

- **Large History Files**: The application handles large Firefox history databases efficiently by creating temporary copies
- **Memory Usage**: Dashboard components use lazy loading for optimal performance
- **Database Optimization**: SQLite database is indexed for fast queries
- **Background Processing**: Scheduler runs in a separate thread to avoid blocking

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `uv run python -m pytest`
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- **Firefox** for providing accessible browser history data
- **Streamlit** for the excellent Python web framework
- **Plotly** for interactive visualization capabilities
- **SQLite** for reliable local data storage
- **UV** for fast and reliable Python package management

---

**Made with care by Firefox users, for Firefox users**