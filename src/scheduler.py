try:
    import schedule
except ImportError:
    schedule = None
import time
import logging
from datetime import date, datetime, timedelta
from typing import Optional
import threading
import signal
import sys

from .config import ConfigManager
from .database import DatabaseManager
from .journal_generator import JournalGenerator
from .markdown_exporter import MarkdownExporter

logger = logging.getLogger(__name__)

class JournalScheduler:
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config = config_manager or ConfigManager()
        self.db_manager = DatabaseManager(self.config.database_path)
        self.journal_generator = JournalGenerator(self.db_manager)
        self.markdown_exporter = MarkdownExporter(
            self.config.journal_output_dir,
            self.config.template_path
        )
        
        self.running = False
        self.scheduler_thread = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}. Shutting down scheduler...")
        self.stop()
        sys.exit(0)
    
    def _generate_daily_journal(self, target_date: Optional[date] = None):
        """Generate daily journal entry."""
        target_date = target_date or date.today()
        
        try:
            logger.info(f"Starting journal generation for {target_date}")
            
            # Generate journal data
            journal_data = self.journal_generator.generate_daily_journal(target_date)
            
            if journal_data:
                # Export to markdown
                output_file = self.markdown_exporter.export_daily_journal(target_date, journal_data)
                
                if output_file:
                    logger.info(f"Journal successfully generated and exported for {target_date}")
                else:
                    logger.warning(f"Journal data generated but export failed for {target_date}")
            else:
                logger.info(f"No journal data to generate for {target_date}")
                
        except Exception as e:
            logger.error(f"Error during journal generation for {target_date}: {e}")
    
    def _run_scheduler(self):
        """Run the scheduler in a separate thread."""
        if not schedule:
            logger.error("Schedule module not available")
            return
            
        logger.info("Scheduler thread started")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Continue running even if there's an error
        
        logger.info("Scheduler thread stopped")
    
    def setup_daily_schedule(self):
        """Setup daily journal generation schedule."""
        if not schedule:
            logger.error("Schedule module not available. Install with: pip install schedule")
            return
            
        if not self.config.scheduler_enabled:
            logger.info("Scheduler is disabled in configuration")
            return
        
        schedule_time = self.config.scheduler_time
        
        try:
            # Schedule daily journal generation
            schedule.every().day.at(schedule_time).do(self._generate_daily_journal)
            logger.info(f"Daily journal generation scheduled at {schedule_time}")
            
            # Also schedule weekly summary generation (on Sundays)
            schedule.every().sunday.at("00:00").do(self._generate_weekly_summary)
            logger.info("Weekly summary generation scheduled for Sundays at midnight")
            
        except Exception as e:
            logger.error(f"Error setting up schedule: {e}")
    
    def _generate_weekly_summary(self):
        """Generate weekly summary."""
        try:
            # Get the start of the current week (Monday)
            today = date.today()
            days_since_monday = today.weekday()
            monday = today - datetime.timedelta(days=days_since_monday)
            
            logger.info(f"Generating weekly summary starting from {monday}")
            
            summary_data = self.journal_generator.generate_weekly_summary(monday)
            
            if summary_data:
                output_file = self.markdown_exporter.export_weekly_summary(monday, summary_data)
                if output_file:
                    logger.info(f"Weekly summary generated: {output_file}")
                else:
                    logger.warning("Weekly summary data generated but export failed")
            else:
                logger.info("No weekly summary data available")
                
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.setup_daily_schedule()
        self.running = True
        
        # Start scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Journal scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        if not self.running:
            return
        
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        # Clear all scheduled jobs
        if schedule:
            schedule.clear()
        logger.info("Journal scheduler stopped")
    
    def run_once(self, target_date: Optional[date] = None):
        """Generate journal for a specific date without scheduling."""
        self._generate_daily_journal(target_date)
    
    def run_weekly_summary(self, start_date: Optional[date] = None):
        """Generate weekly summary without scheduling."""
        if start_date is None:
            # Default to the start of current week
            today = date.today()
            days_since_monday = today.weekday()
            start_date = today - datetime.timedelta(days=days_since_monday)
        
        try:
            summary_data = self.journal_generator.generate_weekly_summary(start_date)
            
            if summary_data:
                output_file = self.markdown_exporter.export_weekly_summary(start_date, summary_data)
                return output_file
            else:
                logger.info("No weekly summary data available")
                return None
                
        except Exception as e:
            logger.error(f"Error generating weekly summary: {e}")
            return None
    
    def get_next_run_time(self) -> Optional[str]:
        """Get the next scheduled run time."""
        jobs = schedule.get_jobs()
        if jobs:
            next_run = min(job.next_run for job in jobs)
            return next_run.strftime("%Y-%m-%d %H:%M:%S")
        return None
    
    def list_scheduled_jobs(self) -> list:
        """List all scheduled jobs."""
        jobs = []
        for job in schedule.get_jobs():
            jobs.append({
                'job': str(job.job_func.__name__),
                'next_run': job.next_run.strftime("%Y-%m-%d %H:%M:%S"),
                'interval': str(job.interval),
                'unit': job.unit
            })
        return jobs

def run_daemon():
    """Run the scheduler as a daemon process."""
    # Setup logging for daemon mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    logger.info("Starting Firefox History Journal Scheduler")
    
    try:
        scheduler = JournalScheduler()
        scheduler.start()
        
        # Keep the main thread alive
        while scheduler.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Scheduler daemon error: {e}")
    finally:
        if 'scheduler' in locals():
            scheduler.stop()
        logger.info("Scheduler daemon stopped")

if __name__ == "__main__":
    run_daemon()