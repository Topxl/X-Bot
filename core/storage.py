"""
Storage Manager pour Bot Twitter Automatisé

Gère toutes les interactions avec Supabase :
- Setup et migration des tables
- CRUD operations pour tweets, replies, stats
- Real-time subscriptions pour les replies
- Storage des images générées

NOUVELLE ARCHITECTURE:
- Error Recovery avec fallbacks
- Event Bus pour notifications  
- Intégration DI Container
- Messages utilisateur informatifs
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from loguru import logger
from supabase import create_client, Client
from tenacity import retry, stop_after_attempt, wait_exponential

# Nouvelle architecture - Imports ajoutés par migration
from events import get_event_bus, EventTypes, EventPriority
from error_handler import get_error_manager, safe_execute, ErrorSeverity


@dataclass
class Tweet:
    """Modèle pour un tweet"""
    id: Optional[str] = None
    tweet_id: str = ""
    content: str = ""
    image_url: Optional[str] = None
    posted_at: Optional[datetime] = None
    engagement: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.engagement is None:
            self.engagement = {}
        if self.posted_at is None:
            self.posted_at = datetime.utcnow()


@dataclass
class Reply:
    """Modèle pour une reply"""
    id: Optional[str] = None
    reply_id: str = ""
    original_tweet_id: str = ""
    author_id: str = ""
    content: str = ""
    created_at: Optional[datetime] = None
    liked: bool = False
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class TweetStats:
    """Modèle pour les statistiques d'un tweet"""
    id: Optional[str] = None
    tweet_id: str = ""
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    impressions: int = 0
    collected_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.collected_at is None:
            self.collected_at = datetime.utcnow()


class StorageManager:
    """
    Gestionnaire de stockage Supabase avec nouvelle architecture
    
    Features:
    - Auto-setup des tables avec migrations
    - CRUD operations avec retry logic et error recovery
    - Real-time subscriptions pour events
    - Image storage dans buckets
    - Cleanup automatique des anciennes données
    - Event Bus pour notifications
    - Error Recovery avec fallbacks
    """
    
    def __init__(self, config_manager=None):
        self.supabase: Optional[Client] = None
        
        # Configuration via DI container ou fallback
        if config_manager is None:
            try:
                from container import get_container
                container = get_container()
                self.config_manager = container.get('config')
            except (ImportError, KeyError):
                logger.warning("⚠️ DI Container not available, using direct config access")
                from config import create_config_manager
                self.config_manager = create_config_manager()
        else:
            self.config_manager = config_manager
            
        # Nouvelle architecture - Event Bus et Error Manager
        self.event_bus = get_event_bus()
        self.error_manager = get_error_manager()
        
        self._subscriptions: List[Any] = []
        self._event_handlers: Dict[str, List[Callable]] = {
            'reply_insert': [],
            'tweet_update': [],
            'stats_insert': []
        }
        
        # Initialize Supabase with error recovery
        self._initialize_with_recovery()
    
    @safe_execute(
        user_message_key="database_error",
        severity=ErrorSeverity.LOW,
        fallback_category="data_storage",
        module="StorageManager"
    )
    def _initialize_with_recovery(self) -> None:
        """Initialize Supabase with comprehensive error recovery"""
        try:
            self._init_supabase()
            self._setup_tables()
            self._setup_storage()
            
            # Publier événement de succès
            self.event_bus.publish(
                EventTypes.MODULE_INITIALIZED,
                data={'module': 'storage_manager', 'status': 'connected'},
                source='StorageManager'
            )
            
        except Exception as e:
            logger.warning(f"⚠️ Supabase initialization failed, running in local-only mode: {e}")
            self.supabase = None
            
            # Publier événement d'échec
            self.event_bus.publish(
                EventTypes.MODULE_FAILED,
                data={
                    'module': 'storage_manager', 
                    'error': str(e),
                    'fallback_mode': 'local_only'
                },
                source='StorageManager',
                priority=EventPriority.HIGH
            )
    
    @safe_execute(
        user_message_key="database_error",
        severity=ErrorSeverity.MEDIUM,
        module="StorageManager"
    )
    def _init_supabase(self) -> None:
        """Initialize Supabase client avec error recovery"""
        try:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("Supabase credentials not found in environment")
            
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase storage client initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase storage: {e}")
            raise e  # Laisse l'error recovery gérer
    
    def _setup_tables(self) -> None:
        """Setup required database tables"""
        try:
            # Note: En production, ces tables devraient être créées via migrations SQL
            # Ici on vérifie juste leur existence
            
            tables_to_check = ['configs', 'tweets', 'replies', 'stats']
            for table in tables_to_check:
                try:
                    # Test query to check if table exists
                    self.supabase.table(table).select('*').limit(1).execute()
                    logger.debug(f"Table '{table}' exists")
                except Exception as e:
                    logger.warning(f"Table '{table}' might not exist: {e}")
            
            logger.info("Database tables check completed")
            
        except Exception as e:
            logger.error(f"Failed to setup tables: {e}")
    
    def _setup_storage(self) -> None:
        """Setup storage buckets for images with enhanced RLS handling"""
        try:
            # Test if bucket exists by trying to list objects in it
            bucket_exists = self._check_bucket_exists('generated-images')
            
            if bucket_exists:
                logger.info("✅ Storage bucket 'generated-images' is available")
                return
            
            # Bucket doesn't exist, try to create it
            logger.info("📦 Attempting to create 'generated-images' bucket...")
            
            try:
                self.supabase.storage.create_bucket(
                    'generated-images',
                    options={'public': True}
                )
                logger.info("✅ Storage bucket 'generated-images' created successfully")
                
            except Exception as bucket_error:
                error_msg = str(bucket_error).lower()
                
                if 'already exists' in error_msg:
                    logger.info("✅ Storage bucket 'generated-images' already exists")
                    
                elif any(rls_keyword in error_msg for rls_keyword in ['row-level security', 'rls', 'policy']):
                    logger.warning("⚠️ RLS Policy blocks bucket creation - Manual setup required")
                    logger.warning("📋 To fix: Run this SQL in your Supabase dashboard:")
                    logger.warning("   INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)")
                    logger.warning("   VALUES ('generated-images', 'generated-images', true, 52428800, ARRAY['image/jpeg', 'image/png', 'image/webp'])")
                    logger.warning("   ON CONFLICT (id) DO NOTHING;")
                    
                elif 'permission' in error_msg or 'unauthorized' in error_msg:
                    logger.warning("⚠️ Insufficient permissions to create bucket")
                    logger.warning("📋 Solution: Create bucket manually in Supabase dashboard or run init_supabase.sql")
                    
                else:
                    logger.warning(f"⚠️ Bucket creation failed: {bucket_error}")
                    logger.warning("📋 Images will be stored locally instead")
                
        except Exception as e:
            logger.warning(f"⚠️ Storage setup failed: {e}")
            logger.warning("📋 Bot will continue without image storage functionality")
    
    def _check_bucket_exists(self, bucket_name: str) -> bool:
        """
        Check if a storage bucket exists by attempting to access it
        
        Args:
            bucket_name: Name of the bucket to check
            
        Returns:
            bool: True if bucket exists and is accessible, False otherwise
        """
        try:
            # Try to list objects in the bucket (more reliable than list_buckets)
            self.supabase.storage.from_(bucket_name).list()
            return True
        except Exception as e:
            error_msg = str(e).lower()
            
            # These errors indicate the bucket exists but might be empty
            if any(indicator in error_msg for indicator in ['not found', 'does not exist', 'bucket_not_found']):
                return False
            
            # Other errors might indicate the bucket exists but we have permission issues
            logger.debug(f"Bucket check for '{bucket_name}' returned: {e}")
            return True  # Assume it exists if we get permission errors
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    @safe_execute(
        user_message_key="database_error",
        severity=ErrorSeverity.MEDIUM,
        fallback_category="data_storage",
        module="StorageManager"
    )
    def save_tweet(self, tweet: Tweet) -> Optional[str]:
        """
        Save tweet to database avec error recovery
        
        Args:
            tweet: Tweet object to save
            
        Returns:
            str: Tweet ID if successful, None otherwise
        """
        if not self.supabase:
            logger.warning("⚠️ Supabase not available, tweet not saved to database")
            
            # Publier événement de fallback
            self.event_bus.publish(
                EventTypes.API_ERROR,
                data={
                    'error_type': 'database_unavailable',
                    'operation': 'save_tweet',
                    'tweet_id': tweet.tweet_id
                },
                source='StorageManager'
            )
            return None
            
        try:
            tweet_data = {
                'tweet_id': tweet.tweet_id,
                'content': tweet.content,
                'image_url': tweet.image_url,
                'posted_at': tweet.posted_at.isoformat() if tweet.posted_at else datetime.utcnow().isoformat(),
                'engagement': tweet.engagement or {}
            }
            
            response = self.supabase.table('tweets').insert(tweet_data).execute()
            
            if response.data:
                tweet_id = response.data[0]['id']
                logger.info(f"✅ Tweet saved successfully: {tweet_id}")
                
                # Publier événement de succès
                self.event_bus.publish(
                    EventTypes.TWEET_POSTED,
                    data={
                        'tweet_id': tweet.tweet_id,
                        'storage_id': tweet_id,
                        'content': tweet.content[:100] + '...' if len(tweet.content) > 100 else tweet.content
                    },
                    source='StorageManager'
                )
                
                return tweet_id
            
        except Exception as e:
            logger.error(f"Failed to save tweet: {e}")
            raise
        
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def upload_image(self, image_path: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Upload image to Supabase Storage
        
        Args:
            image_path: Local path to image file
            filename: Optional custom filename, auto-generated if None
            
        Returns:
            str: Public URL of uploaded image if successful, None otherwise
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Generate filename if not provided
            if not filename:
                ext = os.path.splitext(image_path)[1]
                filename = f"{uuid.uuid4()}{ext}"
            
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Upload to Supabase Storage
            response = self.supabase.storage.from_('generated-images').upload(
                filename,
                image_data,
                file_options={
                    'content-type': 'image/png',
                    'cache-control': '3600',
                    'upsert': True
                }
            )
            
            if response:
                # Get public URL
                public_url = self.supabase.storage.from_('generated-images').get_public_url(filename)
                logger.info(f"Image uploaded successfully: {filename} -> {public_url}")
                return public_url
            
        except Exception as e:
            logger.error(f"Failed to upload image {image_path}: {e}")
        
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def save_reply(self, reply: Reply) -> Optional[str]:
        """
        Save reply to database with duplicate handling
        
        Args:
            reply: Reply object to save
            
        Returns:
            str: Reply ID if successful, None otherwise
        """
        if not self.supabase:
            logger.warning("Supabase not available, cannot save reply")
            return None
            
        try:
            # Vérifier si la réponse existe déjà
            existing_response = self.supabase.table('replies').select('id').eq(
                'reply_id', reply.reply_id
            ).execute()
            
            if existing_response.data:
                # La réponse existe déjà, la mettre à jour si nécessaire
                existing_id = existing_response.data[0]['id']
                
                # Mettre à jour seulement si le statut liked a changé
                if reply.liked:
                    update_response = self.supabase.table('replies').update({
                        'liked': reply.liked
                    }).eq('reply_id', reply.reply_id).execute()
                    
                    if update_response.data:
                        logger.debug(f"Reply {reply.reply_id} updated (liked: {reply.liked})")
                
                logger.debug(f"Reply {reply.reply_id} already exists, skipping insert")
                return existing_id
            
            # La réponse n'existe pas, l'insérer
            reply_data = {
                'reply_id': reply.reply_id,
                'original_tweet_id': reply.original_tweet_id,
                'author_id': reply.author_id,
                'content': reply.content,
                'created_at': reply.created_at.isoformat() if reply.created_at else datetime.utcnow().isoformat(),
                'liked': reply.liked
            }
            
            response = self.supabase.table('replies').insert(reply_data).execute()
            
            if response.data:
                reply_id = response.data[0]['id']
                logger.info(f"Reply saved successfully: {reply_id}")
                return reply_id
            
        except Exception as e:
            # Vérifier si c'est encore une erreur de duplicate key
            if "duplicate key value violates unique constraint" in str(e):
                logger.debug(f"Reply {reply.reply_id} duplicate detected, gracefully handling")
                # Tenter de récupérer l'ID existant
                try:
                    existing_response = self.supabase.table('replies').select('id').eq(
                        'reply_id', reply.reply_id
                    ).execute()
                    if existing_response.data:
                        return existing_response.data[0]['id']
                except:
                    pass
                return None
            else:
                logger.error(f"Failed to save reply: {e}")
                raise
        
        return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def mark_reply_liked(self, reply_id: str) -> bool:
        """
        Mark a reply as liked in the database
        
        Args:
            reply_id: The reply ID to mark as liked
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = self.supabase.table('replies').update({
                'liked': True
            }).eq('reply_id', reply_id).execute()
            
            if response.data:
                logger.info(f"Reply {reply_id} marked as liked")
                return True
            
        except Exception as e:
            logger.error(f"Failed to mark reply as liked: {e}")
            raise
        
        return False
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_recent_tweets(self, hours: int = 24) -> List[Tweet]:
        """
        Get recent tweets from the last X hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List[Tweet]: List of recent tweets
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            response = self.supabase.table('tweets').select('*').gte(
                'posted_at', cutoff_time.isoformat()
            ).order('posted_at', desc=True).execute()
            
            tweets = []
            if response.data:
                for tweet_data in response.data:
                    tweet = Tweet(
                        id=tweet_data['id'],
                        tweet_id=tweet_data['tweet_id'],
                        content=tweet_data['content'],
                        image_url=tweet_data.get('image_url'),
                        posted_at=datetime.fromisoformat(tweet_data['posted_at'].replace('Z', '+00:00')),
                        engagement=tweet_data.get('engagement', {})
                    )
                    tweets.append(tweet)
                    
                logger.info(f"Retrieved {len(tweets)} recent tweets from last {hours} hours")
            
            return tweets
            
        except Exception as e:
            logger.error(f"Failed to get recent tweets: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_tweets(self, limit: int = 10) -> List[Tweet]:
        """
        Get recent tweets with limit
        
        Args:
            limit: Maximum number of tweets to return
            
        Returns:
            List[Tweet]: List of recent tweets
        """
        if not self.supabase:
            logger.warning("Supabase not available, returning empty tweet list")
            return []
            
        try:
            response = self.supabase.table('tweets').select('*').order(
                'posted_at', desc=True
            ).limit(limit).execute()
            
            tweets = []
            if response.data:
                for tweet_data in response.data:
                    tweet = Tweet(
                        id=tweet_data['id'],
                        tweet_id=tweet_data['tweet_id'],
                        content=tweet_data['content'],
                        image_url=tweet_data.get('image_url'),
                        posted_at=datetime.fromisoformat(tweet_data['posted_at'].replace('Z', '+00:00')),
                        engagement=tweet_data.get('engagement', {})
                    )
                    tweets.append(tweet)
                    
                logger.debug(f"Retrieved {len(tweets)} recent tweets")
            
            return tweets
            
        except Exception as e:
            logger.error(f"Failed to get tweets: {e}")
            raise
    
    def get_recent_replies(self, hours: int = 24) -> List[Reply]:
        """
        Get recent replies from the last X hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List[Reply]: List of recent replies
        """
        if not self.supabase:
            logger.warning("Supabase not available, returning empty replies list")
            return []
            
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            response = self.supabase.table('replies').select('*').gte(
                'created_at', cutoff_time.isoformat()
            ).order('created_at', desc=True).execute()
            
            replies = []
            if response.data:
                for reply_data in response.data:
                    reply = Reply(
                        id=reply_data['id'],
                        reply_id=reply_data['reply_id'],
                        original_tweet_id=reply_data['original_tweet_id'],
                        author_id=reply_data['author_id'],
                        content=reply_data['content'],
                        created_at=datetime.fromisoformat(reply_data['created_at'].replace('Z', '+00:00')),
                        liked=reply_data.get('liked', False)
                    )
                    replies.append(reply)
                    
                logger.debug(f"Retrieved {len(replies)} recent replies from last {hours} hours")
            
            return replies
            
        except Exception as e:
            logger.error(f"Failed to get recent replies: {e}")
            return []
    
    def reply_exists(self, reply_id: str) -> bool:
        """
        Check if a reply already exists in the database
        
        Args:
            reply_id: The reply ID to check
            
        Returns:
            bool: True if the reply exists, False otherwise
        """
        if not self.supabase:
            return False
            
        try:
            response = self.supabase.table('replies').select('id').eq(
                'reply_id', reply_id
            ).limit(1).execute()
            
            return bool(response.data)
            
        except Exception as e:
            logger.error(f"Failed to check reply existence: {e}")
            return False
    
    def get_existing_reply_ids(self, reply_ids: List[str]) -> List[str]:
        """
        Get list of reply IDs that already exist in database
        
        Args:
            reply_ids: List of reply IDs to check
            
        Returns:
            List[str]: List of existing reply IDs
        """
        if not self.supabase or not reply_ids:
            return []
            
        try:
            response = self.supabase.table('replies').select('reply_id').in_(
                'reply_id', reply_ids
            ).execute()
            
            if response.data:
                return [item['reply_id'] for item in response.data]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get existing reply IDs: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def save_stats(self, stats: TweetStats) -> Optional[str]:
        """
        Save tweet statistics to database
        
        Args:
            stats: TweetStats object to save
            
        Returns:
            str: Stats ID if successful, None otherwise
        """
        if not self.supabase:
            logger.warning("Supabase not available, stats not saved to database")
            return None
            
        try:
            stats_data = {
                'tweet_id': stats.tweet_id,
                'likes': stats.likes,
                'retweets': stats.retweets,
                'replies': stats.replies,
                'impressions': stats.impressions,
                'collected_at': stats.collected_at.isoformat() if stats.collected_at else datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('stats').insert(stats_data).execute()
            
            if response.data:
                stats_id = response.data[0]['id']
                logger.debug(f"Stats saved successfully for tweet {stats.tweet_id}")
                return stats_id
            else:
                logger.error("No data returned when saving stats")
                return None
                
        except Exception as e:
            logger.error(f"Failed to save stats: {e}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_top_performing_tweets(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get top performing tweets based on engagement metrics
        
        Args:
            limit: Maximum number of tweets to return
            days: Number of days to look back
            
        Returns:
            List of tweets with their stats, sorted by engagement score
        """
        if not self.supabase:
            logger.warning("Supabase not available, returning empty list")
            return []
            
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get tweets from the specified period
            tweets_response = self.supabase.table('tweets')\
                .select('*')\
                .gte('posted_at', cutoff_date.isoformat())\
                .order('posted_at', desc=True)\
                .execute()
            
            if not tweets_response.data:
                return []
            
            tweets_with_stats = []
            
            for tweet in tweets_response.data:
                # Get latest stats for this tweet
                stats_response = self.supabase.table('stats')\
                    .select('*')\
                    .eq('tweet_id', tweet['tweet_id'])\
                    .order('collected_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                if stats_response.data:
                    stats = stats_response.data[0]
                    # Calculate engagement score (weighted)
                    engagement_score = (
                        stats.get('likes', 0) * 1 +
                        stats.get('retweets', 0) * 3 +
                        stats.get('replies', 0) * 2 +
                        stats.get('impressions', 0) * 0.01
                    )
                    
                    tweets_with_stats.append({
                        'tweet_id': tweet['tweet_id'],
                        'content': tweet['content'][:100] + '...' if len(tweet['content']) > 100 else tweet['content'],
                        'full_content': tweet['content'],
                        'posted_at': tweet['posted_at'],
                        'image_url': tweet.get('image_url'),
                        'likes': stats.get('likes', 0),
                        'retweets': stats.get('retweets', 0),
                        'replies': stats.get('replies', 0),
                        'impressions': stats.get('impressions', 0),
                        'engagement_score': round(engagement_score, 2),
                        'collected_at': stats.get('collected_at'),
                        'tweet_url': f"https://twitter.com/i/status/{tweet['tweet_id']}"
                    })
            
            # Sort by engagement score and return top tweets
            tweets_with_stats.sort(key=lambda x: x['engagement_score'], reverse=True)
            return tweets_with_stats[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get top performing tweets: {e}")
            return []
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_tweet_performance_overview(self, days: int = 7) -> Dict[str, Any]:
        """
        Get performance overview for the dashboard
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with performance metrics
        """
        if not self.supabase:
            return {
                'total_tweets': 0,
                'total_engagement': 0,
                'avg_engagement_per_tweet': 0,
                'best_performing_day': None,
                'growth_trend': 0
            }
            
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get tweets and their stats for the period
            response = self.supabase.table('tweets')\
                .select('tweet_id, posted_at')\
                .gte('posted_at', cutoff_date.isoformat())\
                .execute()
            
            if not response.data:
                return {
                    'total_tweets': 0,
                    'total_engagement': 0,
                    'avg_engagement_per_tweet': 0,
                    'best_performing_day': None,
                    'growth_trend': 0
                }
            
            total_engagement = 0
            daily_engagement = {}
            
            for tweet in response.data:
                # Get latest stats for this tweet
                stats_response = self.supabase.table('stats')\
                    .select('likes, retweets, replies, impressions')\
                    .eq('tweet_id', tweet['tweet_id'])\
                    .order('collected_at', desc=True)\
                    .limit(1)\
                    .execute()
                
                if stats_response.data:
                    stats = stats_response.data[0]
                    engagement = (
                        stats.get('likes', 0) +
                        stats.get('retweets', 0) +
                        stats.get('replies', 0)
                    )
                    total_engagement += engagement
                    
                    # Track daily engagement
                    day = datetime.fromisoformat(tweet['posted_at'].replace('Z', '+00:00')).date()
                    daily_engagement[day] = daily_engagement.get(day, 0) + engagement
            
            total_tweets = len(response.data)
            avg_engagement = total_engagement / total_tweets if total_tweets > 0 else 0
            
            # Find best performing day
            best_day = max(daily_engagement.items(), key=lambda x: x[1]) if daily_engagement else None
            
            return {
                'total_tweets': total_tweets,
                'total_engagement': total_engagement,
                'avg_engagement_per_tweet': round(avg_engagement, 2),
                'best_performing_day': {
                    'date': best_day[0].isoformat(),
                    'engagement': best_day[1]
                } if best_day else None,
                'growth_trend': self._calculate_growth_trend(daily_engagement)
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance overview: {e}")
            return {
                'total_tweets': 0,
                'total_engagement': 0,
                'avg_engagement_per_tweet': 0,
                'best_performing_day': None,
                'growth_trend': 0
            }
    
    def _calculate_growth_trend(self, daily_engagement: Dict) -> float:
        """Calculate growth trend percentage"""
        if len(daily_engagement) < 2:
            return 0
        
        sorted_days = sorted(daily_engagement.items())
        if len(sorted_days) >= 2:
            recent_avg = sum(engagement for _, engagement in sorted_days[-3:]) / min(3, len(sorted_days))
            older_avg = sum(engagement for _, engagement in sorted_days[:3]) / min(3, len(sorted_days))
            
            if older_avg > 0:
                return round(((recent_avg - older_avg) / older_avg) * 100, 1)
        
        return 0
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def cleanup_old_data(self) -> Dict[str, int]:
        """
        Clean up old data based on configuration
        
        Returns:
            Dict[str, int]: Cleanup statistics
        """
        try:
            config = self.config_manager.get_config()
            keep_days = config.storage.keep_tweet_history_days
            cutoff_date = datetime.utcnow() - timedelta(days=keep_days)
            
            stats = {'tweets_deleted': 0, 'replies_deleted': 0, 'stats_deleted': 0}
            
            # Clean up old tweets
            response = self.supabase.table('tweets').delete().lt(
                'posted_at', cutoff_date.isoformat()
            ).execute()
            if response.data:
                stats['tweets_deleted'] = len(response.data)
            
            # Clean up old replies
            response = self.supabase.table('replies').delete().lt(
                'created_at', cutoff_date.isoformat()
            ).execute()
            if response.data:
                stats['replies_deleted'] = len(response.data)
            
            # Clean up old stats
            response = self.supabase.table('stats').delete().lt(
                'collected_at', cutoff_date.isoformat()
            ).execute()
            if response.data:
                stats['stats_deleted'] = len(response.data)
            
            logger.info(f"Cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise
    
    def setup_realtime_subscriptions(self) -> None:
        """Setup real-time subscriptions for automatic replies handling"""
        try:
            # Subscribe to new replies
            def handle_reply_insert(payload):
                """Handle new reply insertion"""
                try:
                    logger.info(f"New reply detected: {payload}")
                    
                    # Trigger registered handlers
                    for handler in self._event_handlers['reply_insert']:
                        try:
                            handler(payload)
                        except Exception as e:
                            logger.error(f"Error in reply handler: {e}")
                            
                except Exception as e:
                    logger.error(f"Error handling reply insert: {e}")
            
            # Subscribe to replies table
            subscription = self.supabase.table('replies').on('INSERT', handle_reply_insert).subscribe()
            self._subscriptions.append(subscription)
            
            logger.info("Real-time subscriptions setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup real-time subscriptions: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Add event handler for real-time events
        
        Args:
            event_type: Type of event ('reply_insert', 'tweet_update', 'stats_insert')
            handler: Callback function to handle the event
        """
        if event_type in self._event_handlers:
            self._event_handlers[event_type].append(handler)
            logger.info(f"Added event handler for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    def close(self) -> None:
        """Close connections and clean up resources"""
        try:
            # Unsubscribe from real-time subscriptions
            for subscription in self._subscriptions:
                try:
                    subscription.unsubscribe()
                except:
                    pass
            
            self._subscriptions.clear()
            logger.info("✅ Storage manager closed successfully")
            
            # Publier événement de fermeture
            self.event_bus.publish(
                EventTypes.MODULE_FAILED,  # Ou créer BOT_SHUTDOWN
                data={'module': 'storage_manager', 'status': 'closed'},
                source='StorageManager'
            )
            
        except Exception as e:
            logger.error(f"❌ Error closing storage manager: {e}")


# =============================================================================
# NOUVELLE ARCHITECTURE - DI CONTAINER CONFIGURATION  
# =============================================================================

def create_storage_manager(config_manager=None) -> StorageManager:
    """
    Factory function pour DI Container
    
    Crée une instance StorageManager avec injection de dépendances.
    Utilisé par le DI container au lieu des singletons.
    """
    return StorageManager(config_manager)


# =============================================================================
# COMPATIBILITY LAYER - DEPRECATED (utiliser DI Container à la place)
# =============================================================================

def get_storage_manager() -> StorageManager:
    """
    DEPRECATED: Utiliser container.get('storage') à la place
    
    Fonction de compatibilité maintenue temporairement.
    """
    logger.warning("⚠️ get_storage_manager() is deprecated. Use container.get('storage') instead.")
    try:
        from container import get_container
        container = get_container()
        return container.get('storage')
    except ImportError:
        # Fallback si container pas encore disponible
        return create_storage_manager()


# =============================================================================
# EXTENSIONS FUTURES - Roadmap
# =============================================================================
# - Event-driven data operations
# - Automated data archiving  
# - Real-time analytics streaming
# - Database connection pooling
# - Distributed storage strategies
# - Data encryption at rest
# - Automated backup and recovery
# - Performance monitoring et optimization 