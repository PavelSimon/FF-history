import sqlite3
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "./data/journal.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    total_sites_visited INTEGER,
                    total_time_spent INTEGER,
                    top_categories TEXT,
                    productivity_score REAL,
                    summary TEXT,
                    raw_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS site_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    productivity_weight REAL DEFAULT 0.0
                );
                
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    hour INTEGER NOT NULL,
                    sites_visited INTEGER,
                    time_spent INTEGER,
                    UNIQUE(date, hour)
                );
                
                CREATE INDEX IF NOT EXISTS idx_journal_date ON journal_entries(date);
                CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_stats(date);
            """)
        
        # Insert default site categories
        self._insert_default_categories()
    
    def _insert_default_categories(self):
        """Insert default site categories with productivity weights."""
        default_categories = [
            ("github.com", "Development", 0.8),
            ("stackoverflow.com", "Development", 0.7),
            ("docs.python.org", "Development", 0.8),
            ("youtube.com", "Entertainment", -0.3),
            ("facebook.com", "Social Media", -0.2),
            ("twitter.com", "Social Media", -0.2),
            ("linkedin.com", "Professional", 0.4),
            ("medium.com", "Reading", 0.5),
            ("reddit.com", "Social Media", -0.1),
            ("wikipedia.org", "Research", 0.6),
            ("google.com", "Search", 0.1),
        ]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO site_categories (domain, category, productivity_weight) VALUES (?, ?, ?)",
                default_categories
            )
    
    def save_journal_entry(self, entry_date: date, data: Dict[str, Any]) -> bool:
        """Save a journal entry for a specific date."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO journal_entries 
                    (date, total_sites_visited, total_time_spent, top_categories, 
                     productivity_score, summary, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry_date.isoformat(),
                    data.get('total_sites_visited', 0),
                    data.get('total_time_spent', 0),
                    json.dumps(data.get('top_categories', [])),
                    data.get('productivity_score', 0.0),
                    data.get('summary', ''),
                    json.dumps(data.get('raw_data', {}))
                ))
            return True
        except Exception as e:
            logger.error(f"Error saving journal entry: {e}")
            return False
    
    def get_journal_entry(self, entry_date: date) -> Optional[Dict[str, Any]]:
        """Retrieve a journal entry for a specific date."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM journal_entries WHERE date = ?",
                    (entry_date.isoformat(),)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        'id': row['id'],
                        'date': row['date'],
                        'total_sites_visited': row['total_sites_visited'],
                        'total_time_spent': row['total_time_spent'],
                        'top_categories': json.loads(row['top_categories'] or '[]'),
                        'productivity_score': row['productivity_score'],
                        'summary': row['summary'],
                        'raw_data': json.loads(row['raw_data'] or '{}'),
                        'created_at': row['created_at']
                    }
        except Exception as e:
            logger.error(f"Error retrieving journal entry: {e}")
        return None
    
    def get_journal_entries_range(self, start_date: date, end_date: date) -> List[Dict[str, Any]]:
        """Retrieve journal entries within a date range."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM journal_entries WHERE date BETWEEN ? AND ? ORDER BY date",
                    (start_date.isoformat(), end_date.isoformat())
                )
                
                entries = []
                for row in cursor.fetchall():
                    entries.append({
                        'id': row['id'],
                        'date': row['date'],
                        'total_sites_visited': row['total_sites_visited'],
                        'total_time_spent': row['total_time_spent'],
                        'top_categories': json.loads(row['top_categories'] or '[]'),
                        'productivity_score': row['productivity_score'],
                        'summary': row['summary'],
                        'raw_data': json.loads(row['raw_data'] or '{}'),
                        'created_at': row['created_at']
                    })
                return entries
        except Exception as e:
            logger.error(f"Error retrieving journal entries range: {e}")
        return []
    
    def save_daily_stats(self, entry_date: date, hourly_stats: Dict[int, Dict[str, int]]):
        """Save hourly statistics for a day."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing stats for the date
                conn.execute("DELETE FROM daily_stats WHERE date = ?", (entry_date.isoformat(),))
                
                # Insert new stats
                for hour, stats in hourly_stats.items():
                    conn.execute("""
                        INSERT INTO daily_stats (date, hour, sites_visited, time_spent)
                        VALUES (?, ?, ?, ?)
                    """, (
                        entry_date.isoformat(),
                        hour,
                        stats.get('sites_visited', 0),
                        stats.get('time_spent', 0)
                    ))
        except Exception as e:
            logger.error(f"Error saving daily stats: {e}")
    
    def get_daily_stats(self, entry_date: date) -> Dict[int, Dict[str, int]]:
        """Retrieve hourly statistics for a day."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT hour, sites_visited, time_spent FROM daily_stats WHERE date = ?",
                    (entry_date.isoformat(),)
                )
                
                stats = {}
                for row in cursor.fetchall():
                    hour, sites_visited, time_spent = row
                    stats[hour] = {
                        'sites_visited': sites_visited,
                        'time_spent': time_spent
                    }
                return stats
        except Exception as e:
            logger.error(f"Error retrieving daily stats: {e}")
        return {}
    
    def get_site_category(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get category information for a domain."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM site_categories WHERE domain = ?",
                    (domain,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        'domain': row['domain'],
                        'category': row['category'],
                        'productivity_weight': row['productivity_weight']
                    }
        except Exception as e:
            logger.error(f"Error retrieving site category: {e}")
        return None
    
    def add_site_category(self, domain: str, category: str, productivity_weight: float = 0.0) -> bool:
        """Add or update a site category."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO site_categories (domain, category, productivity_weight)
                    VALUES (?, ?, ?)
                """, (domain, category, productivity_weight))
            return True
        except Exception as e:
            logger.error(f"Error adding site category: {e}")
            return False
    
    def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all site categories."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM site_categories ORDER BY domain")
                
                categories = []
                for row in cursor.fetchall():
                    categories.append({
                        'domain': row['domain'],
                        'category': row['category'],
                        'productivity_weight': row['productivity_weight']
                    })
                return categories
        except Exception as e:
            logger.error(f"Error retrieving all categories: {e}")
        return []