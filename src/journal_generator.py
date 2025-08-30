from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
import logging
from urllib.parse import urlparse
import re

from .firefox_parser import FirefoxParser
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class JournalGenerator:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.firefox_parser = None
        
        try:
            self.firefox_parser = FirefoxParser()
        except FileNotFoundError:
            logger.warning("Firefox profile not found. Journal generation will be limited.")
    
    def _categorize_domain(self, domain: str) -> Dict[str, Any]:
        """Categorize a domain and return category info."""
        category_info = self.db_manager.get_site_category(domain)
        
        if category_info:
            return category_info
        
        # Default categorization based on domain patterns
        category = "Uncategorized"
        productivity_weight = 0.0
        
        if any(keyword in domain for keyword in ['github', 'gitlab', 'stackoverflow', 'docs', 'developer']):
            category = "Development"
            productivity_weight = 0.7
        elif any(keyword in domain for keyword in ['youtube', 'netflix', 'twitch', 'entertainment']):
            category = "Entertainment"
            productivity_weight = -0.3
        elif any(keyword in domain for keyword in ['facebook', 'twitter', 'instagram', 'tiktok', 'social']):
            category = "Social Media"
            productivity_weight = -0.2
        elif any(keyword in domain for keyword in ['news', 'cnn', 'bbc', 'reuters']):
            category = "News"
            productivity_weight = 0.1
        elif any(keyword in domain for keyword in ['wikipedia', 'research', 'academic', 'edu']):
            category = "Research"
            productivity_weight = 0.6
        elif any(keyword in domain for keyword in ['mail', 'email', 'gmail', 'outlook']):
            category = "Communication"
            productivity_weight = 0.3
        elif any(keyword in domain for keyword in ['shop', 'amazon', 'ebay', 'store']):
            category = "Shopping"
            productivity_weight = -0.1
        
        # Save new category to database
        self.db_manager.add_site_category(domain, category, productivity_weight)
        
        return {
            'domain': domain,
            'category': category,
            'productivity_weight': productivity_weight
        }
    
    def _calculate_time_spent(self, visits: List[Dict]) -> int:
        """Estimate time spent browsing based on visit patterns."""
        if not visits:
            return 0
        
        total_time = 0
        visits_by_time = sorted(visits, key=lambda x: x['visit_datetime'])
        
        for i in range(len(visits_by_time) - 1):
            current_visit = visits_by_time[i]
            next_visit = visits_by_time[i + 1]
            
            time_diff = (next_visit['visit_datetime'] - current_visit['visit_datetime']).total_seconds()
            
            # If the gap is less than 30 minutes, assume user was active
            # Cap individual session time at 30 minutes to avoid overestimating
            if time_diff < 1800:  # 30 minutes
                total_time += min(time_diff, 1800)
            else:
                # Assume 2 minutes for standalone visits
                total_time += 120
        
        # Add time for the last visit
        total_time += 120
        
        return int(total_time / 60)  # Return minutes
    
    def _generate_hourly_stats(self, history_data: List[Dict]) -> Dict[int, Dict[str, int]]:
        """Generate hourly browsing statistics."""
        hourly_stats = defaultdict(lambda: {'sites_visited': 0, 'time_spent': 0})
        hourly_visits = defaultdict(list)
        
        # Group visits by hour
        for visit in history_data:
            hour = visit['visit_datetime'].hour
            hourly_visits[hour].append(visit)
        
        # Calculate stats for each hour
        for hour, visits in hourly_visits.items():
            unique_domains = set(visit['domain'] for visit in visits)
            time_spent = self._calculate_time_spent(visits)
            
            hourly_stats[hour] = {
                'sites_visited': len(unique_domains),
                'time_spent': time_spent
            }
        
        return dict(hourly_stats)
    
    def _calculate_productivity_score(self, category_stats: Dict[str, Dict]) -> float:
        """Calculate productivity score based on time spent in different categories."""
        total_time = sum(stats['time_spent'] for stats in category_stats.values())
        if total_time == 0:
            return 0.0
        
        weighted_score = 0.0
        for category, stats in category_stats.items():
            weight = stats['productivity_weight']
            time_ratio = stats['time_spent'] / total_time
            weighted_score += weight * time_ratio
        
        # Normalize to 0-10 scale
        return round(5 + (weighted_score * 5), 2)
    
    def _generate_summary(self, stats: Dict[str, Any]) -> str:
        """Generate a text summary of the day's browsing activity."""
        total_sites = stats['total_sites_visited']
        total_time = stats['total_time_spent']
        productivity_score = stats['productivity_score']
        top_categories = stats['top_categories']
        
        summary_parts = []
        
        # Basic stats
        summary_parts.append(f"Visited {total_sites} unique websites")
        
        if total_time > 0:
            hours = total_time // 60
            minutes = total_time % 60
            if hours > 0:
                summary_parts.append(f"spent approximately {hours}h {minutes}m browsing")
            else:
                summary_parts.append(f"spent approximately {minutes} minutes browsing")
        
        # Productivity assessment
        if productivity_score >= 7:
            summary_parts.append("This was a highly productive day with focus on valuable activities")
        elif productivity_score >= 5:
            summary_parts.append("This was a moderately productive day with balanced activities")
        else:
            summary_parts.append("This day had more entertainment/leisure browsing than productive activities")
        
        # Top categories
        if top_categories:
            top_3 = top_categories[:3]
            categories_text = ", ".join([f"{cat['category']} ({cat['time_spent']}min)" for cat in top_3])
            summary_parts.append(f"Primary focus areas: {categories_text}")
        
        return ". ".join(summary_parts) + "."
    
    def generate_daily_journal(self, target_date: date) -> Optional[Dict[str, Any]]:
        """Generate a complete daily journal entry."""
        if not self.firefox_parser or not self.firefox_parser.is_available:
            logger.error("Firefox parser not available")
            return None
        
        try:
            # Get history data for the date
            history_data = self.firefox_parser.get_history_for_date(target_date)
            
            if not history_data:
                logger.info(f"No browsing history found for {target_date}")
                return None
            
            # Analyze browsing patterns
            domain_stats = defaultdict(lambda: {'visits': 0, 'time_spent': 0, 'titles': set()})
            category_stats = defaultdict(lambda: {'time_spent': 0, 'visits': 0, 'productivity_weight': 0.0})
            
            # Group visits by domain
            domain_visits = defaultdict(list)
            for visit in history_data:
                domain_visits[visit['domain']].append(visit)
            
            # Calculate stats for each domain
            for domain, visits in domain_visits.items():
                category_info = self._categorize_domain(domain)
                time_spent = self._calculate_time_spent(visits)
                
                domain_stats[domain] = {
                    'visits': len(visits),
                    'time_spent': time_spent,
                    'titles': set(visit['title'] for visit in visits),
                    'category': category_info['category'],
                    'productivity_weight': category_info['productivity_weight']
                }
                
                # Aggregate by category
                category = category_info['category']
                category_stats[category]['time_spent'] += time_spent
                category_stats[category]['visits'] += len(visits)
                category_stats[category]['productivity_weight'] = category_info['productivity_weight']
            
            # Calculate overall statistics
            total_sites_visited = len(domain_stats)
            total_time_spent = sum(stats['time_spent'] for stats in domain_stats.values())
            productivity_score = self._calculate_productivity_score(category_stats)
            
            # Get top categories by time spent
            top_categories = sorted(
                [{'category': cat, **stats} for cat, stats in category_stats.items()],
                key=lambda x: x['time_spent'],
                reverse=True
            )
            
            # Get hourly statistics
            hourly_stats = self._generate_hourly_stats(history_data)
            
            # Generate summary
            stats_for_summary = {
                'total_sites_visited': total_sites_visited,
                'total_time_spent': total_time_spent,
                'productivity_score': productivity_score,
                'top_categories': top_categories
            }
            summary = self._generate_summary(stats_for_summary)
            
            # Prepare journal entry data
            journal_data = {
                'total_sites_visited': total_sites_visited,
                'total_time_spent': total_time_spent,
                'top_categories': top_categories,
                'productivity_score': productivity_score,
                'summary': summary,
                'raw_data': {
                    'domain_stats': {domain: {
                        'visits': stats['visits'],
                        'time_spent': stats['time_spent'],
                        'titles': list(stats['titles']),
                        'category': stats['category']
                    } for domain, stats in domain_stats.items()},
                    'hourly_stats': hourly_stats,
                    'category_breakdown': dict(category_stats)
                }
            }
            
            # Save to database
            success = self.db_manager.save_journal_entry(target_date, journal_data)
            if success:
                self.db_manager.save_daily_stats(target_date, hourly_stats)
                logger.info(f"Successfully generated journal entry for {target_date}")
                return journal_data
            else:
                logger.error(f"Failed to save journal entry for {target_date}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating journal for {target_date}: {e}")
            return None
    
    def generate_weekly_summary(self, start_date: date) -> Optional[Dict[str, Any]]:
        """Generate a weekly summary from daily journal entries."""
        end_date = start_date + timedelta(days=6)
        daily_entries = self.db_manager.get_journal_entries_range(start_date, end_date)
        
        if not daily_entries:
            return None
        
        # Aggregate weekly statistics
        total_sites = sum(entry['total_sites_visited'] for entry in daily_entries)
        total_time = sum(entry['total_time_spent'] for entry in daily_entries)
        avg_productivity = sum(entry['productivity_score'] for entry in daily_entries) / len(daily_entries)
        
        # Aggregate categories across the week
        weekly_categories = defaultdict(lambda: {'time_spent': 0, 'visits': 0})
        for entry in daily_entries:
            for category in entry['top_categories']:
                weekly_categories[category['category']]['time_spent'] += category['time_spent']
                weekly_categories[category['category']]['visits'] += category['visits']
        
        top_weekly_categories = sorted(
            [{'category': cat, **stats} for cat, stats in weekly_categories.items()],
            key=lambda x: x['time_spent'],
            reverse=True
        )
        
        return {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_sites_visited': total_sites,
            'total_time_spent': total_time,
            'average_productivity_score': round(avg_productivity, 2),
            'top_categories': top_weekly_categories,
            'daily_entries_count': len(daily_entries)
        }