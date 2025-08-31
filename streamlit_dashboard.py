#!/usr/bin/env python3
"""
Streamlit Dashboard for Firefox History Journal Generator
Interactive web dashboard with charts and analytics.
"""

import sys
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.config import ConfigManager
    from src.database import DatabaseManager
except ImportError:
    st.error("Error: Cannot import required modules. Make sure you're running from the project directory.")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Firefox History Journal Dashboard",
    page_icon="🦊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(days: int = 30, start_date=None, end_date=None):
    """Load and cache journal data."""
    try:
        config = ConfigManager()
        db_manager = DatabaseManager(config.database_path)
        
        # Get entries for specified date range or recent entries
        if start_date and end_date:
            entries = db_manager.get_journal_entries_range(start_date, end_date)
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            entries = db_manager.get_journal_entries_range(start_date, end_date)
        
        if not entries:
            return pd.DataFrame(), {}, {}, {}
        
        # Convert to DataFrame
        df = pd.DataFrame(entries)
        df['date'] = pd.to_datetime(df['date'])
        
        # Get today's entry
        today_entry = db_manager.get_journal_entry(date.today())
        today_stats = {}
        today_sites = {}
        
        if today_entry:
            today_stats = {
                'sites': today_entry['total_sites_visited'],
                'time': today_entry['total_time_spent'],
                'productivity': today_entry['productivity_score']
            }
            
            # Extract domain statistics from raw_data
            raw_data = today_entry.get('raw_data', {})
            domain_stats = raw_data.get('domain_stats', {})
            today_sites = domain_stats
        
        # Get hourly stats for today
        hourly_stats = db_manager.get_daily_stats(date.today())
        
        return df, today_stats, hourly_stats, today_sites
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), {}, {}, {}

@st.cache_data(ttl=300)
def get_date_range():
    """Get the available date range from the database."""
    try:
        config = ConfigManager()
        db_manager = DatabaseManager(config.database_path)
        
        # Get journal entries for a large date range to find min/max dates
        # Use a very wide range to catch all possible entries
        start_range = date(2020, 1, 1)  # Far past date
        end_range = date.today() + timedelta(days=30)  # Future date
        
        all_entries = db_manager.get_journal_entries_range(start_range, end_range)
        if not all_entries:
            return None, None
            
        dates = [datetime.strptime(entry['date'], '%Y-%m-%d').date() for entry in all_entries]
        return min(dates), max(dates)
        
    except Exception as e:
        if st.session_state.get('debug_mode', False):
            st.sidebar.error(f"Debug: Error getting date range: {e}")
        return None, None

def create_productivity_chart(df: pd.DataFrame):
    """Create productivity trend chart."""
    if df.empty:
        return go.Figure().add_annotation(text="No data available", 
                                        xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)
    
    fig = go.Figure()
    
    # Add productivity score line
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['productivity_score'],
        mode='lines+markers',
        name='Productivity Score',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Add trend line
    if len(df) > 1:
        z = np.polyfit(range(len(df)), df['productivity_score'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=p(range(len(df))),
            mode='lines',
            name='Trend',
            line=dict(color='red', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title='Productivity Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Productivity Score (0-10)',
        yaxis=dict(range=[0, 10]),
        hovermode='x unified'
    )
    
    return fig

def create_time_spent_chart(df: pd.DataFrame):
    """Create time spent bar chart."""
    if df.empty:
        return go.Figure()
    
    fig = px.bar(
        df, 
        x='date', 
        y='total_time_spent',
        title='Daily Browsing Time',
        labels={'total_time_spent': 'Time (minutes)', 'date': 'Date'},
        color='productivity_score',
        color_continuous_scale='RdYlBu'
    )
    
    fig.update_layout(hovermode='x unified')
    return fig

def create_sites_chart(df: pd.DataFrame):
    """Create sites visited chart."""
    if df.empty:
        return go.Figure()
    
    fig = px.bar(
        df,
        x='date',
        y='total_sites_visited',
        title='Daily Sites Visited',
        labels={'total_sites_visited': 'Sites Visited', 'date': 'Date'},
        color='total_sites_visited',
        color_continuous_scale='Blues'
    )
    
    return fig

def create_hourly_chart(hourly_stats: Dict[int, Dict[str, int]]):
    """Create hourly activity chart."""
    if not hourly_stats:
        return go.Figure()
    
    hours = list(range(24))
    time_spent = [hourly_stats.get(hour, {}).get('time_spent', 0) for hour in hours]
    sites_visited = [hourly_stats.get(hour, {}).get('sites_visited', 0) for hour in hours]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=hours,
        y=time_spent,
        name='Time Spent (min)',
        marker_color='lightblue'
    ))
    
    fig.update_layout(
        title="Today's Hourly Activity",
        xaxis_title='Hour of Day',
        yaxis_title='Time Spent (minutes)',
        xaxis=dict(tickmode='linear', tick0=0, dtick=2)
    )
    
    return fig

def create_correlation_chart(df: pd.DataFrame):
    """Create productivity vs time correlation."""
    if df.empty or len(df) < 2:
        return go.Figure().add_annotation(text="Not enough data for correlation analysis", 
                                        xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)
    
    fig = go.Figure()
    
    # Add scatter plot points
    fig.add_trace(go.Scatter(
        x=df['total_time_spent'],
        y=df['productivity_score'],
        mode='markers',
        marker=dict(
            size=10,
            color=df['productivity_score'],
            colorscale='RdYlBu',
            colorbar=dict(title="Productivity Score"),
            line=dict(width=1, color='black')
        ),
        text=df['date'].dt.strftime('%Y-%m-%d'),
        hovertemplate='<b>%{text}</b><br>' +
                      'Time Spent: %{x} minutes<br>' +
                      'Productivity: %{y}/10<extra></extra>',
        name='Daily Data'
    ))
    
    # Add a simple trend line if we have enough data points
    if len(df) > 2:
        # Calculate correlation coefficient
        correlation = df['total_time_spent'].corr(df['productivity_score'])
        
        # Add trend line manually
        z = np.polyfit(df['total_time_spent'], df['productivity_score'], 1)
        p = np.poly1d(z)
        
        x_trend = [df['total_time_spent'].min(), df['total_time_spent'].max()]
        y_trend = [p(x) for x in x_trend]
        
        fig.add_trace(go.Scatter(
            x=x_trend,
            y=y_trend,
            mode='lines',
            line=dict(color='red', width=2, dash='dash'),
            name=f'Trend (r={correlation:.3f})',
            hovertemplate='Trend Line<extra></extra>'
        ))
    
    fig.update_layout(
        title='Productivity vs Time Spent Correlation',
        xaxis_title='Time Spent (minutes)',
        yaxis_title='Productivity Score (0-10)',
        yaxis=dict(range=[0, 10])
    )
    
    return fig

def create_sites_visited_chart(sites_data: Dict[str, Dict]):
    """Create top visited sites bar chart."""
    if not sites_data:
        return go.Figure().add_annotation(text="No sites data available", 
                                        xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)
    
    # Convert to list and sort by time spent
    sites_list = []
    for domain, stats in sites_data.items():
        sites_list.append({
            'domain': domain,
            'time_spent': stats.get('time_spent', 0),
            'visits': stats.get('visits', 0),
            'category': stats.get('category', 'Uncategorized')
        })
    
    # Sort by time spent and take top 15
    sites_list = sorted(sites_list, key=lambda x: x['time_spent'], reverse=True)[:15]
    
    if not sites_list:
        return go.Figure()
    
    # Create DataFrame for plotting
    sites_df = pd.DataFrame(sites_list)
    
    # Color mapping for categories
    color_map = {
        'Development': '#2E8B57',
        'Entertainment': '#FF6347', 
        'Social Media': '#FF69B4',
        'Research': '#4682B4',
        'News': '#32CD32',
        'Communication': '#9370DB',
        'Shopping': '#FFD700',
        'Professional': '#20B2AA',
        'Reading': '#DDA0DD',
        'Search': '#F0E68C',
        'Uncategorized': '#808080'
    }
    
    # Add colors
    sites_df['color'] = sites_df['category'].map(lambda x: color_map.get(x, '#808080'))
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=sites_df['domain'],
        x=sites_df['time_spent'],
        orientation='h',
        marker_color=sites_df['color'],
        customdata=list(zip(sites_df['visits'], sites_df['category'])),
        hovertemplate='<b>%{y}</b><br>' +
                      'Time: %{x} minutes<br>' +
                      'Visits: %{customdata[0]}<br>' +
                      'Category: %{customdata[1]}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Today's Top Visited Sites",
        xaxis_title='Time Spent (minutes)',
        yaxis_title='Website',
        height=400
    )
    
    return fig

def show_date_details(selected_date: str):
    """Display detailed statistics for a selected date."""
    try:
        from datetime import datetime
        target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
        
        config = ConfigManager()
        db_manager = DatabaseManager(config.database_path)
        
        # Get journal entry for the selected date
        entry = db_manager.get_journal_entry(target_date)
        
        if not entry:
            st.error(f"No data found for {selected_date}")
            return
        
        # Create a modal-like container
        st.markdown("---")
        st.header(f"📊 Detailed Statistics - {selected_date}")
        
        # Close button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("❌ Close Details", key="close_details"):
                st.session_state.show_details = False
                st.rerun()
        
        # Main statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sites Visited", entry['total_sites_visited'])
        
        with col2:
            time_spent = entry['total_time_spent']
            hours = time_spent // 60
            minutes = time_spent % 60
            st.metric("Total Time", f"{hours}h {minutes}m")
        
        with col3:
            st.metric("Productivity Score", f"{entry['productivity_score']:.1f}/10")
        
        with col4:
            # Get hourly data for this date
            hourly_stats = db_manager.get_daily_stats(target_date)
            active_hours = len([h for h in hourly_stats.values() if h.get('time_spent', 0) > 0])
            st.metric("Active Hours", active_hours)
        
        # Extract detailed data from raw_data
        raw_data = entry.get('raw_data', {})
        domain_stats = raw_data.get('domain_stats', {})
        
        if domain_stats:
            # Create two tabs for different views
            tab1, tab2, tab3 = st.tabs(["📈 Charts", "📋 Detailed Data", "🕒 Hourly Activity"])
            
            with tab1:
                # Top sites chart for this date
                col1, col2 = st.columns(2)
                
                with col1:
                    sites_fig = create_sites_visited_chart(domain_stats)
                    sites_fig.update_layout(title=f"Top Sites - {selected_date}")
                    st.plotly_chart(sites_fig, width='stretch')
                
                with col2:
                    # Category breakdown pie chart
                    categories = {}
                    for domain, stats in domain_stats.items():
                        category = stats.get('category', 'Uncategorized')
                        time_spent = stats.get('time_spent', 0)
                        
                        if category not in categories:
                            categories[category] = 0
                        categories[category] += time_spent
                    
                    if categories:
                        fig = px.pie(
                            values=list(categories.values()),
                            names=list(categories.keys()),
                            title=f"Time by Category - {selected_date}"
                        )
                        st.plotly_chart(fig, width='stretch')
            
            with tab2:
                # Detailed sites table
                sites_data = []
                for domain, stats in domain_stats.items():
                    sites_data.append({
                        'Domain': domain,
                        'Time (min)': stats.get('time_spent', 0),
                        'Visits': stats.get('visits', 0),
                        'Category': stats.get('category', 'Uncategorized'),
                        'Avg Time/Visit': round(stats.get('time_spent', 0) / max(stats.get('visits', 1), 1), 1),
                        'Page Titles': len(stats.get('titles', []))
                    })
                
                sites_df = pd.DataFrame(sites_data)
                sites_df = sites_df.sort_values('Time (min)', ascending=False)
                
                st.dataframe(sites_df, width='stretch')
                
                # Show some page titles
                st.subheader("📄 Sample Page Titles")
                title_examples = []
                for domain, stats in list(domain_stats.items())[:5]:
                    titles = stats.get('titles', [])
                    if titles:
                        for title in titles[:3]:  # Show up to 3 titles per domain
                            if len(title) > 10:  # Skip very short titles
                                title_examples.append(f"**{domain}**: {title}")
                
                if title_examples:
                    for example in title_examples[:10]:  # Show max 10 examples
                        st.text(example)
                else:
                    st.info("No page titles available for this date")
            
            with tab3:
                # Hourly activity chart
                if hourly_stats:
                    hourly_fig = create_hourly_chart(hourly_stats)
                    hourly_fig.update_layout(title=f"Hourly Activity - {selected_date}")
                    st.plotly_chart(hourly_fig, width='stretch')
                    
                    # Hourly breakdown table
                    hourly_data = []
                    for hour in range(24):
                        stats = hourly_stats.get(hour, {})
                        if stats.get('time_spent', 0) > 0:
                            hourly_data.append({
                                'Hour': f"{hour:02d}:00",
                                'Time Spent (min)': stats.get('time_spent', 0),
                                'Sites Visited': stats.get('sites_visited', 0),
                                'Visits': stats.get('total_visits', 0)
                            })
                    
                    if hourly_data:
                        hourly_df = pd.DataFrame(hourly_data)
                        st.dataframe(hourly_df, width='stretch')
                    else:
                        st.info("No hourly activity data available")
                else:
                    st.info("No hourly activity data available for this date")
        else:
            st.warning("No detailed site data available for this date")
        
        st.markdown("---")
        
    except Exception as e:
        st.error(f"Error loading details for {selected_date}: {e}")

def main():
    """Main Streamlit dashboard."""
    
    # Header
    st.title("🦊 Firefox History Journal Dashboard")
    st.markdown("*Analyze your browsing patterns and productivity*")
    
    # Sidebar
    st.sidebar.header("Settings")
    
    # Debug options
    with st.sidebar.expander("🔧 Debug Options"):
        if st.button("🔄 Force Refresh All Data"):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🐛 Debug Mode"):
            st.session_state.debug_mode = not st.session_state.get('debug_mode', False)
            st.rerun()
        
        if st.session_state.get('debug_mode', False):
            st.write("🐛 **Debug Mode Active**")
    
    # Get available date range
    min_date, max_date = get_date_range()
    
    if min_date and max_date:
        st.sidebar.info(f"📅 **Available data range:**\n\n{min_date} to {max_date}")
        
        # Date range selection option
        date_option = st.sidebar.radio(
            "Select time period:",
            ["Recent days", "Custom date range"],
            index=0
        )
        
        if date_option == "Recent days":
            days_to_show = st.sidebar.slider("Days to analyze", 1, 90, 14)
            df, today_stats, hourly_stats, today_sites = load_data(days_to_show)
        else:
            # Custom date range
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start date",
                    value=max_date - timedelta(days=14),
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col2:
                end_date = st.date_input(
                    "End date",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
            
            # Validate date range
            if start_date > end_date:
                st.sidebar.error("Start date must be before end date")
                df, today_stats, hourly_stats, today_sites = pd.DataFrame(), {}, {}, {}
            else:
                df, today_stats, hourly_stats, today_sites = load_data(None, start_date, end_date)
    else:
        # Fallback to days slider if no date range available
        st.sidebar.warning("No data available yet")
        days_to_show = st.sidebar.slider("Days to analyze", 1, 90, 14)
        df, today_stats, hourly_stats, today_sites = load_data(days_to_show)
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    if df.empty:
        st.warning("No journal data found. Generate your first journal entry:")
        st.code("uv run python main.py generate")
        st.info("After generating journal entries, refresh this dashboard to see your data.")
        return
    
    # Today's stats
    st.header("📊 Today's Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sites_today = today_stats.get('sites', 0)
        st.metric("Sites Visited Today", sites_today)
    
    with col2:
        time_today = today_stats.get('time', 0)
        hours = time_today // 60
        minutes = time_today % 60
        st.metric("Time Spent Today", f"{hours}h {minutes}m")
    
    with col3:
        productivity_today = today_stats.get('productivity', 0)
        st.metric("Productivity Score", f"{productivity_today:.1f}/10")
    
    with col4:
        active_days = len(df)
        st.metric("Active Days", active_days)
    
    # Charts
    st.header("📈 Analytics")
    
    # First row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        productivity_fig = create_productivity_chart(df)
        st.plotly_chart(productivity_fig, width='stretch')
    
    with col2:
        time_fig = create_time_spent_chart(df)
        st.plotly_chart(time_fig, width='stretch')
    
    # Second row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        sites_fig = create_sites_chart(df)
        st.plotly_chart(sites_fig, width='stretch')
    
    with col2:
        hourly_fig = create_hourly_chart(hourly_stats)
        st.plotly_chart(hourly_fig, width='stretch')
    
    # Sites visited section
    st.header("🌐 Today's Visited Sites")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sites_fig = create_sites_visited_chart(today_sites)
        st.plotly_chart(sites_fig, width='stretch')
    
    with col2:
        if today_sites:
            st.subheader("Site Summary")
            
            # Category breakdown
            categories = {}
            total_time = 0
            for domain, stats in today_sites.items():
                category = stats.get('category', 'Uncategorized')
                time_spent = stats.get('time_spent', 0)
                total_time += time_spent
                
                if category not in categories:
                    categories[category] = {'time': 0, 'sites': 0}
                categories[category]['time'] += time_spent
                categories[category]['sites'] += 1
            
            # Show top categories
            sorted_categories = sorted(categories.items(), key=lambda x: x[1]['time'], reverse=True)
            
            for category, stats in sorted_categories[:5]:
                percentage = (stats['time'] / total_time * 100) if total_time > 0 else 0
                st.metric(
                    category,
                    f"{stats['time']} min",
                    f"{percentage:.1f}% • {stats['sites']} sites"
                )
        else:
            st.info("No sites data available for today")
    
    # Detailed sites table
    if today_sites:
        with st.expander("📋 View All Visited Sites Details", expanded=False):
            sites_data = []
            for domain, stats in today_sites.items():
                sites_data.append({
                    'Domain': domain,
                    'Time Spent (min)': stats.get('time_spent', 0),
                    'Visits': stats.get('visits', 0),
                    'Category': stats.get('category', 'Uncategorized'),
                    'Titles Count': len(stats.get('titles', []))
                })
            
            sites_df = pd.DataFrame(sites_data)
            sites_df = sites_df.sort_values('Time Spent (min)', ascending=False)
            
            st.dataframe(sites_df, width='stretch')
            
            # Show some page titles if available
            st.subheader("📄 Sample Page Titles")
            title_examples = []
            for domain, stats in list(today_sites.items())[:5]:
                titles = stats.get('titles', [])
                if titles:
                    for title in titles[:2]:  # Show up to 2 titles per domain
                        if len(title) > 10:  # Skip very short titles
                            title_examples.append(f"**{domain}**: {title}")
            
            if title_examples:
                for example in title_examples[:8]:  # Show max 8 examples
                    st.text(example)
            else:
                st.info("No page titles available")
    
    # Correlation analysis
    st.header("🔍 Advanced Analytics")
    correlation_fig = create_correlation_chart(df)
    st.plotly_chart(correlation_fig, width='stretch')
    
    # Data table
    st.header("📋 Recent Journal Entries")
    
    if not df.empty:
        # Prepare display data
        display_df = df.copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df['time_formatted'] = display_df['total_time_spent'].apply(
            lambda x: f"{x//60}h {x%60}m" if x >= 60 else f"{x}m"
        )
        
        # Create clickable entries using columns and buttons
        st.markdown("*Click on a date to view detailed statistics*")
        
        # Display entries with clickable dates
        for idx, row in display_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
            
            with col1:
                # Use button for clickable date
                if st.button(f"📅 {row['date']}", key=f"date_{row['date']}", help="Click to view details"):
                    st.session_state.selected_date = row['date']
                    st.session_state.show_details = True
            
            with col2:
                st.write(f"**{row['total_sites_visited']}** sites")
            
            with col3:
                st.write(f"**{row['time_formatted']}**")
            
            with col4:
                st.write(f"**{row['productivity_score']:.1f}/10**")
            
            with col5:
                # Get productivity color
                score = row['productivity_score']
                if score >= 7:
                    color = "🟢"
                elif score >= 5:
                    color = "🟡"
                else:
                    color = "🔴"
                st.write(color)
        
        # Show detailed view if a date is selected
        if st.session_state.get('show_details', False) and st.session_state.get('selected_date'):
            show_date_details(st.session_state.selected_date)
    
    # Summary statistics
    if not df.empty:
        st.header("📊 Summary Statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_sites = df['total_sites_visited'].mean()
            st.metric("Average Sites/Day", f"{avg_sites:.1f}")
        
        with col2:
            avg_time = df['total_time_spent'].mean()
            avg_hours = avg_time // 60
            avg_minutes = avg_time % 60
            st.metric("Average Time/Day", f"{avg_hours:.0f}h {avg_minutes:.0f}m")
        
        with col3:
            avg_productivity = df['productivity_score'].mean()
            st.metric("Average Productivity", f"{avg_productivity:.1f}/10")
    
    # Footer with commands
    st.header("🔧 Available Commands")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.code("""
# Generate new journal entry
uv run python main.py generate

# Start scheduler
uv run python main.py schedule --start
        """)
    
    with col2:
        st.code("""
# Export data
uv run python main.py export --format json

# Simple HTML dashboard
uv run python simple_dashboard.py
        """)

if __name__ == "__main__":
    main()