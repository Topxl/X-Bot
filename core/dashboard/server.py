"""
Serveur Dashboard FastAPI
"""

import os
import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

# Ajouter le répertoire racine au PATH pour les imports
current_dir = Path(__file__).parent
core_dir = current_dir.parent  # core/
root_dir = core_dir.parent     # racine du projet

sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(core_dir))

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from starlette.middleware.cors import CORSMiddleware
except ImportError:
    print("❌ Dashboard requires FastAPI and uvicorn")
    print("💡 Install with: pip install fastapi uvicorn")
    uvicorn = None
    FastAPI = None

from loguru import logger

from .config import DashboardConfig, DEFAULT_CONFIG
from .routes import setup_routes
from .templates import get_dashboard_html


class DashboardServer:
    """Serveur du dashboard web refactorisé"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080, config: Optional[DashboardConfig] = None):
        if not FastAPI:
            raise ImportError("FastAPI not available. Install with: pip install fastapi uvicorn")
            
        self.config = config or DEFAULT_CONFIG
        self.config.host = host
        self.config.port = port
        
        self.app = FastAPI(
            title=self.config.title,
            version="2.0.0",
            description=self.config.description
        )
        
        # Managers du bot (avec gestion d'erreur)
        self.bot_managers = self._init_bot_managers()
        
        self.start_time = datetime.utcnow()
        
        # Configuration
        self._setup_middleware()
        self._setup_routes()
    
    def _init_bot_managers(self) -> dict:
        """Initialise les managers du bot avec gestion d'erreur - DASHBOARD MODE"""
        managers = {
            "config_manager": None,
            "twitter_manager": None, 
            "storage_manager": None,
            "scheduler": None
        }
        
        try:
            # Dashboard utilise UNIQUEMENT config et storage (lecture seule)
            from container import get_container
            container = get_container()
            
            # Services minimaux pour dashboard (pas d'initialisation complète)
            managers["config_manager"] = container.get('config')
            managers["storage_manager"] = container.get('storage')
            
            # Twitter et Scheduler : NE PAS INITIALISER dans dashboard
            # Ces services restent None pour éviter les doubles initialisations
            logger.info("🖥️ Dashboard managers initialized (read-only mode)")
            
        except ImportError as e:
            logger.warning(f"Some bot managers not available: {e}")
        except Exception as e:
            logger.error(f"Error initializing bot managers: {e}")
        
        return managers
    
    def _setup_middleware(self):
        """Configuration des middlewares"""
        if self.config.enable_cors:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
    
    def _setup_routes(self):
        """Configuration des routes"""
        # Route principale
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            return get_dashboard_html(self.config)
        
        # Routes API depuis le module routes
        setup_routes(self.app, self.bot_managers, self.start_time, self.config)
    
    def run(self):
        """Démarre le serveur"""
        try:
            logger.info(f"🚀 Starting dashboard server on {self.config.host}:{self.config.port}")
            logger.info(f"🌐 Access at: http://{self.config.host}:{self.config.port}")
            
            uvicorn.run(
                self.app,
                host=self.config.host,
                port=self.config.port,
                log_level="warning",  # Réduire les logs répétitifs
                access_log=False      # Désactiver les logs d'accès HTTP
            )
        except Exception as e:
            logger.error(f"Failed to start dashboard server: {e}")
            raise
    
    def get_status(self) -> dict:
        """Retourne le statut du serveur"""
        return {
            "status": "running",
            "uptime": str(datetime.utcnow() - self.start_time).split('.')[0],
            "managers": {
                name: manager is not None 
                for name, manager in self.bot_managers.items()
            },
            "config": self.config.to_dict()
        } 