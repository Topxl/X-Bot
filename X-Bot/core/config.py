"""
Configuration Manager pour Bot Twitter Automatisé

Gère la lecture du config.json local et la synchronisation avec Supabase
pour permettre hot reload et configuration centralisée.

NOUVELLE ARCHITECTURE:
- Utilise Event Bus pour notifications de changement
- Error Recovery avec messages utilisateur  
- Intégration DI Container
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field, validator
from supabase import create_client, Client

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity

# Load environment variables
load_dotenv()


class XAPIPlan(BaseModel):
    """Configuration pour les quotas X API selon le plan"""
    posts_per_month: int
    reads_per_month: int
    posts_per_day: int
    reads_per_day: int


class XAPIConfig(BaseModel):
    """Configuration X API"""
    plan: str = Field(default="basic", pattern="^(basic|pro|enterprise)$")
    quotas: Dict[str, XAPIPlan]
    
    @validator('plan')
    def validate_plan(cls, v):
        if v not in ['basic', 'pro', 'enterprise']:
            raise ValueError('Plan must be basic, pro, or enterprise')
        return v


class PostingConfig(BaseModel):
    """Configuration des publications"""
    enabled: bool = True
    frequency_per_day: int = Field(default=3, ge=1, le=50)
    time_range: Dict[str, str]
    timezone: str = "Europe/Paris"


class EngagementConfig(BaseModel):
    """Configuration de l'engagement automatique"""
    auto_like_replies: bool = True
    likes_per_day: int = Field(default=100, ge=0, le=1000)
    max_likes_per_hour: int = Field(default=20, ge=0, le=100)
    
    # Auto-reply settings
    auto_reply_enabled: bool = False
    reply_check_interval_minutes: int = Field(default=15, ge=1, le=60)
    max_replies_per_day: int = Field(default=20, ge=0, le=100)
    max_replies_per_conversation: int = Field(default=1, ge=0, le=5)
    reply_check_24h: bool = True  # Si False, respecte les heures de posting


class ContentGenerationConfig(BaseModel):
    """Configuration de la génération de contenu"""
    provider: str = "openai"
    model: str = "gpt-4"
    enable_images: bool = True
    image_model: str = "dall-e-3"
    max_tokens: int = Field(default=150, ge=50, le=500)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    viral_keywords: list[str] = []


class MonitoringConfig(BaseModel):
    """Configuration du monitoring"""
    collect_stats: bool = True
    stats_frequency_hours: int = Field(default=1, ge=1, le=24)
    daily_report: bool = True
    report_time: str = "08:00"
    alert_on_quota_warning: bool = True
    quota_warning_threshold: float = Field(default=0.8, ge=0.5, le=0.95)


class StorageConfig(BaseModel):
    """Configuration du stockage"""
    supabase_config_sync: bool = True
    keep_tweet_history_days: int = Field(default=90, ge=7, le=365)
    cleanup_frequency_days: int = Field(default=7, ge=1, le=30)


class LoggingConfig(BaseModel):
    """Configuration des logs"""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    format: str = "json"
    file_rotation: str = "1 day"
    max_file_size: str = "10 MB"


class BotConfig(BaseModel):
    """Configuration complète du bot"""
    x_api: XAPIConfig
    posting: PostingConfig
    engagement: EngagementConfig
    content_generation: ContentGenerationConfig
    monitoring: MonitoringConfig
    storage: StorageConfig
    logging: LoggingConfig


class ConfigManager:
    """
    Gestionnaire de configuration centralisé avec nouvelle architecture
    
    Features:
    - Lecture JSON local avec validation Pydantic
    - Sync bidirectionnelle avec Supabase
    - Hot reload depuis Supabase
    - Fallback gracieux si Supabase indisponible
    - Cache local pour performance
    - Event Bus pour notifications de changement
    - Error Recovery avec messages utilisateur
    """
    
    def __init__(self, config_file: str = "config.json"):
        # If a relative path is provided, make it relative to the project root
        if not os.path.isabs(config_file) and config_file == "config.json":
            # Default case - use config/config.json relative to project root
            project_root = Path(__file__).parent.parent.resolve()
            self.config_file = project_root / "config" / "config.json"
        else:
            self.config_file = Path(config_file)
            
        self.supabase: Optional[Client] = None
        self._config: Optional[BotConfig] = None
        self._last_sync: Optional[datetime] = None
        
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        # Initialize Supabase if credentials available
        self._init_supabase()
        
        # Load initial configuration
        self.reload_config()
    
    @safe_execute(
        user_message_key="config_error",
        severity=ErrorSeverity.LOW,
        module="ConfigManager"
    )
    def _init_supabase(self) -> None:
        """Initialize Supabase client avec error recovery"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)
                logger.info("✅ Supabase client initialized successfully")
                
                # Publier événement de succès
                self.event_bus.publish(
                    EventTypes.MODULE_INITIALIZED,
                    data={'module': 'supabase_client', 'status': 'connected'},
                    source='ConfigManager'
                )
            else:
                logger.warning("⚠️ Supabase credentials not found, working in local-only mode")
                self.supabase = None
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
            self.supabase = None
            raise e  # Laisse l'error recovery gérer
    
    @safe_execute(
        user_message_key="config_error",
        severity=ErrorSeverity.HIGH,
        module="ConfigManager"
    )
    def _load_local_config(self) -> Dict[str, Any]:
        """Load configuration from local JSON file avec error recovery"""
        try:
            if not self.config_file.exists():
                error_msg = f"Config file {self.config_file} not found"
                logger.error(f"❌ {error_msg}")
                raise FileNotFoundError(error_msg)
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            logger.info(f"✅ Loaded configuration from {self.config_file}")
            
            # Publier événement de chargement
            self.event_bus.publish(
                EventTypes.CONFIG_RELOADED,
                data={'source': 'local_file', 'file': str(self.config_file)},
                source='ConfigManager'
            )
            
            return config_data
        
        except Exception as e:
            logger.error(f"❌ Failed to load local config: {e}")
            raise e  # Laisse l'error recovery gérer
    
    def _load_supabase_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from Supabase"""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table('configs').select('*').execute()
            
            if response.data:
                # Reconstruct config from key-value pairs
                config_dict = {}
                for row in response.data:
                    key = row['key']
                    value = row['value']
                    
                    # Handle nested keys (e.g., 'x_api.plan')
                    keys = key.split('.')
                    current = config_dict
                    for k in keys[:-1]:
                        if k not in current:
                            current[k] = {}
                        current = current[k]
                    current[keys[-1]] = value
                
                logger.info("Loaded configuration from Supabase")
                return config_dict
            
        except Exception as e:
            logger.error(f"Failed to load Supabase config: {e}")
        
        return None
    
    def _save_to_supabase(self, config: Dict[str, Any]) -> bool:
        """Save configuration to Supabase"""
        if not self.supabase:
            return False
        
        try:
            # Flatten config for key-value storage
            flat_config = self._flatten_dict(config)
            
            # Clear existing config
            self.supabase.table('configs').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            
            # Insert new config
            for key, value in flat_config.items():
                self.supabase.table('configs').insert({
                    'key': key,
                    'value': value,
                    'updated_at': datetime.utcnow().isoformat()
                }).execute()
            
            logger.info("Configuration saved to Supabase")
            self._last_sync = datetime.utcnow()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save config to Supabase: {e}")
            return False
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary for storage"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @safe_execute(
        user_message_key="config_error",
        severity=ErrorSeverity.HIGH,
        module="ConfigManager"
    )
    def reload_config(self) -> None:
        """
        Reload configuration with priority avec error recovery:
        1. Supabase (if available and newer)
        2. Local JSON file
        """
        try:
            # Load local config as baseline
            local_config = self._load_local_config()
            
            # Try to load from Supabase if available
            if self.supabase:
                supabase_config = self._load_supabase_config()
                if supabase_config:
                    # Merge configs (Supabase overrides local)
                    config_data = {**local_config, **supabase_config}
                    logger.info("📡 Configuration merged from Supabase + local")
                else:
                    config_data = local_config
                    # Sync local to Supabase if first time
                    if not self._last_sync:
                        self._save_to_supabase(local_config)
            else:
                config_data = local_config
            
            # Validate and create config object
            self._config = BotConfig(**config_data)
            logger.info("✅ Configuration reloaded successfully")
            
            # Publier événement de reload complet
            self.event_bus.publish(
                EventTypes.CONFIG_RELOADED,
                data={
                    'status': 'success',
                    'source': 'supabase+local' if self.supabase else 'local',
                    'timestamp': datetime.utcnow().isoformat()
                },
                source='ConfigManager',
                priority=EventPriority.HIGH
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to reload config: {e}")
            if self._config is None:
                raise RuntimeError("No valid configuration available")
    
    def get_config(self) -> BotConfig:
        """Get current configuration"""
        if self._config is None:
            self.reload_config()
        return self._config
    
    @safe_execute(
        user_message_key="config_error",
        severity=ErrorSeverity.MEDIUM,
        module="ConfigManager"
    )
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration and sync to Supabase avec error recovery
        
        Args:
            updates: Dictionary with config updates (can be nested)
        
        Returns:
            bool: Success status
        """
        try:
            # Get current config as dict
            current_config = self._config.dict() if self._config else self._load_local_config()
            
            # Apply updates (deep merge)
            updated_config = self._deep_merge(current_config, updates)
            
            # Validate new config
            new_config = BotConfig(**updated_config)
            
            # Save to local file
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f, indent=2, ensure_ascii=False)
            
            # Save to Supabase
            if self.supabase:
                self._save_to_supabase(updated_config)
            
            # Update current config
            self._config = new_config
            
            logger.info("✅ Configuration updated successfully")
            
            # Publier événement de mise à jour
            self.event_bus.publish(
                EventTypes.CONFIG_UPDATED,
                data={
                    'updates': updates,
                    'timestamp': datetime.utcnow().isoformat(),
                    'sync_supabase': self.supabase is not None
                },
                source='ConfigManager',
                priority=EventPriority.HIGH
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update config: {e}")
            
            # Publier événement d'erreur
            self.event_bus.publish(
                EventTypes.API_ERROR,
                data={
                    'error_type': 'config_update_failed',
                    'error_message': str(e),
                    'updates': updates
                },
                source='ConfigManager',
                priority=EventPriority.HIGH
            )
            
            return False
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get_x_api_credentials(self) -> Dict[str, str]:
        """Get X API credentials from environment"""
        return {
            'api_key': os.getenv('X_API_KEY'),
            'api_secret': os.getenv('X_API_SECRET'),
            'access_token': os.getenv('X_ACCESS_TOKEN'),
            'access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET'),
            'bearer_token': os.getenv('X_BEARER_TOKEN')
        }
    
    def get_openai_api_key(self) -> str:
        """Get OpenAI API key from environment"""
        return os.getenv('OPENAI_API_KEY')
    
    def get_current_quotas(self) -> XAPIPlan:
        """Get current X API quotas based on plan"""
        config = self.get_config()
        plan = config.x_api.plan
        return config.x_api.quotas[plan]


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION
# =============================================================================

def create_config_manager() -> ConfigManager:
    """
    Factory function pour DI Container
    
    Crée une instance ConfigManager avec la configuration d'environnement
    appropriée. Utilisé par le DI container au lieu des singletons.
    """
    config_file = os.getenv('CONFIG_FILE', 'config.json')
    return ConfigManager(config_file)


def get_config() -> BotConfig:
    """
    Shortcut pour obtenir la configuration via DI Container
    
    Cette fonction est maintenue pour compatibilité mais utilise
    désormais le DI container au lieu des singletons.
    """
    try:
        from container import get_container
        container = get_container()
        config_manager = container.get('config')
        return config_manager.get_config()
    except ImportError:
        # Fallback si container pas encore disponible
        logger.warning("⚠️ DI Container not available, using direct instantiation")
        return create_config_manager().get_config()


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_config_manager() -> ConfigManager:
    """
    DEPRECATED: Utiliser container.get('config') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_config_manager() is deprecated. Use container.get('config') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('config')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_config_manager()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - Config validation avec schemas JSON
# - Encryption des valeurs sensibles 
# - Multi-environment configs (dev/staging/prod)
# - Configuration versioning et rollback
# - Real-time config updates via Supabase realtime
# - Config A/B testing framework
# - Event-driven config hot reload
# - Configuration audit trail
# - A/B testing des configurations 