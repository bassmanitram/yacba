"""
Tests for core.config.dataclass module.

Tests the YacbaConfig dataclass including validation methods,
property methods, and error handling.
"""

import pytest
from typing import List

from core.config.dataclass import YacbaConfig
from yacba_types.config import ToolConfig, FileUpload, ToolDiscoveryResult


class TestYacbaConfigValidation:
    """Test validation methods in YacbaConfig."""

    def test_valid_config_creation(self):
        """Test creating a valid YacbaConfig instance."""
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None
        )
        
        assert config.model_string == "litellm:gemini/gemini-1.5-flash"
        assert config.system_prompt == "Test prompt"
        assert config.prompt_source == "test"
        assert config.tool_configs == []
        assert config.startup_files_content is None

    def test_max_files_validation_valid(self):
        """Test max_files validation with valid values."""
        # Test valid values
        for max_files in [1, 10, 100, 1000]:
            config = YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                max_files=max_files
            )
            assert config.max_files == max_files

    def test_max_files_validation_invalid(self):
        """Test max_files validation with invalid values."""
        # Test too small
        with pytest.raises(ValueError, match="max_files must be at least 1"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                max_files=0
            )
        
        # Test too large
        with pytest.raises(ValueError, match="max_files cannot exceed 1000"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                max_files=1001
            )

    def test_files_to_upload_truncation(self):
        """Test that files_to_upload gets truncated to max_files."""
        # Create more files than max_files
        files = [
            FileUpload(path=f"/test/file{i}.txt", mimetype="text/plain", size=100)
            for i in range(15)
        ]
        
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            max_files=10,
            files_to_upload=files
        )
        
        assert len(config.files_to_upload) == 10
        assert config.files_to_upload == files[:10]

    def test_conversation_manager_validation_valid(self):
        """Test conversation manager validation with valid values."""
        valid_configs = [
            # sliding_window mode
            {
                'conversation_manager_type': 'sliding_window',
                'sliding_window_size': 40,
                'preserve_recent_messages': 10
            },
            # summarizing mode
            {
                'conversation_manager_type': 'summarizing',
                'sliding_window_size': 40,
                'preserve_recent_messages': 10,
                'summary_ratio': 0.3
            },
            # null mode
            {
                'conversation_manager_type': 'null',
                'sliding_window_size': 40,
                'preserve_recent_messages': 10
            }
        ]
        
        for conv_config in valid_configs:
            config = YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                **conv_config
            )
            assert config.conversation_manager_type == conv_config['conversation_manager_type']

    def test_conversation_manager_validation_invalid_window_size(self):
        """Test conversation manager validation with invalid window sizes."""
        # Window size too small
        with pytest.raises(ValueError, match="sliding_window_size must be at least 1"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                sliding_window_size=0
            )
        
        # Window size too large
        with pytest.raises(ValueError, match="sliding_window_size cannot exceed 1000"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                sliding_window_size=1001
            )

    def test_conversation_manager_validation_invalid_preserve_recent(self):
        """Test conversation manager validation with invalid preserve_recent values."""
        # preserve_recent too small
        with pytest.raises(ValueError, match="preserve_recent_messages must be at least 1"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                preserve_recent_messages=0
            )
        
        # preserve_recent too large for summarizing mode
        with pytest.raises(ValueError, match="preserve_recent_messages cannot exceed 100"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                conversation_manager_type='summarizing',
                preserve_recent_messages=101
            )

    def test_summary_ratio_validation(self):
        """Test summary_ratio validation."""
        # Valid ratios
        for ratio in [0.1, 0.3, 0.5, 0.8]:
            config = YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                summary_ratio=ratio
            )
            assert config.summary_ratio == ratio
        
        # Invalid ratios
        for ratio in [0.0, 0.05, 0.9, 1.0]:
            with pytest.raises(ValueError, match="summary_ratio must be between 0.1 and 0.8"):
                YacbaConfig(
                    model_string="litellm:gemini/gemini-1.5-flash",
                    system_prompt="Test prompt",
                    prompt_source="test",
                    tool_configs=[],
                    startup_files_content=None,
                    summary_ratio=ratio
                )

    def test_summarization_model_validation(self):
        """Test summarization_model validation."""
        # Valid model strings (with framework:model format)
        valid_models = [
            "litellm:gemini/gemini-1.5-flash",
            "openai:gpt-4",
            "anthropic:claude-3-haiku"
        ]
        
        for model in valid_models:
            config = YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                summarization_model=model
            )
            assert config.summarization_model == model
        
        # Single-word models should pass (will be processed by framework detection)
        single_word_models = ["gpt-4", "claude-3-haiku", "gemini-flash"]
        for model in single_word_models:
            config = YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                summarization_model=model
            )
            assert config.summarization_model == model
        
        # Invalid model strings (with colon but missing parts)
        invalid_models = [
            ":",
            "framework:",
            ":model"
        ]
        
        for model in invalid_models:
            with pytest.raises(ValueError, match="Invalid summarization_model format"):
                YacbaConfig(
                    model_string="litellm:gemini/gemini-1.5-flash",
                    system_prompt="Test prompt",
                    prompt_source="test",
                    tool_configs=[],
                    startup_files_content=None,
                    summarization_model=model
                )

    def test_headless_mode_validation(self):
        """Test headless mode validation."""
        # Valid: headless with initial_message
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            headless=True,
            initial_message="Test message"
        )
        assert config.headless is True
        assert config.initial_message == "Test message"
        
        # Valid: not headless without initial_message
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            headless=False
        )
        assert config.headless is False
        
        # Invalid: headless without initial_message
        with pytest.raises(ValueError, match="Headless mode requires an initial message"):
            YacbaConfig(
                model_string="litellm:gemini/gemini-1.5-flash",
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None,
                headless=True
            )


class TestYacbaConfigProperties:
    """Test property methods in YacbaConfig."""

    def test_framework_name_property(self):
        """Test framework_name property extraction."""
        test_cases = [
            ("litellm:gemini/gemini-1.5-flash", "litellm"),
            ("openai:gpt-4", "openai"),
            ("anthropic:claude-3-sonnet", "anthropic"),
            ("bedrock:anthropic.claude-3-sonnet-20240229-v1:0", "bedrock"),
            ("gemini-1.5-flash", "litellm"),  # Default when no colon
            ("gpt-4", "litellm")  # Default when no colon
        ]
        
        for model_string, expected_framework in test_cases:
            config = YacbaConfig(
                model_string=model_string,
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None
            )
            assert config.framework_name == expected_framework

    def test_model_name_property(self):
        """Test model_name property extraction."""
        test_cases = [
            ("litellm:gemini/gemini-1.5-flash", "gemini/gemini-1.5-flash"),
            ("openai:gpt-4", "gpt-4"),
            ("anthropic:claude-3-sonnet", "claude-3-sonnet"),
            ("bedrock:anthropic.claude-3-sonnet-20240229-v1:0", "anthropic.claude-3-sonnet-20240229-v1:0"),
            ("gemini-1.5-flash", "gemini-1.5-flash"),  # No colon case
            ("gpt-4", "gpt-4")  # No colon case
        ]
        
        for model_string, expected_model in test_cases:
            config = YacbaConfig(
                model_string=model_string,
                system_prompt="Test prompt",
                prompt_source="test",
                tool_configs=[],
                startup_files_content=None
            )
            assert config.model_name == expected_model

    def test_boolean_properties(self):
        """Test boolean property methods."""
        # Test is_interactive
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            headless=False
        )
        assert config.is_interactive is True
        
        config.headless = True
        config.initial_message = "Test"
        assert config.is_interactive is False
        
        # Test has_session
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None
        )
        assert config.has_session is False
        
        config.session_name = "test_session"
        assert config.has_session is True
        
        # Test has_startup_files
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None
        )
        assert config.has_startup_files is False
        
        config.files_to_upload = [FileUpload(path="/test.txt", mimetype="text/plain", size=100)]
        assert config.has_startup_files is True

    def test_conversation_manager_properties(self):
        """Test conversation manager property methods."""
        # Test uses_conversation_manager
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            conversation_manager_type="null"
        )
        assert config.uses_conversation_manager is False
        
        config.conversation_manager_type = "sliding_window"
        assert config.uses_conversation_manager is True
        
        # Test uses_sliding_window
        assert config.uses_sliding_window is True
        assert config.uses_summarizing is False
        
        # Test uses_summarizing
        config.conversation_manager_type = "summarizing"
        assert config.uses_sliding_window is False
        assert config.uses_summarizing is True


class TestYacbaConfigDefaults:
    """Test default values in YacbaConfig."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None
        )
        
        # Test defaults
        assert config.headless is False
        assert config.model_config == {}
        assert config.session_name is None
        assert config.agent_id is None
        assert config.emulate_system_prompt is False
        assert config.show_tool_use is False
        assert config.initial_message is None
        assert config.max_files == 20
        assert config.files_to_upload == []
        assert config.tool_discovery_result is None
        assert config.conversation_manager_type == "sliding_window"
        assert config.sliding_window_size == 40
        assert config.preserve_recent_messages == 10
        assert config.summary_ratio == 0.3
        assert config.summarization_model is None
        assert config.custom_summarization_prompt is None
        assert config.should_truncate_results is True
        assert config.clear_cache is False
        assert config.show_perf_stats is False
        assert config.disable_cache is False


class TestYacbaConfigWithComplexData:
    """Test YacbaConfig with more complex data structures."""

    def test_with_tool_configs(self):
        """Test YacbaConfig with tool configurations."""
        ]
        
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=tool_configs,
            startup_files_content=None
        )
        
        assert len(config.tool_configs) == 1
        assert config.tool_configs[0].name == "test_tool"

    def test_with_tool_discovery_result(self):
        """Test YacbaConfig with tool discovery results."""
        discovery_result = ToolDiscoveryResult(
            loaded_configs=[],
            failed_configs=[],
            total_discovered=0
        )
        
        config = YacbaConfig(
            model_string="litellm:gemini/gemini-1.5-flash",
            system_prompt="Test prompt",
            prompt_source="test",
            tool_configs=[],
            startup_files_content=None,
            tool_discovery_result=discovery_result
        )
        
        assert config.tool_discovery_result is discovery_result
        assert config.tool_discovery_result.total_discovered == 0