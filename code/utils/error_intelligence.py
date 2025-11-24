"""
Error Intelligence System for YACBA.

Provides pattern matching for exceptions to generate actionable, context-aware
error messages. All patterns are defined in ~/.yacba/error_patterns.yaml

Features:
- Context-aware templates with variable substitution
- Regex capture groups for extracting specific values
- Console suppression for internal/handled errors
- Fully user-configurable via YAML
"""

import os
import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import logging


# ============================================================================
# Helper Functions
# ============================================================================


def _safe_format(template: str, context: Dict[str, str]) -> str:
    """
    Safe template formatting that supports {1}, {2}, {message}, etc.

    Uses regex replacement to avoid .format() positional argument issues.
    Python's str.format() treats {1} as positional args, but we want them
    as keyword args for regex capture groups.

    Args:
        template: Template string with {variables}
        context: Dictionary mapping variable names to values

    Returns:
        Formatted string with variables replaced
    """

    def replace(match):
        key = match.group(1)
        return str(context.get(key, match.group(0)))  # Keep original if not found

    return re.sub(r"\{([^}]+)\}", replace, template)


# ============================================================================
# Data Structures
# ============================================================================


@dataclass
class ErrorAdvice:
    """
    Actionable advice for an error.

    Attributes:
        error_type: Short name for the error type (e.g., "ThrottlingException")
        summary: Brief human-readable description (supports templates)
        action: What the user should do (supports templates)
        doc_url: URL to relevant documentation (optional)

    Template Variables:
        {message} - Full exception message
        {excerpt} - First 100 chars of exception message
        {type} - Exception type name
        {0}, {1}, {2}, ... - Regex capture groups (if pattern has groups)
    """

    error_type: str
    summary: str
    action: Optional[str] = None
    doc_url: Optional[str] = None

    def format_console_message(
        self, exc: Exception, captured_groups: Optional[Tuple[str, ...]] = None
    ) -> str:
        """
        Format advice for console display with template variable expansion.

        Args:
            exc: The exception being formatted
            captured_groups: Regex capture groups from pattern matching

        Returns:
            Formatted message with actionable advice
        """
        # Build context dict for template variables
        exc_message = str(exc)
        context = {
            "message": exc_message,
            "excerpt": exc_message[:100],
            "type": type(exc).__name__,
        }

        # Add regex capture groups if available
        if captured_groups:
            for i, group in enumerate(captured_groups, start=1):
                context[str(i)] = group

        # Safely expand templates in summary and action using regex replacement
        summary = _safe_format(self.summary, context)

        action = None
        if self.action:
            action = _safe_format(self.action, context)

        # Format final message
        parts = [f"{self.error_type}: {summary}"]
        if action:
            parts.append(action)

        return ". ".join(parts)


@dataclass
class ErrorPattern:
    """
    Pattern for matching exceptions and providing advice.

    Attributes:
        exception_type: Exception class name to match (e.g., "ValueError")
        advice: The advice to provide when this pattern matches
        message_regex: Optional regex pattern to match exception message
        priority: Higher priority patterns are checked first (default: 0)
        show_console: Whether to show on console (default: True)
    """

    exception_type: str
    advice: ErrorAdvice
    message_regex: Optional[str] = None
    priority: int = 0
    show_console: bool = True

    def matches(self, exc: Exception) -> Tuple[bool, Optional[Tuple[str, ...]]]:
        """
        Check if this pattern matches the given exception.

        Args:
            exc: Exception to check

        Returns:
            Tuple of (matched, captured_groups)
            - matched: True if pattern matches
            - captured_groups: Tuple of regex groups if message_regex matched
        """
        # Check exception type match
        exc_type_name = type(exc).__name__
        if exc_type_name != self.exception_type:
            return False, None

        # Check message pattern match (with capture)
        if self.message_regex:
            try:
                match = re.search(self.message_regex, str(exc), re.IGNORECASE)
                if match:
                    return True, match.groups()
                return False, None
            except re.error as e:
                logging.warning(f"Invalid regex pattern '{self.message_regex}': {e}")
                return False, None

        return True, None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ErrorPattern":
        """
        Create ErrorPattern from dictionary (e.g., from YAML config).

        Args:
            data: Dictionary with pattern definition

        Returns:
            ErrorPattern instance
        """
        advice_data = data.get("advice", {})
        advice = ErrorAdvice(
            error_type=advice_data.get("error_type", data.get("exception_type")),
            summary=advice_data.get("summary", "An error occurred"),
            action=advice_data.get("action"),
            doc_url=advice_data.get("doc_url"),
        )

        return cls(
            exception_type=data["exception_type"],
            message_regex=data.get("message_pattern"),
            advice=advice,
            priority=data.get("priority", 0),
            show_console=data.get("show_console", True),
        )


# ============================================================================
# Error Intelligence System
# ============================================================================


class ErrorIntelligenceSystem:
    """
    System for matching exceptions to actionable advice.

    All patterns are loaded from ~/.yacba/error_patterns.yaml
    No built-in patterns - fully user-configurable.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize and load patterns from configuration.

        Args:
            config_path: Path to error patterns config
                        (default: ~/.yacba/error_patterns.yaml)
        """
        self.patterns: List[ErrorPattern] = []
        self.config_path = config_path or (
            Path.home() / ".yacba" / "error_patterns.yaml"
        )
        self._load_patterns()

    def _load_patterns(self) -> None:
        """Load patterns from configuration file."""
        if not self.config_path.exists():
            logging.debug(
                f"Error patterns file not found: {self.config_path}. "
                "No error intelligence available."
            )
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config or "patterns" not in config:
                logging.warning(
                    f"No patterns found in {self.config_path}. "
                    "Expected 'patterns' key at root level."
                )
                return

            patterns = []
            for pattern_data in config["patterns"]:
                try:
                    pattern = ErrorPattern.from_dict(pattern_data)
                    patterns.append(pattern)
                except Exception as e:
                    logging.warning(
                        f"Skipping invalid error pattern in {self.config_path}: {e}"
                    )

            self.patterns = patterns

            # Sort by priority (higher first)
            self.patterns.sort(key=lambda p: p.priority, reverse=True)

            logging.debug(
                f"Loaded {len(self.patterns)} error patterns from {self.config_path}"
            )

        except Exception as e:
            logging.warning(
                f"Error loading error patterns from {self.config_path}: {e}"
            )

    def get_pattern_for_exception(self, exc: Exception) -> Optional[ErrorPattern]:
        """
        Get the pattern that matches this exception.

        Args:
            exc: The exception to match

        Returns:
            Matching ErrorPattern or None
        """
        for pattern in self.patterns:
            matched, _ = pattern.matches(exc)
            if matched:
                return pattern
        return None

    def get_advice(
        self, exc: Exception, context: str = ""
    ) -> Optional[Tuple[ErrorAdvice, Optional[Tuple[str, ...]]]]:
        """
        Get actionable advice for an exception.

        Args:
            exc: The exception to analyze
            context: Optional context string (e.g., original log message)

        Returns:
            Tuple of (advice, captured_groups) if pattern found, None otherwise
        """
        for pattern in self.patterns:
            matched, groups = pattern.matches(exc)
            if matched:
                return pattern.advice, groups
        return None

    def register_pattern(self, pattern: ErrorPattern) -> None:
        """
        Register a new error pattern dynamically.

        Args:
            pattern: The pattern to register
        """
        self.patterns.append(pattern)
        # Re-sort by priority
        self.patterns.sort(key=lambda p: p.priority, reverse=True)


# Global instance
_error_intelligence = None


def get_error_intelligence() -> ErrorIntelligenceSystem:
    """Get or create the global ErrorIntelligenceSystem instance."""
    global _error_intelligence
    if _error_intelligence is None:
        _error_intelligence = ErrorIntelligenceSystem()
    return _error_intelligence


def get_error_advice(
    exc: Exception, context: str = ""
) -> Optional[Tuple[ErrorAdvice, Optional[Tuple[str, ...]]]]:
    """
    Convenience function to get advice for an exception.

    Args:
        exc: The exception to analyze
        context: Optional context string

    Returns:
        Tuple of (advice, captured_groups) if found, None otherwise
    """
    return get_error_intelligence().get_advice(exc, context)


# ============================================================================
# Logging Integration
# ============================================================================


class ErrorIntelligenceFilter(logging.Filter):
    """
    Logging filter that enhances ERROR messages with actionable advice.

    This filter:
    - Only processes ERROR level messages with exception info
    - Extracts the exception and gets advice
    - Enhances the message with actionable guidance
    - Can suppress messages from console (but not from log files)
    - Supports template variables and regex capture groups

    Note: Should only be applied to console handlers, not file handlers.
    """

    def __init__(self):
        """Initialize the filter."""
        super().__init__()
        self.intelligence = get_error_intelligence()
        self.suppressed_count = 0
        self.show_all = os.environ.get("YACBA_SHOW_ALL_ERRORS") == "1"

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Process log record and potentially enhance or suppress message.

        Args:
            record: The log record to process

        Returns:
            True to show message, False to suppress from console
        """
        # Only process ERROR level messages with exception info
        if record.levelno != logging.ERROR or not record.exc_info:
            return True

        # Extract exception
        exc = record.exc_info[1]
        if exc is None:
            return True

        # Get matching pattern
        pattern = self.intelligence.get_pattern_for_exception(exc)
        if not pattern:
            return True  # No pattern, show original error

        # Check if should suppress from console (unless override set)
        if not pattern.show_console and not self.show_all:
            self.suppressed_count += 1
            return False  # Suppress from console

        # Get advice with captured groups
        result = self.intelligence.get_advice(exc, record.getMessage())
        if not result:
            return True

        advice, groups = result

        # Format message with templates
        enhanced_msg = advice.format_console_message(exc, groups)

        # Update record message
        record.msg = enhanced_msg
        record.args = ()  # Clear args since we've already formatted

        return True

    def get_suppressed_count(self) -> int:
        """
        Get count of suppressed errors (for exit summary).

        Returns:
            Number of errors suppressed from console
        """
        return self.suppressed_count


# ============================================================================
# Testing
# ============================================================================


def test_error_intelligence():
    """Test the error intelligence system with various exceptions."""

    # Create a test config file
    test_config = Path("test_error_patterns.yaml")
    test_config_content = """
patterns:
  - exception_type: "ModelThrottledException"
    message_pattern: 'received (\\d+).*?limit.*?(\\d+)'
    priority: 10
    show_console: true
    advice:
      error_type: "ThrottlingException"
      summary: "Rate limit: {1} tokens sent, limit is {2}"
      action: "Wait ~60s, then send 'continue' to resume"

  - exception_type: "ValueError"
    message_pattern: 'Model "(.+?)" not found'
    priority: 5
    show_console: true
    advice:
      error_type: "InvalidModel"
      summary: "Model \\"{1}\\" not found"
      action: "Run 'yacba list-models' to see available models"

  - exception_type: "FileNotFoundError"
    priority: 5
    show_console: true
    advice:
      error_type: "FileNotFound"
      summary: "{message}"
      action: "Verify the path exists"

  - exception_type: "CacheError"
    priority: 3
    show_console: false
    advice:
      error_type: "CacheMiss"
      summary: "Cache miss (internal)"

  - exception_type: "Exception"
    message_pattern: "cycle failed"
    priority: 1
    show_console: true
    advice:
      error_type: "AgentCycleError"
      summary: "Agent processing cycle failed"
      action: "Check full log for details. Send 'continue' to retry"
"""

    with open(test_config, "w") as f:
        f.write(test_config_content)

    try:
        # Create test exceptions
        class ModelThrottledException(Exception):
            pass

        class CacheError(Exception):
            pass

        test_cases = [
            (
                ModelThrottledException(
                    "Too many tokens: received 50000, limit is 40000"
                ),
                "ThrottlingException",
                True,  # should show
                "50000",  # should extract
            ),
            (
                ValueError('Model "gpt-9-turbo" not found'),
                "InvalidModel",
                True,
                "gpt-9-turbo",
            ),
            (
                FileNotFoundError("/path/to/config.yaml not found"),
                "FileNotFound",
                True,
                "/path/to/config.yaml",
            ),
            (
                CacheError("Cache key not found"),
                "CacheMiss",
                False,  # should suppress
                None,
            ),
            (
                Exception("cycle failed"),
                "AgentCycleError",
                True,
                None,
            ),
        ]

        intelligence = ErrorIntelligenceSystem(config_path=test_config)

        print("Testing Error Intelligence System")
        print("=" * 70)

        passed = 0
        failed = 0

        for exc, expected_type, should_show, expected_extract in test_cases:
            result = intelligence.get_advice(exc)
            pattern = intelligence.get_pattern_for_exception(exc)

            if result:
                advice, groups = result
                formatted = advice.format_console_message(exc, groups)

                print(f"\n{type(exc).__name__}: {exc}")
                print(f"  → {formatted}")
                print(f"  → Show on console: {should_show}")

                try:
                    assert (
                        advice.error_type == expected_type
                    ), f"Expected {expected_type}, got {advice.error_type}"

                    assert (
                        pattern.show_console == should_show
                    ), f"Expected show_console={should_show}"

                    if expected_extract:
                        assert (
                            expected_extract in formatted
                        ), f"Expected '{expected_extract}' in message"

                    passed += 1
                except AssertionError as e:
                    print(f"  ✗ FAILED: {e}")
                    failed += 1
            else:
                print(f"\n{type(exc).__name__}: {exc}")
                print("  → No advice found")
                failed += 1

        print("\n" + "=" * 70)
        if failed == 0:
            print(f"✓ All tests passed! ({passed}/{passed})")
        else:
            print(f"✗ Some tests failed: {passed} passed, {failed} failed")
            return False

        return True

    finally:
        # Clean up test config
        if test_config.exists():
            test_config.unlink()


if __name__ == "__main__":
    import sys

    success = test_error_intelligence()
    sys.exit(0 if success else 1)
