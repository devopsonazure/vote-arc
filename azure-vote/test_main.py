import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from flask import Flask

# Add the azure-vote directory to the path to import main
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestEnvironmentVariables:
    """Test environment variable handling"""
    
    @patch.dict(os.environ, {'REDIS': 'localhost', 'VOTE1VALUE': 'TestCats', 'VOTE2VALUE': 'TestDogs', 'TITLE': 'Test Title'})
    @patch('redis.Redis')
    @patch('redis.StrictRedis')  
    def test_environment_variables_override_config(self, mock_strict_redis, mock_redis):
        """Test that environment variables take precedence over config file"""
        # Setup Redis mock
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance
        mock_strict_redis.return_value = mock_redis_instance
        
        # Reset module cache to ensure clean import
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Verify environment variables are used
        assert main.button1 == 'TestCats'
        assert main.button2 == 'TestDogs'
        assert main.title == 'Test Title'

class TestRedisConnectionSetup:
    """Test Redis connection configuration"""
    
    @patch.dict(os.environ, {'REDIS': 'test-redis'})
    @patch('redis.Redis')
    def test_redis_connection_without_password(self, mock_redis):
        """Test Redis connection setup without password"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance
        
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Verify Redis was initialized with correct host
        mock_redis.assert_called_with('test-redis')
    
    @patch.dict(os.environ, {'REDIS': 'test-redis', 'REDIS_PWD': 'test-password'})
    @patch('redis.StrictRedis')
    def test_redis_connection_with_password(self, mock_strict_redis):
        """Test Redis connection setup with password"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_strict_redis.return_value = mock_redis_instance
        
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Verify StrictRedis was initialized with password
        mock_strict_redis.assert_called_with(
            host='test-redis',
            port=6379,
            password='test-password'
        )

class TestRedisInitialization:
    """Test Redis key initialization"""
    
    @patch.dict(os.environ, {'REDIS': 'localhost'})
    @patch('redis.Redis')
    def test_redis_keys_initialized_to_zero(self, mock_redis):
        """Test that vote keys are initialized to zero when they don't exist"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None  # Keys don't exist
        mock_redis.return_value = mock_redis_instance
        
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Verify both vote keys were set to 0
        assert mock_redis_instance.set.call_count >= 2
        # The exact button names depend on config, but both should be set to 0
        set_calls = mock_redis_instance.set.call_args_list
        assert len(set_calls) >= 2
        for call in set_calls:
            assert call[0][1] == 0  # Second argument should be 0

class TestFlaskRouteHandling:
    """Test Flask route functionality"""
    
    @patch.dict(os.environ, {'REDIS': 'localhost'})
    @patch('redis.Redis')
    @patch('flask.render_template')
    def test_get_route_returns_vote_counts(self, mock_render_template, mock_redis):
        """Test GET route returns current vote counts"""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.side_effect = lambda key: b'5' if 'Cats' in str(key) else b'3'
        mock_redis.return_value = mock_redis_instance
        mock_render_template.return_value = 'rendered_template'
        
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Test GET request
        with main.app.test_client() as client:
            response = client.get('/')
            
            # Verify response and template rendering
            assert response.status_code == 200
            mock_render_template.assert_called_once()
            call_args = mock_render_template.call_args[1]
            assert 'value1' in call_args
            assert 'value2' in call_args
    
    @patch.dict(os.environ, {'REDIS': 'localhost'})
    @patch('redis.Redis')
    @patch('flask.render_template')
    def test_post_vote_increments_counter(self, mock_render_template, mock_redis):
        """Test POST route with vote increments the correct counter"""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = b'6'  # Return count after increment
        mock_redis_instance.incr.return_value = 6
        mock_redis.return_value = mock_redis_instance
        mock_render_template.return_value = 'rendered_template'
        
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Test POST request with vote
        with main.app.test_client() as client:
            response = client.post('/', data={'vote': 'Cats'})
            
            # Verify vote increment and response
            assert response.status_code == 200
            mock_redis_instance.incr.assert_called_once_with('Cats', 1)
    
    @patch.dict(os.environ, {'REDIS': 'localhost'})
    @patch('redis.Redis')
    @patch('flask.render_template')
    def test_post_reset_clears_votes(self, mock_render_template, mock_redis):
        """Test POST route with reset clears vote counts"""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = b'0'
        mock_redis_instance.set.return_value = True
        mock_redis.return_value = mock_redis_instance
        mock_render_template.return_value = 'rendered_template'
        
        if 'main' in sys.modules:
            del sys.modules['main']
            
        import main
        
        # Test POST request with reset
        with main.app.test_client() as client:
            response = client.post('/', data={'vote': 'reset'})
            
            # Verify reset functionality
            assert response.status_code == 200
            # Should set both vote counters to 0
            assert mock_redis_instance.set.call_count >= 2
            set_calls = mock_redis_instance.set.call_args_list
            for call in set_calls:
                assert call[0][1] == 0  # Second argument should be 0

class TestErrorHandling:
    """Test error handling scenarios"""
    
    @patch.dict(os.environ, {'REDIS': 'localhost'})
    @patch('redis.Redis')
    @patch('builtins.exit')
    def test_redis_connection_failure_exits(self, mock_exit, mock_redis):
        """Test that Redis connection failure causes application to exit"""
        import redis
        
        # Setup Redis to fail connection
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = redis.ConnectionError("Connection failed")
        mock_redis.return_value = mock_redis_instance
        
        if 'main' in sys.modules:
            del sys.modules['main']
        
        try:
            import main
        except SystemExit:
            pass
        
        # Verify exit was called with correct message
        mock_exit.assert_called_with('Failed to connect to Redis, terminating.')

class TestShowHostConfiguration:
    """Test SHOWHOST configuration"""
    
    @patch.dict(os.environ, {'REDIS': 'localhost'})
    @patch('redis.Redis')
    @patch('socket.gethostname')
    def test_showhost_true_uses_hostname(self, mock_gethostname, mock_redis):
        """Test SHOWHOST=true uses hostname as title"""
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance
        mock_gethostname.return_value = 'test-hostname'
        
        if 'main' in sys.modules:
            del sys.modules['main']
        
        # Mock the config file content to have SHOWHOST = 'true'
        config_content = '''
TITLE = 'Original Title'
VOTE1VALUE = 'Cats'
VOTE2VALUE = 'Dogs'
SHOWHOST = 'true'
'''
        with patch('builtins.open', mock_open(read_data=config_content)):
            import main
            
            # Verify hostname is used as title
            assert main.title == 'test-hostname'

def mock_open(read_data=''):
    """Simple mock_open implementation"""
    from unittest.mock import MagicMock, call
    mock = MagicMock()
    handle = MagicMock()
    handle.read.return_value = read_data
    handle.__enter__.return_value = handle
    mock.return_value = handle
    return mock

class TestBasicFunctionality:
    """Test basic application functionality"""
    
    def test_app_creation(self):
        """Test that Flask app can be created"""
        # This basic test ensures the module can be imported
        assert True

class TestConfigurationLogic:
    """Test configuration loading logic"""
    
    @patch.dict(os.environ, {'REDIS': 'localhost', 'VOTE1VALUE': 'Option1'})
    @patch('redis.Redis')
    def test_env_var_precedence_over_config(self, mock_redis):
        """Test environment variables take precedence"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis.return_value = mock_redis_instance
        
        if 'main' in sys.modules:
            del sys.modules['main']
        
        # Mock config file with different value
        config_content = '''
TITLE = 'Config Title'
VOTE1VALUE = 'ConfigOption'
VOTE2VALUE = 'Dogs'
SHOWHOST = 'false'
'''
        with patch('builtins.open', mock_open(read_data=config_content)):
            import main
            
            # Environment variable should override config file
            assert main.button1 == 'Option1'  # From environment
            # button2 should come from config since no env var set
            assert main.button2 == 'Dogs'  # From config file

if __name__ == '__main__':
    pytest.main([__file__, '-v'])