#!/usr/bin/env python3
"""
Statistics Generator Script

Manually change start_date and end_date variables below to generate 
statistics day by day for the specified interval.
"""

import subprocess
from datetime import datetime, timedelta

# CHANGE THESE DATES AS NEEDED
start_date = "2024-01-01"  # Format: YYYY-MM-DD
end_date = "2024-12-31"    # Format: YYYY-MM-DD

def generate_statistics():
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    current_date = start
    
    print(f"Generating statistics from {start_date} to {end_date}")
    print("-" * 50)
    
    while current_date <= end:
        date_str = current_date.strftime("%Y-%m-%d")
        print(f"\nGenerating statistics for {date_str}...")
        
        try:
            result = subprocess.run([
                "uv", "run", "python", "main.py", "generate", "--date", date_str
            ], capture_output=True, text=True, check=True)
            
            print(f" Success for {date_str}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
                
        except subprocess.CalledProcessError as e:
            print(f" Error for {date_str}: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr.strip()}")
        
        current_date += timedelta(days=1)
    
    print("\n" + "=" * 50)
    print("Statistics generation complete!")

if __name__ == "__main__":
    generate_statistics()