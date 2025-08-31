import sqlite3
import os
import platform
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class FirefoxParser:
    def __init__(self, profile_path: Optional[str] = None):
        self.profile_path = profile_path or self._find_firefox_profile()
        self.places_db = None
        
        if self.profile_path:
            self.places_db = Path(self.profile_path) / "places.sqlite"
        
        if not self.places_db or not self.places_db.exists():
            logger.error("Firefox places.sqlite database not found")
            raise FileNotFoundError("Firefox places.sqlite database not found")
    
    def _find_firefox_profile(self) -> Optional[str]:
        """Find Firefox profile directory based on OS."""
        system = platform.system()
        
        if system == "Windows":
            firefox_dir = Path(os.environ.get("APPDATA", "")) / "Mozilla" / "Firefox" / "Profiles"
        elif system == "Darwin":  # macOS
            firefox_dir = Path.home() / "Library" / "Application Support" / "Firefox" / "Profiles"
        else:  # Linux and others
            firefox_dir = Path.home() / ".mozilla" / "firefox"
        
        if not firefox_dir.exists():
            logger.warning(f"Firefox profile directory not found: {firefox_dir}")
            return None
        
        # Find all profiles with places.sqlite and get their last modification times
        valid_profiles = []
        for profile in firefox_dir.iterdir():
            if profile.is_dir():
                places_file = profile / "places.sqlite"
                if places_file.exists():
                    # Get the modification time of the places.sqlite file
                    mod_time = places_file.stat().st_mtime
                    valid_profiles.append((profile, mod_time))
        
        if not valid_profiles:
            return None
        
        # Sort by modification time (most recent first) and use the most recent profile
        valid_profiles.sort(key=lambda x: x[1], reverse=True)
        most_recent_profile = valid_profiles[0][0]
        logger.info(f"Using most recently used Firefox profile: {most_recent_profile}")
        return str(most_recent_profile)
        
        return None
    
    def _create_temp_db_copy(self) -> Path:
        """Create a temporary copy of places.sqlite to avoid locking issues."""
        import tempfile
        import shutil
        import time
        
        temp_dir = Path(tempfile.gettempdir())
        
        # Use a more unique timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        temp_db = temp_dir / f"places_copy_{timestamp}.sqlite"
        
        try:
            shutil.copy2(self.places_db, temp_db)
            return temp_db
        except Exception as e:
            logger.error(f"Failed to copy Firefox database: {e}")
            raise
    
    def get_history_for_date(self, target_date: date, exclude_private: bool = True) -> List[Dict]:
        """Get browsing history for a specific date."""
        temp_db = self._create_temp_db_copy()
        history_data = []
        
        try:
            # Convert date to Unix timestamp range (microseconds)
            start_timestamp = int(datetime.combine(target_date, datetime.min.time()).timestamp() * 1_000_000)
            end_timestamp = int(datetime.combine(target_date, datetime.max.time()).timestamp() * 1_000_000)
            
            with sqlite3.connect(temp_db) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                SELECT 
                    p.url,
                    p.title,
                    p.visit_count,
                    h.visit_date,
                    h.visit_type,
                    h.from_visit
                FROM moz_places p
                JOIN moz_historyvisits h ON p.id = h.place_id
                WHERE h.visit_date BETWEEN ? AND ?
                ORDER BY h.visit_date ASC
                """
                
                cursor = conn.execute(query, (start_timestamp, end_timestamp))
                
                for row in cursor.fetchall():
                    # Skip private browsing if requested
                    if exclude_private and row['visit_type'] == 7:  # Private browsing visit type
                        continue
                    
                    # Convert timestamp back to datetime
                    visit_datetime = datetime.fromtimestamp(row['visit_date'] / 1_000_000)
                    
                    # Parse URL to get domain
                    parsed_url = urlparse(row['url'])
                    domain = parsed_url.netloc.lower()
                    
                    # Clean domain (remove www. prefix)
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    history_data.append({
                        'url': row['url'],
                        'title': row['title'] or 'Untitled',
                        'domain': domain,
                        'visit_count': row['visit_count'],
                        'visit_datetime': visit_datetime,
                        'visit_type': row['visit_type'],
                        'from_visit': row['from_visit']
                    })
        
        except Exception as e:
            logger.error(f"Error reading Firefox history: {e}")
        
        finally:
            # Clean up temporary file
            try:
                if temp_db.exists():
                    temp_db.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary database file: {e}")
        
        return history_data
    
    def get_history_range(self, start_date: date, end_date: date, exclude_private: bool = True) -> Dict[str, List[Dict]]:
        """Get browsing history for a date range, grouped by date."""
        temp_db = self._create_temp_db_copy()
        history_data = {}
        
        try:
            # Convert dates to Unix timestamp range (microseconds)
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp() * 1_000_000)
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp() * 1_000_000)
            
            with sqlite3.connect(temp_db) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                SELECT 
                    p.url,
                    p.title,
                    p.visit_count,
                    h.visit_date,
                    h.visit_type,
                    h.from_visit
                FROM moz_places p
                JOIN moz_historyvisits h ON p.id = h.place_id
                WHERE h.visit_date BETWEEN ? AND ?
                ORDER BY h.visit_date ASC
                """
                
                cursor = conn.execute(query, (start_timestamp, end_timestamp))
                
                for row in cursor.fetchall():
                    # Skip private browsing if requested
                    if exclude_private and row['visit_type'] == 7:
                        continue
                    
                    # Convert timestamp back to datetime
                    visit_datetime = datetime.fromtimestamp(row['visit_date'] / 1_000_000)
                    visit_date_str = visit_datetime.date().isoformat()
                    
                    # Parse URL to get domain
                    parsed_url = urlparse(row['url'])
                    domain = parsed_url.netloc.lower()
                    
                    # Clean domain (remove www. prefix)
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    entry = {
                        'url': row['url'],
                        'title': row['title'] or 'Untitled',
                        'domain': domain,
                        'visit_count': row['visit_count'],
                        'visit_datetime': visit_datetime,
                        'visit_type': row['visit_type'],
                        'from_visit': row['from_visit']
                    }
                    
                    if visit_date_str not in history_data:
                        history_data[visit_date_str] = []
                    
                    history_data[visit_date_str].append(entry)
        
        except Exception as e:
            logger.error(f"Error reading Firefox history range: {e}")
        
        finally:
            # Clean up temporary file
            try:
                if temp_db.exists():
                    temp_db.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temporary database file: {e}")
        
        return history_data
    
    def get_most_visited_sites(self, limit: int = 20) -> List[Dict]:
        """Get most visited sites from Firefox history."""
        temp_db = self._create_temp_db_copy()
        sites = []
        
        try:
            with sqlite3.connect(temp_db) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                SELECT 
                    p.url,
                    p.title,
                    p.visit_count,
                    p.last_visit_date
                FROM moz_places p
                WHERE p.visit_count > 0
                ORDER BY p.visit_count DESC
                LIMIT ?
                """
                
                cursor = conn.execute(query, (limit,))
                
                for row in cursor.fetchall():
                    parsed_url = urlparse(row['url'])
                    domain = parsed_url.netloc.lower()
                    
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    # Convert last visit timestamp
                    last_visit = None
                    if row['last_visit_date']:
                        last_visit = datetime.fromtimestamp(row['last_visit_date'] / 1_000_000)
                    
                    sites.append({
                        'url': row['url'],
                        'title': row['title'] or 'Untitled',
                        'domain': domain,
                        'visit_count': row['visit_count'],
                        'last_visit': last_visit
                    })
        
        except Exception as e:
            logger.error(f"Error getting most visited sites: {e}")
        
        finally:
            temp_db.unlink(missing_ok=True)
        
        return sites
    
    def get_bookmarks(self) -> List[Dict]:
        """Get bookmarks from Firefox."""
        temp_db = self._create_temp_db_copy()
        bookmarks = []
        
        try:
            with sqlite3.connect(temp_db) as conn:
                conn.row_factory = sqlite3.Row
                
                query = """
                SELECT 
                    b.title,
                    p.url,
                    b.dateAdded,
                    b.lastModified
                FROM moz_bookmarks b
                JOIN moz_places p ON b.fk = p.id
                WHERE b.type = 1 AND p.url IS NOT NULL
                ORDER BY b.dateAdded DESC
                """
                
                cursor = conn.execute(query)
                
                for row in cursor.fetchall():
                    parsed_url = urlparse(row['url'])
                    domain = parsed_url.netloc.lower()
                    
                    if domain.startswith('www.'):
                        domain = domain[4:]
                    
                    # Convert timestamps
                    date_added = None
                    last_modified = None
                    
                    if row['dateAdded']:
                        date_added = datetime.fromtimestamp(row['dateAdded'] / 1_000_000)
                    
                    if row['lastModified']:
                        last_modified = datetime.fromtimestamp(row['lastModified'] / 1_000_000)
                    
                    bookmarks.append({
                        'title': row['title'] or 'Untitled',
                        'url': row['url'],
                        'domain': domain,
                        'date_added': date_added,
                        'last_modified': last_modified
                    })
        
        except Exception as e:
            logger.error(f"Error getting bookmarks: {e}")
        
        finally:
            temp_db.unlink(missing_ok=True)
        
        return bookmarks
    
    @property
    def is_available(self) -> bool:
        """Check if Firefox data is available."""
        return self.places_db is not None and self.places_db.exists()