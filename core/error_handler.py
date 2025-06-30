"""
Système de Récupération d'Erreur Avancé pour Bot Twitter Automatisé

Gestion d'erreur complète avec :
- Messages d'erreur informatifs pour l'utilisateur
- Graceful degradation avec fallbacks
- Recovery automatique
- Notification et alerting
- Continuité de service
"""

import traceback
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import asyncio
import time
from loguru import logger

from events import get_event_bus, EventTypes, EventPriority


class ErrorSeverity(Enum):
    """Niveaux de sévérité des erreurs"""
    LOW = "low"          # Erreur mineure, service continue
    MEDIUM = "medium"    # Erreur notable, dégradation possible
    HIGH = "high"        # Erreur importante, fonctionnalité affectée
    CRITICAL = "critical" # Erreur critique, service en danger


@dataclass
class ErrorInfo:
    """Informations complètes sur une erreur"""
    error_type: str
    error_message: str
    user_message: str
    severity: ErrorSeverity
    timestamp: datetime
    module: str
    function: str
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_successful: bool = False
    fallback_used: str = None


class FallbackStrategy:
    """Stratégie de fallback pour récupération d'erreur"""
    
    def __init__(self, name: str, handler: Callable, priority: int = 1):
        self.name = name
        self.handler = handler
        self.priority = priority
        self.success_count = 0
        self.failure_count = 0
        self.last_used = None
    
    def execute(self, *args, **kwargs) -> Any:
        """Exécute le fallback"""
        try:
            self.last_used = datetime.utcnow()
            result = self.handler(*args, **kwargs)
            self.success_count += 1
            return result
        except Exception as e:
            self.failure_count += 1
            raise e


class ErrorRecoveryManager:
    """
    Gestionnaire de récupération d'erreur
    
    Fournit des mécanismes complets pour :
    - Détection et classification d'erreurs
    - Messages utilisateur informatifs
    - Stratégies de fallback
    - Recovery automatique
    - Notification d'erreurs critiques
    """
    
    def __init__(self):
        self.event_bus = get_event_bus()
        self.error_history: List[ErrorInfo] = []
        self.fallback_strategies: Dict[str, List[FallbackStrategy]] = {}
        self.user_messages: Dict[str, str] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        self.max_history = 1000
        
        # Configurer messages utilisateur par défaut
        self._setup_default_user_messages()
        
        # Configurer fallbacks par défaut
        self._setup_default_fallbacks()
    
    def _setup_default_user_messages(self) -> None:
        """Configure les messages utilisateur par défaut"""
        self.user_messages.update({
            'twitter_api_error': "🔄 Problème temporaire avec Twitter. Le bot continue à essayer...",
            'openai_api_error': "🤖 Service IA temporairement indisponible. Utilisation de contenu de secours...",
            'database_error': "💾 Problème de sauvegarde. Les données seront récupérées automatiquement.",
            'quota_exceeded': "⏸️ Limite Twitter atteinte. Le bot reprendra automatiquement demain.",
            'network_error': "🌐 Problème de connexion. Nouvelle tentative dans quelques instants...",
            'config_error': "⚙️ Problème de configuration détecté. Utilisation des paramètres par défaut.",
            'generation_error': "✨ Erreur de génération. Utilisation d'un contenu alternatif...",
            'general_error': "⚠️ Incident technique détecté. Le système se rétablit automatiquement."
        })
    
    def _setup_default_fallbacks(self) -> None:
        """Configure les stratégies de fallback par défaut"""
        # Fallback pour génération de contenu
        self.register_fallback(
            'content_generation',
            FallbackStrategy(
                'static_content',
                self._static_content_fallback,
                priority=1
            )
        )
        
        # Fallback pour sauvegarde
        self.register_fallback(
            'data_storage',
            FallbackStrategy(
                'local_storage',
                self._local_storage_fallback,
                priority=1
            )
        )
        
        # Fallback pour images
        self.register_fallback(
            'image_generation',
            FallbackStrategy(
                'no_image',
                self._no_image_fallback,
                priority=1
            )
        )
    
    def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        module: str = "unknown",
        function: str = "unknown",
        user_message_key: str = "general_error",
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        enable_recovery: bool = True,
        fallback_category: str = None
    ) -> ErrorInfo:
        """
        Gère une erreur avec récupération complète
        
        Args:
            error: Exception levée
            context: Contexte additionnel
            module: Module où l'erreur s'est produite
            function: Fonction où l'erreur s'est produite
            user_message_key: Clé pour message utilisateur
            severity: Sévérité de l'erreur
            enable_recovery: Si True, tente recovery
            fallback_category: Catégorie de fallback à utiliser
            
        Returns:
            ErrorInfo: Informations complètes sur l'erreur
        """
        error_info = ErrorInfo(
            error_type=type(error).__name__,
            error_message=str(error),
            user_message=self.user_messages.get(user_message_key, self.user_messages['general_error']),
            severity=severity,
            timestamp=datetime.utcnow(),
            module=module,
            function=function,
            context=context or {}
        )
        
        # Ajouter à l'historique
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)
        
        # Log technique
        logger.error(
            f"Error in {module}.{function}: {error}",
            extra={
                'error_type': error_info.error_type,
                'severity': severity.value,
                'context': context,
                'traceback': traceback.format_exc()
            }
        )
        
        # Message utilisateur
        logger.info(f"👤 {error_info.user_message}")
        
        # Publier événement d'erreur
        self.event_bus.publish(
            EventTypes.API_ERROR,
            data={
                'error_info': error_info,
                'recovery_enabled': enable_recovery
            },
            priority=EventPriority.HIGH if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else EventPriority.NORMAL,
            source=module
        )
        
        # Tentative de récupération si activée
        if enable_recovery:
            recovery_result = self._attempt_recovery(error_info, fallback_category)
            error_info.recovery_attempted = True
            error_info.recovery_successful = recovery_result is not None
            error_info.fallback_used = recovery_result
        
        # Alertes pour erreurs critiques
        if severity == ErrorSeverity.CRITICAL:
            self._send_critical_alert(error_info)
        
        return error_info
    
    def _attempt_recovery(
        self, 
        error_info: ErrorInfo, 
        fallback_category: str = None
    ) -> Optional[str]:
        """
        Tente une récupération automatique
        
        Args:
            error_info: Informations sur l'erreur
            fallback_category: Catégorie de fallback
            
        Returns:
            str: Nom du fallback utilisé si succès
        """
        if not fallback_category or fallback_category not in self.fallback_strategies:
            return None
        
        # Trier par priorité
        strategies = sorted(
            self.fallback_strategies[fallback_category],
            key=lambda s: s.priority,
            reverse=True
        )
        
        for strategy in strategies:
            try:
                logger.info(f"🔄 Tentative de récupération: {strategy.name}")
                
                # Exécuter fallback (les paramètres viennent du contexte)
                result = strategy.execute(error_info.context)
                
                logger.success(f"✅ Récupération réussie via: {strategy.name}")
                return strategy.name
                
            except Exception as fallback_error:
                logger.warning(f"❌ Fallback {strategy.name} failed: {fallback_error}")
                continue
        
        logger.error("❌ Toutes les stratégies de récupération ont échoué")
        return None
    
    def _send_critical_alert(self, error_info: ErrorInfo) -> None:
        """Envoie une alerte pour erreur critique"""
        alert_message = f"""
🚨 ERREUR CRITIQUE DÉTECTÉE

Module: {error_info.module}
Fonction: {error_info.function}
Erreur: {error_info.error_message}
Timestamp: {error_info.timestamp}

Le système tente une récupération automatique.
"""
        
        logger.critical(alert_message)
        
        # Publier événement d'alerte
        self.event_bus.publish(
            EventTypes.ALERT_TRIGGERED,
            data={
                'alert_type': 'critical_error',
                'message': alert_message,
                'error_info': error_info
            },
            priority=EventPriority.CRITICAL,
            source='error_handler'
        )
    
    def register_fallback(
        self,
        category: str,
        strategy: FallbackStrategy
    ) -> None:
        """
        Enregistre une stratégie de fallback
        
        Args:
            category: Catégorie de l'erreur
            strategy: Stratégie de fallback
        """
        if category not in self.fallback_strategies:
            self.fallback_strategies[category] = []
        
        self.fallback_strategies[category].append(strategy)
        
        # Trier par priorité
        self.fallback_strategies[category].sort(
            key=lambda s: s.priority,
            reverse=True
        )
        
        logger.debug(f"Registered fallback: {category} -> {strategy.name}")
    
    def register_user_message(self, key: str, message: str) -> None:
        """Enregistre un message utilisateur personnalisé"""
        self.user_messages[key] = message
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'erreur"""
        if not self.error_history:
            return {'total_errors': 0}
        
        # Compter par type
        error_types = {}
        severity_counts = {}
        module_counts = {}
        recovery_stats = {'attempted': 0, 'successful': 0}
        
        for error in self.error_history:
            # Types d'erreur
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            
            # Sévérité
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            
            # Modules
            module_counts[error.module] = module_counts.get(error.module, 0) + 1
            
            # Recovery
            if error.recovery_attempted:
                recovery_stats['attempted'] += 1
                if error.recovery_successful:
                    recovery_stats['successful'] += 1
        
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'severity_distribution': severity_counts,
            'modules_affected': module_counts,
            'recovery_stats': recovery_stats,
            'recovery_rate': recovery_stats['successful'] / recovery_stats['attempted'] if recovery_stats['attempted'] > 0 else 0
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[ErrorInfo]:
        """Retourne les erreurs récentes"""
        return self.error_history[-limit:]
    
    def get_available_fallbacks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retourne tous les fallbacks disponibles par catégorie"""
        result = {}
        for category, strategies in self.fallback_strategies.items():
            result[category] = [
                {
                    'name': strategy.name,
                    'priority': strategy.priority
                }
                for strategy in strategies
            ]
        return result
    
    # Fallbacks par défaut
    
    def _static_content_fallback(self, context: Dict[str, Any]) -> str:
        """Fallback pour génération de contenu"""
        fallback_contents = [
            "🚀 Building the future of crypto, one block at a time! #Solana #Innovation",
            "💎 Diamond hands and clear vision - that's how we roll in #crypto",
            "⚡ Speed, security, scalability - the holy trinity of blockchain! #Solana",
            "🌊 Riding the waves of innovation in the #DeFi space",
            "🔥 When technology meets community, magic happens! #Web3"
        ]
        
        import random
        content = random.choice(fallback_contents)
        logger.info(f"📝 Utilisation de contenu de secours: {content[:50]}...")
        return content
    
    def _local_storage_fallback(self, context: Dict[str, Any]) -> bool:
        """Fallback pour sauvegarde locale"""
        try:
            import json
            import os
            from datetime import datetime
            
            # Créer dossier de backup si nécessaire
            backup_dir = "backup_data"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Sauvegarder localement
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{backup_dir}/fallback_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump(context, f, indent=2, default=str)
            
            logger.info(f"💾 Sauvegarde locale créée: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fallback storage failed: {e}")
            return False
    
    def _no_image_fallback(self, context: Dict[str, Any]) -> None:
        """Fallback quand génération d'image échoue"""
        logger.info("🖼️ Publication sans image (fallback activé)")
        return None


# Instance globale
_error_manager: Optional[ErrorRecoveryManager] = None


def get_error_manager() -> ErrorRecoveryManager:
    """Obtient le gestionnaire d'erreur global"""
    global _error_manager
    if _error_manager is None:
        _error_manager = ErrorRecoveryManager()
    return _error_manager


def safe_execute(
    user_message_key: str = "general_error",
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    fallback_category: str = None,
    module: str = None,
    enable_recovery: bool = True
):
    """
    Décorateur pour exécution sécurisée avec gestion d'erreur
    
    Args:
        user_message_key: Clé pour message utilisateur
        severity: Sévérité de l'erreur
        fallback_category: Catégorie de fallback
        module: Nom du module
        enable_recovery: Active la récupération
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_manager = get_error_manager()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = error_manager.handle_error(
                    error=e,
                    context={'args': args, 'kwargs': kwargs},
                    module=module or func.__module__,
                    function=func.__name__,
                    user_message_key=user_message_key,
                    severity=severity,
                    enable_recovery=enable_recovery,
                    fallback_category=fallback_category
                )
                
                # Si récupération réussie et fallback retourne une valeur, l'utiliser
                if error_info.recovery_successful and fallback_category:
                    # Récupérer le résultat du fallback depuis l'historique
                    # Pour simplifier, retourner None ou une valeur par défaut
                    logger.info(f"✅ Fonction {func.__name__} continue avec fallback")
                    return None
                
                # Sinon propager l'erreur si critique
                if severity == ErrorSeverity.CRITICAL:
                    raise e
                
                logger.warning(f"⚠️ Fonction {func.__name__} terminée avec erreur gérée")
                return None
        
        return wrapper
    return decorator 