import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List
import solara

def create_productivity_trend_chart(data: pd.DataFrame) -> go.Figure:
    """Create productivity trend line chart."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = go.Figure()
    
    # Add productivity score line
    fig.add_trace(go.Scatter(
        x=data['date'],
        y=data['productivity_score'],
        mode='lines+markers',
        name='Productivity Score',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    # Add moving average if available
    if 'productivity_ma' in data.columns:
        fig.add_trace(go.Scatter(
            x=data['date'],
            y=data['productivity_ma'],
            mode='lines',
            name='7-day Moving Average',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
    
    fig.update_layout(
        title='Productivity Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Productivity Score (0-10)',
        yaxis=dict(range=[0, 10]),
        hovermode='x unified',
        template='plotly_white'
    )
    
    return fig

def create_category_breakdown_chart(data: pd.DataFrame) -> go.Figure:
    """Create category breakdown pie chart."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Aggregate by category
    category_totals = data.groupby('category')['time_spent'].sum().reset_index()
    category_totals = category_totals.sort_values('time_spent', ascending=False)
    
    # Color map for categories
    color_map = {
        'Development': '#2E8B57',
        'Entertainment': '#FF6347',
        'Social Media': '#FF69B4',
        'Research': '#4682B4',
        'News': '#32CD32',
        'Communication': '#9370DB',
        'Shopping': '#FFD700',
        'Uncategorized': '#808080'
    }
    
    colors = [color_map.get(cat, '#808080') for cat in category_totals['category']]
    
    fig = go.Figure(data=[go.Pie(
        labels=category_totals['category'],
        values=category_totals['time_spent'],
        marker_colors=colors,
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Time: %{value} minutes<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title='Time Spent by Category',
        template='plotly_white'
    )
    
    return fig

def create_daily_activity_chart(data: pd.DataFrame) -> go.Figure:
    """Create daily activity bar chart."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Ensure data is sorted by hour
    data = data.sort_values('hour')
    
    fig = go.Figure(data=[
        go.Bar(
            x=data['hour'],
            y=data['time_spent'],
            name='Time Spent',
            marker_color='lightblue',
            hovertemplate='<b>Hour %{x}:00</b><br>Time Spent: %{y} minutes<br>Sites Visited: %{customdata}<extra></extra>',
            customdata=data['sites_visited']
        )
    ])
    
    fig.update_layout(
        title='Hourly Activity Distribution',
        xaxis_title='Hour of Day',
        yaxis_title='Time Spent (minutes)',
        xaxis=dict(tickmode='linear', tick0=0, dtick=2),
        template='plotly_white'
    )
    
    return fig

def create_activity_heatmap(data: pd.DataFrame) -> go.Figure:
    """Create activity heatmap showing day vs hour."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Pivot data for heatmap
    heatmap_data = data.pivot(index='date', columns='hour', values='activity_level')
    heatmap_data = heatmap_data.fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=[f"{h:02d}:00" for h in range(24)],
        y=[d.strftime('%Y-%m-%d') for d in heatmap_data.index],
        colorscale='Blues',
        hovertemplate='<b>%{y}</b><br>Hour: %{x}<br>Activity: %{z} minutes<extra></extra>'
    ))
    
    fig.update_layout(
        title='Activity Heatmap (Date vs Hour)',
        xaxis_title='Hour of Day',
        yaxis_title='Date',
        template='plotly_white'
    )
    
    return fig

def create_top_domains_chart(data: pd.DataFrame) -> go.Figure:
    """Create top domains horizontal bar chart."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Sort by time spent and take top 10
    data = data.sort_values('time_spent', ascending=True).tail(10)
    
    # Color by category
    category_colors = {
        'Development': '#2E8B57',
        'Entertainment': '#FF6347',
        'Social Media': '#FF69B4',
        'Research': '#4682B4',
        'News': '#32CD32',
        'Communication': '#9370DB',
        'Shopping': '#FFD700',
        'Uncategorized': '#808080'
    }
    
    colors = [category_colors.get(cat, '#808080') for cat in data['category']]
    
    fig = go.Figure(data=[
        go.Bar(
            x=data['time_spent'],
            y=data['domain'],
            orientation='h',
            marker_color=colors,
            hovertemplate='<b>%{y}</b><br>Time: %{x} minutes<br>Visits: %{customdata}<extra></extra>',
            customdata=data['visits']
        )
    ])
    
    fig.update_layout(
        title='Top Domains by Time Spent',
        xaxis_title='Time Spent (minutes)',
        yaxis_title='Domain',
        template='plotly_white'
    )
    
    return fig

def create_weekly_pattern_chart(data: pd.DataFrame) -> go.Figure:
    """Create weekly pattern chart showing average activity by day of week."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    # Group by day of week and calculate average activity
    weekly_pattern = data.groupby('day_of_week')['activity_level'].mean().reset_index()
    
    # Map day numbers to names
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_pattern['day_name'] = weekly_pattern['day_of_week'].map(lambda x: day_names[x])
    
    fig = go.Figure(data=[
        go.Bar(
            x=weekly_pattern['day_name'],
            y=weekly_pattern['activity_level'],
            marker_color='lightgreen',
            hovertemplate='<b>%{x}</b><br>Average Activity: %{y:.1f} minutes<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Average Activity by Day of Week',
        xaxis_title='Day of Week',
        yaxis_title='Average Activity (minutes)',
        template='plotly_white'
    )
    
    return fig

def create_productivity_vs_time_scatter(data: pd.DataFrame) -> go.Figure:
    """Create scatter plot of productivity vs time spent."""
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        return fig
    
    fig = go.Figure(data=[
        go.Scatter(
            x=data['total_time_spent'],
            y=data['productivity_score'],
            mode='markers',
            marker=dict(
                size=10,
                color=data['productivity_score'],
                colorscale='RdYlBu',
                colorbar=dict(title="Productivity Score"),
                line=dict(width=1, color='black')
            ),
            text=data['date'].dt.strftime('%Y-%m-%d'),
            hovertemplate='<b>%{text}</b><br>Time Spent: %{x} minutes<br>Productivity: %{y}/10<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title='Productivity vs Time Spent',
        xaxis_title='Time Spent (minutes)',
        yaxis_title='Productivity Score (0-10)',
        yaxis=dict(range=[0, 10]),
        template='plotly_white'
    )
    
    return fig