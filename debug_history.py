#!/usr/bin/env python3
"""
Debug script to check Firefox history data availability
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from src.firefox_parser import FirefoxParser
import sqlite3
from datetime import datetime

def debug_firefox_history():
    try:
        parser = FirefoxParser()
        print(f"Firefox profile found: {parser.profile_path}")
        print(f"Places database exists: {parser.places_db.exists()}")
        
        # Check database directly
        temp_db = parser._create_temp_db_copy()
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM moz_historyvisits")
            total_visits = cursor.fetchone()[0]
            print(f"Total history visits in database: {total_visits}")
            
            if total_visits > 0:
                # Get recent visits
                cursor = conn.execute("""
                    SELECT h.visit_date, p.url, p.title 
                    FROM moz_historyvisits h 
                    JOIN moz_places p ON h.place_id = p.id 
                    ORDER BY h.visit_date DESC 
                    LIMIT 5
                """)
                
                print("\nMost recent visits:")
                for row in cursor.fetchall():
                    visit_time = datetime.fromtimestamp(row[0] / 1_000_000)
                    print(f"  {visit_time}: {row[1]} - {row[2]}")
                
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
                    print(f"\nHistory date range: {earliest.date()} to {latest.date()}")
        
        temp_db.unlink(missing_ok=True)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_firefox_history()