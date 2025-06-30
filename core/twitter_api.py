"""
Twitter API Manager pour Bot Twitter Automatisé

Gère toutes les interactions avec X API v2 via Tweepy :
- Authentication et rate limiting automatique
- Post tweets avec ou sans images
- Recherche de tweets viraux
- Gestion des replies et likes
- Collecte des métriques et statistiques

NOUVELLE ARCHITECTURE:
- Error Recovery avec fallbacks intelligents
- Event Bus pour notifications temps réel
- Intégration DI Container
- Messages utilisateur informatifs
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO

import tweepy
import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from PIL import Image

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity
from storage import Reply, TweetStats


class TwitterAPIManager:
    """
    Gestionnaire de l'API Twitter/X avec nouvelle architecture
    
    Features:
    - Auth automatique OAuth 1.0a + Bearer Token
    - Rate limiting respecté (wait_on_rate_limit=True)
    - Retry logic avec error recovery
    - Quota tracking selon plan
    - Image upload et media handling
    - Event Bus pour notifications temps réel
    - Messages utilisateur informatifs en cas d'erreur
    """
    
    def __init__(self, config_manager=None, storage_manager=None):
        # Configuration via DI container ou fallback
        if config_manager is None or storage_manager is None:
            try:
                from container import get_container
                container = get_container()
                self.config_manager = config_manager or container.get('config')
                self.storage_manager = storage_manager or container.get('storage')
            except (ImportError, KeyError):
                logger.warning("⚠️ DI Container not available, using direct access")
                if config_manager is None:
                    from config import create_config_manager
                    self.config_manager = create_config_manager()
                else:
                    self.config_manager = config_manager
                    
                if storage_manager is None:
                    from storage import create_storage_manager
                    self.storage_manager = create_storage_manager(self.config_manager)
                else:
                    self.storage_manager = storage_manager
        else:
            self.config_manager = config_manager
            self.storage_manager = storage_manager
            
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        self.client: Optional[tweepy.Client] = None
        self.api: Optional[tweepy.API] = None
        self.bot_user_id: Optional[str] = None  # Store bot's own user ID
        self._quota_usage = {'posts': 0, 'reads': 0, 'likes': 0}
        self._last_quota_reset = datetime.utcnow()
        
        # Initialize Twitter clients with error recovery
        self._initialize_with_recovery()
    
    @safe_execute(
        user_message_key="twitter_api_error",
        severity=ErrorSeverity.HIGH,
        module="TwitterAPIManager"
    )
    def _initialize_with_recovery(self) -> None:
        """Initialize Twitter API with comprehensive error recovery"""
        try:
            self._init_clients()
            self._setup_reply_handler()
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.MODULE_INITIALIZED,
                data={
                    'module': 'twitter_api',
                    'status': 'connected',
                    'bot_user_id': self.bot_user_id
                },
                source='TwitterAPIManager'
            )
            
        except Exception as e:
            logger.error(f"❌ Twitter API initialization failed: {e}")
            
            # Publier événement d'échec
            self.event_bus.publish(
                EventTypes.MODULE_FAILED,
                data={
                    'module': 'twitter_api',
                    'error': str(e),
                    'fallback_mode': 'disabled'
                },
                source='TwitterAPIManager',
                priority=EventPriority.CRITICAL
            )
            
            raise e  # Laisse l'error recovery gérer
    
    @safe_execute(
        user_message_key="twitter_api_error",
        severity=ErrorSeverity.CRITICAL,
        module="TwitterAPIManager"
    )
    def _init_clients(self) -> None:
        """Initialize Tweepy clients avec error recovery"""
        try:
            credentials = self.config_manager.get_x_api_credentials()
            
            # Validate credentials
            required_keys = ['api_key', 'api_secret', 'access_token', 'access_token_secret', 'bearer_token']
            missing_keys = [key for key in required_keys if not credentials.get(key)]
            
            if missing_keys:
                raise ValueError(f"Missing Twitter API credentials: {missing_keys}")
            
            # Initialize Client (v2 API) - for most operations
            self.client = tweepy.Client(
                consumer_key=credentials['api_key'],
                consumer_secret=credentials['api_secret'],
                access_token=credentials['access_token'],
                access_token_secret=credentials['access_token_secret'],
                bearer_token=credentials['bearer_token'],
                wait_on_rate_limit=True,
                return_type=dict
            )
            
            # Initialize API (v1.1) - for media upload
            auth = tweepy.OAuth1UserHandler(
                credentials['api_key'],
                credentials['api_secret'],
                credentials['access_token'],
                credentials['access_token_secret']
            )
            
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Test authentication and get bot's user ID
            me = self.client.get_me()
            
            # Handle different response formats and store bot's user ID
            if hasattr(me, 'data') and me.data:
                username = me.data.get('username', 'unknown')
                self.bot_user_id = me.data.get('id')
                logger.info(f"✅ Twitter API initialized successfully for user: @{username} (ID: {self.bot_user_id})")
            elif isinstance(me, dict) and 'data' in me:
                username = me['data'].get('username', 'unknown')
                self.bot_user_id = me['data'].get('id')
                logger.info(f"✅ Twitter API initialized successfully for user: @{username} (ID: {self.bot_user_id})")
            elif me:
                logger.info("✅ Twitter API initialized successfully")
            else:
                raise Exception("Failed to authenticate with Twitter API")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Twitter API: {e}")
            raise e  # Laisse l'error recovery gérer
    
    def _setup_reply_handler(self) -> None:
        """Setup handler for real-time reply likes"""
        def handle_new_reply(payload):
            """Handle new reply and auto-like if enabled"""
            try:
                config = self.config_manager.get_config()
                if not config.engagement.auto_like_replies:
                    return
                
                # Extract reply data
                new_reply = payload.get('new', {})
                reply_id = new_reply.get('reply_id')
                original_tweet_id = new_reply.get('original_tweet_id')
                
                if reply_id and original_tweet_id:
                    # Check if this is a reply to our tweet
                    our_tweets = self.storage_manager.get_tweets(limit=10)
                    our_tweet_ids = [tweet.tweet_id for tweet in our_tweets]
                    
                    if original_tweet_id in our_tweet_ids:
                        # Auto-like the reply
                        success = self.like_tweet(reply_id)
                        if success:
                            # Mark as liked in database
                            self.storage_manager.mark_reply_liked(reply_id)
                            logger.info(f"Auto-liked reply {reply_id} to our tweet {original_tweet_id}")
                
            except Exception as e:
                logger.error(f"Error in reply handler: {e}")
        
        # Register handler
        self.storage_manager.add_event_handler('reply_insert', handle_new_reply)
    
    def _check_quota(self, operation: str, count: int = 1) -> bool:
        """
        Check if operation is within quota limits
        
        Args:
            operation: 'posts', 'reads', or 'likes'
            count: Number of operations to check
            
        Returns:
            bool: True if within limits, False otherwise
        """
        try:
            config = self.config_manager.get_config()
            quotas = self.config_manager.get_current_quotas()
            
            # Reset daily counters if needed
            now = datetime.utcnow()
            if (now - self._last_quota_reset).days >= 1:
                self._quota_usage = {'posts': 0, 'reads': 0, 'likes': 0}
                self._last_quota_reset = now
            
            # Check daily limits
            current_usage = self._quota_usage.get(operation, 0)
            
            if operation == 'posts':
                daily_limit = quotas.posts_per_day
            elif operation == 'reads':
                daily_limit = quotas.reads_per_day
            elif operation == 'likes':
                daily_limit = config.engagement.likes_per_day
            else:
                daily_limit = float('inf')
            
            # Check if adding count would exceed limit
            if daily_limit > 0 and (current_usage + count) > daily_limit:
                logger.warning(f"Quota limit reached for {operation}: {current_usage}/{daily_limit}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking quota: {e}")
            return False
    
    def _update_quota(self, operation: str, count: int = 1) -> None:
        """Update quota usage counter"""
        self._quota_usage[operation] = self._quota_usage.get(operation, 0) + count
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    @safe_execute(
        user_message_key="twitter_posting_error",
        severity=ErrorSeverity.HIGH,
        module="TwitterAPIManager"
    )
    def post_tweet(self, text: str, image_url: Optional[str] = None, reply_to: Optional[str] = None) -> Optional[str]:
        """
        Post a tweet with optional image avec error recovery
        
        Args:
            text: Tweet text content
            image_url: Optional URL or path to image
            reply_to: Optional tweet ID to reply to
            
        Returns:
            str: Tweet ID if successful, None otherwise
        """
        try:
            # Check quota
            if not self._check_quota('posts'):
                logger.error("Post quota exceeded")
                return None
            
            media_ids = []
            
            # Handle image upload if provided
            if image_url:
                media_id = self._upload_media(image_url)
                if media_id:
                    media_ids.append(media_id)
                else:
                    logger.warning("Failed to upload image, posting without media")
            
            # Post tweet
            tweet_data = {'text': text}
            
            if media_ids:
                tweet_data['media'] = {'media_ids': media_ids}
            
            if reply_to:
                tweet_data['in_reply_to_tweet_id'] = reply_to
            
            response = self.client.create_tweet(**tweet_data)
            
            # Handle different response formats
            tweet_id = None
            if hasattr(response, 'data') and response.data:
                tweet_id = response.data.get('id')
            elif isinstance(response, dict) and 'data' in response:
                tweet_id = response['data'].get('id')
            
            if tweet_id:
                self._update_quota('posts')
                logger.info(f"Tweet posted successfully: {tweet_id}")
                return tweet_id
            
        except Exception as e:
            logger.error(f"Failed to post tweet: {e}")
            raise
        
        return None
    
    def _upload_media(self, image_source: str) -> Optional[str]:
        """
        Upload media to Twitter
        
        Args:
            image_source: URL or local path to image
            
        Returns:
            str: Media ID if successful, None otherwise
        """
        try:
            # Download image if URL
            if image_source.startswith(('http://', 'https://')):
                response = requests.get(image_source, timeout=30)
                response.raise_for_status()
                image_data = BytesIO(response.content)
            else:
                # Local file
                image_data = image_source
            
            # Upload media using API v1.1
            media = self.api.media_upload(filename="image.jpg", file=image_data)
            logger.info(f"Media uploaded successfully: {media.media_id}")
            return media.media_id_string
            
        except Exception as e:
            logger.error(f"Failed to upload media: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def like_tweet(self, tweet_id: str) -> bool:
        """
        Like a tweet
        
        Args:
            tweet_id: ID of tweet to like
            
        Returns:
            bool: Success status
        """
        try:
            # Check quota
            if not self._check_quota('likes'):
                logger.error("Like quota exceeded")
                return False
            
            # 🚨 CRITICAL FIX: Get tweet info to check if it's our own tweet
            try:
                tweet_response = self.client.get_tweet(tweet_id, tweet_fields=['author_id'])
                tweet_data = tweet_response.data if hasattr(tweet_response, 'data') else tweet_response.get('data')
                
                if tweet_data:
                    tweet_author_id = tweet_data.get('author_id')
                    # Don't like our own tweets!
                    if self.bot_user_id and tweet_author_id == self.bot_user_id:
                        logger.debug(f"Skipping like for bot's own tweet {tweet_id}")
                        return False
                        
            except Exception as e:
                logger.warning(f"Could not check tweet author for {tweet_id}: {e}")
                # If we can't check, better to skip
                return False
            
            # Get authenticated user ID
            me = self.client.get_me()
            
            # Handle different response formats
            user_id = None
            if hasattr(me, 'data') and me.data:
                user_id = me.data.get('id')
            elif isinstance(me, dict) and 'data' in me:
                user_id = me['data'].get('id')
                
            if not user_id:
                logger.error("Failed to get authenticated user ID")
                return False
            
            # Like the tweet
            response = self.client.like(tweet_id, user_auth=True)
            
            # Handle different response formats
            liked = False
            if hasattr(response, 'data') and response.data:
                liked = response.data.get('liked', False)
            elif isinstance(response, dict) and 'data' in response:
                liked = response['data'].get('liked', False)
            
            if liked:
                self._update_quota('likes')
                logger.info(f"Successfully liked tweet: {tweet_id}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to like tweet {tweet_id}: {e}")
        
        return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_tweet_replies(self, tweet_id: str, max_results: int = 10) -> List[Reply]:
        """
        Get replies to a specific tweet
        
        Args:
            tweet_id: Tweet ID to get replies for
            max_results: Maximum number of replies to fetch
            
        Returns:
            List[Reply]: List of Reply objects
        """
        try:
            # Check quota
            if not self._check_quota('reads', max_results):
                logger.error("Read quota would be exceeded")
                return []
            
            # Search for replies using conversation_id
            query = f"conversation_id:{tweet_id} -from:YOUR_USERNAME"  # Exclude our own replies
            
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max(max_results, 10), 100),
                tweet_fields=['author_id', 'created_at', 'conversation_id', 'in_reply_to_user_id']
            )
            
            replies = []
            # Handle both dict and object response formats
            tweets_data = response.data if hasattr(response, 'data') else response.get('data', [])
            if tweets_data:
                for tweet in tweets_data:
                    # Handle both dict and object tweet formats
                    tweet_id_val = tweet.get('id') if isinstance(tweet, dict) else getattr(tweet, 'id', None)
                    conversation_id = tweet.get('conversation_id') if isinstance(tweet, dict) else getattr(tweet, 'conversation_id', None)
                    author_id = tweet.get('author_id') if isinstance(tweet, dict) else getattr(tweet, 'author_id', None)
                    text = tweet.get('text') if isinstance(tweet, dict) else getattr(tweet, 'text', '')
                    created_at_str = tweet.get('created_at') if isinstance(tweet, dict) else str(getattr(tweet, 'created_at', ''))
                    
                    # Skip if not actually a reply to our tweet
                    if conversation_id != tweet_id:
                        continue
                    
                    # 🚨 CRITICAL FIX: Skip our own tweets to prevent infinite loops
                    if self.bot_user_id and author_id == self.bot_user_id:
                        logger.debug(f"Skipping bot's own tweet {tweet_id_val} to prevent reply loop")
                        continue
                    
                    # Parse created_at
                    try:
                        if 'Z' in created_at_str:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        else:
                            created_at = datetime.fromisoformat(created_at_str)
                    except:
                        created_at = datetime.utcnow()
                    
                    reply = Reply(
                        reply_id=tweet_id_val,
                        original_tweet_id=tweet_id,
                        author_id=author_id,
                        content=text,
                        created_at=created_at
                    )
                    replies.append(reply)
                
                self._update_quota('reads', len(tweets_data))
                # Log seulement si replies trouvées
                if len(replies) > 0:
                    logger.info(f"Found {len(replies)} replies for tweet {tweet_id}")
            
            return replies
            
        except Exception as e:
            logger.error(f"Failed to get replies for tweet {tweet_id}: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_tweet_metrics(self, tweet_id: str) -> Optional[TweetStats]:
        """
        Get engagement metrics for a tweet
        
        Args:
            tweet_id: Tweet ID to get metrics for
            
        Returns:
            TweetStats: Statistics object if successful, None otherwise
        """
        try:
            # Check quota
            if not self._check_quota('reads'):
                logger.error("Read quota exceeded")
                return None
            
            # Get tweet with metrics
            response = self.client.get_tweet(
                tweet_id,
                tweet_fields=['public_metrics', 'non_public_metrics'],
                user_auth=True
            )
            
            # Handle both dict and object response formats
            tweet_data = response.data if hasattr(response, 'data') else response.get('data')
            
            if tweet_data:
                # Handle both dict and object tweet formats
                if isinstance(tweet_data, dict):
                    public_metrics = tweet_data.get('public_metrics', {})
                    non_public_metrics = tweet_data.get('non_public_metrics', {})
                else:
                    public_metrics = getattr(tweet_data, 'public_metrics', {})
                    non_public_metrics = getattr(tweet_data, 'non_public_metrics', {})
                
                # Convert to dict if necessary
                if hasattr(public_metrics, '__dict__'):
                    public_metrics = public_metrics.__dict__
                if hasattr(non_public_metrics, '__dict__'):
                    non_public_metrics = non_public_metrics.__dict__
                
                stats = TweetStats(
                    tweet_id=tweet_id,
                    likes=public_metrics.get('like_count', 0),
                    retweets=public_metrics.get('retweet_count', 0),
                    replies=public_metrics.get('reply_count', 0),
                    impressions=non_public_metrics.get('impression_count', 0)
                )
                
                self._update_quota('reads')
                logger.debug(f"Retrieved metrics for tweet {tweet_id}: {stats.likes}L {stats.retweets}RT {stats.replies}R")
                return stats
            else:
                logger.warning(f"No tweet data returned for {tweet_id}")
            
        except Exception as e:
            logger.error(f"Failed to get metrics for tweet {tweet_id}: {e}")
        
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_viral_tweets(self, keywords: List[str], max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for viral tweets containing keywords
        
        Args:
            keywords: List of keywords to search for
            max_results: Maximum number of tweets to return
            
        Returns:
            List[Dict]: List of tweet data dictionaries
        """
        try:
            # Check quota
            if not self._check_quota('reads', max_results):
                logger.error("Read quota would be exceeded")
                return []
            
            # Build search query (Basic plan compatible)
            keyword_query = ' OR '.join(keywords)
            query = f"({keyword_query}) lang:fr -is:retweet"
            
            # Search tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=['public_metrics', 'created_at', 'author_id'],
                sort_order='relevancy'
            )
            
            viral_tweets = []
            # Handle both dict and object response formats
            tweets_data = response.data if hasattr(response, 'data') else response.get('data', [])
            if tweets_data:
                for tweet in tweets_data:
                    # Handle both dict and object tweet formats
                    tweet_id_val = tweet.get('id') if isinstance(tweet, dict) else getattr(tweet, 'id', None)
                    text = tweet.get('text') if isinstance(tweet, dict) else getattr(tweet, 'text', '')
                    author_id = tweet.get('author_id') if isinstance(tweet, dict) else getattr(tweet, 'author_id', None)
                    created_at = tweet.get('created_at') if isinstance(tweet, dict) else getattr(tweet, 'created_at', '')
                    public_metrics = tweet.get('public_metrics') if isinstance(tweet, dict) else getattr(tweet, 'public_metrics', {})
                    
                    # Calculate virality score
                    metrics = public_metrics or {}
                    likes = metrics.get('like_count', 0)
                    retweets = metrics.get('retweet_count', 0)
                    replies = metrics.get('reply_count', 0)
                    
                    # Simple virality score
                    virality_score = likes + (retweets * 3) + (replies * 2)
                    
                    viral_tweets.append({
                        'id': tweet_id_val,
                        'text': text,
                        'author_id': author_id,
                        'created_at': created_at,
                        'metrics': metrics,
                        'virality_score': virality_score
                    })
                
                # Sort by virality score
                viral_tweets.sort(key=lambda x: x['virality_score'], reverse=True)
                
                self._update_quota('reads', len(tweets_data))
                logger.info(f"Found {len(viral_tweets)} viral tweets")
            
            return viral_tweets
            
        except Exception as e:
            logger.error(f"Failed to search viral tweets: {e}")
            return []
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota usage status"""
        config = self.config_manager.get_config()
        quotas = self.config_manager.get_current_quotas()
        
        return {
            'daily_usage': self._quota_usage,
            'daily_limits': {
                'posts': quotas.posts_per_day if quotas.posts_per_day > 0 else 'unlimited',
                'reads': quotas.reads_per_day if quotas.reads_per_day > 0 else 'unlimited',
                'likes': config.engagement.likes_per_day
            },
            'plan': config.x_api.plan,
            'last_reset': self._last_quota_reset.isoformat()
        }
    
    def reset_quota_counters(self) -> None:
        """Manually reset quota counters (for testing)"""
        self._quota_usage = {'posts': 0, 'reads': 0, 'likes': 0}
        self._last_quota_reset = datetime.utcnow()
        logger.info("✅ Quota counters reset manually")


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION
# =============================================================================

def create_twitter_manager(config_manager=None, storage_manager=None) -> TwitterAPIManager:
    """
    Factory function pour DI Container
    
    Crée une instance TwitterAPIManager avec injection de dépendances.
    Utilisé par le DI container au lieu des singletons.
    """
    return TwitterAPIManager(config_manager, storage_manager)


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_twitter_manager() -> TwitterAPIManager:
    """
    DEPRECATED: Utiliser container.get('twitter') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_twitter_manager() is deprecated. Use container.get('twitter') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('twitter')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_twitter_manager()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - Support multi-comptes avec factory pattern
# - Cache intelligent pour éviter API calls redondants
# - Retry avec backoff exponentiel plus sophistiqué
# - Monitoring des rate limits en temps réel
# - Event-driven quota management  
# - Support Twitter Ads API pour analytics avancées
# - Integration avec Twitter Spaces API
# - Support pour les Twitter Lists
# - Analytics prédictives basées sur l'historique
# - Real-time sentiment analysis
# - Auto-engagement optimization basé sur performance 