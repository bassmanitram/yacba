"""
Tests for config.arguments module.

Target Coverage: 70%+
"""

import pytest
from argparse import ArgumentParser


class TestArgumentDefaults:
    """Tests for ARGUMENT_DEFAULTS dictionary."""
    
    def test_defaults_exist(self):
        """Test that ARGUMENT_DEFAULTS is defined."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        assert isinstance(ARGUMENT_DEFAULTS, dict)
        assert len(ARGUMENT_DEFAULTS) > 0
    
    def test_model_default(self):
        """Test default model setting."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        assert 'model' in ARGUMENT_DEFAULTS
        assert isinstance(ARGUMENT_DEFAULTS['model'], str)
        assert len(ARGUMENT_DEFAULTS['model']) > 0
    
    def test_system_prompt_default(self):
        """Test default system prompt."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        assert 'system_prompt' in ARGUMENT_DEFAULTS
        assert isinstance(ARGUMENT_DEFAULTS['system_prompt'], str)
        assert 'assistant' in ARGUMENT_DEFAULTS['system_prompt'].lower()
    
    def test_boolean_defaults(self):
        """Test boolean default values."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        bool_keys = ['emulate_system_prompt', 'show_tool_use', 'headless', 'no_truncate_results']
        
        for key in bool_keys:
            if key in ARGUMENT_DEFAULTS:
                assert isinstance(ARGUMENT_DEFAULTS[key], bool)
    
    def test_numeric_defaults(self):
        """Test numeric default values."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        numeric_keys = ['window_size', 'preserve_recent', 'max_files']
        
        for key in numeric_keys:
            if key in ARGUMENT_DEFAULTS:
                assert isinstance(ARGUMENT_DEFAULTS[key], (int, float))
                assert ARGUMENT_DEFAULTS[key] > 0


class TestFilesSpecAction:
    """Tests for FilesSpec custom Action (if available)."""
    
    def test_files_spec_action_import(self):
        """Test importing FilesSpec action."""
        try:
            from config.arguments import FilesSpecAction
            assert FilesSpecAction is not None
        except ImportError:
            pytest.skip("FilesSpecAction not available")


class TestArgumentParserIntegration:
    """Integration tests for argument parsing."""
    
    def test_import_functions(self):
        """Test that argument functions can be imported."""
        # Check what's available
        import config.arguments as args_module
        
        # Should have some exports
        assert hasattr(args_module, 'ARGUMENT_DEFAULTS')
    
    def test_defaults_are_valid_types(self):
        """Test that all defaults are valid Python types."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        valid_types = (str, int, float, bool, dict, list, type(None))
        
        for key, value in ARGUMENT_DEFAULTS.items():
            assert isinstance(value, valid_types), f"{key} has invalid type {type(value)}"


@pytest.mark.integration
class TestArgumentConfiguration:
    """Integration tests for argument configuration."""
    
    def test_defaults_match_expected_types(self):
        """Test that defaults match their expected types."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        # String defaults
        string_keys = ['model', 'system_prompt', 'conversation_manager']
        for key in string_keys:
            if key in ARGUMENT_DEFAULTS:
                assert isinstance(ARGUMENT_DEFAULTS[key], str)
        
        # Integer defaults  
        int_keys = ['window_size', 'preserve_recent', 'max_files']
        for key in int_keys:
            if key in ARGUMENT_DEFAULTS:
                assert isinstance(ARGUMENT_DEFAULTS[key], int)
        
        # Float defaults
        float_keys = ['summary_ratio']
        for key in float_keys:
            if key in ARGUMENT_DEFAULTS:
                assert isinstance(ARGUMENT_DEFAULTS[key], (int, float))
                if isinstance(ARGUMENT_DEFAULTS[key], float):
                    assert 0 <= ARGUMENT_DEFAULTS[key] <= 1
    
    def test_conversation_manager_valid(self):
        """Test that conversation_manager default is a valid option."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        if 'conversation_manager' in ARGUMENT_DEFAULTS:
            valid_managers = ['null', 'sliding_window', 'summarizing']
            assert ARGUMENT_DEFAULTS['conversation_manager'] in valid_managers
    
    def test_numeric_defaults_reasonable(self):
        """Test that numeric defaults are reasonable values."""
        from config.arguments import ARGUMENT_DEFAULTS
        
        # Window size should be reasonable (not too small or huge)
        if 'window_size' in ARGUMENT_DEFAULTS:
            assert 10 <= ARGUMENT_DEFAULTS['window_size'] <= 1000
        
        # Preserve recent should be less than window size
        if 'preserve_recent' in ARGUMENT_DEFAULTS and 'window_size' in ARGUMENT_DEFAULTS:
            assert ARGUMENT_DEFAULTS['preserve_recent'] < ARGUMENT_DEFAULTS['window_size']
        
        # Max files should be reasonable
        if 'max_files' in ARGUMENT_DEFAULTS:
            assert 1 <= ARGUMENT_DEFAULTS['max_files'] <= 1000
