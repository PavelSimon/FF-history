import sys
import os
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

try:
    from src.config import ConfigManager
    from src.database import DatabaseManager
except ImportError:
    # Fallback for different import scenarios
    from config import ConfigManager
    from database import DatabaseManager

class DataLoader:
    def __init__(self):
        self.config = ConfigManager()
        self.db_manager = DatabaseManager(self.config.database_path)
    
    def load_journal_entries(self, days: int = 30) -> pd.DataFrame:
        """Load recent journal entries as DataFrame."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        entries = self.db_manager.get_journal_entries_range(start_date, end_date)
        
        if not entries:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(entries)
        df['date'] = pd.to_datetime(df['date'])
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        return df
    
    def load_daily_stats(self, target_date: date = None) -> pd.DataFrame:
        """Load hourly stats for a specific date."""
        target_date = target_date or date.today()
        
        stats = self.db_manager.get_daily_stats(target_date)
        
        if not stats:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for hour, stat in stats.items():
            data.append({
                'hour': hour,
                'sites_visited': stat['sites_visited'],
                'time_spent': stat['time_spent']
            })
        
        return pd.DataFrame(data)
    
    def load_category_breakdown(self, days: int = 7) -> pd.DataFrame:
        """Load category breakdown for recent days."""
        entries_df = self.load_journal_entries(days)
        
        if entries_df.empty:
            return pd.DataFrame()
        
        # Extract category data
        category_data = []
        for _, entry in entries_df.iterrows():
            entry_date = entry['date'].date()
            categories = entry['top_categories']
            
            for category in categories:
                category_data.append({
                    'date': entry_date,
                    'category': category['category'],
                    'time_spent': category['time_spent'],
                    'visits': category.get('visits', 0),
                    'productivity_weight': category.get('productivity_weight', 0.0)
                })
        
        return pd.DataFrame(category_data)
    
    def load_domain_stats(self, target_date: date = None) -> pd.DataFrame:
        """Load domain statistics for a specific date."""
        target_date = target_date or date.today()
        
        entry = self.db_manager.get_journal_entry(target_date)
        
        if not entry or not entry.get('raw_data'):
            return pd.DataFrame()
        
        domain_stats = entry['raw_data'].get('domain_stats', {})
        
        data = []
        for domain, stats in domain_stats.items():
            data.append({
                'domain': domain,
                'visits': stats['visits'],
                'time_spent': stats['time_spent'],
                'category': stats.get('category', 'Uncategorized'),
                'titles_count': len(stats.get('titles', []))
            })
        
        return pd.DataFrame(data)
    
    def get_productivity_trend(self, days: int = 30) -> pd.DataFrame:
        """Get productivity score trend over time."""
        entries_df = self.load_journal_entries(days)
        
        if entries_df.empty:
            return pd.DataFrame()
        
        # Select relevant columns and sort by date
        trend_df = entries_df[['date', 'productivity_score', 'total_time_spent']].copy()
        trend_df = trend_df.sort_values('date')
        
        # Calculate moving average
        trend_df['productivity_ma'] = trend_df['productivity_score'].rolling(window=7, min_periods=1).mean()
        
        return trend_df
    
    def get_activity_heatmap_data(self, days: int = 30) -> pd.DataFrame:
        """Get hourly activity data for heatmap visualization."""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get all dates in range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        
        heatmap_data = []
        
        for current_date in date_range:
            current_date = current_date.date()
            daily_stats = self.db_manager.get_daily_stats(current_date)
            
            # Create entry for each hour
            for hour in range(24):
                activity_level = 0
                if hour in daily_stats:
                    activity_level = daily_stats[hour]['time_spent']
                
                heatmap_data.append({
                    'date': current_date,
                    'hour': hour,
                    'activity_level': activity_level,
                    'weekday': current_date.strftime('%A'),
                    'day_of_week': current_date.weekday()
                })
        
        return pd.DataFrame(heatmap_data)
    
    def get_top_sites_data(self, days: int = 7) -> pd.DataFrame:
        """Get aggregated top sites data."""
        category_df = self.load_category_breakdown(days)
        
        if category_df.empty:
            return pd.DataFrame()
        
        # Aggregate by category
        aggregated = category_df.groupby('category').agg({
            'time_spent': 'sum',
            'visits': 'sum',
            'productivity_weight': 'mean'
        }).reset_index()
        
        # Sort by time spent
        aggregated = aggregated.sort_values('time_spent', ascending=False)
        
        return aggregated
    
    def get_summary_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        entries_df = self.load_journal_entries(days)
        
        if entries_df.empty:
            return {
                'total_sites': 0,
                'total_time': 0,
                'avg_productivity': 0.0,
                'active_days': 0,
                'most_productive_day': 'N/A',
                'least_productive_day': 'N/A'
            }
        
        # Calculate summary statistics
        total_sites = entries_df['total_sites_visited'].sum()
        total_time = entries_df['total_time_spent'].sum()
        avg_productivity = entries_df['productivity_score'].mean()
        active_days = len(entries_df)
        
        # Find most/least productive days
        most_productive_idx = entries_df['productivity_score'].idxmax()
        least_productive_idx = entries_df['productivity_score'].idxmin()
        
        most_productive_day = entries_df.loc[most_productive_idx, 'date'].strftime('%Y-%m-%d')
        least_productive_day = entries_df.loc[least_productive_idx, 'date'].strftime('%Y-%m-%d')
        
        return {
            'total_sites': int(total_sites),
            'total_time': int(total_time),
            'avg_productivity': round(float(avg_productivity), 2),
            'active_days': active_days,
            'most_productive_day': most_productive_day,
            'least_productive_day': least_productive_day
        }