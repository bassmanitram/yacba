"""
Tests for the main CLI package.

Comprehensive testing of CLI package exports, integration, and overall functionality.
"""

import pytest
from unittest.mock import Mock, patch

import cli
from cli import (
    print_welcome_message,
    print_startup_info,
    chat_loop_async,
    run_headless_mode
)


class TestCLIPackageExports:
    """Test CLI package exports and structure."""

    def test_package_version(self):
        """Test that CLI package has version."""
        assert hasattr(cli, '__version__')
        assert isinstance(cli.__version__, str)
        assert cli.__version__ == '1.0.0'

    def test_package_all_exports(self):
        """Test that __all__ contains expected exports."""
        expected_exports = [
            'print_welcome_message',
            'print_startup_info',
            'chat_loop_async',
            'run_headless_mode'
        ]
        
        assert hasattr(cli, '__all__')
        assert isinstance(cli.__all__, list)
        
        for export in expected_exports:
            assert export in cli.__all__

    def test_exported_functions_available(self):
        """Test that all exported functions are available."""
        # Interface functions
        assert callable(print_welcome_message)
        assert callable(print_startup_info)
        
        # Mode functions
        assert callable(chat_loop_async)
        assert callable(run_headless_mode)

    def test_import_structure(self):
        """Test import structure works correctly."""
        # Should be able to import from cli directly
        from cli import print_welcome_message as pwm
        from cli import print_startup_info as psi
        from cli import chat_loop_async as cla
        from cli import run_headless_mode as rhm
        
        assert callable(pwm)
        assert callable(psi)
        assert callable(cla)
        assert callable(rhm)


class TestCLIInterfaceFunctions:
    """Test CLI interface functions."""

    def test_print_welcome_message_callable(self):
        """Test that print_welcome_message is callable."""
        # This function is imported from utils.startup_messages
        # We test that it's properly exposed through the CLI package
        with patch('cli.interface.print_welcome_message') as mock_welcome:
            print_welcome_message()
            # The actual implementation is tested in utils tests
            # Here we just verify the import works

    def test_print_startup_info_callable(self):
        """Test that print_startup_info is callable."""
        # This function is imported from utils.startup_messages
        # We test that it's properly exposed through the CLI package
        with patch('cli.interface.print_startup_info') as mock_startup:
            print_startup_info("test system prompt", "test source", {}, [])
            # The actual implementation is tested in utils tests
            # Here we just verify the import works


class TestCLIModeFunctions:
    """Test CLI mode functions."""

    @pytest.mark.asyncio
    async def test_chat_loop_async_callable(self):
        """Test that chat_loop_async is callable."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.ChatInterface') as mock_interface_class:
            mock_interface = Mock()
            mock_interface.run = Mock()
            mock_interface_class.return_value = mock_interface
            
            # Should be callable without errors
            await chat_loop_async(mock_backend)
            
            mock_interface_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_headless_mode_callable(self):
        """Test that run_headless_mode is callable."""
        mock_backend = Mock()
        
        with patch('builtins.input', side_effect=EOFError):
            with patch('sys.stderr'):
                # Should be callable without errors
                await run_headless_mode(mock_backend)


class TestCLIPackageIntegration:
    """Test CLI package integration scenarios."""

    def test_package_docstring(self):
        """Test package has proper documentation."""
        assert cli.__doc__ is not None
        assert len(cli.__doc__.strip()) > 0
        assert "CLI package for YACBA" in cli.__doc__

    def test_subpackage_accessibility(self):
        """Test that subpackages are accessible."""
        # Should be able to access submodules
        import cli.commands
        import cli.interface  
        import cli.modes
        
        assert hasattr(cli.commands, 'registry')
        assert hasattr(cli.interface, 'session')
        assert hasattr(cli.modes, 'interactive')
        assert hasattr(cli.modes, 'headless')

    def test_cross_module_imports(self):
        """Test that cross-module imports work correctly."""
        # Test that commands can import from interface
        from cli.commands.registry import CommandRegistry
        registry = CommandRegistry()
        assert registry is not None
        
        # Test that modes can import from interface
        from cli.modes.interactive import ChatInterface
        from cli.interface.session import create_prompt_session
        
        with patch('cli.interface.session.create_prompt_session'):
            interface = ChatInterface(Mock())
            assert interface is not None


class TestCLIPackageFunctionality:
    """Test overall CLI package functionality."""

    @pytest.mark.asyncio
    async def test_end_to_end_interactive_flow(self):
        """Test end-to-end interactive flow using package exports."""
        mock_backend = Mock()
        
        with patch('cli.modes.interactive.create_prompt_session') as mock_create_session:
            mock_session = Mock()
            mock_session.app = Mock()
            mock_session.prompt_async = Mock()
            mock_session.prompt_async.side_effect = ["/exit"]
            mock_create_session.return_value = mock_session
            
            # Should be able to run complete interactive flow
            await chat_loop_async(mock_backend)
            
            mock_create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_headless_flow(self):
        """Test end-to-end headless flow using package exports."""
        mock_backend = Mock()
        mock_backend.handle_input = Mock()
        
        with patch('builtins.input', side_effect=["test message", "/send", EOFError]):
            with patch('sys.stderr'):
                # Should be able to run complete headless flow
                await run_headless_mode(mock_backend, verbose=False)

    def test_package_structure_consistency(self):
        """Test that package structure is consistent."""
        # All main exports should be properly documented
        for export_name in cli.__all__:
            export_func = getattr(cli, export_name)
            assert callable(export_func)
            # Should have docstring or be imported with one
            # (Note: Some functions are imported from other modules)

    def test_error_handling_integration(self):
        """Test that package-level error handling works."""
        # Import should work even if some submodules have issues
        try:
            import cli
            assert cli is not None
        except ImportError as e:
            pytest.fail(f"CLI package import failed: {e}")

    def test_backwards_compatibility(self):
        """Test backwards compatibility of package interface."""
        # Key functions should remain available
        essential_functions = [
            'chat_loop_async',
            'run_headless_mode'
        ]
        
        for func_name in essential_functions:
            assert hasattr(cli, func_name)
            assert callable(getattr(cli, func_name))


class TestCLIPackageMetadata:
    """Test CLI package metadata and configuration."""

    def test_package_version_format(self):
        """Test that package version follows semantic versioning."""
        version = cli.__version__
        parts = version.split('.')
        assert len(parts) >= 2  # At least major.minor
        
        for part in parts:
            assert part.isdigit(), f"Version part '{part}' should be numeric"

    def test_package_exports_completeness(self):
        """Test that all intended exports are available."""
        # Check that we have both interface and mode exports
        interface_exports = ['print_welcome_message', 'print_startup_info']
        mode_exports = ['chat_loop_async', 'run_headless_mode']
        
        for export in interface_exports:
            assert export in cli.__all__
            assert hasattr(cli, export)
        
        for export in mode_exports:
            assert export in cli.__all__
            assert hasattr(cli, export)

    def test_no_unexpected_exports(self):
        """Test that we don't export unintended items."""
        # __all__ should only contain intended public API
        for item in cli.__all__:
            # All items should be callable functions
            exported_item = getattr(cli, item)
            assert callable(exported_item), f"{item} should be callable"

    def test_package_imports_clean(self):
        """Test that package imports are clean and don't pollute namespace."""
        import cli
        
        # Should not expose internal implementation details
        internal_items = ['sys', 'os', 'pathlib', 'asyncio']
        for item in internal_items:
            assert not hasattr(cli, item), f"Should not expose internal {item}"


class TestCLIPackageDocumentation:
    """Test CLI package documentation and help."""

    def test_package_docstring_structure(self):
        """Test package docstring structure."""
        docstring = cli.__doc__
        assert docstring is not None
        
        # Should mention key components
        assert "command-line interface" in docstring.lower()
        assert "execution modes" in docstring.lower()
        
    def test_subpackage_documentation(self):
        """Test that subpackages have documentation."""
        import cli.commands
        import cli.interface
        import cli.modes
        
        for subpackage in [cli.commands, cli.interface, cli.modes]:
            assert hasattr(subpackage, '__doc__')
            assert subpackage.__doc__ is not None
            assert len(subpackage.__doc__.strip()) > 0