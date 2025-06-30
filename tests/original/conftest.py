import pytest
import os
import tempfile
import json
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Test configuration
TEST_CONFIG = {
    "x_api": {
        "plan": "basic",
        "quotas": {
            "basic": {"monthly_posts": 1500, "monthly_reads": 50000},
            "pro": {"monthly_posts": 50000, "monthly_reads": 2000000},
            "enterprise": {"monthly_posts": -1, "monthly_reads": -1}
        }
    },
    "posting": {
        "enabled": True,
        "schedule": {
            "start_hour": 9,
            "end_hour": 21,
            "posts_per_day": 5
        }
    },
    "engagement": {
        "auto_like_replies": True,
        "max_likes_per_hour": 100
    },
    "content": {
        "generate_images": False,
        "topics": ["tech", "ai", "startup"],
        "avoid_repetition_hours": 24
    },
    "monitoring": {
        "enabled": True,
        "health_check_port": 8000,
        "daily_reports": True
    }
}

TEST_ENV = {
    "X_API_KEY": "test_api_key",
    "X_API_SECRET": "test_api_secret",
    "X_ACCESS_TOKEN": "test_access_token",
    "X_ACCESS_TOKEN_SECRET": "test_access_token_secret",
    "X_BEARER_TOKEN": "test_bearer_token",
    "OPENAI_API_KEY": "test_openai_key",
    "SUPABASE_URL": "https://test.supabase.co",
    "SUPABASE_KEY": "test_supabase_key",
    "LOG_LEVEL": "DEBUG",
    "ENVIRONMENT": "test"
}

@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def test_config_file(temp_dir):
    """Create test configuration file"""
    config_path = temp_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(TEST_CONFIG, f, indent=2)
    return config_path

@pytest.fixture
def test_env(monkeypatch):
    """Set test environment variables"""
    for key, value in TEST_ENV.items():
        monkeypatch.setenv(key, value)
    return TEST_ENV

@pytest.fixture
def mock_tweepy_client():
    """Mock Tweepy client"""
    client = Mock()
    client.create_tweet.return_value = {
        'data': {'id': '1234567890', 'text': 'Test tweet'}
    }
    client.like.return_value = {'data': {'liked': True}}
    client.get_tweet.return_value = {
        'data': {
            'id': '1234567890',
            'text': 'Test tweet',
            'public_metrics': {
                'like_count': 10,
                'retweet_count': 5,
                'reply_count': 2,
                'impression_count': 100
            }
        }
    }
    client.get_users_mentions.return_value = {
        'data': [
            {
                'id': '9876543210',
                'text': '@testbot Great tweet!',
                'author_id': '1111111111',
                'in_reply_to_user_id': '1234567890'
            }
        ]
    }
    return client

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Generated test tweet content"))]
    )
    client.images.generate.return_value = Mock(
        data=[Mock(url="https://example.com/generated-image.jpg")]
    )
    return client

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    client = Mock()
    
    # Mock table operations
    table_mock = Mock()
    table_mock.insert.return_value = Mock(execute=Mock(return_value=Mock(data=[{'id': '123'}])))
    table_mock.select.return_value = Mock(execute=Mock(return_value=Mock(data=[])))
    table_mock.update.return_value = Mock(execute=Mock(return_value=Mock(data=[{'id': '123'}])))
    table_mock.delete.return_value = Mock(execute=Mock(return_value=Mock(data=[])))
    
    client.table.return_value = table_mock
    
    # Mock storage operations
    storage_mock = Mock()
    storage_mock.upload.return_value = Mock(path="test/image.jpg")
    storage_mock.get_public_url.return_value = Mock(public_url="https://example.com/image.jpg")
    client.storage.from_.return_value = storage_mock
    
    # Mock realtime
    realtime_mock = Mock()
    realtime_mock.on.return_value = realtime_mock
    realtime_mock.subscribe.return_value = None
    client.realtime.channel.return_value = realtime_mock
    
    return client

@pytest.fixture
def mock_apscheduler():
    """Mock APScheduler"""
    scheduler = Mock()
    scheduler.start.return_value = None
    scheduler.shutdown.return_value = None
    scheduler.add_job.return_value = None
    scheduler.remove_job.return_value = None
    scheduler.get_jobs.return_value = []
    return scheduler

@pytest.fixture
def sample_tweet_data():
    """Sample tweet data for testing"""
    return {
        'id': '1234567890',
        'text': 'This is a test tweet #AI #tech',
        'created_at': '2024-01-01T10:00:00.000Z',
        'author_id': '1111111111',
        'public_metrics': {
            'like_count': 10,
            'retweet_count': 5,
            'reply_count': 2,
            'impression_count': 100
        }
    }

@pytest.fixture
def sample_reply_data():
    """Sample reply data for testing"""
    return {
        'id': '9876543210',
        'text': '@testbot Great tweet!',
        'created_at': '2024-01-01T10:05:00.000Z',
        'author_id': '2222222222',
        'in_reply_to_user_id': '1234567890',
        'referenced_tweets': [
            {'type': 'replied_to', 'id': '1234567890'}
        ]
    }

@pytest.fixture
def sample_stats_data():
    """Sample statistics data for testing"""
    return {
        'tweet_id': '1234567890',
        'likes': 10,
        'retweets': 5,
        'replies': 2,
        'impressions': 100,
        'collected_at': '2024-01-01T11:00:00.000Z'
    }

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )

# Test utilities
class MockResponse:
    """Mock HTTP response"""
    def __init__(self, json_data, status_code=200):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

# Test data cleanup
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Cleanup test data after each test"""
    yield
    # Cleanup logic here if needed 