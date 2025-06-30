import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import tweepy

from twitter_api import TwitterAPI, TwitterAPIError, RateLimitError


class TestTwitterAPI:
    """Test cases for TwitterAPI"""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for Twitter API"""
        config = Mock()
        config.get.side_effect = lambda key, default=None: {
            'x_api.plan': 'basic',
            'x_api.quotas.basic.monthly_posts': 1500,
            'x_api.quotas.basic.monthly_reads': 50000,
            'engagement.auto_like_replies': True,
            'engagement.max_likes_per_hour': 100
        }.get(key, default)
        return config

    @pytest.fixture
    def twitter_api(self, mock_config, mock_tweepy_client):
        """Create TwitterAPI instance with mocked dependencies"""
        with patch('twitter_api.tweepy.Client', return_value=mock_tweepy_client):
            with patch.dict('os.environ', {
                'X_API_KEY': 'test_key',
                'X_API_SECRET': 'test_secret',
                'X_ACCESS_TOKEN': 'test_token',
                'X_ACCESS_TOKEN_SECRET': 'test_token_secret',
                'X_BEARER_TOKEN': 'test_bearer'
            }):
                api = TwitterAPI(mock_config)
                yield api

    def test_init_success(self, mock_config):
        """Test successful Twitter API initialization"""
        with patch('twitter_api.tweepy.Client') as mock_client:
            with patch.dict('os.environ', {
                'X_API_KEY': 'test_key',
                'X_API_SECRET': 'test_secret',
                'X_ACCESS_TOKEN': 'test_token',
                'X_ACCESS_TOKEN_SECRET': 'test_token_secret',
                'X_BEARER_TOKEN': 'test_bearer'
            }):
                api = TwitterAPI(mock_config)
                assert api.client is not None
                mock_client.assert_called_once()

    def test_init_missing_credentials(self, mock_config):
        """Test initialization with missing credentials"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(TwitterAPIError, match="Missing required credentials"):
                TwitterAPI(mock_config)

    def test_post_tweet_success(self, twitter_api, mock_tweepy_client):
        """Test successful tweet posting"""
        content = "Test tweet content"
        result = twitter_api.post_tweet(content)
        
        assert result['success'] is True
        assert result['tweet_id'] == '1234567890'
        mock_tweepy_client.create_tweet.assert_called_once_with(text=content)

    def test_post_tweet_with_image(self, twitter_api, mock_tweepy_client):
        """Test posting tweet with image"""
        with patch('twitter_api.upload_media') as mock_upload:
            mock_upload.return_value = 'media_id_123'
            mock_tweepy_client.create_tweet.return_value = {
                'data': {'id': '1234567890', 'text': 'Test tweet'}
            }
            
            content = "Test tweet with image"
            image_path = "/path/to/image.jpg"
            result = twitter_api.post_tweet(content, image_path=image_path)
            
            assert result['success'] is True
            mock_upload.assert_called_once_with(image_path)
            mock_tweepy_client.create_tweet.assert_called_once_with(
                text=content, 
                media_ids=['media_id_123']
            )

    def test_post_tweet_rate_limit(self, twitter_api, mock_tweepy_client):
        """Test posting tweet when rate limited"""
        mock_tweepy_client.create_tweet.side_effect = tweepy.TooManyRequests(
            "Rate limit exceeded"
        )
        
        with pytest.raises(RateLimitError):
            twitter_api.post_tweet("Test tweet")

    def test_post_tweet_api_error(self, twitter_api, mock_tweepy_client):
        """Test posting tweet with API error"""
        mock_tweepy_client.create_tweet.side_effect = tweepy.BadRequest(
            "Invalid request"
        )
        
        with pytest.raises(TwitterAPIError):
            twitter_api.post_tweet("Test tweet")

    def test_like_tweet_success(self, twitter_api, mock_tweepy_client):
        """Test successful tweet liking"""
        tweet_id = "1234567890"
        result = twitter_api.like_tweet(tweet_id)
        
        assert result['success'] is True
        mock_tweepy_client.like.assert_called_once_with(tweet_id)

    def test_like_tweet_already_liked(self, twitter_api, mock_tweepy_client):
        """Test liking already liked tweet"""
        mock_tweepy_client.like.side_effect = tweepy.Forbidden("Already liked")
        
        tweet_id = "1234567890"
        result = twitter_api.like_tweet(tweet_id)
        
        assert result['success'] is True  # Should handle gracefully
        assert "already liked" in result['message'].lower()

    def test_get_replies_success(self, twitter_api, mock_tweepy_client):
        """Test getting replies to tweets"""
        user_id = "1111111111"
        replies = twitter_api.get_replies(user_id)
        
        assert len(replies) == 1
        assert replies[0]['id'] == '9876543210'
        mock_tweepy_client.get_users_mentions.assert_called_once()

    def test_get_tweet_metrics_success(self, twitter_api, mock_tweepy_client):
        """Test getting tweet metrics"""
        tweet_id = "1234567890"
        metrics = twitter_api.get_tweet_metrics(tweet_id)
        
        assert metrics['likes'] == 10
        assert metrics['retweets'] == 5
        assert metrics['replies'] == 2
        assert metrics['impressions'] == 100
        mock_tweepy_client.get_tweet.assert_called_once()

    def test_search_viral_tweets_success(self, twitter_api, mock_tweepy_client):
        """Test searching for viral tweets"""
        mock_tweepy_client.search_recent_tweets.return_value = {
            'data': [
                {
                    'id': '1111111111',
                    'text': 'Viral tweet about AI',
                    'public_metrics': {'like_count': 1000, 'retweet_count': 500}
                }
            ]
        }
        
        viral_tweets = twitter_api.search_viral_tweets(['AI', 'tech'])
        
        assert len(viral_tweets) == 1
        assert viral_tweets[0]['text'] == 'Viral tweet about AI'
        mock_tweepy_client.search_recent_tweets.assert_called_once()

    def test_quota_tracking(self, twitter_api):
        """Test quota tracking functionality"""
        # Test initial quota state
        quota_info = twitter_api.get_quota_info()
        assert 'monthly_posts_used' in quota_info
        assert 'monthly_reads_used' in quota_info
        assert 'posts_remaining' in quota_info
        assert 'reads_remaining' in quota_info

    def test_quota_exceeded_check(self, twitter_api):
        """Test quota exceeded checking"""
        # Mock quota exceeded scenario
        twitter_api.quota_tracker.monthly_posts_used = 1500  # At limit
        
        with pytest.raises(RateLimitError, match="Monthly posting quota exceeded"):
            twitter_api._check_quotas('post')

    def test_quota_warning_threshold(self, twitter_api):
        """Test quota warning threshold"""
        # Mock near quota limit
        twitter_api.quota_tracker.monthly_posts_used = 1200  # 80% of 1500
        
        # Should not raise error but log warning
        twitter_api._check_quotas('post')  # Should succeed

    def test_retry_on_rate_limit(self, twitter_api, mock_tweepy_client):
        """Test retry logic on rate limit"""
        # First call fails, second succeeds
        mock_tweepy_client.create_tweet.side_effect = [
            tweepy.TooManyRequests("Rate limit"),
            {'data': {'id': '1234567890', 'text': 'Test tweet'}}
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = twitter_api.post_tweet("Test tweet")
            assert result['success'] is True

    def test_health_check(self, twitter_api, mock_tweepy_client):
        """Test API health check"""
        mock_tweepy_client.get_me.return_value = {'data': {'id': '1111111111'}}
        
        health = twitter_api.health_check()
        assert health['status'] == 'healthy'
        assert health['api_accessible'] is True

    def test_health_check_failure(self, twitter_api, mock_tweepy_client):
        """Test API health check failure"""
        mock_tweepy_client.get_me.side_effect = tweepy.Unauthorized("Invalid token")
        
        health = twitter_api.health_check()
        assert health['status'] == 'unhealthy'
        assert health['api_accessible'] is False

    def test_bulk_like_replies(self, twitter_api, mock_tweepy_client):
        """Test bulk liking of replies"""
        reply_ids = ['111', '222', '333']
        results = twitter_api.bulk_like_replies(reply_ids)
        
        assert len(results) == 3
        assert all(r['success'] for r in results)
        assert mock_tweepy_client.like.call_count == 3

    def test_bulk_like_with_rate_limit(self, twitter_api, mock_tweepy_client):
        """Test bulk liking with rate limit handling"""
        # Simulate rate limit on second call
        mock_tweepy_client.like.side_effect = [
            {'data': {'liked': True}},
            tweepy.TooManyRequests("Rate limit"),
            {'data': {'liked': True}}
        ]
        
        reply_ids = ['111', '222', '333']
        with patch('time.sleep'):
            results = twitter_api.bulk_like_replies(reply_ids)
            
        # Should handle rate limit gracefully
        assert len(results) == 3

    def test_get_user_info(self, twitter_api, mock_tweepy_client):
        """Test getting user information"""
        mock_tweepy_client.get_me.return_value = {
            'data': {
                'id': '1111111111',
                'username': 'testbot',
                'name': 'Test Bot'
            }
        }
        
        user_info = twitter_api.get_user_info()
        assert user_info['id'] == '1111111111'
        assert user_info['username'] == 'testbot'

    def test_upload_media_success(self, twitter_api):
        """Test successful media upload"""
        with patch('twitter_api.tweepy.API') as mock_api_v1:
            mock_v1_client = Mock()
            mock_api_v1.return_value = mock_v1_client
            mock_v1_client.media_upload.return_value = Mock(media_id=12345)
            
            media_id = twitter_api.upload_media('/path/to/image.jpg')
            assert media_id == 12345

    def test_singleton_pattern(self, mock_config):
        """Test that TwitterAPI follows singleton pattern"""
        with patch('twitter_api.tweepy.Client'):
            with patch.dict('os.environ', {
                'X_API_KEY': 'test_key',
                'X_API_SECRET': 'test_secret',
                'X_ACCESS_TOKEN': 'test_token',
                'X_ACCESS_TOKEN_SECRET': 'test_token_secret',
                'X_BEARER_TOKEN': 'test_bearer'
            }):
                api1 = TwitterAPI(mock_config)
                api2 = TwitterAPI(mock_config)
                assert api1 is api2 