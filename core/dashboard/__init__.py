"""
Dashboard Module pour Bot Twitter Automatisé

Structure modulaire du dashboard de configuration.
Maintenant intégré dans core/dashboard/
"""

from .server import DashboardServer
from .config import DashboardConfig

__version__ = "2.0.0"
__all__ = ["DashboardServer", "DashboardConfig"]

def create_dashboard(host: str = "0.0.0.0", port: int = 8080) -> DashboardServer:
    """
    Crée une instance du dashboard configurée
    
    Args:
        host: Adresse d'écoute
        port: Port d'écoute
        
    Returns:
        Instance du serveur dashboard
    """
    return DashboardServer(host=host, port=port)

def start_dashboard(host: str = "0.0.0.0", port: int = 8080):
    """
    Démarre le dashboard web
    
    Args:
        host: Adresse d'écoute
        port: Port d'écoute
    """
    dashboard = create_dashboard(host=host, port=port)
    dashboard.run() 