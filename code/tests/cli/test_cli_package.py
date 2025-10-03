"""
Tests for the main CLI package.

Comprehensive testing of CLI package exports, integration, and overall functionality.
"""

import pytest
from unittest.mock import Mock, patch

import cli
from cli import (
    run_async_repl,
    run_headless
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
            'run_async_repl',
            'run_headless'
        ]
        
        assert hasattr(cli, '__all__')
        assert isinstance(cli.__all__, list)
        
        for export in expected_exports:
            assert export in cli.__all__

    def test_exported_functions_available(self):
        """Test that all exported functions are available."""
        # Mode functions
        assert callable(run_async_repl)
        assert callable(run_headless)

    def test_import_structure(self):
        """Test import structure works correctly."""
        # Should be able to import from cli directly
        from cli import run_async_repl as rar
        from cli import run_headless as rh
        
        assert callable(rar)
        assert callable(rh)


class TestCLIModeFunctions:
    """Test CLI mode functions."""

    def test_run_async_repl_callable(self):
        """Test that run_async_repl is callable."""
        # Just test that the function exists and is callable
        assert callable(run_async_repl)

    def test_run_headless_callable(self):
        """Test that run_headless is callable."""
        # Just test that the function exists and is callable
        assert callable(run_headless)


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
        
        assert hasattr(cli.commands, 'registry')

    def test_cross_module_imports(self):
        """Test that cross-module imports work correctly."""
        # Test that commands can import from base
        from cli.commands.registry import CommandRegistry
        registry = CommandRegistry()
        assert registry is not None
        
        # Test that async_repl can be imported
        from cli.async_repl import AsyncREPL
        
        mock_backend = Mock()
        with patch('cli.async_repl.PromptSession'):
            interface = AsyncREPL(mock_backend)
            assert interface is not None


class TestCLIPackageFunctionality:
    """Test overall CLI package functionality."""

    def test_package_structure_consistency(self):
        """Test that package structure is consistent."""
        # All main exports should be properly documented
        for export_name in cli.__all__:
            export_func = getattr(cli, export_name)
            assert callable(export_func)

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
            'run_async_repl',
            'run_headless'
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
        mode_exports = ['run_async_repl', 'run_headless']
        
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
        
        for subpackage in [cli.commands]:
            assert hasattr(subpackage, '__doc__')
            assert subpackage.__doc__ is not None
            assert len(subpackage.__doc__.strip()) > 0