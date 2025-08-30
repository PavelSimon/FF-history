#!/usr/bin/env python3
"""
Simple Flask-based dashboard for Firefox History Journal Generator
A lightweight alternative to the Solara dashboard that's easier to run.
"""

import sys
from pathlib import Path
import json
from datetime import date, datetime, timedelta
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config import ConfigManager
    from src.database import DatabaseManager
except ImportError:
    print("Error: Cannot import required modules. Make sure you're running from the project directory.")
    sys.exit(1)

def generate_html_dashboard() -> str:
    """Generate a simple HTML dashboard with current statistics."""
    try:
        # Load data
        config = ConfigManager()
        db_manager = DatabaseManager(config.database_path)
        
        # Get recent entries (last 7 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        entries = db_manager.get_journal_entries_range(start_date, end_date)
        
        if not entries:
            return generate_empty_dashboard()
        
        # Calculate summary statistics
        total_sites = sum(entry['total_sites_visited'] for entry in entries)
        total_time = sum(entry['total_time_spent'] for entry in entries)
        avg_productivity = sum(entry['productivity_score'] for entry in entries) / len(entries)
        
        # Get today's data if available
        today_entry = db_manager.get_journal_entry(date.today())
        today_stats = {
            'sites': today_entry['total_sites_visited'] if today_entry else 0,
            'time': today_entry['total_time_spent'] if today_entry else 0,
            'productivity': today_entry['productivity_score'] if today_entry else 0.0
        }
        
        # Get today's visited sites
        today_sites = {}
        if today_entry:
            raw_data = today_entry.get('raw_data', {})
            today_sites = raw_data.get('domain_stats', {})
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Firefox History Journal Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            color: #333;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2196F3;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 1.1em;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .section h2 {{
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #2196F3;
            padding-bottom: 10px;
        }}
        .entry-item {{
            padding: 10px;
            border-left: 4px solid #2196F3;
            margin: 10px 0;
            background-color: #f8f9fa;
        }}
        .entry-date {{
            font-weight: bold;
            color: #333;
        }}
        .entry-stats {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .productivity-high {{ border-left-color: #4CAF50; }}
        .productivity-medium {{ border-left-color: #FF9800; }}
        .productivity-low {{ border-left-color: #F44336; }}
        .commands {{
            background-color: #263238;
            color: #fff;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }}
        .commands code {{
            background-color: #37474F;
            padding: 2px 6px;
            border-radius: 4px;
        }}
        .refresh-note {{
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 20px;
        }}
        .entry-date {{
            font-weight: bold;
            color: #333;
            cursor: pointer;
            transition: color 0.3s ease;
        }}
        .entry-date:hover {{
            color: #2196F3;
            text-decoration: underline;
        }}
        .entry-details {{
            display: none;
            margin-top: 15px;
            padding: 15px;
            background-color: #fff;
            border-radius: 5px;
            border: 1px solid #e0e0e0;
            animation: slideDown 0.3s ease;
        }}
        .entry-details.show {{
            display: block;
        }}
        @keyframes slideDown {{
            from {{ opacity: 0; max-height: 0; }}
            to {{ opacity: 1; max-height: 1000px; }}
        }}
        .sites-grid {{
            display: grid;
            gap: 8px;
            margin-top: 10px;
        }}
        .site-entry {{
            padding: 8px;
            background-color: #f8f9fa;
            border-left: 3px solid;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        .site-domain {{
            font-weight: bold;
            color: #333;
        }}
        .site-stats {{
            color: #666;
            font-size: 0.85em;
        }}
        .loading {{
            color: #666;
            font-style: italic;
        }}
        .detail-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 15px;
        }}
        .detail-stat {{
            text-align: center;
            padding: 10px;
            background-color: #e3f2fd;
            border-radius: 5px;
        }}
        .detail-stat-value {{
            font-size: 1.2em;
            font-weight: bold;
            color: #1976d2;
        }}
        .detail-stat-label {{
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Firefox History Journal Dashboard</h1>
            <p>Last 7 days overview • Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{today_stats['sites']}</div>
                <div class="stat-label">Sites Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{today_stats['time']//60}h {today_stats['time']%60}m</div>
                <div class="stat-label">Time Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{today_stats['productivity']:.1f}/10</div>
                <div class="stat-label">Productivity Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(entries)}</div>
                <div class="stat-label">Active Days</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Weekly Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_sites}</div>
                    <div class="stat-label">Total Sites Visited</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_time//60}h {total_time%60}m</div>
                    <div class="stat-label">Total Browsing Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_productivity:.1f}/10</div>
                    <div class="stat-label">Average Productivity</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Recent Journal Entries</h2>
"""
        
        # Add recent entries with detailed data
        for entry in sorted(entries, key=lambda x: x['date'], reverse=True):
            entry_date = datetime.fromisoformat(entry['date']).date()
            productivity_class = (
                'productivity-high' if entry['productivity_score'] >= 7
                else 'productivity-medium' if entry['productivity_score'] >= 5
                else 'productivity-low'
            )
            
            # Get domain stats for this entry
            raw_data = entry.get('raw_data', {})
            domain_stats = raw_data.get('domain_stats', {})
            hourly_stats = raw_data.get('hourly_stats', {})
            category_breakdown = raw_data.get('category_breakdown', {})
            
            entry_id = entry_date.strftime('%Y%m%d')
            
            html += f"""
            <div class="entry-item {productivity_class}">
                <div class="entry-date" onclick="toggleDetails('{entry_id}')">{entry_date.strftime('%A, %B %d, %Y')}</div>
                <div class="entry-stats">
                    {entry['total_sites_visited']} sites • 
                    {entry['total_time_spent']//60}h {entry['total_time_spent']%60}m • 
                    Productivity: {entry['productivity_score']:.1f}/10
                    <span style="font-size: 0.8em; color: #999;"> (click for details)</span>
                </div>
                <div class="entry-details" id="details_{entry_id}">
                    <div class="detail-stats">
                        <div class="detail-stat">
                            <div class="detail-stat-value">{entry['total_sites_visited']}</div>
                            <div class="detail-stat-label">Sites Visited</div>
                        </div>
                        <div class="detail-stat">
                            <div class="detail-stat-value">{entry['total_time_spent']//60}h {entry['total_time_spent']%60}m</div>
                            <div class="detail-stat-label">Total Time</div>
                        </div>
                        <div class="detail-stat">
                            <div class="detail-stat-value">{entry['productivity_score']:.1f}/10</div>
                            <div class="detail-stat-label">Productivity</div>
                        </div>
                        <div class="detail-stat">
                            <div class="detail-stat-value">{len(category_breakdown)}</div>
                            <div class="detail-stat-label">Categories</div>
                        </div>
                    </div>"""
            
            # Add top categories if available
            if entry.get('top_categories'):
                html += "<h4>Top Categories:</h4><div class='sites-grid'>"
                for category in entry['top_categories'][:5]:
                    category_colors = {
                        'Development': '#2E8B57',
                        'Entertainment': '#FF6347',
                        'Social Media': '#FF69B4',
                        'Research': '#4682B4',
                        'News': '#32CD32',
                        'Communication': '#9370DB',
                        'Shopping': '#FFD700',
                        'Professional': '#20B2AA',
                        'Reading': '#DDA0DD',
                        'Uncategorized': '#808080'
                    }
                    color = category_colors.get(category['category'], '#808080')
                    html += f"""
                    <div class="site-entry" style="border-left-color: {color};">
                        <div class="site-domain">{category['category']}</div>
                        <div class="site-stats">{category['time_spent']} minutes • {category.get('visits', 0)} visits</div>
                    </div>"""
                html += "</div>"
            
            # Add top sites if available
            if domain_stats:
                sorted_sites = sorted(domain_stats.items(), key=lambda x: x[1].get('time_spent', 0), reverse=True)[:8]
                html += "<h4>Top Sites:</h4><div class='sites-grid'>"
                for domain, stats in sorted_sites:
                    category = stats.get('category', 'Uncategorized')
                    category_colors = {
                        'Development': '#2E8B57',
                        'Entertainment': '#FF6347',
                        'Social Media': '#FF69B4',
                        'Research': '#4682B4',
                        'News': '#32CD32',
                        'Communication': '#9370DB',
                        'Shopping': '#FFD700',
                        'Professional': '#20B2AA',
                        'Reading': '#DDA0DD',
                        'Uncategorized': '#808080'
                    }
                    color = category_colors.get(category, '#808080')
                    html += f"""
                    <div class="site-entry" style="border-left-color: {color};">
                        <div class="site-domain">{domain}</div>
                        <div class="site-stats">{stats.get('time_spent', 0)} min • {stats.get('visits', 0)} visits • {category}</div>
                    </div>"""
                html += "</div>"
            
            html += "</div></div>"
        
        html += """
        </div>
"""
        
        # Add visited sites section
        if today_sites:
            # Sort sites by time spent
            sorted_sites = sorted(today_sites.items(), key=lambda x: x[1].get('time_spent', 0), reverse=True)[:15]
            
            html += """
        <div class="section">
            <h2>Today's Top Visited Sites</h2>
"""
            for domain, stats in sorted_sites:
                time_spent = stats.get('time_spent', 0)
                visits = stats.get('visits', 0)
                category = stats.get('category', 'Uncategorized')
                
                # Color code by category
                category_colors = {
                    'Development': '#2E8B57',
                    'Entertainment': '#FF6347',
                    'Social Media': '#FF69B4',
                    'Research': '#4682B4',
                    'News': '#32CD32',
                    'Communication': '#9370DB',
                    'Shopping': '#FFD700',
                    'Professional': '#20B2AA',
                    'Reading': '#DDA0DD',
                    'Uncategorized': '#808080'
                }
                
                color = category_colors.get(category, '#808080')
                
                html += f"""
            <div class="entry-item" style="border-left-color: {color};">
                <div class="entry-date"><strong>{domain}</strong> ({category})</div>
                <div class="entry-stats">
                    {time_spent} minutes • {visits} visits
                </div>
            </div>
"""
            
            html += """
        </div>
"""
        else:
            html += """
        <div class="section">
            <h2>Today's Visited Sites</h2>
            <p>No sites data available for today. Generate a journal entry to see visited sites.</p>
        </div>
"""
        
        html += """
        <div class="section">
            <h2>Available Commands</h2>
            <div class="commands">
                <p><strong>Generate Journal:</strong><br>
                <code>uv run python main.py generate</code></p>
                
                <p><strong>Start Scheduler:</strong><br>
                <code>uv run python main.py schedule --start</code></p>
                
                <p><strong>Export Data:</strong><br>
                <code>uv run python main.py export --format json</code></p>
                
                <p><strong>View Journal Files:</strong><br>
                Check the <code>journals/</code> directory for markdown files</p>
            </div>
        </div>
        
        <div class="refresh-note">
            Refresh this page after generating new journal entries to see updated data.
        </div>
    </div>
</body>
</html>
"""
        return html
        
    except Exception as e:
        return f"""
<html><body>
<h1>Error Loading Dashboard</h1>
<p>Error: {str(e)}</p>
<p>Make sure you have generated at least one journal entry first:</p>
<pre>uv run python main.py generate</pre>
</body></html>
"""

def generate_empty_dashboard() -> str:
    """Generate dashboard when no data is available."""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Firefox History Journal Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
        .welcome { background: #f0f8ff; padding: 30px; border-radius: 10px; margin: 20px 0; }
        .command { background: #263238; color: white; padding: 15px; border-radius: 5px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="welcome">
        <h1>Welcome to Firefox History Journal Dashboard</h1>
        <p>No journal entries found. Generate your first journal entry to see analytics here.</p>
    </div>
    
    <div class="command">
        <strong>Get Started:</strong><br>
        uv run python main.py generate
    </div>
    
    <div class="command">
        <strong>Then refresh this page to see your data!</strong>
    </div>
</body>
</html>
"""

def main():
    """Generate and save HTML dashboard."""
    try:
        html_content = generate_html_dashboard()
        
        # Save to file
        dashboard_file = Path("dashboard.html")
        dashboard_file.write_text(html_content, encoding='utf-8')
        
        print(f"Dashboard generated: {dashboard_file.absolute()}")
        print(f"Open in browser: file://{dashboard_file.absolute()}")
        
        # Try to open in default browser
        try:
            import webbrowser
            webbrowser.open(f"file://{dashboard_file.absolute()}")
            print("Dashboard opened in your default browser!")
        except:
            print("Could not automatically open browser. Open the file manually.")
            
    except Exception as e:
        print(f"Error generating dashboard: {e}")

if __name__ == "__main__":
    main()