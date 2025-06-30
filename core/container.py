"""
Dependency Injection Container pour Bot Twitter Automatisé

Remplace les singletons par un système DI flexible :
- Registration de services
- Gestion du cycle de vie 
- Configuration par environnement
- Tests facilitités
"""

import inspect
from typing import Dict, Any, Type, TypeVar, Optional, Callable
from loguru import logger

T = TypeVar('T')


class DIContainer:
    """
    Container de Dependency Injection
    
    Gère l'enregistrement et la résolution des dépendances
    de manière flexible et testable.
    """
    
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {}
        self._instances: Dict[str, Any] = {}
        self._initializers: Dict[str, Callable] = {}
        
    def register(
        self, 
        interface: str, 
        implementation: Type[T], 
        singleton: bool = True,
        initializer: Optional[Callable] = None
    ) -> 'DIContainer':
        """
        Enregistre un service dans le container
        
        Args:
            interface: Nom du service (clé)
            implementation: Classe d'implémentation
            singleton: Si True, une seule instance créée
            initializer: Fonction d'initialisation custom
            
        Returns:
            DIContainer: Pour chaînage fluent
        """
        self._services[interface] = {
            'implementation': implementation,
            'singleton': singleton,
            'initialized': False
        }
        
        if initializer:
            self._initializers[interface] = initializer
            
        impl_name = implementation.__name__ if implementation else f"{interface}_factory"
        logger.debug(f"Registered service: {interface} -> {impl_name}")
        return self
    
    def register_instance(self, interface: str, instance: Any) -> 'DIContainer':
        """
        Enregistre une instance déjà créée
        
        Args:
            interface: Nom du service
            instance: Instance du service
            
        Returns:
            DIContainer: Pour chaînage fluent
        """
        self._instances[interface] = instance
        self._services[interface] = {
            'implementation': type(instance),
            'singleton': True,
            'initialized': True
        }
        
        logger.debug(f"Registered instance: {interface} -> {type(instance).__name__}")
        return self
    
    def get(self, interface: str) -> Any:
        """
        Résout et retourne un service
        
        Args:
            interface: Nom du service à résoudre
            
        Returns:
            Instance du service
            
        Raises:
            KeyError: Si le service n'est pas enregistré
            Exception: Si l'instanciation échoue
        """
        if interface not in self._services:
            raise KeyError(f"Service '{interface}' not registered")
        
        service_config = self._services[interface]
        
        # Si singleton et déjà instancié, retourner l'instance
        if service_config['singleton'] and interface in self._instances:
            return self._instances[interface]
        
        # Créer nouvelle instance
        try:
            implementation = service_config['implementation']
            
            # Vérifier si custom initializer
            if interface in self._initializers:
                instance = self._initializers[interface](self)
            else:
                # Auto-injection des dépendances via constructeur
                instance = self._create_with_injection(implementation)
            
            # Stocker si singleton
            if service_config['singleton']:
                self._instances[interface] = instance
                self._services[interface]['initialized'] = True
            
            logger.debug(f"Created instance: {interface} -> {type(instance).__name__}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create service '{interface}': {e}")
            raise
    
    def _create_with_injection(self, implementation: Type[T]) -> T:
        """
        Crée une instance avec auto-injection des dépendances
        
        Args:
            implementation: Classe à instancier
            
        Returns:
            Instance créée avec dépendances injectées
        """
        # Analyser le constructeur
        signature = inspect.signature(implementation.__init__)
        
        # Résoudre les dépendances
        kwargs = {}
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            # Vérifier si annotation de type disponible
            if param.annotation and param.annotation != inspect.Parameter.empty:
                # Chercher par nom de type
                type_name = param.annotation.__name__.lower()
                
                # Mappage des types vers services
                type_mappings = {
                    'configmanager': 'config',
                    'storagemanager': 'storage', 
                    'twitterapimanager': 'twitter',
                    'contentgenerator': 'content',
                    'taskscheduler': 'scheduler',
                    'replyhandler': 'reply_handler',
                    'promptmanager': 'prompts'
                }
                
                service_name = type_mappings.get(type_name)
                if service_name and service_name in self._services:
                    kwargs[param_name] = self.get(service_name)
            
            # Chercher par nom de paramètre
            elif param_name in self._services:
                kwargs[param_name] = self.get(param_name)
        
        return implementation(**kwargs)
    
    def has(self, interface: str) -> bool:
        """Vérifie si un service est enregistré"""
        return interface in self._services
    
    def is_initialized(self, interface: str) -> bool:
        """Vérifie si un service singleton est déjà initialisé"""
        if interface not in self._services:
            return False
        return self._services[interface].get('initialized', False)
    
    def clear(self) -> None:
        """Nettoie tous les services (utile pour les tests)"""
        self._services.clear()
        self._instances.clear()
        self._initializers.clear()
        logger.debug("Container cleared")
    
    def get_registered_services(self) -> Dict[str, str]:
        """Retourne la liste des services enregistrés"""
        result = {}
        for name, config in self._services.items():
            if config['implementation'] is None:
                # Service avec initializer custom
                result[name] = f"{name}_factory"
            else:
                result[name] = config['implementation'].__name__
        return result


# Container global - remplace les anciens singletons
_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    Obtient le container DI global
    
    Returns:
        DIContainer: Instance du container
    """
    global _container
    if _container is None:
        _container = DIContainer()
        _setup_default_services(_container)
    return _container


def _create_stats_collector():
    """Factory function pour StatsCollector"""
    from stats import get_stats_collector
    return get_stats_collector()


def _create_llm_manager():
    """Factory function pour LLMProviderManager"""
    from llm_providers import get_llm_manager
    return get_llm_manager()


def _create_viral_strategies():
    """Factory function pour ViralStrategies"""
    from viral_strategies import create_viral_strategies
    return create_viral_strategies()


def _setup_default_services(container: DIContainer) -> None:
    """
    Configure les services par défaut du bot
    
    Args:
        container: Container à configurer
    """
    # Import lazy pour éviter les dépendances circulaires
    from config import create_config_manager
    from storage import create_storage_manager
    from twitter_api import create_twitter_manager
    from generator import create_content_generator
    from scheduler import create_task_scheduler
    from reply_handler import create_reply_handler
    from prompt_manager import create_prompt_manager
    
    # Enregistrement des services principaux avec factory functions
    container.register(
        'config', 
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_config_manager()
    )
    
    container.register(
        'storage',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_storage_manager(c.get('config'))
    )
    
    container.register(
        'twitter',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_twitter_manager(c.get('config'), c.get('storage'))
    )
    
    container.register(
        'content',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_content_generator(
            c.get('config'), 
            c.get('twitter'), 
            c.get('storage'), 
            c.get('prompts'),
            c.get('viral_strategies')
        )
    )
    
    # Services nouvellement migrés avec factory functions
    container.register(
        'scheduler',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_task_scheduler(
            c.get('config'),
            c.get('twitter'),
            c.get('content'),
            c.get('storage'),
            c.get('stats'),
            reply_handler=None  # Éviter la dépendance circulaire
        )
    )
    
    container.register(
        'reply_handler',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_reply_handler(
            c.get('twitter'),
            c.get('storage'),
            c.get('config'),
            c.get('content'),
            c.get('prompts'),
            c.get('llm_manager')
        )
    )
    
    container.register(
        'prompts',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: create_prompt_manager()
    )
    
    # Services supplémentaires
    container.register(
        'stats',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: _create_stats_collector()
    )
    
    container.register(
        'llm_manager',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: _create_llm_manager()
    )
    
    container.register(
        'viral_strategies',
        None,  # Pas de classe directe
        singleton=True,
        initializer=lambda c: _create_viral_strategies()
    )
    
    logger.info("Default services registered in DI container with new architecture")


def reset_container() -> None:
    """Reset le container (pour les tests)"""
    global _container
    if _container:
        _container.clear()
    _container = None 