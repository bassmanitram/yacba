"""
Shared pytest configuration and fixtures for YACBA tests.

This file contains fixtures and configuration that are shared across
all test modules.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import pytest
import yaml


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing."""
    return {
        'default_profile': 'development',
        'defaults': {
            'conversation_manager': 'sliding_window',
            'window_size': 40,
            'max_files': 10
        },
        'profiles': {
            'development': {
                'model': 'litellm:gemini/gemini-1.5-flash',
                'system_prompt': 'You are a helpful development assistant.',
                'tool_configs_dir': '~/.yacba/tools/',
                'show_tool_use': True
            },
            'production': {
                'model': 'openai:gpt-4',
                'system_prompt': 'You are a production assistant.',
                'tool_configs_dir': '~/.yacba/tools/production/',
                'show_tool_use': False,
                'conversation_manager': 'summarizing',
                'session': 'prod-session'
            },
            'coding': {
                'inherits': 'development',
                'model': 'anthropic:claude-3-sonnet',
                'system_prompt': 'You are an expert programmer.',
                'max_files': 50
            }
        }
    }


@pytest.fixture
def sample_model_config():
    """Sample model configuration for testing."""
    return {
        'temperature': 0.7,
        'max_tokens': 2048,
        'top_p': 0.95,
        'frequency_penalty': 0.0,
        'presence_penalty': 0.0
    }


@pytest.fixture 
def sample_files_for_upload(temp_dir):
    """Create sample files for upload testing."""
    files = {}
    
    # Create text file
    text_file = temp_dir / "sample.txt"
    text_file.write_text("This is a sample text file for testing.")
    files['text'] = str(text_file)
    
    # Create Python file
    py_file = temp_dir / "script.py"
    py_file.write_text("#!/usr/bin/env python3\nprint('Hello, World!')")
    files['python'] = str(py_file)
    
    # Create config file
    config_file = temp_dir / "config.yaml"
    config_file.write_text("key: value\nlist:\n  - item1\n  - item2")
    files['yaml'] = str(config_file)
    
    return files


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        'YACBA_MODEL_ID': 'litellm:gemini/gemini-2.5-flash',
        'YACBA_SYSTEM_PROMPT': 'Environment system prompt',
        'YACBA_SESSION_NAME': 'env-session',
        'HOME': '/home/testuser',
        'PROJECT_NAME': 'test-project'
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def config_file_with_profiles(temp_dir, sample_config_data):
    """Create a config file with profiles for testing."""
    config_file = temp_dir / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(sample_config_data, f)
    return config_file


@pytest.fixture
def model_config_file(temp_dir, sample_model_config):
    """Create a model config file for testing."""
    model_file = temp_dir / "model.json"
    import json
    with open(model_file, 'w') as f:
        json.dump(sample_model_config, f)
    return model_file


@pytest.fixture
def system_prompt_file(temp_dir):
    """Create a system prompt file for testing."""
    prompt_file = temp_dir / "system_prompt.txt"
    prompt_file.write_text("This is a system prompt loaded from a file.")
    return prompt_file


@pytest.fixture
def initial_message_file(temp_dir):
    """Create an initial message file for testing."""
    message_file = temp_dir / "initial_message.txt"
    message_file.write_text("This is an initial message loaded from a file.")
    return message_file


# Test data constants for validation testing
VALID_MODEL_STRINGS = [
    'litellm:gemini/gemini-1.5-flash',
    'openai:gpt-4',
    'anthropic:claude-3-sonnet',
    'bedrock:anthropic.claude-3-sonnet-20240229-v1:0',
    'gemini-1.5-flash',  # shorthand
    'gpt-4',             # shorthand
    'claude-3-sonnet'    # shorthand
]

INVALID_MODEL_STRINGS = [
    '',
    ':',
    'framework:',
    ':model',
    'invalid',
    'framework::model',
    None
]

VALID_BOOL_VALUES = [
    (True, True),
    (False, False),
    ('true', True),
    ('True', True),
    ('TRUE', True),
    ('false', False),
    ('False', False),
    ('FALSE', False),
    ('1', True),
    ('0', False),
    ('yes', True),
    ('no', False)
]

INVALID_BOOL_VALUES = [
    'maybe',
    'invalid',
    '2',
    '-1',
    'on',
    'off'
]