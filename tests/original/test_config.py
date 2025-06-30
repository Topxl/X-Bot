import pytest
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from config import ConfigManager, ConfigError


class TestConfigManager:
    """Test cases for ConfigManager"""

    def test_init_with_valid_config(self, test_config_file, test_env):
        """Test initialization with valid config file"""
        with patch('config.create_client') as mock_supabase:
            mock_supabase.return_value = Mock()
            config = ConfigManager(str(test_config_file))
            assert config.get('x_api.plan') == 'basic'
            assert config.get('posting.enabled') is True

    def test_init_with_missing_config_file(self, test_env):
        """Test initialization with missing config file"""
        with pytest.raises(ConfigError):
            ConfigManager('nonexistent.json')

    def test_init_with_invalid_json(self, temp_dir, test_env):
        """Test initialization with invalid JSON"""
        invalid_config = temp_dir / "invalid.json"
        invalid_config.write_text("{ invalid json }")
        
        with pytest.raises(ConfigError):
            ConfigManager(str(invalid_config))

    def test_get_nested_config(self, test_config_file, test_env):
        """Test getting nested configuration values"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            assert config.get('x_api.quotas.basic.monthly_posts') == 1500
            assert config.get('posting.schedule.start_hour') == 9

    def test_get_with_default_value(self, test_config_file, test_env):
        """Test getting non-existent key with default value"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            assert config.get('nonexistent.key', 'default') == 'default'
            assert config.get('nonexistent.key') is None

    def test_set_config_value(self, test_config_file, test_env):
        """Test setting configuration values"""
        with patch('config.create_client') as mock_supabase:
            mock_client = Mock()
            mock_supabase.return_value = mock_client
            
            config = ConfigManager(str(test_config_file))
            config.set('new.setting', 'test_value')
            
            assert config.get('new.setting') == 'test_value'

    def test_validate_config(self, test_config_file, test_env):
        """Test configuration validation"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            # Should not raise any errors for valid config
            config._validate_config()

    def test_validate_invalid_config(self, temp_dir, test_env):
        """Test validation with invalid configuration"""
        invalid_config = {
            "x_api": {
                "plan": "invalid_plan"  # Invalid plan
            }
        }
        config_path = temp_dir / "invalid_config.json"
        with open(config_path, 'w') as f:
            json.dump(invalid_config, f)
        
        with patch('config.create_client'):
            with pytest.raises(ConfigError):
                ConfigManager(str(config_path))

    def test_reload_config(self, test_config_file, test_env):
        """Test configuration reload"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            original_value = config.get('posting.enabled')
            
            # Modify config file
            with open(test_config_file, 'r') as f:
                data = json.load(f)
            data['posting']['enabled'] = not original_value
            with open(test_config_file, 'w') as f:
                json.dump(data, f)
            
            config.reload()
            assert config.get('posting.enabled') == (not original_value)

    @patch('config.create_client')
    def test_sync_with_supabase(self, mock_supabase, test_config_file, test_env):
        """Test syncing configuration with Supabase"""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        mock_supabase.return_value = mock_client
        
        # Mock successful sync
        mock_table.upsert.return_value = Mock(
            execute=Mock(return_value=Mock(data=[]))
        )
        
        config = ConfigManager(str(test_config_file))
        config._sync_with_supabase()
        
        # Verify upsert was called
        mock_table.upsert.assert_called()

    @patch('config.create_client')
    def test_sync_with_supabase_failure(self, mock_supabase, test_config_file, test_env):
        """Test handling Supabase sync failures"""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        mock_supabase.return_value = mock_client
        
        # Mock sync failure
        mock_table.upsert.side_effect = Exception("Supabase error")
        
        config = ConfigManager(str(test_config_file))
        # Should not raise exception, just log error
        config._sync_with_supabase()

    def test_quota_calculations(self, test_config_file, test_env):
        """Test quota-related calculations"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            
            # Test basic plan quotas
            assert config.get_monthly_post_quota() == 1500
            assert config.get_monthly_read_quota() == 50000
            
            # Test daily calculations
            daily_posts = config.get_daily_post_quota()
            assert daily_posts == 1500 // 30  # Approximately

    def test_posting_schedule_validation(self, test_config_file, test_env):
        """Test posting schedule validation"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            
            schedule = config.get('posting.schedule')
            assert schedule['start_hour'] < schedule['end_hour']
            assert schedule['posts_per_day'] > 0

    def test_environment_variable_override(self, test_env):
        """Test that environment variables are properly loaded"""
        with patch('config.create_client'):
            # Test environment variables are accessible
            assert test_env['X_API_KEY'] == 'test_api_key'
            assert test_env['OPENAI_API_KEY'] == 'test_openai_key'

    def test_singleton_pattern(self, test_config_file, test_env):
        """Test that ConfigManager follows singleton pattern"""
        with patch('config.create_client'):
            config1 = ConfigManager(str(test_config_file))
            config2 = ConfigManager()  # Should return same instance
            assert config1 is config2

    def test_hot_reload_callback(self, test_config_file, test_env):
        """Test hot reload callback functionality"""
        callback_called = False
        
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            config.add_reload_callback(test_callback)
            config.reload()
            
            assert callback_called

    def test_config_schema_validation(self, temp_dir, test_env):
        """Test configuration schema validation"""
        # Test with missing required fields
        incomplete_config = {"x_api": {}}
        config_path = temp_dir / "incomplete.json"
        with open(config_path, 'w') as f:
            json.dump(incomplete_config, f)
        
        with patch('config.create_client'):
            with pytest.raises(ConfigError):
                ConfigManager(str(config_path))

    def test_config_backup_and_restore(self, test_config_file, test_env):
        """Test configuration backup and restore functionality"""
        with patch('config.create_client'):
            config = ConfigManager(str(test_config_file))
            
            # Create backup
            backup_data = config.backup()
            assert 'x_api' in backup_data
            assert 'posting' in backup_data
            
            # Modify config
            config.set('test.key', 'test_value')
            
            # Restore from backup
            config.restore(backup_data)
            assert config.get('test.key') is None 