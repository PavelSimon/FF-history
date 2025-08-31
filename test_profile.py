#!/usr/bin/env python3
"""
Test script to check different Firefox profiles
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from src.firefox_parser import FirefoxParser
import sqlite3
from datetime import datetime, date
import os

def test_profile(profile_path):
    print(f"\n=== Testing profile: {profile_path} ===")
    try:
        parser = FirefoxParser(profile_path)
        print(f"Places database exists: {parser.places_db.exists()}")
        
        if not parser.places_db.exists():
            return
            
        # Check database directly
        temp_db = parser._create_temp_db_copy()
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM moz_historyvisits")
            total_visits = cursor.fetchone()[0]
            print(f"Total history visits: {total_visits}")
            
            if total_visits > 0:
                # Check date range
                cursor = conn.execute("""
                    SELECT 
                        MIN(h.visit_date) as earliest,
                        MAX(h.visit_date) as latest
                    FROM moz_historyvisits h
                """)
                row = cursor.fetchone()
                if row[0] and row[1]:
                    earliest = datetime.fromtimestamp(row[0] / 1_000_000)
                    latest = datetime.fromtimestamp(row[1] / 1_000_000)
                    print(f"History date range: {earliest.date()} to {latest.date()}")
                    
                # Check for today's data
                today = date.today()
                start_timestamp = int(datetime.combine(today, datetime.min.time()).timestamp() * 1_000_000)
                end_timestamp = int(datetime.combine(today, datetime.max.time()).timestamp() * 1_000_000)
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM moz_historyvisits h
                    WHERE h.visit_date BETWEEN ? AND ?
                """, (start_timestamp, end_timestamp))
                today_visits = cursor.fetchone()[0]
                print(f"Visits today ({today}): {today_visits}")
        
        temp_db.unlink(missing_ok=True)
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    profiles_dir = Path(os.environ.get("APPDATA")) / "Mozilla" / "Firefox" / "Profiles"
    
    for profile_dir in profiles_dir.iterdir():
        if profile_dir.is_dir():
            test_profile(str(profile_dir))

if __name__ == "__main__":
    main()