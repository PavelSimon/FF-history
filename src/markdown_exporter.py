from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MarkdownExporter:
    def __init__(self, output_dir: str = "./journals", template_path: str = "./templates/daily_template.md"):
        self.output_dir = Path(output_dir)
        self.template_path = Path(template_path)
        self.output_dir.mkdir(exist_ok=True)
        
        # Load template
        self.template = ""
        if self.template_path.exists():
            self.template = self.template_path.read_text(encoding='utf-8')
        else:
            logger.warning(f"Template file not found: {template_path}. Using default template.")
            self.template = self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Return a default template if no template file is found."""
        return """# Daily Journal - {date}

## Summary
{summary}

## Statistics
- **Total Sites Visited**: {total_sites_visited}
- **Total Time Spent**: {total_time_spent} minutes ({total_time_hours})
- **Productivity Score**: {productivity_score}/10

## Activity Breakdown

### Top Categories by Time
{top_categories}

### Hourly Activity
{hourly_activity}

## Detailed Site Analysis

### Most Visited Domains
{top_domains}

### Notable Activities
{notable_activities}

## Insights
{insights}

---
*Generated on {generated_at} by Firefox History Journal Generator*"""
    
    def _format_time_duration(self, minutes: int) -> str:
        """Convert minutes to human-readable format."""
        if minutes < 60:
            return f"{minutes} minutes"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"
    
    def _format_categories(self, categories: list) -> str:
        """Format category data into markdown."""
        if not categories:
            return "No browsing activity recorded."
        
        lines = []
        for i, category in enumerate(categories, 1):
            category_name = category['category']
            time_spent = category['time_spent']
            visits = category.get('visits', 0)
            
            time_str = self._format_time_duration(time_spent)
            lines.append(f"{i}. **{category_name}** - {time_str} ({visits} visits)")
        
        return "\n".join(lines)
    
    def _format_hourly_activity(self, hourly_stats: Dict[int, Dict[str, int]]) -> str:
        """Format hourly activity into markdown."""
        if not hourly_stats:
            return "No hourly data available."
        
        lines = ["| Hour | Sites Visited | Time Spent |", "|------|---------------|------------|"]
        
        for hour in range(24):
            if hour in hourly_stats:
                stats = hourly_stats[hour]
                sites = stats['sites_visited']
                time_spent = stats['time_spent']
                time_str = self._format_time_duration(time_spent) if time_spent > 0 else "0 minutes"
                lines.append(f"| {hour:02d}:00 | {sites} | {time_str} |")
            else:
                lines.append(f"| {hour:02d}:00 | 0 | 0 minutes |")
        
        return "\n".join(lines)
    
    def _format_top_domains(self, domain_stats: Dict[str, Dict]) -> str:
        """Format top domains into markdown."""
        if not domain_stats:
            return "No domain data available."
        
        # Sort domains by time spent
        sorted_domains = sorted(
            domain_stats.items(),
            key=lambda x: x[1]['time_spent'],
            reverse=True
        )
        
        lines = []
        for i, (domain, stats) in enumerate(sorted_domains[:10], 1):
            time_spent = stats['time_spent']
            visits = stats['visits']
            category = stats.get('category', 'Uncategorized')
            
            time_str = self._format_time_duration(time_spent)
            lines.append(f"{i}. **{domain}** ({category}) - {time_str} ({visits} visits)")
        
        return "\n".join(lines)
    
    def _format_notable_activities(self, domain_stats: Dict[str, Dict]) -> str:
        """Extract and format notable activities."""
        if not domain_stats:
            return "No notable activities."
        
        activities = []
        
        # Find domains with high activity
        for domain, stats in domain_stats.items():
            time_spent = stats['time_spent']
            visits = stats['visits']
            category = stats.get('category', 'Uncategorized')
            titles = stats.get('titles', [])
            
            if time_spent > 30:  # More than 30 minutes
                activities.append(f"- Spent significant time on **{domain}** ({category}) - {self._format_time_duration(time_spent)}")
            elif visits > 10:  # Many visits
                activities.append(f"- Frequently visited **{domain}** ({category}) - {visits} visits")
            
            # Add interesting titles
            if titles and len(titles) > 0:
                interesting_titles = [title for title in titles if len(title) > 20 and title != 'Untitled'][:3]
                if interesting_titles:
                    for title in interesting_titles:
                        activities.append(f"  - \"{title[:80]}{'...' if len(title) > 80 else ''}\"")
        
        if not activities:
            return "No significant activities detected."
        
        return "\n".join(activities[:15])  # Limit to top 15 activities
    
    def _generate_insights(self, journal_data: Dict[str, Any]) -> str:
        """Generate insights based on the data."""
        insights = []
        
        productivity_score = journal_data.get('productivity_score', 0)
        total_time = journal_data.get('total_time_spent', 0)
        top_categories = journal_data.get('top_categories', [])
        
        # Productivity insights
        if productivity_score >= 8:
            insights.append("🎯 Excellent productivity! You focused on valuable activities.")
        elif productivity_score >= 6:
            insights.append("👍 Good productivity with a healthy balance of work and leisure.")
        elif productivity_score >= 4:
            insights.append("⚖️ Moderate productivity. Consider focusing more on valuable activities.")
        else:
            insights.append("⚠️ Low productivity day. Mostly entertainment or social media browsing.")
        
        # Time insights
        if total_time > 480:  # More than 8 hours
            insights.append("⏰ Heavy browsing day with over 8 hours of activity.")
        elif total_time > 240:  # 4-8 hours
            insights.append("📊 Moderate browsing activity (4-8 hours).")
        elif total_time > 60:  # 1-4 hours
            insights.append("📱 Light browsing activity (1-4 hours).")
        else:
            insights.append("🔵 Minimal browsing activity today.")
        
        # Category insights
        if top_categories:
            top_category = top_categories[0]
            if top_category['category'] == 'Development':
                insights.append("💻 Strong focus on development and technical activities.")
            elif top_category['category'] == 'Entertainment':
                insights.append("🎬 Entertainment was the primary focus today.")
            elif top_category['category'] == 'Social Media':
                insights.append("📱 Social media consumed most of your browsing time.")
            elif top_category['category'] == 'Research':
                insights.append("📚 Great focus on research and learning activities.")
        
        # Patterns
        raw_data = journal_data.get('raw_data', {})
        hourly_stats = raw_data.get('hourly_stats', {})
        
        if hourly_stats:
            peak_hours = sorted(hourly_stats.items(), key=lambda x: x[1]['time_spent'], reverse=True)[:3]
            if peak_hours:
                peak_hour = peak_hours[0][0]
                if 9 <= peak_hour <= 17:
                    insights.append("🏢 Peak activity during business hours.")
                elif 18 <= peak_hour <= 23:
                    insights.append("🌆 Most active during evening hours.")
                else:
                    insights.append("🌙 Unusual activity pattern with late-night browsing.")
        
        if not insights:
            insights.append("📊 Standard browsing pattern detected.")
        
        return "\n".join(f"- {insight}" for insight in insights)
    
    def export_daily_journal(self, journal_date: date, journal_data: Dict[str, Any]) -> Optional[Path]:
        """Export journal data to a markdown file."""
        try:
            # Prepare template variables
            total_minutes = journal_data.get('total_time_spent', 0)
            raw_data = journal_data.get('raw_data', {})
            domain_stats = raw_data.get('domain_stats', {})
            hourly_stats = raw_data.get('hourly_stats', {})
            
            template_vars = {
                'date': journal_date.strftime('%B %d, %Y'),
                'summary': journal_data.get('summary', 'No summary available.'),
                'total_sites_visited': journal_data.get('total_sites_visited', 0),
                'total_time_spent': total_minutes,
                'total_time_hours': self._format_time_duration(total_minutes),
                'productivity_score': journal_data.get('productivity_score', 0),
                'top_categories': self._format_categories(journal_data.get('top_categories', [])),
                'hourly_activity': self._format_hourly_activity(hourly_stats),
                'top_domains': self._format_top_domains(domain_stats),
                'notable_activities': self._format_notable_activities(domain_stats),
                'insights': self._generate_insights(journal_data),
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Fill template
            markdown_content = self.template.format(**template_vars)
            
            # Create output file path
            filename = f"journal_{journal_date.isoformat()}.md"
            output_file = self.output_dir / filename
            
            # Write to file
            output_file.write_text(markdown_content, encoding='utf-8')
            
            logger.info(f"Journal exported to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting journal to markdown: {e}")
            return None
    
    def export_weekly_summary(self, start_date: date, summary_data: Dict[str, Any]) -> Optional[Path]:
        """Export weekly summary to markdown."""
        try:
            end_date_str = summary_data.get('end_date', '')
            end_date_obj = datetime.fromisoformat(end_date_str).date() if end_date_str else start_date
            
            content = f"""# Weekly Summary - {start_date.strftime('%B %d')} to {end_date_obj.strftime('%B %d, %Y')}

## Overview
- **Total Sites Visited**: {summary_data.get('total_sites_visited', 0)}
- **Total Time Spent**: {self._format_time_duration(summary_data.get('total_time_spent', 0))}
- **Average Productivity Score**: {summary_data.get('average_productivity_score', 0)}/10
- **Days with Data**: {summary_data.get('daily_entries_count', 0)}

## Top Categories This Week
{self._format_categories(summary_data.get('top_categories', []))}

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Firefox History Journal Generator*"""
            
            # Create output file path
            filename = f"weekly_summary_{start_date.isoformat()}.md"
            output_file = self.output_dir / filename
            
            # Write to file
            output_file.write_text(content, encoding='utf-8')
            
            logger.info(f"Weekly summary exported to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Error exporting weekly summary: {e}")
            return None