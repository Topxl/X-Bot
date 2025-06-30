"""
Event Bus System pour Bot Twitter Automatisé

Système d'événements centralisé pour découpler les modules :
- Publication/souscription d'événements
- Handlers asynchrones et synchrones
- Gestion d'erreurs robuste
- Monitoring des événements
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Callable, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum
from loguru import logger
import threading
import time


class EventPriority(Enum):
    """Priorité des événements"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """
    Événement du système
    
    Attributes:
        type: Type d'événement
        data: Données associées
        priority: Priorité de traitement
        timestamp: Moment de création
        source: Module source de l'événement
        correlation_id: ID pour traçabilité
    """
    type: str
    data: Any
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = None
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EventHandler:
    """Wrapper pour les handlers d'événements"""
    
    def __init__(
        self, 
        handler: Callable,
        async_handler: bool = False,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None
    ):
        self.handler = handler
        self.async_handler = async_handler
        self.priority = priority
        self.filter_func = filter_func
        self.call_count = 0
        self.last_called = None
        self.error_count = 0


class EventBus:
    """
    Bus d'événements centralisé
    
    Gère la publication et distribution des événements
    dans tout le système de manière découplée.
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._stats = {
            'events_published': 0,
            'events_handled': 0,
            'handler_errors': 0
        }
        self._lock = threading.Lock()
        
    def subscribe(
        self, 
        event_type: str, 
        handler: Callable,
        async_handler: bool = False,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> 'EventBus':
        """
        Souscrit à un type d'événement
        
        Args:
            event_type: Type d'événement à écouter
            handler: Fonction de traitement (event) -> None
            async_handler: Si True, handler async
            priority: Priorité du handler
            filter_func: Fonction de filtrage optionnelle
            
        Returns:
            EventBus: Pour chaînage fluent
        """
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            event_handler = EventHandler(
                handler, async_handler, priority, filter_func
            )
            
            self._handlers[event_type].append(event_handler)
            
            # Trier par priorité (HIGH en premier)
            self._handlers[event_type].sort(
                key=lambda h: h.priority.value, 
                reverse=True
            )
        
        logger.debug(f"Subscribed to event: {event_type}")
        return self
    
    def subscribe_global(
        self, 
        handler: Callable,
        async_handler: bool = False,
        priority: EventPriority = EventPriority.NORMAL,
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> 'EventBus':
        """
        Souscrit à tous les événements
        
        Args:
            handler: Fonction de traitement globale
            async_handler: Si True, handler async
            priority: Priorité du handler
            filter_func: Fonction de filtrage optionnelle
            
        Returns:
            EventBus: Pour chaînage fluent
        """
        with self._lock:
            event_handler = EventHandler(
                handler, async_handler, priority, filter_func
            )
            self._global_handlers.append(event_handler)
            
            # Trier par priorité
            self._global_handlers.sort(
                key=lambda h: h.priority.value,
                reverse=True
            )
        
        logger.debug("Subscribed to global events")
        return self
    
    def publish(
        self, 
        event_type: str, 
        data: Any = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        async_publish: bool = False
    ) -> Optional[Event]:
        """
        Publie un événement
        
        Args:
            event_type: Type d'événement
            data: Données associées
            priority: Priorité de l'événement
            source: Module source
            correlation_id: ID de corrélation
            async_publish: Publication asynchrone
            
        Returns:
            Event: Événement créé
        """
        event = Event(
            type=event_type,
            data=data,
            priority=priority,
            source=source,
            correlation_id=correlation_id
        )
        
        # Ajouter à l'historique
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
            
            self._stats['events_published'] += 1
        
        logger.debug(f"Publishing event: {event_type} from {source}")
        
        if async_publish:
            # Publication asynchrone en thread séparé
            threading.Thread(
                target=self._process_event,
                args=(event,),
                daemon=True
            ).start()
        else:
            # Publication synchrone
            self._process_event(event)
        
        return event
    
    def _process_event(self, event: Event) -> None:
        """
        Traite un événement en appelant tous les handlers
        
        Args:
            event: Événement à traiter
        """
        handlers_to_call = []
        
        # Récupérer handlers spécifiques
        with self._lock:
            if event.type in self._handlers:
                handlers_to_call.extend(self._handlers[event.type])
            
            # Ajouter handlers globaux
            handlers_to_call.extend(self._global_handlers)
        
        # Traiter chaque handler
        for handler_wrapper in handlers_to_call:
            try:
                # Vérifier filtre si défini
                if handler_wrapper.filter_func:
                    if not handler_wrapper.filter_func(event):
                        continue
                
                # Appeler le handler
                if handler_wrapper.async_handler:
                    # Handler asynchrone
                    asyncio.create_task(
                        self._call_async_handler(handler_wrapper, event)
                    )
                else:
                    # Handler synchrone
                    handler_wrapper.handler(event)
                
                # Mettre à jour statistiques
                with self._lock:
                    handler_wrapper.call_count += 1
                    handler_wrapper.last_called = datetime.utcnow()
                    self._stats['events_handled'] += 1
                
            except Exception as e:
                with self._lock:
                    handler_wrapper.error_count += 1
                    self._stats['handler_errors'] += 1
                
                logger.error(
                    f"Event handler failed for {event.type}: {e}",
                    extra={
                        'event_type': event.type,
                        'handler': handler_wrapper.handler.__name__,
                        'error': str(e)
                    }
                )
    
    async def _call_async_handler(
        self, 
        handler_wrapper: EventHandler, 
        event: Event
    ) -> None:
        """
        Appelle un handler asynchrone
        
        Args:
            handler_wrapper: Wrapper du handler
            event: Événement à traiter
        """
        try:
            await handler_wrapper.handler(event)
        except Exception as e:
            logger.error(f"Async handler failed: {e}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """
        Se désabonne d'un événement
        
        Args:
            event_type: Type d'événement
            handler: Handler à supprimer
            
        Returns:
            bool: True si supprimé avec succès
        """
        with self._lock:
            if event_type not in self._handlers:
                return False
            
            # Chercher et supprimer le handler
            for i, handler_wrapper in enumerate(self._handlers[event_type]):
                if handler_wrapper.handler == handler:
                    del self._handlers[event_type][i]
                    logger.debug(f"Unsubscribed from {event_type}")
                    return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du bus d'événements
        
        Returns:
            Dict: Statistiques détaillées
        """
        with self._lock:
            handler_stats = {}
            
            for event_type, handlers in self._handlers.items():
                handler_stats[event_type] = {
                    'handler_count': len(handlers),
                    'total_calls': sum(h.call_count for h in handlers),
                    'total_errors': sum(h.error_count for h in handlers)
                }
            
            return {
                'events_published': self._stats['events_published'],
                'events_handled': self._stats['events_handled'],
                'handler_errors': self._stats['handler_errors'],
                'registered_event_types': len(self._handlers),
                'global_handlers': len(self._global_handlers),
                'event_history_size': len(self._event_history),
                'handler_stats': handler_stats
            }
    
    def get_recent_events(self, limit: int = 50) -> List[Event]:
        """
        Retourne les événements récents
        
        Args:
            limit: Nombre max d'événements
            
        Returns:
            List[Event]: Événements récents
        """
        with self._lock:
            return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """Vide l'historique des événements"""
        with self._lock:
            self._event_history.clear()
            logger.debug("Event history cleared")


# Bus d'événements global
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """
    Obtient le bus d'événements global
    
    Returns:
        EventBus: Instance du bus d'événements
    """
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        _setup_default_events(_event_bus)
    return _event_bus


def _setup_default_events(bus: EventBus) -> None:
    """
    Configure les événements par défaut du système
    
    Args:
        bus: Bus d'événements à configurer
    """
    # Logger global pour tous les événements critiques
    def log_critical_events(event: Event):
        if event.priority == EventPriority.CRITICAL:
            logger.critical(
                f"Critical event: {event.type}",
                extra={
                    'event_data': event.data,
                    'source': event.source,
                    'correlation_id': event.correlation_id
                }
            )
    
    bus.subscribe_global(
        log_critical_events,
        priority=EventPriority.CRITICAL,
        filter_func=lambda e: e.priority == EventPriority.CRITICAL
    )
    
    logger.info("Default event handlers configured")


def reset_event_bus() -> None:
    """Reset le bus d'événements (pour les tests)"""
    global _event_bus
    if _event_bus:
        _event_bus.clear_history()
    _event_bus = None


# Types d'événements standard du système
class EventTypes:
    """Types d'événements prédéfinis du système"""
    
    # Événements Twitter
    TWEET_POSTED = "tweet.posted"
    TWEET_FAILED = "tweet.failed" 
    REPLY_RECEIVED = "reply.received"
    REPLY_LIKED = "reply.liked"
    METRICS_COLLECTED = "metrics.collected"
    
    # Événements système
    BOT_STARTED = "bot.started"
    BOT_STOPPED = "bot.stopped"
    MODULE_INITIALIZED = "module.initialized"
    MODULE_FAILED = "module.failed"
    
    # Événements configuration
    CONFIG_UPDATED = "config.updated"
    CONFIG_RELOADED = "config.reloaded"
    
    # Événements erreur
    API_ERROR = "api.error"
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"
    
    # Événements monitoring
    HEALTH_CHECK = "health.check"
    ALERT_TRIGGERED = "alert.triggered" 