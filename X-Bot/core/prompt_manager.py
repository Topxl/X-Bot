"""
Prompt Manager pour Bot Twitter Automatisé

Gère tous les prompts système, templates et configurations
de génération de contenu de manière centralisée.

NOUVELLE ARCHITECTURE:
- Error Recovery pour chargement de fichiers
- Event Bus pour notifications de reload
- Intégration DI Container
- Messages utilisateur informatifs
"""

import json
import os
from typing import Dict, List, Optional, Any
from loguru import logger

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity


class PromptManager:
    """
    Gestionnaire centralisé des prompts et templates avec nouvelle architecture
    
    Features:
    - Chargement des prompts depuis prompts.json
    - Templates dynamiques avec variables
    - Gestion des prompts système et utilisateur
    - Hot-reload des configurations
    - Error Recovery pour chargement de fichiers
    - Event Bus pour notifications de reload
    """
    
    def __init__(self, prompts_file: str = "config/prompts.json", config_file: str = "config/config.json"):
        self.prompts_file = prompts_file
        self.config_file = config_file
        self.prompts_data: Dict[str, Any] = {}
        self.config_data: Dict[str, Any] = {}
        
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        # Initialize with error recovery
        self._initialize_with_recovery()
    
    @safe_execute(
        user_message_key="config_error",
        severity=ErrorSeverity.LOW,
        fallback_category="prompt_loading",
        module="PromptManager"
    )
    def _initialize_with_recovery(self) -> None:
        """Initialize prompt manager with comprehensive error recovery"""
        try:
            self._load_prompts()
            self._load_config()
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.MODULE_INITIALIZED,
                data={
                    'module': 'prompt_manager',
                    'status': 'initialized',
                    'prompts_loaded': len(self.prompts_data),
                    'config_loaded': len(self.config_data)
                },
                source='PromptManager'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Prompt manager initialization warning: {e}")
            
            # Publier événement d'avertissement avec fallback
            self.event_bus.publish(
                EventTypes.MODULE_FAILED,
                data={
                    'module': 'prompt_manager',
                    'error': str(e),
                    'fallback_mode': 'default_prompts'
                },
                source='PromptManager'
            )
    
    @safe_execute(
        user_message_key="prompt_loading_error",
        severity=ErrorSeverity.LOW,
        fallback_category="prompt_loading",
        module="PromptManager"
    )
    def _load_prompts(self) -> None:
        """Charge les prompts depuis le fichier JSON avec error recovery"""
        try:
            if not os.path.exists(self.prompts_file):
                logger.warning(f"⚠️ Prompts file not found: {self.prompts_file}")
                self._create_default_prompts()
                return
            
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                self.prompts_data = json.load(f)
                
            logger.info(f"✅ Prompts loaded successfully from {self.prompts_file}")
            
            # Publier événement de chargement
            self.event_bus.publish(
                EventTypes.CONFIG_RELOADED,
                data={
                    'file_type': 'prompts',
                    'file_path': self.prompts_file,
                    'prompts_count': len(self.prompts_data)
                },
                source='PromptManager'
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to load prompts: {e}")
            self._create_default_prompts()
            raise e  # Laisse l'error recovery gérer
    
    def _load_config(self) -> None:
        """Charge la configuration depuis config.json"""
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Config file not found: {self.config_file}")
                self.config_data = {}
                return
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
                
            logger.info(f"Config loaded successfully from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self.config_data = {}
    
    def _create_default_prompts(self) -> None:
        """Crée les prompts par défaut en cas d'échec de chargement"""
        self.prompts_data = {
            "system_prompts": {
                "tweet_generation": {
                    "role": "system",
                    "content": "You are an expert crypto content creator for Twitter/X."
                },
                "auto_reply": {
                    "role": "system",
                    "content": "You are a friendly crypto enthusiast."
                }
            },
            "templates": {
                "simple_replies": [
                    "Thanks for engaging! 🙏 #Solana"
                ]
            }
        }
        logger.info("Using default prompts")
    
    @safe_execute(
        user_message_key="prompt_reload_error",
        severity=ErrorSeverity.LOW,
        module="PromptManager"
    )
    def reload_prompts(self) -> bool:
        """
        Recharge les prompts et la config depuis les fichiers avec error recovery
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            logger.info("🔄 Reloading prompts and configuration...")
            
            # Publier événement de début de reload
            self.event_bus.publish(
                EventTypes.CONFIG_RELOADING,
                data={
                    'module': 'prompt_manager',
                    'action': 'reload_started'
                },
                source='PromptManager'
            )
            
            self._load_prompts()
            self._load_config()
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.CONFIG_RELOADED,
                data={
                    'module': 'prompt_manager',
                    'status': 'success',
                    'prompts_count': len(self.prompts_data),
                    'config_size': len(self.config_data)
                },
                source='PromptManager'
            )
            
            logger.info("✅ Prompts and configuration reloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to reload prompts/config: {e}")
            
            # Publier événement d'échec
            self.event_bus.publish(
                EventTypes.CONFIG_RELOAD_FAILED,
                data={
                    'module': 'prompt_manager',
                    'error': str(e)
                },
                source='PromptManager',
                priority=EventPriority.HIGH
            )
            
            return False
    
    def get_system_prompt(self, prompt_type: str) -> Dict[str, str]:
        """
        Récupère un prompt système
        
        Args:
            prompt_type: Type de prompt (tweet_generation, auto_reply, etc.)
            
        Returns:
            Dict contenant role et content pour OpenAI
        """
        try:
            return self.prompts_data["system_prompts"][prompt_type]
        except KeyError:
            logger.warning(f"System prompt not found: {prompt_type}")
            return {
                "role": "system",
                "content": "You are a helpful AI assistant."
            }
    
    def get_user_prompt(self, prompt_type: str, **kwargs) -> str:
        """
        Récupère et formate un prompt utilisateur avec variables
        
        Args:
            prompt_type: Type de prompt
            **kwargs: Variables à injecter dans le template
            
        Returns:
            str: Prompt formaté
        """
        try:
            template = self.prompts_data["user_prompts"][prompt_type]["template"]
            return template.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"User prompt formatting failed for {prompt_type}: {e}")
            return f"Please help with {prompt_type}"
    
    def get_template(self, template_name: str) -> Any:
        """
        Récupère un template
        
        Args:
            template_name: Nom du template
            
        Returns:
            Template data (liste, dict, str)
        """
        try:
            return self.prompts_data["templates"][template_name]
        except KeyError:
            logger.warning(f"Template not found: {template_name}")
            return []
    
    def get_setting(self, setting_type: str, key: str = None) -> Any:
        """
        Récupère une configuration depuis config.json
        
        Args:
            setting_type: Type de setting (tweet_generation, auto_reply, etc.)
            key: Clé spécifique (optionnel)
            
        Returns:
            Configuration value
        """
        try:
            # Lire depuis content_generation dans config.json
            content_gen = self.config_data.get("content_generation", {})
            
            if setting_type == "auto_reply":
                settings = content_gen.get("auto_reply", {})
            elif setting_type == "tweet_generation":
                settings = content_gen.get("tweet_generation", {})
            elif setting_type == "image_generation":
                # Pour l'image generation, utiliser les valeurs principales + dall-e
                settings = {
                    "model": content_gen.get("image_model", "dall-e-3"),
                    "size": "1024x1024", 
                    "quality": "standard"
                }
            else:
                # Fallback pour compatibility
                settings = content_gen
            
            if key:
                return settings.get(key)
            return settings
        except Exception as e:
            logger.warning(f"Setting not found: {setting_type}.{key} - {e}")
            return None
    
    def update_prompt(self, category: str, prompt_type: str, content: Dict[str, Any]) -> bool:
        """
        Met à jour un prompt
        
        Args:
            category: Catégorie (system_prompts, user_prompts, templates, settings)
            prompt_type: Type de prompt
            content: Nouveau contenu
            
        Returns:
            bool: True si succès
        """
        try:
            if category not in self.prompts_data:
                self.prompts_data[category] = {}
            
            self.prompts_data[category][prompt_type] = content
            
            # Sauvegarder dans le fichier
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Updated prompt: {category}.{prompt_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update prompt: {e}")
            return False
    
    def get_image_prompt(self, content: str, theme: str = "default") -> str:
        """
        Génère un prompt pour l'image basé sur le contenu
        
        Args:
            content: Contenu du tweet
            theme: Thème visuel
            
        Returns:
            str: Prompt pour DALL-E
        """
        try:
            base_prompt = self.prompts_data["system_prompts"]["image_generation"]["base_prompt"]
            style_suffix = self.prompts_data["system_prompts"]["image_generation"]["style_suffix"]
            
            # Déterminer le thème
            themes = self.prompts_data["templates"]["image_themes"]
            theme_desc = themes.get(theme, themes["default"])
            
            return f"{base_prompt} {theme_desc}. {style_suffix}"
            
        except Exception as e:
            logger.error(f"Failed to generate image prompt: {e}")
            return "Create a modern, professional illustration for social media."
    
    def get_crypto_topics(self) -> List[str]:
        """Récupère la liste des topics crypto"""
        return self.get_template("crypto_topics")
    
    def get_simple_replies(self) -> List[str]:
        """Récupère les réponses simples prédéfinies (deprecated - use LLM)"""
        logger.warning("simple_replies is deprecated - using force_llm instead")
        return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du prompt manager"""
        return {
            'prompts_file': self.prompts_file,
            'system_prompts_count': len(self.prompts_data.get("system_prompts", {})),
            'user_prompts_count': len(self.prompts_data.get("user_prompts", {})),
            'templates_count': len(self.prompts_data.get("templates", {})),
            'settings_count': len(self.prompts_data.get("settings", {}))
        }


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION
# =============================================================================

def create_prompt_manager(prompts_file: str = "config/prompts.json", 
                         config_file: str = "config/config.json") -> PromptManager:
    """
    Factory function pour DI Container
    
    Crée une instance PromptManager avec injection de dépendances.
    Utilisé par le DI container au lieu des singletons.
    """
    return PromptManager(prompts_file, config_file)


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_prompt_manager() -> PromptManager:
    """
    DEPRECATED: Utiliser container.get('prompts') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_prompt_manager() is deprecated. Use container.get('prompts') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('prompts')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_prompt_manager()


# =============================================================================
# FONCTIONS HELPER - DEPRECATED (accéder via DI Container)
# =============================================================================

def get_system_prompt(prompt_type: str) -> Dict[str, str]:
    """
    DEPRECATED: Accès direct via container recommandé
    Accès rapide aux prompts système
    """
    return get_prompt_manager().get_system_prompt(prompt_type)


def get_user_prompt(prompt_type: str, **kwargs) -> str:
    """
    DEPRECATED: Accès direct via container recommandé
    Accès rapide aux prompts utilisateur
    """
    return get_prompt_manager().get_user_prompt(prompt_type, **kwargs)


def get_template(template_name: str) -> Any:
    """
    DEPRECATED: Accès direct via container recommandé
    Accès rapide aux templates
    """
    return get_prompt_manager().get_template(template_name)


def reload_prompts() -> bool:
    """
    DEPRECATED: Accès direct via container recommandé
    Recharge tous les prompts
    """
    return get_prompt_manager().reload_prompts()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - AI-powered prompt optimization
# - Dynamic prompt adaptation based on performance
# - A/B testing for prompt variations
# - Multi-language prompt support
# - Context-aware prompt selection
# - Real-time prompt performance analytics
# - Prompt versioning and rollback
# - External prompt source integration 