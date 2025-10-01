"""
Tests for template variable substitution functionality.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from core.config.file_loader import ConfigFileLoader


class TestVariableSubstitution:
    """Test template variable substitution."""

    def test_substitute_simple_variables(self):
        """Test basic variable substitution."""
        settings = {
            "model": "gpt-4",
            "system_prompt": "Hello ${USER}!",
            "config_path": "${HOME}/.yacba/config"
        }
        
        with patch.dict(os.environ, {'USER': 'testuser', 'HOME': '/home/testuser'}):
            result = ConfigFileLoader.substitute_variables(settings)
        
        expected = {
            "model": "gpt-4",
            "system_prompt": "Hello testuser!",
            "config_path": "/home/testuser/.yacba/config"
        }
        assert result == expected

    def test_substitute_nested_structures(self):
        """Test variable substitution in nested dictionaries and lists."""
        settings = {
            "model_config": {
                "temperature": 0.7,
                "api_key": "${API_KEY}",
                "endpoints": ["${BASE_URL}/v1", "${BASE_URL}/v2"]
            },
            "tools": ["${HOME}/tools", "${PROJECT_NAME}/local-tools"]
        }
        
        env_vars = {
            'API_KEY': 'secret123',
            'BASE_URL': 'https://api.example.com',
            'HOME': '/home/user',
            'PROJECT_NAME': 'myproject'
        }
        
        with patch.dict(os.environ, env_vars):
            result = ConfigFileLoader.substitute_variables(settings)
        
        expected = {
            "model_config": {
                "temperature": 0.7,
                "api_key": "secret123",
                "endpoints": ["https://api.example.com/v1", "https://api.example.com/v2"]
            },
            "tools": ["/home/user/tools", "myproject/local-tools"]
        }
        assert result == expected

    def test_substitute_default_variables(self):
        """Test substitution with default variables (PROJECT_NAME, USER_HOME)."""
        settings = {
            "project": "${PROJECT_NAME}",
            "home": "${USER_HOME}"
        }
        
        # Mock Path.cwd() and Path.home()
        with patch('pathlib.Path.cwd', return_value=Path('/current/project')):
            with patch('pathlib.Path.home', return_value=Path('/home/user')):
                result = ConfigFileLoader.substitute_variables(settings)
        
        expected = {
            "project": "project",  # Last part of current directory
            "home": "/home/user"
        }
        assert result == expected

    def test_substitute_missing_variables(self):
        """Test substitution with missing environment variables."""
        settings = {
            "existing": "${HOME}",
            "missing": "${NONEXISTENT_VAR}",
            "partial": "prefix-${ALSO_MISSING}-suffix"
        }
        
        with patch.dict(os.environ, {'HOME': '/home/user'}, clear=True):
            result = ConfigFileLoader.substitute_variables(settings)
        
        # Missing variables should be left as-is (safe_substitute)
        expected = {
            "existing": "/home/user",
            "missing": "${NONEXISTENT_VAR}",
            "partial": "prefix-${ALSO_MISSING}-suffix"
        }
        assert result == expected

    def test_substitute_no_variables(self):
        """Test substitution with no variables present."""
        settings = {
            "model": "gpt-4",
            "temperature": 0.7,
            "tools": ["tool1", "tool2"],
            "nested": {"key": "value"}
        }
        
        result = ConfigFileLoader.substitute_variables(settings)
        
        # Should return identical structure
        assert result == settings
        # Should be a copy, not the same object
        assert result is not settings

    def test_substitute_complex_patterns(self):
        """Test substitution with complex variable patterns."""
        settings = {
            "mixed": "Start ${VAR1} middle ${VAR2} end",
            "repeated": "${VAR1}-${VAR1}",
            "escaped": "Not a variable: first",  # Note: Template doesn't escape $$ by default
            "empty": "${EMPTY_VAR}",
            "numbers": "${VAR_123}"
        }
        
        env_vars = {
            'VAR1': 'first',
            'VAR2': 'second', 
            'EMPTY_VAR': '',
            'VAR_123': 'numbered'
        }
        
        with patch.dict(os.environ, env_vars):
            result = ConfigFileLoader.substitute_variables(settings)
        
        expected = {
            "mixed": "Start first middle second end",
            "repeated": "first-first",
            "escaped": "Not a variable: first",  # $$ would remain as $$
            "empty": "",
            "numbers": "numbered"
        }
        assert result == expected

    def test_substitute_recursive_protection(self):
        """Test that substitution handles non-string types correctly."""
        settings = {
            "string": "${HOME}",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": ["${HOME}", 123, None],
            "dict": {"path": "${HOME}", "count": 5}
        }
        
        with patch.dict(os.environ, {'HOME': '/home/user'}):
            result = ConfigFileLoader.substitute_variables(settings)
        
        expected = {
            "string": "/home/user",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "none": None,
            "list": ["/home/user", 123, None],
            "dict": {"path": "/home/user", "count": 5}
        }
        assert result == expected

    @patch('core.config.file_loader.logger')
    def test_substitute_invalid_template(self, mock_logger):
        """Test handling of invalid template syntax."""
        settings = {
            "valid": "${HOME}",
            "invalid": "${INVALID{SYNTAX}",  # Invalid template syntax
        }
        
        with patch.dict(os.environ, {'HOME': '/home/user'}):
            result = ConfigFileLoader.substitute_variables(settings)
        
        # Should substitute valid ones and leave invalid as-is
        expected = {
            "valid": "/home/user", 
            "invalid": "${INVALID{SYNTAX}"  # Left unchanged
        }
        assert result == expected
        
