import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from main import TwitterBot
from config import ConfigManager
from twitter_api import TwitterAPI
from generator import ContentGenerator
from storage import StorageManager
from scheduler import TaskScheduler


@pytest.mark.integration
class TestTwitterBotIntegration:
    """Integration tests for the complete Twitter bot system"""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies"""
        with patch('main.ConfigManager') as mock_config, \
             patch('main.TwitterAPI') as mock_twitter, \
             patch('main.ContentGenerator') as mock_generator, \
             patch('main.StorageManager') as mock_storage, \
             patch('main.TaskScheduler') as mock_scheduler:
            
            # Configure mocks
            mock_config_instance = Mock()
            mock_config_instance.get.side_effect = lambda key, default=None: {
                'monitoring.enabled': True,
                'monitoring.health_check_port': 8000,
                'posting.enabled': True,
                'engagement.auto_like_replies': True
            }.get(key, default)
            mock_config.return_value = mock_config_instance
            
            mock_twitter_instance = Mock()
            mock_twitter_instance.health_check.return_value = {'status': 'healthy'}
            mock_twitter.return_value = mock_twitter_instance
            
            mock_generator_instance = Mock()
            mock_generator.return_value = mock_generator_instance
            
            mock_storage_instance = Mock()
            mock_storage_instance.health_check.return_value = {'status': 'healthy'}
            mock_storage.return_value = mock_storage_instance
            
            mock_scheduler_instance = Mock()
            mock_scheduler.return_value = mock_scheduler_instance
            
            yield {
                'config': mock_config_instance,
                'twitter': mock_twitter_instance,
                'generator': mock_generator_instance,
                'storage': mock_storage_instance,
                'scheduler': mock_scheduler_instance
            }

    def test_bot_initialization(self, mock_dependencies):
        """Test complete bot initialization"""
        bot = TwitterBot()
        
        assert bot.config is not None
        assert bot.twitter_api is not None
        assert bot.generator is not None
        assert bot.storage is not None
        assert bot.scheduler is not None

    def test_bot_startup_sequence(self, mock_dependencies):
        """Test bot startup sequence"""
        bot = TwitterBot()
        
        # Mock health checks
        mock_dependencies['twitter'].health_check.return_value = {'status': 'healthy'}
        mock_dependencies['storage'].health_check.return_value = {'status': 'healthy'}
        
        with patch('main.start_health_server'):
            bot.start()
            
            # Verify startup sequence
            mock_dependencies['scheduler'].start.assert_called_once()

    def test_bot_shutdown_sequence(self, mock_dependencies):
        """Test bot shutdown sequence"""
        bot = TwitterBot()
        bot.start()
        
        bot.shutdown()
        
        # Verify shutdown sequence
        mock_dependencies['scheduler'].shutdown.assert_called_once()

    @pytest.mark.slow
    def test_complete_posting_workflow(self, mock_dependencies):
        """Test complete tweet posting workflow"""
        bot = TwitterBot()
        
        # Mock content generation
        mock_dependencies['generator'].generate_tweet.return_value = {
            'content': 'Generated tweet content #AI',
            'topics': ['AI'],
            'image_url': None
        }
        
        # Mock tweet posting
        mock_dependencies['twitter'].post_tweet.return_value = {
            'success': True,
            'tweet_id': '1234567890',
            'message': 'Tweet posted successfully'
        }
        
        # Mock storage
        mock_dependencies['storage'].store_tweet.return_value = {'id': 'stored_id'}
        
        # Execute posting workflow
        result = bot.post_scheduled_tweet()
        
        assert result['success'] is True
        mock_dependencies['generator'].generate_tweet.assert_called_once()
        mock_dependencies['twitter'].post_tweet.assert_called_once()
        mock_dependencies['storage'].store_tweet.assert_called_once()

    def test_reply_engagement_workflow(self, mock_dependencies):
        """Test automatic reply engagement workflow"""
        bot = TwitterBot()
        
        # Mock new reply detection
        new_reply = {
            'id': '9876543210',
            'author_id': '2222222222',
            'original_tweet_id': '1234567890',
            'content': '@testbot Great tweet!'
        }
        
        # Mock like operation
        mock_dependencies['twitter'].like_tweet.return_value = {
            'success': True,
            'message': 'Tweet liked successfully'
        }
        
        # Mock storage update
        mock_dependencies['storage'].update_reply.return_value = True
        
        # Execute engagement workflow
        bot.handle_new_reply(new_reply)
        
        mock_dependencies['twitter'].like_tweet.assert_called_once_with('9876543210')
        mock_dependencies['storage'].update_reply.assert_called_once()

    def test_stats_collection_workflow(self, mock_dependencies):
        """Test statistics collection workflow"""
        bot = TwitterBot()
        
        # Mock recent tweets
        mock_dependencies['storage'].get_recent_tweets.return_value = [
            {'tweet_id': '1234567890', 'posted_at': datetime.utcnow() - timedelta(hours=1)}
        ]
        
        # Mock tweet metrics
        mock_dependencies['twitter'].get_tweet_metrics.return_value = {
            'likes': 10,
            'retweets': 5,
            'replies': 2,
            'impressions': 100
        }
        
        # Mock stats storage
        mock_dependencies['storage'].store_stats.return_value = {'id': 'stats_id'}
        
        # Execute stats collection
        bot.collect_tweet_stats()
        
        mock_dependencies['storage'].get_recent_tweets.assert_called_once()
        mock_dependencies['twitter'].get_tweet_metrics.assert_called_once()
        mock_dependencies['storage'].store_stats.assert_called_once()

    def test_error_handling_and_recovery(self, mock_dependencies):
        """Test error handling and recovery mechanisms"""
        bot = TwitterBot()
        
        # Mock API error
        mock_dependencies['twitter'].post_tweet.side_effect = Exception("API Error")
        
        # Mock content generation
        mock_dependencies['generator'].generate_tweet.return_value = {
            'content': 'Test tweet',
            'topics': ['test'],
            'image_url': None
        }
        
        # Execute with error
        result = bot.post_scheduled_tweet()
        
        # Should handle error gracefully
        assert result['success'] is False
        assert 'error' in result

    def test_quota_management_integration(self, mock_dependencies):
        """Test quota management across components"""
        bot = TwitterBot()
        
        # Mock quota exceeded scenario
        from twitter_api import RateLimitError
        mock_dependencies['twitter'].post_tweet.side_effect = RateLimitError("Quota exceeded")
        
        # Mock content generation
        mock_dependencies['generator'].generate_tweet.return_value = {
            'content': 'Test tweet',
            'topics': ['test'],
            'image_url': None
        }
        
        # Execute posting
        result = bot.post_scheduled_tweet()
        
        # Should handle quota exceeded gracefully
        assert result['success'] is False
        assert 'quota' in result.get('error', '').lower()

    def test_realtime_reply_subscription(self, mock_dependencies):
        """Test realtime reply subscription and handling"""
        bot = TwitterBot()
        
        # Mock Supabase realtime subscription
        mock_channel = Mock()
        mock_dependencies['storage'].supabase.realtime.channel.return_value = mock_channel
        
        # Start realtime subscription
        bot.start_realtime_listeners()
        
        # Verify subscription setup
        mock_dependencies['storage'].supabase.realtime.channel.assert_called()
        mock_channel.on.assert_called()
        mock_channel.subscribe.assert_called()

    def test_health_monitoring_integration(self, mock_dependencies):
        """Test health monitoring across all components"""
        bot = TwitterBot()
        
        # Test overall health check
        health = bot.get_health_status()
        
        assert 'overall_status' in health
        assert 'components' in health
        assert 'twitter_api' in health['components']
        assert 'storage' in health['components']
        assert 'config' in health['components']

    def test_daily_report_generation(self, mock_dependencies):
        """Test daily report generation"""
        bot = TwitterBot()
        
        # Mock daily stats
        mock_dependencies['storage'].get_daily_stats.return_value = {
            'tweets_posted': 5,
            'total_likes': 50,
            'total_retweets': 25,
            'total_replies': 10,
            'engagement_rate': 0.15
        }
        
        # Generate report
        report = bot.generate_daily_report()
        
        assert 'tweets_posted' in report
        assert 'engagement_rate' in report
        mock_dependencies['storage'].get_daily_stats.assert_called_once()

    def test_configuration_hot_reload(self, mock_dependencies):
        """Test configuration hot reload functionality"""
        bot = TwitterBot()
        
        # Mock config change
        mock_dependencies['config'].get.side_effect = lambda key, default=None: {
            'posting.enabled': False,  # Changed from True to False
            'monitoring.enabled': True
        }.get(key, default)
        
        # Trigger config reload
        bot.on_config_changed()
        
        # Verify components are updated
        # In a real scenario, this would check if posting is disabled

    @pytest.mark.slow
    def test_full_bot_lifecycle(self, mock_dependencies):
        """Test complete bot lifecycle from start to shutdown"""
        bot = TwitterBot()
        
        # Mock all operations as successful
        mock_dependencies['twitter'].health_check.return_value = {'status': 'healthy'}
        mock_dependencies['storage'].health_check.return_value = {'status': 'healthy'}
        mock_dependencies['generator'].generate_tweet.return_value = {
            'content': 'Test tweet',
            'topics': ['test'],
            'image_url': None
        }
        mock_dependencies['twitter'].post_tweet.return_value = {
            'success': True,
            'tweet_id': '1234567890'
        }
        
        # Start bot
        with patch('main.start_health_server'):
            bot.start()
        
        # Simulate some operations
        bot.post_scheduled_tweet()
        bot.collect_tweet_stats()
        
        # Check health
        health = bot.get_health_status()
        assert health['overall_status'] in ['healthy', 'degraded']
        
        # Shutdown bot
        bot.shutdown()
        
        # Verify proper shutdown
        mock_dependencies['scheduler'].shutdown.assert_called_once()

    def test_concurrent_operations(self, mock_dependencies):
        """Test concurrent operations handling"""
        bot = TwitterBot()
        
        # Mock successful operations
        mock_dependencies['twitter'].like_tweet.return_value = {'success': True}
        mock_dependencies['storage'].update_reply.return_value = True
        
        # Simulate concurrent reply handling
        replies = [
            {'id': f'reply_{i}', 'author_id': f'user_{i}', 'original_tweet_id': '123', 'content': f'Reply {i}'}
            for i in range(5)
        ]
        
        # Process replies concurrently
        import threading
        threads = []
        for reply in replies:
            thread = threading.Thread(target=bot.handle_new_reply, args=(reply,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all replies were processed
        assert mock_dependencies['twitter'].like_tweet.call_count == 5

    def test_data_consistency(self, mock_dependencies):
        """Test data consistency across operations"""
        bot = TwitterBot()
        
        # Mock tweet posting and storage
        tweet_data = {
            'content': 'Test tweet',
            'topics': ['test'],
            'image_url': None
        }
        
        mock_dependencies['generator'].generate_tweet.return_value = tweet_data
        mock_dependencies['twitter'].post_tweet.return_value = {
            'success': True,
            'tweet_id': '1234567890'
        }
        mock_dependencies['storage'].store_tweet.return_value = {'id': 'stored_id'}
        
        # Post tweet
        result = bot.post_scheduled_tweet()
        
        # Verify data consistency
        assert result['success'] is True
        
        # Check that storage was called with correct data
        storage_call_args = mock_dependencies['storage'].store_tweet.call_args[0][0]
        assert storage_call_args['tweet_id'] == '1234567890'
        assert storage_call_args['content'] == tweet_data['content'] 