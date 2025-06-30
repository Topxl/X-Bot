#!/usr/bin/env python3
"""
Reply Handler pour Bot Twitter Automatisé

Gère la détection et la réponse automatique aux replies via polling.
Compatible avec l'API Basic X/Twitter.

NOUVELLE ARCHITECTURE:
- Error Recovery pour gestion des réponses
- Event Bus pour notifications en temps réel
- Intégration DI Container
- Messages utilisateur informatifs
"""

import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity
from storage import Reply


class ReplyHandler:
    """
    Gestionnaire de réponses automatiques avec nouvelle architecture
    
    Features:
    - Polling des replies toutes les X minutes
    - Auto-like des nouvelles réponses
    - Auto-réponse optionnelle avec GPT
    - Cache anti-doublons
    - Startup catch-up pour récupérer les réponses manquées
    - Error Recovery pour gestion robuste
    - Event Bus pour notifications temps réel
    """
    
    def __init__(self, twitter_manager=None, storage_manager=None, config_manager=None, 
                 content_generator=None, prompt_manager=None, llm_manager=None):
        # Configuration via DI container ou fallback
        if any(x is None for x in [twitter_manager, storage_manager, config_manager, 
                                   content_generator, prompt_manager, llm_manager]):
            try:
                from container import get_container
                container = get_container()
                self.twitter_manager = twitter_manager or container.get('twitter')
                self.storage_manager = storage_manager or container.get('storage')
                self.config_manager = config_manager or container.get('config')
                self.content_generator = content_generator or container.get('content')
                
                # Modules nouvellement migrés vers DI Container
                self.prompt_manager = prompt_manager or container.get('prompts')
                self.llm_manager = llm_manager or container.get('llm_manager')
                        
            except ImportError:
                logger.warning("⚠️ DI Container not available, using direct access")
                # Fallbacks directs
                from twitter_api import create_twitter_manager
                from storage import create_storage_manager
                from config import create_config_manager
                from generator import create_content_generator
                from prompt_manager import get_prompt_manager
                from llm_providers import get_llm_manager
                
                self.config_manager = config_manager or create_config_manager()
                self.storage_manager = storage_manager or create_storage_manager(self.config_manager)
                self.twitter_manager = twitter_manager or create_twitter_manager(self.config_manager, self.storage_manager)
                self.content_generator = content_generator or create_content_generator(self.config_manager, self.twitter_manager, self.storage_manager, None)
                self.prompt_manager = prompt_manager or get_prompt_manager()
                self.llm_manager = llm_manager or get_llm_manager()
        else:
            self.twitter_manager = twitter_manager
            self.storage_manager = storage_manager
            self.config_manager = config_manager
            self.content_generator = content_generator
            self.prompt_manager = prompt_manager
            self.llm_manager = llm_manager
            
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        self._last_check = datetime.utcnow() - timedelta(hours=1)
        self._processed_replies = set()  # Cache pour éviter les doublons
        self._startup_check_done = False  # Flag pour le check initial
        self._conversation_replies = {}  # Compteur de réponses par conversation
        
        # Publier événement d'initialisation
        self.event_bus.publish(
            EventTypes.MODULE_INITIALIZED,
            data={'module': 'reply_handler', 'status': 'initialized'},
            source='ReplyHandler'
        )
        
    @safe_execute(
        user_message_key="reply_handling_error",
        severity=ErrorSeverity.MEDIUM,
        module="ReplyHandler"
    )
    def check_and_handle_replies(self) -> Dict[str, int]:
        """
        Vérifie et traite les nouvelles réponses avec error recovery
        
        Returns:
            Dict avec statistiques de traitement
        """
        try:
            stats = {
                'checked_tweets': 0,
                'new_replies': 0,
                'likes_sent': 0,
                'replies_sent': 0,
                'errors': 0,
                'startup_check': False
            }
            
            config = self.config_manager.get_config()
            
            # Au premier appel après redémarrage, vérifier plus loin dans le passé
            if not self._startup_check_done:
                logger.info("🚀 Startup reply check - scanning older tweets...")
                our_tweets = self.storage_manager.get_recent_tweets(hours=168)  # 7 jours
                stats['startup_check'] = True
                self._startup_check_done = True
            else:
                # Vérifications normales (dernières 24h)
                our_tweets = self.storage_manager.get_recent_tweets(hours=24)
            
            stats['checked_tweets'] = len(our_tweets)
            
            if stats['startup_check']:
                logger.info(f"🔍 STARTUP CHECK: Scanning {len(our_tweets)} tweets from last 7 days for missed replies...")
            else:
                logger.info(f"🔍 Regular check: Scanning {len(our_tweets)} tweets from last 24 hours...")
            
            for tweet in our_tweets:
                try:
                    # Chercher les réponses pour ce tweet
                    replies = self.twitter_manager.get_tweet_replies(
                        tweet.tweet_id, 
                        max_results=10
                    )
                    
                    if not replies:
                        continue
                    
                    # 🚀 OPTIMISATION: Vérifier en lot quelles réponses existent déjà
                    reply_ids = [reply.reply_id for reply in replies]
                    existing_reply_ids = set(self.storage_manager.get_existing_reply_ids(reply_ids))
                    
                    for reply in replies:
                        # Éviter les doublons (cache mémoire)
                        if reply.reply_id in self._processed_replies:
                            continue
                        
                        # 🚀 NOUVEAU: Éviter les doublons (base de données)
                        if reply.reply_id in existing_reply_ids:
                            # Ajouter au cache pour éviter les vérifications futures
                            self._processed_replies.add(reply.reply_id)
                            logger.debug(f"Reply {reply.reply_id} already exists in database, skipping")
                            continue
                            
                        # Marquer comme traité
                        self._processed_replies.add(reply.reply_id)
                        stats['new_replies'] += 1
                        
                        # Sauvegarder la réponse (maintenant avec gestion des duplicatas intégrée)
                        saved_id = self.storage_manager.save_reply(reply)
                        
                        if saved_id:
                            # Auto-like si activé
                            if config.engagement.auto_like_replies:
                                if self._auto_like_reply(reply.reply_id):
                                    stats['likes_sent'] += 1
                                    # Marquer comme liké en base
                                    self.storage_manager.mark_reply_liked(reply.reply_id)
                            
                            # Auto-réponse si activée
                            if config.engagement.auto_reply_enabled:
                                if self._auto_reply_to_comment(reply):
                                    stats['replies_sent'] += 1
                        else:
                            logger.debug(f"Reply {reply.reply_id} was not saved (likely duplicate)")
                    
                    # Petit délai pour éviter rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing replies for tweet {tweet.tweet_id}: {e}")
                    stats['errors'] += 1
            
            # Nettoyer le cache (garder seulement les 1000 derniers)
            if len(self._processed_replies) > 1000:
                self._processed_replies = set(list(self._processed_replies)[-500:])
            
            # Nettoyer le cache des conversations (garder seulement les 100 dernières)
            if len(self._conversation_replies) > 100:
                sorted_conversations = sorted(self._conversation_replies.items(), key=lambda x: x[1], reverse=True)
                self._conversation_replies = dict(sorted_conversations[:50])
            
            self._last_check = datetime.utcnow()
            
            # Log seulement si activité ou erreurs
            if stats.get('new_replies', 0) > 0 or stats.get('errors', 0) > 0:
                logger.info(f"Reply check completed: {stats}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error in reply checking: {e}")
            return {'error': str(e)}
    
    def _auto_like_reply(self, reply_id: str) -> bool:
        """
        Like automatique d'une réponse
        
        Args:
            reply_id: ID de la réponse à liker
            
        Returns:
            bool: True si succès
        """
        try:
            # 🚨 ADDITIONAL CHECK: Don't like our own tweets (double protection)
            if self.twitter_manager.bot_user_id:
                try:
                    # Get tweet to check author
                    tweet_response = self.twitter_manager.client.get_tweet(reply_id, tweet_fields=['author_id'])
                    tweet_data = tweet_response.data if hasattr(tweet_response, 'data') else tweet_response.get('data')
                    
                    if tweet_data and tweet_data.get('author_id') == self.twitter_manager.bot_user_id:
                        logger.debug(f"Skipping auto-like for bot's own tweet {reply_id}")
                        return False
                        
                except Exception as e:
                    logger.debug(f"Could not verify tweet author for {reply_id}: {e}")
            
            success = self.twitter_manager.like_tweet(reply_id)
            if success:
                logger.info(f"Auto-liked reply: {reply_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error auto-liking reply {reply_id}: {e}")
            return False
    
    def _auto_reply_to_comment(self, reply: Reply) -> bool:
        """
        Réponse automatique à un commentaire avec limite par conversation
        
        Args:
            reply: Objet Reply à traiter
            
        Returns:
            bool: True si succès
        """
        try:
            config = self.config_manager.get_config()
            
            # Vérifier la limite par conversation
            conversation_key = reply.original_tweet_id
            max_replies_per_conversation = getattr(config.engagement, 'max_replies_per_conversation', 1)
            
            current_replies = self._conversation_replies.get(conversation_key, 0)
            if current_replies >= max_replies_per_conversation:
                logger.debug(f"Conversation limit reached for tweet {conversation_key} ({current_replies}/{max_replies_per_conversation})")
                return False
            
            # Générer une réponse contextuelle
            response_content = self._generate_reply_content(reply)
            
            if not response_content:
                return False
            
            # Poster la réponse
            response_tweet_id = self.twitter_manager.post_tweet(
                text=response_content,
                reply_to=reply.reply_id
            )
            
            if response_tweet_id:
                # Incrémenter le compteur de conversation
                self._conversation_replies[conversation_key] = current_replies + 1
                logger.info(f"Auto-replied to {reply.reply_id} with {response_tweet_id} ({current_replies + 1}/{max_replies_per_conversation})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error auto-replying to {reply.reply_id}: {e}")
            return False
    
    def _generate_reply_content(self, reply: Reply) -> Optional[str]:
        """
        Génère le contenu d'une réponse automatique (LLM uniquement)
        
        Args:
            reply: Réponse originale
            
        Returns:
            str: Contenu de la réponse ou None
        """
        try:
            # Force LLM utilization - no templates
            force_llm = self.prompt_manager.get_setting("auto_reply", "force_llm")
            if not force_llm:
                logger.warning("LLM not forced - falling back to template generation")
            
            # Generate contextual response with LLM (OpenAI or LM Studio)
            contextual_response = self._generate_llm_reply(reply)
            if contextual_response:
                return contextual_response
            
            logger.warning("LLM reply generation failed - no fallback available")
            return None
            
        except Exception as e:
            logger.error(f"Error generating reply content: {e}")
            return None
    

    
    def _generate_llm_reply(self, reply: Reply) -> Optional[str]:
        """
        Génère une réponse contextuelle avec LLM (OpenAI ou LM Studio)
        
        Args:
            reply: Réponse originale
            
        Returns:
            str: Réponse générée ou None
        """
        try:
            # Obtenir les settings depuis la config centralisée
            model = self.prompt_manager.get_setting("auto_reply", "model")
            max_tokens = self.prompt_manager.get_setting("auto_reply", "max_tokens")
            temperature = self.prompt_manager.get_setting("auto_reply", "temperature")
            
            # 🔧 Récupérer le username de l'auteur du commentaire
            username = self._get_username_from_author_id(reply.author_id)
            if not username:
                logger.warning(f"Could not get username for author_id {reply.author_id}")
                username = "friend"  # Fallback
            
            # Obtenir les prompts avec username
            user_prompt = self.prompt_manager.get_user_prompt(
                "auto_reply",
                reply_content=reply.content,
                username=username
            )
            system_prompt_obj = self.prompt_manager.get_system_prompt("auto_reply")
            system_prompt = system_prompt_obj.get("content", "") if isinstance(system_prompt_obj, dict) else str(system_prompt_obj)
            
            # Utiliser le gestionnaire LLM modulaire avec fallback automatique
            response = self.llm_manager.generate_reply(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if response and len(response) <= 280:  # Vérifier limite Twitter
                return response
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating LLM reply: {e}")
            return None
    
    def _get_username_from_author_id(self, author_id: str) -> Optional[str]:
        """
        Récupère le username Twitter à partir de l'author_id
        
        Args:
            author_id: ID de l'auteur
            
        Returns:
            str: Username ou None si erreur
        """
        try:
            # Utiliser l'API Twitter pour récupérer les infos utilisateur
            user_response = self.twitter_manager.client.get_user(
                id=author_id,
                user_fields=['username']
            )
            
            # Handle both dict and object response formats
            user_data = user_response.data if hasattr(user_response, 'data') else user_response.get('data')
            
            if user_data:
                username = user_data.get('username') if isinstance(user_data, dict) else getattr(user_data, 'username', None)
                return username
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting username for {author_id}: {e}")
            return None
    
    def get_reply_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de traitement des réponses"""
        return {
            'last_check': self._last_check.isoformat(),
            'processed_count': len(self._processed_replies),
            'handler_active': True,
            'startup_check_done': self._startup_check_done
        }
    
    def force_startup_check(self) -> Dict[str, int]:
        """
        Force un nouveau startup check (scan 7 jours)
        
        Returns:
            Dict avec statistiques de traitement
        """
        logger.info("🔄 Forcing startup check for older tweets...")
        self._startup_check_done = False
        return self.check_and_handle_replies()
    
    def reset_processed_cache(self) -> None:
        """Vide le cache des réponses traitées (pour retraiter tout)"""
        old_count = len(self._processed_replies)
        self._processed_replies.clear()
        logger.info(f"🧹 Cleared processed replies cache ({old_count} entries)")
    
    def manual_deep_scan(self, days: int = 30) -> Dict[str, int]:
        """
        Scan manuel sur X jours (ignorer le cache)
        
        Args:
            days: Nombre de jours à scanner
            
        Returns:
            Dict avec statistiques
        """
        try:
            logger.info(f"🔍 MANUAL DEEP SCAN: Checking last {days} days...")
            
            stats = {
                'checked_tweets': 0,
                'new_replies': 0,
                'likes_sent': 0,
                'replies_sent': 0,
                'errors': 0,
                'deep_scan': True,
                'scan_days': days
            }
            
            config = self.config_manager.get_config()
            
            # Obtenir tweets sur période demandée
            our_tweets = self.storage_manager.get_recent_tweets(hours=days * 24)
            stats['checked_tweets'] = len(our_tweets)
            
            logger.info(f"🔍 DEEP SCAN: Found {len(our_tweets)} tweets from last {days} days")
            
            # Sauvegarder le cache actuel
            original_cache = self._processed_replies.copy()
            
            # Vider temporairement le cache pour retraiter
            self._processed_replies.clear()
            
            for tweet in our_tweets:
                try:
                    # Chercher les réponses pour ce tweet
                    replies = self.twitter_manager.get_tweet_replies(
                        tweet.tweet_id, 
                        max_results=10
                    )
                    
                    for reply in replies:
                        # Vérifier si déjà dans le cache original
                        if reply.reply_id in original_cache:
                            continue
                            
                        stats['new_replies'] += 1
                        
                        # Sauvegarder la réponse
                        self.storage_manager.save_reply(reply)
                        
                        # Auto-like si activé
                        if config.engagement.auto_like_replies:
                            if self._auto_like_reply(reply.reply_id):
                                stats['likes_sent'] += 1
                                self.storage_manager.mark_reply_liked(reply.reply_id)
                        
                        # Auto-réponse si activée
                        if config.engagement.auto_reply_enabled:
                            if self._auto_reply_to_comment(reply):
                                stats['replies_sent'] += 1
                    
                    # Petit délai pour éviter rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error processing replies for tweet {tweet.tweet_id}: {e}")
                    stats['errors'] += 1
            
            # Restaurer le cache + nouvelles entrées
            self._processed_replies = original_cache
            
            logger.info(f"🎯 DEEP SCAN completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in manual deep scan: {e}")
            return {'error': str(e)}


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION
# =============================================================================

def create_reply_handler(twitter_manager=None, storage_manager=None, config_manager=None, 
                        content_generator=None, prompt_manager=None, llm_manager=None) -> ReplyHandler:
    """
    Factory function pour DI Container
    
    Crée une instance ReplyHandler avec injection de dépendances.
    Utilisé par le DI container au lieu des singletons.
    """
    return ReplyHandler(twitter_manager, storage_manager, config_manager, 
                       content_generator, prompt_manager, llm_manager)


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_reply_handler() -> ReplyHandler:
    """
    DEPRECATED: Utiliser container.get('reply_handler') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_reply_handler() is deprecated. Use container.get('reply_handler') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('reply_handler')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_reply_handler()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - AI-powered sentiment analysis for reply prioritization
# - Multi-language reply generation
# - Context-aware conversation memory
# - Real-time engagement prediction
# - Auto-escalation for critical mentions
# - Advanced conversation threading
# - Reply quality scoring and optimization
# - Event-driven reply triggers based on keywords 