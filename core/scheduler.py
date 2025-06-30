"""
Scheduler Manager pour Bot Twitter Automatisé

Gère l'automatisation de toutes les tâches :
- Publication automatique selon fréquence configurée
- Collecte de statistiques périodique
- Nettoyage des données anciennes
- Respect des quotas et plages horaires

NOUVELLE ARCHITECTURE:
- Error Recovery pour tâches automatisées
- Event Bus pour notifications d'état  
- Intégration DI Container
- Messages utilisateur informatifs
"""

import os
from datetime import datetime, time
from typing import Dict, List, Optional, Any
import pytz

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity
from storage import Tweet


class TaskScheduler:
    """
    Gestionnaire de tâches automatisées avec nouvelle architecture
    
    Features:
    - Scheduling intelligent basé sur configuration
    - Respect des quotas et rate limits
    - Plages horaires personnalisables
    - Retry automatique en cas d'échec
    - Monitoring des tâches
    - Error Recovery pour tâches automatisées
    - Event Bus pour notifications d'état
    """
    
    def __init__(self, config_manager=None, twitter_manager=None, content_generator=None, 
                 storage_manager=None, stats_collector=None, reply_handler=None):
        # Configuration via DI container ou fallback
        if any(x is None for x in [config_manager, twitter_manager, content_generator, 
                                   storage_manager, stats_collector, reply_handler]):
            try:
                from container import get_container
                container = get_container()
                self.config_manager = config_manager or container.get('config')
                self.twitter_manager = twitter_manager or container.get('twitter')
                self.content_generator = content_generator or container.get('content')
                self.storage_manager = storage_manager or container.get('storage')
                
                # Modules nouvellement migrés vers DI Container
                self.stats_collector = stats_collector or container.get('stats')
                self.reply_handler = reply_handler or container.get('reply_handler')
                        
            except ImportError:
                logger.warning("⚠️ DI Container not available, using direct access")
                # Fallbacks directs
                from config import create_config_manager
                from twitter_api import create_twitter_manager  
                from generator import create_content_generator
                from storage import create_storage_manager
                from stats import get_stats_collector
                from reply_handler import get_reply_handler
                
                self.config_manager = config_manager or create_config_manager()
                self.storage_manager = storage_manager or create_storage_manager(self.config_manager)
                self.twitter_manager = twitter_manager or create_twitter_manager(self.config_manager, self.storage_manager)
                self.content_generator = content_generator or create_content_generator(self.config_manager, self.twitter_manager, self.storage_manager, None)
                self.stats_collector = stats_collector or get_stats_collector()
                self.reply_handler = reply_handler or get_reply_handler()
        else:
            self.config_manager = config_manager
            self.twitter_manager = twitter_manager
            self.content_generator = content_generator
            self.storage_manager = storage_manager
            self.stats_collector = stats_collector
            self.reply_handler = reply_handler
            
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        self.scheduler = BackgroundScheduler()
        self._job_stats = {'successful': 0, 'failed': 0, 'skipped': 0}
        self._is_running = False
        
        # Setup jobs with error recovery
        self._initialize_with_recovery()
    
    @safe_execute(
        user_message_key="scheduler_error",
        severity=ErrorSeverity.HIGH,
        module="TaskScheduler"
    )
    def _initialize_with_recovery(self) -> None:
        """Initialize scheduler with comprehensive error recovery"""
        try:
            self._setup_jobs()
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.MODULE_INITIALIZED,
                data={
                    'module': 'task_scheduler',
                    'status': 'configured',
                    'jobs_count': len(self.scheduler.get_jobs())
                },
                source='TaskScheduler'
            )
            
        except Exception as e:
            logger.error(f"❌ Scheduler initialization failed: {e}")
            
            # Publier événement d'échec
            self.event_bus.publish(
                EventTypes.MODULE_FAILED,
                data={
                    'module': 'task_scheduler',
                    'error': str(e),
                    'fallback_mode': 'manual_only'
                },
                source='TaskScheduler',
                priority=EventPriority.HIGH
            )
            
            raise e  # Laisse l'error recovery gérer
    
    @safe_execute(
        user_message_key="scheduler_error",
        severity=ErrorSeverity.MEDIUM,
        module="TaskScheduler"
    )
    def _setup_jobs(self) -> None:
        """Configure tous les jobs schedulés avec error recovery"""
        try:
            config = self.config_manager.get_config()
            
            # Job principal : génération et publication de tweets
            if config.posting.enabled:
                self._setup_posting_job()
            
            # Job de collecte de statistiques
            if config.monitoring.collect_stats:
                self._setup_stats_collection_job()
            
            # Job de rapport quotidien
            if config.monitoring.daily_report:
                self._setup_daily_report_job()
            
            # Job de nettoyage périodique
            self._setup_cleanup_job()
            
            # Job de vérification des réponses (remplace real-time subscriptions)
            if config.engagement.auto_like_replies or config.engagement.auto_reply_enabled:
                self._setup_reply_check_job()
            
            logger.info("✅ All scheduled jobs configured successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup jobs: {e}")
            raise e  # Laisse l'error recovery gérer
    
    def _setup_posting_job(self) -> None:
        """Configure le job de publication de tweets"""
        try:
            config = self.config_manager.get_config()
            
            # Calculer l'intervalle entre posts
            frequency_per_day = config.posting.frequency_per_day
            time_range_start = config.posting.time_range['start']
            time_range_end = config.posting.time_range['end']
            timezone = pytz.timezone(config.posting.timezone)
            
            # Convertir les heures en objets time
            start_time = datetime.strptime(time_range_start, '%H:%M').time()
            end_time = datetime.strptime(time_range_end, '%H:%M').time()
            
            # Calculer les heures de publication dans la plage
            active_hours = self._calculate_active_hours(start_time, end_time)
            interval_hours = active_hours / frequency_per_day
            
            # Créer le trigger avec intervalle calculé
            trigger = IntervalTrigger(
                hours=interval_hours,
                timezone=timezone,
                start_date=datetime.now(timezone).replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=0,
                    microsecond=0
                )
            )
            
            # Ajouter le job
            self.scheduler.add_job(
                func=self._generate_and_post_job,
                trigger=trigger,
                id='generate_and_post',
                name='Generate and Post Tweet',
                max_instances=1,
                replace_existing=True
            )
            
            logger.info(f"Posting job scheduled: {frequency_per_day} times/day, every {interval_hours:.1f}h")
            
        except Exception as e:
            logger.error(f"Failed to setup posting job: {e}")
            raise
    
    def _calculate_active_hours(self, start_time: time, end_time: time) -> float:
        """Calcule le nombre d'heures actives dans la plage"""
        start_minutes = start_time.hour * 60 + start_time.minute
        end_minutes = end_time.hour * 60 + end_time.minute
        
        if end_minutes <= start_minutes:
            # Plage qui traverse minuit
            active_minutes = (24 * 60 - start_minutes) + end_minutes
        else:
            active_minutes = end_minutes - start_minutes
        
        return active_minutes / 60.0
    
    def _setup_stats_collection_job(self) -> None:
        """Configure le job de collecte de statistiques"""
        try:
            config = self.config_manager.get_config()
            frequency_hours = config.monitoring.stats_frequency_hours
            
            trigger = IntervalTrigger(hours=frequency_hours)
            
            self.scheduler.add_job(
                func=self._collect_stats_job,
                trigger=trigger,
                id='collect_stats',
                name='Collect Tweet Statistics',
                max_instances=1,
                replace_existing=True
            )
            
            logger.info(f"Stats collection job scheduled every {frequency_hours} hours")
            
        except Exception as e:
            logger.error(f"Failed to setup stats collection job: {e}")
    
    def _setup_daily_report_job(self) -> None:
        """Configure le job de rapport quotidien"""
        try:
            config = self.config_manager.get_config()
            report_time = config.monitoring.report_time
            timezone = pytz.timezone(config.posting.timezone)
            
            # Parser l'heure du rapport
            hour, minute = map(int, report_time.split(':'))
            
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=timezone
            )
            
            self.scheduler.add_job(
                func=self._daily_report_job,
                trigger=trigger,
                id='daily_report',
                name='Generate Daily Report',
                max_instances=1,
                replace_existing=True
            )
            
            logger.info(f"Daily report job scheduled at {report_time}")
            
        except Exception as e:
            logger.error(f"Failed to setup daily report job: {e}")
    
    def _setup_cleanup_job(self) -> None:
        """Configure le job de nettoyage périodique"""
        try:
            config = self.config_manager.get_config()
            cleanup_frequency = config.storage.cleanup_frequency_days
            
            # Exécuter le nettoyage tous les N jours à 2h du matin
            trigger = CronTrigger(
                hour=2,
                minute=0,
                day=f'*/{cleanup_frequency}'
            )
            
            self.scheduler.add_job(
                func=self._cleanup_job,
                trigger=trigger,
                id='cleanup',
                name='Cleanup Old Data',
                max_instances=1,
                replace_existing=True
            )
            
            logger.info(f"Cleanup job scheduled every {cleanup_frequency} days")
            
        except Exception as e:
            logger.error(f"Failed to setup cleanup job: {e}")
    
    def _setup_reply_check_job(self) -> None:
        """Configure le job de vérification des réponses (polling)"""
        try:
            config = self.config_manager.get_config()
            interval_minutes = config.engagement.reply_check_interval_minutes
            
            trigger = IntervalTrigger(minutes=interval_minutes)
            
            self.scheduler.add_job(
                func=self._check_replies_job,
                trigger=trigger,
                id='check_replies',
                name='Check and Handle Replies',
                max_instances=1,
                replace_existing=True
            )
            
            logger.info(f"Reply check job scheduled every {interval_minutes} minutes")
            
        except Exception as e:
            logger.error(f"Failed to setup reply check job: {e}")
    
    @safe_execute(
        user_message_key="posting_error",
        severity=ErrorSeverity.HIGH,
        fallback_category="content_generation",
        module="TaskScheduler"
    )
    def _generate_and_post_job(self) -> None:
        """Job principal : génère et poste un tweet avec error recovery"""
        try:
            logger.info("🚀 Starting generate and post job")
            
            # Publier événement de début
            self.event_bus.publish(
                EventTypes.TWEET_GENERATION_STARTED,
                data={'timestamp': datetime.utcnow().isoformat()},
                source='TaskScheduler'
            )
            
            # Vérifier si on est dans la plage horaire
            if not self._is_in_posting_hours():
                logger.info("⏰ Outside posting hours, skipping")
                self._job_stats['skipped'] += 1
                
                # Publier événement de skip
                self.event_bus.publish(
                    EventTypes.TWEET_GENERATION_FAILED,
                    data={
                        'reason': 'outside_posting_hours',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    source='TaskScheduler'
                )
                return
            
            # Vérifier les quotas
            quota_status = self.twitter_manager.get_quota_status()
            if not self._check_posting_quota(quota_status):
                logger.warning("⚠️ Posting quota exceeded, skipping")
                self._job_stats['skipped'] += 1
                
                # Publier événement de quota
                self.event_bus.publish(
                    EventTypes.API_ERROR,
                    data={
                        'error_type': 'quota_exceeded',
                        'quota_status': quota_status,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    source='TaskScheduler',
                    priority=EventPriority.HIGH
                )
                return
            
            # Générer le contenu
            tweet_content, image_url = self.content_generator.generate_complete_post()
            
            if not tweet_content:
                logger.error("❌ Failed to generate tweet content")
                self._job_stats['failed'] += 1
                
                # Publier événement d'échec de génération
                self.event_bus.publish(
                    EventTypes.TWEET_GENERATION_FAILED,
                    data={
                        'reason': 'content_generation_failed',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    source='TaskScheduler',
                    priority=EventPriority.HIGH
                )
                return
            
            # Poster le tweet
            tweet_id = self.twitter_manager.post_tweet(
                text=tweet_content,
                image_url=image_url
            )
            
            if tweet_id:
                # Sauvegarder en base
                tweet = Tweet(
                    tweet_id=tweet_id,
                    content=tweet_content,
                    image_url=image_url
                )
                
                saved_id = self.storage_manager.save_tweet(tweet)
                
                if saved_id:
                    logger.info(f"✅ Tweet posted and saved successfully: {tweet_id}")
                    self._job_stats['successful'] += 1
                    
                    # Publier événement de succès
                    self.event_bus.publish(
                        EventTypes.TWEET_POSTED,
                        data={
                            'tweet_id': tweet_id,
                            'content': tweet_content[:100] + '...' if len(tweet_content) > 100 else tweet_content,
                            'has_image': image_url is not None,
                            'storage_id': saved_id,
                            'timestamp': datetime.utcnow().isoformat()
                        },
                        source='TaskScheduler'
                    )
                else:
                    logger.warning(f"⚠️ Tweet posted but failed to save to database: {tweet_id}")
                    self._job_stats['successful'] += 1  # Tweet still posted successfully
            else:
                logger.error("❌ Failed to post tweet")
                self._job_stats['failed'] += 1
                
                # Publier événement d'échec de posting
                self.event_bus.publish(
                    EventTypes.TWEET_GENERATION_FAILED,
                    data={
                        'reason': 'posting_failed',
                        'content': tweet_content[:100] + '...' if len(tweet_content) > 100 else tweet_content,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    source='TaskScheduler',
                    priority=EventPriority.HIGH
                )
                
        except Exception as e:
            logger.error(f"❌ Error in generate and post job: {e}")
            self._job_stats['failed'] += 1
            
            # Publier événement d'erreur critique
            self.event_bus.publish(
                EventTypes.API_ERROR,
                data={
                    'error_type': 'scheduler_job_failed',
                    'job_name': 'generate_and_post',
                    'error_message': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                source='TaskScheduler',
                priority=EventPriority.CRITICAL
            )
            
            raise e  # Laisse l'error recovery gérer
    
    def _is_in_posting_hours(self) -> bool:
        """Vérifie si on est dans les heures de publication"""
        try:
            config = self.config_manager.get_config()
            timezone = pytz.timezone(config.posting.timezone)
            now = datetime.now(timezone).time()
            
            start_time = datetime.strptime(config.posting.time_range['start'], '%H:%M').time()
            end_time = datetime.strptime(config.posting.time_range['end'], '%H:%M').time()
            
            if start_time <= end_time:
                # Plage normale (ex: 9h-21h)
                return start_time <= now <= end_time
            else:
                # Plage qui traverse minuit (ex: 22h-6h)
                return now >= start_time or now <= end_time
                
        except Exception as e:
            logger.error(f"Error checking posting hours: {e}")
            return False
    
    def _check_posting_quota(self, quota_status: Dict[str, Any]) -> bool:
        """Vérifie si les quotas permettent de poster"""
        try:
            daily_usage = quota_status['daily_usage']
            daily_limits = quota_status['daily_limits']
            
            posts_used = daily_usage.get('posts', 0)
            posts_limit = daily_limits.get('posts')
            
            if isinstance(posts_limit, int) and posts_used >= posts_limit:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking posting quota: {e}")
            return False
    
    def _collect_stats_job(self) -> None:
        """Job de collecte de statistiques"""
        try:
            logger.info("Starting stats collection job")
            
            # Obtenir les tweets récents (dernières 24h)
            recent_tweets = self.storage_manager.get_tweets(limit=20)
            
            collected_count = 0
            for tweet in recent_tweets:
                # Collecter les métriques pour chaque tweet
                stats = self.twitter_manager.get_tweet_metrics(tweet.tweet_id)
                
                if stats:
                    saved_id = self.storage_manager.save_stats(stats)
                    if saved_id:
                        collected_count += 1
            
            logger.info(f"Stats collection completed: {collected_count} tweets processed")
            
        except Exception as e:
            logger.error(f"Error in stats collection job: {e}")
    
    def _daily_report_job(self) -> None:
        """Job de génération du rapport quotidien"""
        try:
            logger.info("Starting daily report job")
            
            # Générer le rapport
            report = self.stats_collector.generate_daily_report()
            
            if report:
                logger.info("Daily report generated successfully")
                # Le rapport est automatiquement sauvegardé par stats_collector
            else:
                logger.error("Failed to generate daily report")
                
        except Exception as e:
            logger.error(f"Error in daily report job: {e}")
    
    def _cleanup_job(self) -> None:
        """Job de nettoyage des données anciennes"""
        try:
            logger.info("Starting cleanup job")
            
            # Nettoyer les données anciennes
            self.storage_manager.cleanup_old_data()
            
            logger.info("Cleanup job completed successfully")
            
        except Exception as e:
            logger.error(f"Error in cleanup job: {e}")
    
    def _check_replies_job(self) -> None:
        """Job de vérification et traitement des réponses"""
        try:
            # Log de début seulement si activité détectée ou erreur
            config = self.config_manager.get_config()
            
            # Vérifier si restriction d'heures activée
            if not config.engagement.reply_check_24h and not self._is_in_posting_hours():
                # Log silencieux pour éviter le spam
                self._job_stats['skipped'] += 1
                return
            
            # Exécuter la vérification des réponses
            stats = self.reply_handler.check_and_handle_replies()
            
            # Log seulement si erreur ou nouvelles activités
            if 'error' in stats:
                logger.error(f"Reply check failed: {stats['error']}")
                self._job_stats['failed'] += 1
            else:
                self._job_stats['successful'] += 1
                
                # Log seulement si activités trouvées
                if stats.get('new_replies', 0) > 0 or stats.get('likes_sent', 0) > 0 or stats.get('replies_sent', 0) > 0:
                    logger.info(
                        f"✅ Reply activity: {stats['new_replies']} new replies, "
                        f"{stats.get('likes_sent', 0)} likes, "
                        f"{stats.get('replies_sent', 0)} replies sent"
                    )
                # Log silencieux quand pas d'activité (max 1 fois par heure)
                elif self._job_stats['successful'] % 60 == 0:
                    logger.debug(f"🔍 Reply check: {stats['checked_tweets']} tweets, no new activity")
            
        except Exception as e:
            logger.error(f"Reply check job failed: {e}")
            self._job_stats['failed'] += 1
    
    def start(self) -> None:
        """Démarre le scheduler"""
        try:
            if not self._is_running:
                self.scheduler.start()
                self._is_running = True
                logger.info("Task scheduler started successfully")
                
                # Log des jobs actifs
                jobs = self.scheduler.get_jobs()
                for job in jobs:
                    logger.info(f"Active job: {job.name} (ID: {job.id}) - Next run: {job.next_run_time}")
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self) -> None:
        """Arrête le scheduler"""
        try:
            if self._is_running:
                self.scheduler.shutdown(wait=True)
                self._is_running = False
                logger.info("Task scheduler stopped successfully")
            else:
                logger.warning("Scheduler is not running")
                
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def pause_job(self, job_id: str) -> bool:
        """Met en pause un job spécifique"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Job {job_id} paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Reprend un job en pause"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Job {job_id} resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job {job_id}: {e}")
            return False
    
    def run_job_now(self, job_id: str) -> bool:
        """Exécute immédiatement un job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"Job {job_id} executed manually")
                return True
            else:
                logger.error(f"Job {job_id} not found")
                return False
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            return False
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Retourne le statut du scheduler"""
        jobs_info = []
        
        if self._is_running:
            for job in self.scheduler.get_jobs():
                jobs_info.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
        
        return {
            'running': self._is_running,
            'job_stats': self._job_stats,
            'active_jobs': jobs_info,
            'total_jobs': len(jobs_info)
        }
    
    def reload_config(self) -> None:
        """Recharge la configuration et reconfigure les jobs"""
        try:
            logger.info("Reloading scheduler configuration")
            
            # Recharger la configuration
            self.config_manager.reload_config()
            
            # Supprimer tous les jobs existants
            self.scheduler.remove_all_jobs()
            
            # Reconfigurer les jobs
            self._setup_jobs()
            
            logger.info("Scheduler configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to reload scheduler configuration: {e}")


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION
# =============================================================================

def create_task_scheduler(config_manager=None, twitter_manager=None, content_generator=None, 
                         storage_manager=None, stats_collector=None, reply_handler=None) -> TaskScheduler:
    """
    Factory function pour DI Container
    
    Crée une instance TaskScheduler avec injection de dépendances.
    Utilisé par le DI container au lieu des singletons.
    """
    return TaskScheduler(config_manager, twitter_manager, content_generator, 
                        storage_manager, stats_collector, reply_handler)


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_task_scheduler() -> TaskScheduler:
    """
    DEPRECATED: Utiliser container.get('scheduler') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_task_scheduler() is deprecated. Use container.get('scheduler') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('scheduler')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_task_scheduler()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - Scheduling adaptatif basé sur engagement historique
# - Jobs conditionnels basés sur métriques externes
# - Integration avec calendar APIs pour éviter posting pendant events
# - Load balancing pour multi-instances
# - Scheduling basé sur analytics prédictives
# - Jobs de backup automatique vers stockage externe
# - Monitoring avancé avec alertes Slack/Discord
# - Support pour time zones multiples selon audience
# - Event-driven job execution based on social media trends
# - AI-powered optimal timing prediction
# - Auto-scaling based on engagement patterns
# - Distributed scheduling for high-volume operations 