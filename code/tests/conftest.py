"""
Shared pytest fixtures and configuration for YACBA tests.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock
import json


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture
def test_data_dir():
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text("""
profiles:
  test:
    model_string: "gpt-4o"
    headless: false
""")
    return config_file


# ============================================================================
# Mock strands-agent-factory Components
# ============================================================================

@pytest.fixture
def mock_agent():
    """Mock AgentProxy from strands-agent-factory."""
    agent = Mock()
    agent.send_message_to_agent = AsyncMock(return_value=iter([
        {'type': 'text', 'content': 'Hello'}
    ]))
    agent.tool_specs = []
    agent.has_initial_messages = False
    agent.clear_messages = Mock()
    agent.__enter__ = Mock(return_value=agent)
    agent.__exit__ = Mock(return_value=None)
    return agent


@pytest.fixture
def mock_agent_factory():
    """Mock AgentFactory from strands-agent-factory."""
    factory = Mock()
    factory.initialize = AsyncMock()
    factory.create_agent = Mock()
    return factory


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def minimal_yacba_config():
    """Minimal valid YacbaConfig for testing."""
    from config import YacbaConfig
    
    return YacbaConfig(
        model_string="gpt-4o",
        tool_config_paths=[],
        startup_files_content=None,
        prompt_source="default",
        system_prompt="You are a test assistant",
        emulate_system_prompt=False,
        model_config=None,
        summarization_model_config=None,
        files_to_upload=[],
        max_files=10,
        tool_configs_dir=None,
        tool_discovery_result=None,
        session_name=None,
        agent_id=None,
        conversation_manager_type="sliding_window",
        sliding_window_size=40,
        preserve_recent_messages=10,
        summary_ratio=0.3,
        summarization_model=None,
        custom_summarization_prompt=None,
        should_truncate_results=True,
        headless=False,
        initial_message=None,
        show_tool_use=False,
        cli_prompt=None,
        response_prefix=None,
    )


@pytest.fixture
def full_yacba_config():
    """Fully populated YacbaConfig for testing."""
    from config import YacbaConfig
    
    return YacbaConfig(
        model_string="anthropic:claude-3-5-sonnet-20241022",
        tool_config_paths=[Path("./tools")],
        startup_files_content=None,
        prompt_source="cli",
        system_prompt="You are a test assistant",
        emulate_system_prompt=False,
        model_config="model_config.json",
        summarization_model_config="summ_config.json",
        files_to_upload=[("test.txt", "text/plain")],
        max_files=20,
        tool_configs_dir="./tools",
        tool_discovery_result=None,
        session_name="test_session",
        agent_id="test_agent",
        conversation_manager_type="summarizing",
        sliding_window_size=50,
        preserve_recent_messages=15,
        summary_ratio=0.25,
        summarization_model="gpt-3.5-turbo",
        custom_summarization_prompt="Summarize this",
        should_truncate_results=False,
        headless=True,
        initial_message="Test message",
        show_tool_use=True,
        cli_prompt="Test> ",
        response_prefix="AI: ",
    )


@pytest.fixture
def sample_model_config():
    """Sample model configuration dictionary."""
    return {
        "temperature": 0.7,
        "max_tokens": 2000,
        "top_p": 0.9,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
    }


# ============================================================================
# File Fixtures
# ============================================================================

@pytest.fixture
def sample_tool_config(tmp_path):
    """Create a sample tool configuration file."""
    tool_config = tmp_path / "tools.json"
    tool_config.write_text(json.dumps({
        "type": "python",
        "id": "test-tools",
        "module_path": "test_module",
        "functions": ["test_func"]
    }))
    return tool_config


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("This is test content.")
    return text_file


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_env(monkeypatch):
    """Provide clean environment without YACBA-specific vars."""
    env_vars = ['YACBA_CONFIG', 'YACBA_PROFILE', 'LOGURU_LEVEL']
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


@pytest.fixture
def mock_env_with_profile(monkeypatch):
    """Set up environment with a test profile."""
    monkeypatch.setenv('YACBA_PROFILE', 'test')
    return monkeypatch


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Mock repl-toolkit Components
# ============================================================================

@pytest.fixture
def mock_async_repl():
    """Mock AsyncREPL from repl-toolkit."""
    repl = Mock()
    repl.run = AsyncMock()
    return repl


@pytest.fixture
def mock_backend():
    """Mock Backend for testing actions."""
    backend = Mock()
    backend.agent = Mock()
    backend.agent.tool_specs = []
    backend.send_message = AsyncMock()
    return backend


# ============================================================================
# Completion Fixtures
# ============================================================================

@pytest.fixture
def mock_document():
    """Mock prompt_toolkit Document."""
    doc = Mock()
    doc.text = ""
    doc.text_before_cursor = ""
    doc.cursor_position = 0
    return doc


@pytest.fixture
def mock_complete_event():
    """Mock prompt_toolkit CompleteEvent."""
    return Mock()


# ============================================================================
# Configuration for pytest
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "asyncio: Async tests")


# ============================================================================
# Utilities
# ============================================================================

@pytest.fixture
def capture_logs(caplog):
    """Fixture to capture and analyze logs."""
    import logging
    caplog.set_level(logging.DEBUG)
    return caplog
