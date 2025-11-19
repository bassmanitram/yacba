# Changelog

All notable changes to YACBA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2025-01-15

### Added
- Profile system using profile-config library for configuration management
- Meta-arguments: `--profile`, `--list-profiles`, `--show-config`, `--init-config`
- `YACBA_PROFILE` environment variable for profile selection
- Profile inheritance support in configuration files
- Keyboard shortcuts: F6 (accept suggestion), Escape+! (shell expansion)
- Session repair utility (`scripts/fix_strands_session.py`)
- Structured logging with per-module level control (structlog)
- `PTHN_LOG` environment variable for logging control (Rust RUST_LOG syntax)
- Context manager pattern for agent lifecycle management
- Printer abstraction (auto-format vs plain output for interactive/headless modes)
- HeadlessREPL mode with `/send` separator and EOF handling
- Tab completion for shell commands with 2-second timeout
- Tool configuration discovery from directories
- Support for `@file.txt` syntax in profile and environment configurations

### Changed
- CLI argument parsing now uses dataclass-args for automatic generation
- Configuration system completely rewritten with profile-config integration
- Configuration precedence: DEFAULTS → PROFILE → ENV VARS → --config → CLI
- Help output reorganized: common options first, related options grouped
- REPL backend uses repl-toolkit library (AsyncREPL and HeadlessREPL)
- Agent creation uses strands-agent-factory's AgentFactory pattern
- Logging system migrated to structlog from loguru
- Session storage moved to `~/.yacba/sessions/` directory
- Adapter pattern for config conversion (YacbaToStrandsConfigConverter)

### Removed
- `/shell` command (replaced by shell expansion completion)
- Redundant help text in CLI options
- Monolithic architecture (now thin wrapper over strands-agent-factory)

### Fixed
- Configuration file discovery now searches project and home directories
- Boolean flag handling improved (--flag / --no-flag pairs)
- Context repair now properly configured via `disable_context_repair` option
- Session persistence paths now consistent across modes

### Security
- Session files now stored with user-only permissions (0600)
- Shell expansion only executes on explicit Tab press with timeout protection
- Environment variable expansion properly sanitized
- Profile inheritance validated to prevent cycles

## [1.0.0] - Initial Release

### Added
- Basic CLI wrapper for strands-agents
- Direct strands-agents integration
- Manual CLI parsing with argparse
- Basic configuration file support
- Interactive REPL mode
- Session persistence
- Tool loading support (Python, MCP)

[Unreleased]: https://github.com/yourusername/yacba/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/yourusername/yacba/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/yourusername/yacba/releases/tag/v1.0.0
