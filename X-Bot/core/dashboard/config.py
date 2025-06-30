"""
Configuration du Dashboard
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DashboardConfig:
    """Configuration du dashboard"""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    title: str = "Twitter Bot Dashboard"
    description: str = "Configuration et monitoring en temps réel"
    auto_refresh_interval: int = 30  # secondes
    log_lines_limit: int = 20
    enable_cors: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "host": self.host,
            "port": self.port,
            "debug": self.debug,
            "title": self.title,
            "description": self.description,
            "auto_refresh_interval": self.auto_refresh_interval,
            "log_lines_limit": self.log_lines_limit,
            "enable_cors": self.enable_cors
        }


# Configuration par défaut
DEFAULT_CONFIG = DashboardConfig()

# Thème sombre par défaut
DARK_THEME = {
    "primary_bg": "#0f172a",
    "secondary_bg": "#1e293b", 
    "accent_bg": "#334155",
    "primary_color": "#e2e8f0",
    "secondary_color": "#94a3b8",
    "accent_color": "#3b82f6",
    "success_color": "#10b981",
    "error_color": "#ef4444",
    "warning_color": "#f59e0b"
} 