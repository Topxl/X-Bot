"""
Bot Twitter Automatisé - Main avec Nouvelle Architecture

Utilise la nouvelle architecture avec :
- Dependency Injection Container 
- Event Bus pour découplage
- Error Recovery Manager
- Messages utilisateur informatifs
"""

import os
import sys
import signal
import time
from datetime import datetime
from typing import Optional

from loguru import logger

# Nouvelle architecture
from container import get_container, reset_container
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity


class TwitterBot:
    """
    Bot Twitter principal avec nouvelle architecture
    
    Utilise dependency injection et event bus pour un
    système plus modulaire et maintenable.
    """
    
    def __init__(self):
        self.container = get_container()
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        self._is_running = False
        self._shutdown_requested = False
        
        # Setup signal handlers pour arrêt propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire de signaux pour arrêt propre"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self._shutdown_requested = True
    
    def _setup_event_handlers(self):
        """Configure les handlers d'événements"""
        
        # Handler pour tweets postés
        def on_tweet_posted(event):
            logger.success(f"✅ Tweet publié avec succès: {event.data.get('tweet_id', 'unknown')}")
            # Auto-notification pour engagement
            self.event_bus.publish(
                EventTypes.METRICS_COLLECTED,
                data={'tweet_id': event.data.get('tweet_id')},
                source='twitter_bot'
            )
        
        # Handler pour erreurs critiques
        def on_critical_error(event):
            logger.critical(f"🚨 Erreur critique détectée: {event.data}")
            # Ici on pourrait envoyer des notifications externes
        
        # Handler pour monitoring
        def on_health_check(event):
            health_status = self._check_services_health()
            logger.info(f"💊 Health check: {health_status}")
        
        # Enregistrer les handlers
        self.event_bus.subscribe(EventTypes.TWEET_POSTED, on_tweet_posted)
        self.event_bus.subscribe(EventTypes.ALERT_TRIGGERED, on_critical_error)
        self.event_bus.subscribe(EventTypes.HEALTH_CHECK, on_health_check)
        
        logger.info("Event handlers configured")
    
    @safe_execute(
        user_message_key="general_error",
        severity=ErrorSeverity.HIGH,
        module="TwitterBot"
    )
    def initialize(self) -> bool:
        """
        Initialise tous les modules du bot avec la nouvelle architecture
        
        Returns:
            bool: True si l'initialisation réussit, False sinon
        """
        logger.info("🚀 Initializing Twitter Bot with new architecture...")
        
        # Setup logging
        self._setup_logging()
        
        # Les services sont créés automatiquement par le container DI
        logger.info("📝 Loading services via DI container...")
        
        # Publier événement d'initialisation
        self.event_bus.publish(
            EventTypes.MODULE_INITIALIZED,
            data={'module': 'TwitterBot'},
            source='main'
        )
        
        # Afficher la configuration
        self._log_configuration_summary()
        
        logger.info("✅ Twitter Bot initialized successfully with new architecture!")
        return True
    
    @safe_execute(
        user_message_key="config_error",
        severity=ErrorSeverity.MEDIUM,
        fallback_category="content_generation",
        module="TwitterBot"
    )
    def _setup_logging(self):
        """Configure le système de logging avec error recovery"""
        try:
            config_manager = self.container.get('config')
            config = config_manager.get_config()
            log_config = config.logging
            
            # Configuration de loguru
            logger.remove()
            
            # Format des logs
            if log_config.format == "json":
                log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message} | {extra}"
            elif log_config.format == "minimal":
                log_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <5}</level> | <level>{message}</level>"
            else:
                log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
            
            # Handler console
            logger.add(
                sys.stdout,
                format=log_format,
                level=log_config.level,
                colorize=True if log_config.format != "json" else False
            )
            
            # Handler fichier avec rotation
            logger.add(
                "logs/bot_{time:YYYY-MM-DD}.log",
                format=log_format,
                level=log_config.level,
                rotation=log_config.file_rotation,
                retention="30 days",
                compression="zip",
                encoding="utf-8"
            )
            
            # Réduire verbosité des librairies externes
            import logging
            logging.getLogger("tweepy").setLevel(logging.WARNING)
            logging.getLogger("apscheduler").setLevel(logging.WARNING)  
            logging.getLogger("httpcore").setLevel(logging.WARNING)
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
            
            logger.info("✅ Logging configured with optimization and error recovery")
            
        except Exception as e:
            # Fallback configuration sera gérée par @safe_execute
            logger.add(sys.stdout, level="INFO")
            raise e
    
    def _log_configuration_summary(self):
        """Affiche un résumé de la configuration avec error handling"""
        try:
            config_manager = self.container.get('config')
            config = config_manager.get_config()
            quotas = config_manager.get_current_quotas()
            
            logger.info("📊 Configuration Summary:")
            logger.info(f"   • X API Plan: {config.x_api.plan}")
            logger.info(f"   • Daily Post Limit: {quotas.posts_per_day}")
            logger.info(f"   • Posts per Day: {config.posting.frequency_per_day}")
            logger.info(f"   • Posting Hours: {config.posting.time_range['start']} - {config.posting.time_range['end']}")
            logger.info(f"   • Auto-like Replies: {config.engagement.auto_like_replies}")
            logger.info(f"   • Images Enabled: {config.content_generation.enable_images}")
            logger.info(f"   • Stats Collection: {config.monitoring.collect_stats}")
            logger.info(f"   • Daily Reports: {config.monitoring.daily_report}")
            
            # Publier événement
            self.event_bus.publish(
                EventTypes.CONFIG_RELOADED,
                data={'config_summary': 'displayed'},
                source='main'
            )
            
        except Exception as e:
            self.error_manager.handle_error(
                error=e,
                module="TwitterBot",
                function="_log_configuration_summary",
                user_message_key="config_error",
                severity=ErrorSeverity.LOW
            )
    
    @safe_execute(
        user_message_key="general_error",
        severity=ErrorSeverity.CRITICAL,
        module="TwitterBot"
    )
    def start(self) -> None:
        """Démarre le bot avec la nouvelle architecture"""
        if self._is_running:
            logger.warning("Bot is already running")
            return
        
        logger.info("🎯 Starting Twitter Bot services with new architecture...")
        
        # Publier événement de démarrage
        self.event_bus.publish(
            EventTypes.BOT_STARTED,
            data={'timestamp': datetime.utcnow()},
            source='main'
        )
        
        # Démarrer le scheduler via DI
        try:
            scheduler = self.container.get('scheduler')
            scheduler.start()
        except Exception as e:
            self.error_manager.handle_error(
                error=e,
                module="TwitterBot",
                function="start",
                user_message_key="general_error",
                severity=ErrorSeverity.HIGH
            )
        
        self._is_running = True
        logger.info("🟢 Twitter Bot is now running with new architecture!")
        
        # 🚀 POST AUTOMATIQUE AU DÉMARRAGE avec error recovery
        logger.info("🤖 Posting startup tweet with error recovery...")
        startup_success = self.run_manual_post()
        if startup_success:
            logger.info("✅ Startup tweet posted successfully!")
        else:
            logger.warning("⚠️ Failed to post startup tweet (continuing with fallback)")
        
        # Boucle principale avec monitoring
        self._main_loop()
    
    def _main_loop(self):
        """Boucle principale avec event-driven monitoring"""
        logger.info("🔄 Entering main loop with event-driven architecture...")
        
        # Health check périodique via événements
        last_health_check = time.time()
        health_check_interval = 300  # 5 minutes
        
        try:
            while not self._shutdown_requested:
                # Health check périodique
                current_time = time.time()
                if current_time - last_health_check > health_check_interval:
                    self.event_bus.publish(
                        EventTypes.HEALTH_CHECK,
                        data={'timestamp': datetime.utcnow()},
                        source='main_loop'
                    )
                    last_health_check = current_time
                
                # Sleep court pour permettre interruption
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Keyboard interrupt received")
            self._shutdown_requested = True
        except Exception as e:
            self.error_manager.handle_error(
                error=e,
                module="TwitterBot",
                function="_main_loop",
                user_message_key="general_error",
                severity=ErrorSeverity.HIGH
            )
        finally:
            logger.info("🔴 Main loop exiting...")
    
    def _check_services_health(self) -> dict:
        """Vérifie la santé des services via DI"""
        health_status = {'overall': True, 'services': {}}
        
        # Vérifier chaque service enregistré
        for service_name, service_class in self.container.get_registered_services().items():
            try:
                service = self.container.get(service_name)
                # Ici on pourrait ajouter des méthodes health check spécifiques
                health_status['services'][service_name] = True
            except Exception as e:
                health_status['services'][service_name] = False
                health_status['overall'] = False
                logger.warning(f"⚠️ Service {service_name} health check failed: {e}")
        
        return health_status
    
    @safe_execute(
        user_message_key="general_error",
        severity=ErrorSeverity.MEDIUM,
        fallback_category="content_generation",
        module="TwitterBot"
    )
    def run_manual_post(self) -> bool:
        """Post manuel avec error recovery"""
        try:
            logger.info("📝 Generating content with error recovery...")
            
            # Utiliser les services via DI
            content_generator = self.container.get('content')
            twitter_manager = self.container.get('twitter')
            storage_manager = self.container.get('storage')
            
            # Générer contenu avec fallback automatique
            content = content_generator.generate_tweet_content()
            if not content:
                # Le fallback sera géré par @safe_execute
                raise Exception("Content generation failed")
            
            # Poster avec error recovery
            tweet_id = twitter_manager.post_tweet(content)
            if not tweet_id:
                raise Exception("Tweet posting failed")
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.TWEET_POSTED,
                data={
                    'tweet_id': tweet_id,
                    'content': content,
                    'timestamp': datetime.utcnow()
                },
                source='manual_post'
            )
            
            logger.success(f"✅ Manual tweet posted: {tweet_id}")
            return True
            
        except Exception as e:
            # L'erreur sera gérée par @safe_execute avec fallback
            logger.error(f"❌ Manual post failed: {e}")
            return False
    
    @safe_execute(
        user_message_key="general_error",
        severity=ErrorSeverity.MEDIUM,
        module="TwitterBot"
    )
    def stop(self) -> None:
        """Arrête le bot proprement"""
        if not self._is_running:
            logger.info("Bot is not running")
            return
        
        logger.info("🛑 Stopping Twitter Bot with new architecture...")
        
        # Publier événement d'arrêt
        self.event_bus.publish(
            EventTypes.BOT_STOPPED,
            data={'timestamp': datetime.utcnow()},
            source='main'
        )
        
        try:
            # Arrêter le scheduler
            scheduler = self.container.get('scheduler')
            scheduler.stop()
            
            # Fermer les connexions storage
            storage_manager = self.container.get('storage')
            storage_manager.close()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        self._is_running = False
        logger.info("✅ Twitter Bot stopped successfully with new architecture")
    
    def get_status(self) -> dict:
        """Retourne le statut du bot avec métriques"""
        try:
            return {
                'running': self._is_running,
                'container_services': len(self.container.get_registered_services()),
                'event_stats': self.event_bus.get_stats(),
                'error_stats': self.error_manager.get_error_stats(),
                'recent_events': [
                    {
                        'type': event.type,
                        'timestamp': event.timestamp.isoformat(),
                        'source': event.source
                    }
                    for event in self.event_bus.get_recent_events(5)
                ]
            }
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            return {'error': str(e)}


def main():
    """Point d'entrée principal avec nouvelle architecture"""
    print("🤖 Twitter Bot Automatisé - Nouvelle Architecture")
    print("=" * 60)
    
    # Créer et initialiser le bot
    bot = TwitterBot()
    
    if not bot.initialize():
        print("❌ Failed to initialize bot. Check logs for details.")
        sys.exit(1)
    
    try:
        # Démarrer le bot
        bot.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}")
    finally:
        bot.stop()
        print("👋 Bot stopped. Goodbye!")


if __name__ == "__main__":
    main() 