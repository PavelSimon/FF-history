#!/usr/bin/env python3
"""
Firefox History Daily Journal Generator
Main entry point for the application.
"""

import sys
import logging
from datetime import date, datetime
from pathlib import Path
import argparse

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.config import ConfigManager
from src.database import DatabaseManager
from src.journal_generator import JournalGenerator
from src.markdown_exporter import MarkdownExporter
from src.scheduler import JournalScheduler

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Setup file and console logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suppress some verbose third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def generate_journal(args):
    """Generate journal for a specific date."""
    config = ConfigManager()
    db_manager = DatabaseManager(config.database_path)
    journal_generator = JournalGenerator(db_manager)
    markdown_exporter = MarkdownExporter(config.journal_output_dir, config.template_path)
    
    # Parse target date
    target_date = date.today()
    if args.date and args.date != "today":
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Use YYYY-MM-DD format.")
            return
    
    print(f"Generating journal for {target_date}...")
    
    # Generate journal data
    journal_data = journal_generator.generate_daily_journal(target_date)
    
    if journal_data:
        # Export to markdown
        output_file = markdown_exporter.export_daily_journal(target_date, journal_data)
        
        if output_file:
            print(f"[SUCCESS] Journal generated successfully: {output_file}")
            
            # Print summary
            print(f"\nSummary:")
            print(f"   Sites visited: {journal_data.get('total_sites_visited', 0)}")
            print(f"   Time spent: {journal_data.get('total_time_spent', 0)} minutes")
            print(f"   Productivity score: {journal_data.get('productivity_score', 0)}/10")
        else:
            print("[ERROR] Failed to export journal to markdown")
    else:
        print("[INFO] No browsing history found for the specified date")

def start_scheduler(args):
    """Start the journal scheduler."""
    print("Starting Firefox History Journal Scheduler...")
    
    scheduler = JournalScheduler()
    
    try:
        scheduler.start()
        
        print("[SUCCESS] Scheduler started successfully")
        print(f"Next run: {scheduler.get_next_run_time()}")
        print("Press Ctrl+C to stop")
        
        # Keep running
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[INFO] Stopping scheduler...")
        scheduler.stop()
        print("[SUCCESS] Scheduler stopped")

def start_dashboard(args):
    """Start the dashboard - try Streamlit first, fallback to simple HTML dashboard."""
    print(f"Starting dashboard on port {args.port}...")
    
    # Try Streamlit dashboard first
    try:
        import subprocess
        
        streamlit_dashboard_path = Path(__file__).parent / "streamlit_dashboard.py"
        
        print("Starting Streamlit dashboard...")
        print(f"Dashboard will open at: http://localhost:{args.port}")
        
        # Run streamlit server using uv run
        subprocess.run([
            "uv", "run", "streamlit", "run", str(streamlit_dashboard_path),
            "--server.port", str(args.port),
            "--server.headless", "false",
            "--browser.gatherUsageStats", "false"
        ], check=True)
        
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[INFO] Streamlit not available, using simple HTML dashboard instead")
        print(f"To install Streamlit: uv add streamlit")
        
        # Fallback to simple HTML dashboard
        try:
            simple_dashboard_path = Path(__file__).parent / "simple_dashboard.py"
            result = subprocess.run([
                sys.executable, str(simple_dashboard_path)
            ], capture_output=True, text=True, check=True)
            
            print(result.stdout)
            if result.stderr:
                print(f"Warnings: {result.stderr}")
                
        except Exception as fallback_error:
            print(f"[ERROR] Failed to generate HTML dashboard: {fallback_error}")
            print("Try running manually: uv run python simple_dashboard.py")

def export_data(args):
    """Export journal data to various formats."""
    config = ConfigManager()
    db_manager = DatabaseManager(config.database_path)
    
    # Parse date range
    try:
        if args.date_range:
            start_str, end_str = args.date_range.split(",")
            start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d").date()
            end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d").date()
        else:
            # Default to last 30 days
            end_date = date.today()
            start_date = end_date - datetime.timedelta(days=30)
    except ValueError:
        print("Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'")
        return
    
    print(f"Exporting data from {start_date} to {end_date}...")
    
    # Get journal entries
    entries = db_manager.get_journal_entries_range(start_date, end_date)
    
    if not entries:
        print("[INFO] No data found for the specified date range")
        return
    
    # Export based on format
    output_file = f"export_{start_date}_to_{end_date}.{args.format}"
    
    if args.format == "json":
        import json
        with open(output_file, 'w') as f:
            json.dump(entries, f, indent=2, default=str)
    elif args.format == "csv":
        import csv
        with open(output_file, 'w', newline='') as f:
            if entries:
                writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                writer.writeheader()
                writer.writerows(entries)
    
    print(f"[SUCCESS] Data exported to {output_file}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Firefox History Daily Journal Generator")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate journal for a specific date")
    generate_parser.add_argument("--date", default="today", help="Date in YYYY-MM-DD format or 'today'")
    
    # Schedule command
    schedule_parser = subparsers.add_parser("schedule", help="Start the journal scheduler")
    schedule_parser.add_argument("--start", action="store_true", help="Start the scheduler daemon")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start the web dashboard")
    dashboard_parser.add_argument("--host", default="localhost", help="Host to bind to")
    dashboard_parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export journal data")
    export_parser.add_argument("--format", choices=["json", "csv"], default="json", help="Export format")
    export_parser.add_argument("--date-range", help="Date range in 'YYYY-MM-DD,YYYY-MM-DD' format")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Execute command
    if args.command == "generate":
        generate_journal(args)
    elif args.command == "schedule":
        start_scheduler(args)
    elif args.command == "dashboard":
        start_dashboard(args)
    elif args.command == "export":
        export_data(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
