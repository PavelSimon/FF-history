import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "firefox": {
                "profile_path": "auto",
                "exclude_private": True,
                "excluded_domains": ["localhost", "127.0.0.1"]
            },
            "journal": {
                "output_directory": "./journals",
                "template_path": "./templates/daily_template.md",
                "include_statistics": True,
                "minimum_visit_duration": 30
            },
            "database": {
                "path": "./data/journal.db",
                "backup_enabled": True,
                "retention_days": 365
            },
            "scheduler": {
                "enabled": True,
                "time": "23:30",
                "timezone": "local"
            },
            "dashboard": {
                "host": "localhost",
                "port": 8765,
                "theme": "light",
                "auto_refresh": 300
            }
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                logger.info("Configuration file not found, creating default configuration")
                default_config = self._get_default_config()
                self._save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            return self._get_default_config()
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'firefox.profile_path')."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        return self._save_config(self.config)
    
    def reload(self) -> Dict[str, Any]:
        """Reload configuration from file."""
        self.config = self._load_config()
        return self.config
    
    def validate(self) -> bool:
        """Validate configuration structure."""
        required_sections = ['firefox', 'journal', 'database', 'scheduler', 'dashboard']
        
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Missing configuration section: {section}")
                return False
        
        # Validate specific required fields
        required_fields = [
            'journal.output_directory',
            'database.path',
            'scheduler.time',
            'dashboard.port'
        ]
        
        for field in required_fields:
            if self.get(field) is None:
                logger.warning(f"Missing required configuration field: {field}")
                return False
        
        return True
    
    # Convenience methods for common config access
    @property
    def firefox_profile_path(self) -> Optional[str]:
        """Get Firefox profile path."""
        path = self.get('firefox.profile_path')
        return None if path == 'auto' else path
    
    @property
    def exclude_private_browsing(self) -> bool:
        """Check if private browsing should be excluded."""
        return self.get('firefox.exclude_private', True)
    
    @property
    def excluded_domains(self) -> list:
        """Get list of excluded domains."""
        return self.get('firefox.excluded_domains', [])
    
    @property
    def journal_output_dir(self) -> str:
        """Get journal output directory."""
        return self.get('journal.output_directory', './journals')
    
    @property
    def template_path(self) -> str:
        """Get template path."""
        return self.get('journal.template_path', './templates/daily_template.md')
    
    @property
    def database_path(self) -> str:
        """Get database path."""
        return self.get('database.path', './data/journal.db')
    
    @property
    def scheduler_enabled(self) -> bool:
        """Check if scheduler is enabled."""
        return self.get('scheduler.enabled', True)
    
    @property
    def scheduler_time(self) -> str:
        """Get scheduler time."""
        return self.get('scheduler.time', '23:30')
    
    @property
    def dashboard_host(self) -> str:
        """Get dashboard host."""
        return self.get('dashboard.host', 'localhost')
    
    @property
    def dashboard_port(self) -> int:
        """Get dashboard port."""
        return self.get('dashboard.port', 8765)
    
    @property
    def dashboard_theme(self) -> str:
        """Get dashboard theme."""
        return self.get('dashboard.theme', 'light')