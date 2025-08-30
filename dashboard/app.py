import sys
from pathlib import Path

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "dashboard"))

import solara
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional
import plotly.graph_objects as go

from utils.data_loader import DataLoader
from components.charts import (
    create_productivity_trend_chart,
    create_category_breakdown_chart,
    create_daily_activity_chart,
    create_activity_heatmap,
    create_top_domains_chart,
    create_weekly_pattern_chart,
    create_productivity_vs_time_scatter
)

# Global data loader
data_loader = DataLoader()

# Reactive state
days_filter = solara.reactive(7)
selected_date = solara.reactive(date.today())
current_page = solara.reactive("overview")

@solara.component
def Header():
    """App header with navigation."""
    with solara.Row():
        with solara.Column(size=8):
            solara.Markdown("# 📊 Firefox History Journal Dashboard")
            solara.Markdown("*Analyze your browsing patterns and productivity*")
        
        with solara.Column(size=4):
            solara.Markdown(f"**Today:** {date.today().strftime('%B %d, %Y')}")

@solara.component
def NavigationTabs():
    """Navigation tabs for different pages."""
    pages = [
        ("overview", "📈 Overview"),
        ("analytics", "🔍 Analytics"),
        ("historical", "📅 Historical")
    ]
    
    with solara.Row():
        for page_key, page_name in pages:
            is_active = current_page.value == page_key
            style = {"background-color": "#e3f2fd" if is_active else "transparent"}
            
            def set_page(page=page_key):
                current_page.set(page)
            
            solara.Button(
                page_name,
                on_click=lambda: set_page(),
                style=style
            )

@solara.component
def Filters():
    """Filter components."""
    with solara.Card("Filters"):
        with solara.Row():
            # Days filter
            solara.SliderInt(
                "Days to Show",
                value=days_filter,
                min=1,
                max=90,
                step=1
            )
            
            # Date picker for specific date analysis
            solara.InputDate(
                "Selected Date",
                value=selected_date
            )

@solara.component
def SummaryCards(summary_stats: Dict[str, Any]):
    """Summary statistics cards."""
    with solara.Row():
        with solara.Column(size=3):
            with solara.Card():
                solara.Markdown(f"### {summary_stats['total_sites']}")
                solara.Markdown("**Total Sites Visited**")
        
        with solara.Column(size=3):
            with solara.Card():
                hours = summary_stats['total_time'] // 60
                minutes = summary_stats['total_time'] % 60
                solara.Markdown(f"### {hours}h {minutes}m")
                solara.Markdown("**Total Time Spent**")
        
        with solara.Column(size=3):
            with solara.Card():
                solara.Markdown(f"### {summary_stats['avg_productivity']}/10")
                solara.Markdown("**Average Productivity**")
        
        with solara.Column(size=3):
            with solara.Card():
                solara.Markdown(f"### {summary_stats['active_days']}")
                solara.Markdown("**Active Days**")

@solara.component
def OverviewPage():
    """Main overview page."""
    # Load data
    summary_stats = data_loader.get_summary_stats(days_filter.value)
    productivity_data = data_loader.get_productivity_trend(days_filter.value)
    category_data = data_loader.get_category_breakdown(days_filter.value)
    daily_stats = data_loader.load_daily_stats(selected_date.value)
    
    # Summary cards
    SummaryCards(summary_stats)
    
    # Charts
    with solara.Row():
        with solara.Column(size=6):
            with solara.Card("Productivity Trend"):
                fig = create_productivity_trend_chart(productivity_data)
                solara.FigurePlotly(fig)
        
        with solara.Column(size=6):
            with solara.Card("Category Breakdown"):
                fig = create_category_breakdown_chart(category_data)
                solara.FigurePlotly(fig)
    
    with solara.Row():
        with solara.Column(size=12):
            with solara.Card(f"Daily Activity - {selected_date.value.strftime('%B %d, %Y')}"):
                fig = create_daily_activity_chart(daily_stats)
                solara.FigurePlotly(fig)

@solara.component
def AnalyticsPage():
    """Advanced analytics page."""
    # Load data
    domain_data = data_loader.load_domain_stats(selected_date.value)
    heatmap_data = data_loader.get_activity_heatmap_data(days_filter.value)
    productivity_data = data_loader.get_productivity_trend(days_filter.value)
    
    with solara.Row():
        with solara.Column(size=6):
            with solara.Card("Top Domains"):
                fig = create_top_domains_chart(domain_data)
                solara.FigurePlotly(fig)
        
        with solara.Column(size=6):
            with solara.Card("Weekly Pattern"):
                fig = create_weekly_pattern_chart(heatmap_data)
                solara.FigurePlotly(fig)
    
    with solara.Row():
        with solara.Column(size=6):
            with solara.Card("Activity Heatmap"):
                fig = create_activity_heatmap(heatmap_data)
                solara.FigurePlotly(fig)
        
        with solara.Column(size=6):
            with solara.Card("Productivity vs Time Correlation"):
                entries_df = data_loader.load_journal_entries(days_filter.value)
                fig = create_productivity_vs_time_scatter(entries_df)
                solara.FigurePlotly(fig)

@solara.component
def HistoricalPage():
    """Historical data view."""
    entries_df = data_loader.load_journal_entries(days_filter.value)
    
    with solara.Card("Historical Journal Entries"):
        if entries_df.empty:
            solara.Markdown("No historical data available.")
        else:
            # Display data table
            display_df = entries_df[['date', 'total_sites_visited', 'total_time_spent', 'productivity_score']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df.columns = ['Date', 'Sites Visited', 'Time Spent (min)', 'Productivity Score']
            
            solara.DataFrame(display_df)
    
    # Export functionality
    with solara.Card("Data Export"):
        solara.Markdown("**Export Options:**")
        
        def export_json():
            # This would trigger a download in a real implementation
            solara.Info("JSON export would be triggered here")
        
        def export_csv():
            # This would trigger a download in a real implementation
            solara.Info("CSV export would be triggered here")
        
        with solara.Row():
            solara.Button("Export JSON", on_click=export_json)
            solara.Button("Export CSV", on_click=export_csv)

@solara.component
def ErrorBoundary(children):
    """Error boundary to catch and display errors gracefully."""
    try:
        return children
    except Exception as e:
        with solara.Card("Error"):
            solara.Error(f"An error occurred: {str(e)}")
            solara.Markdown("Please check your data and try again.")

@solara.component
def Page():
    """Main page component."""
    with ErrorBoundary():
        # Header
        Header()
        
        # Navigation
        NavigationTabs()
        
        # Filters
        Filters()
        
        # Page content based on current page
        if current_page.value == "overview":
            OverviewPage()
        elif current_page.value == "analytics":
            AnalyticsPage()
        elif current_page.value == "historical":
            HistoricalPage()
        else:
            OverviewPage()

# Auto-refresh functionality
@solara.component
def AutoRefresh():
    """Auto-refresh component to update data periodically."""
    refresh_interval = 300  # 5 minutes in seconds
    
    def refresh_data():
        # Force data reload by updating reactive state
        current_time = datetime.now()
        # This would trigger a re-render and data reload
        pass
    
    # In a real implementation, you'd set up a timer here
    # For now, we'll just provide a manual refresh button
    with solara.Row():
        with solara.Column(size=12):
            def manual_refresh():
                # Clear any cached data and force reload
                solara.Info("Data refreshed!")
            
            solara.Button("🔄 Refresh Data", on_click=manual_refresh)

def main(host: str = "localhost", port: int = 8765):
    """Main entry point for the dashboard."""
    print(f"Starting Firefox History Dashboard on http://{host}:{port}")
    print("Dashboard features:")
    print("  - Real-time browsing analytics") 
    print("  - Productivity tracking")
    print("  - Interactive visualizations")
    print("  - Historical data analysis")
    print("\nPress Ctrl+C to stop the server")
    
    # Use subprocess to run solara command
    import subprocess
    import os
    
    try:
        # Get the current file path for the dashboard app
        app_file = os.path.abspath(__file__)
        
        # Run solara server
        subprocess.run([
            "solara", "run", f"{app_file}:Page",
            "--host", host,
            "--port", str(port)
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to start Solara server: {e}")
        print("Try running manually: solara run dashboard/app.py:Page")
    except FileNotFoundError:
        print("[ERROR] Solara command not found. Make sure Solara is installed.")
        print("Install with: pip install solara")

if __name__ == "__main__":
    main()