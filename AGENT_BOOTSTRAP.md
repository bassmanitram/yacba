# YACBA Agent Bootstrap Document

**Purpose**: Quick onboarding for AI agents working on this project across clean sessions.

**Last Updated**: 2024-12-05  
**Project**: YACBA (Yet Another ChatBot Agent) v2.0.0  
**Repository**: https://github.com/bassmanitram/yacba

---

## What is YACBA?

YACBA is a **CLI wrapper** for AI chatbot agents. It provides:
- Command-line interface with profile-based configuration
- Interactive REPL with tab completion and history
- Headless mode for automation/scripting
- Session management with conversation tagging
- Tool integration (Python functions, MCP servers, A2A agents)

**Architecture**: Thin wrapper over [strands-agent-factory](https://github.com/bassmanitram/strands-agent-factory), which is built on [strands-agents](https://github.com/pydantic/strands-agents).

---

## Current Status

**Branch**: `feature/tagging`  
**Clean Status**: One modified file (see Known Issues)  
**Recent Work**: Tagging and undo functionality (checkpointing system)  
**Version**: 2.0.0 (major rewrite with profile system)

### Recent Commits (most recent first):
```
291a0c3 - Fixes
c805052 - Merge branch 'main' into feature/tagging
d09034e - Fix reporting of uploaded files
4cb76f0 - Fix -f
881c442 - Get BIG error reports - useful while honing the error intelligence stuff
ee6d94c - Allow verbose errors in the console
76f8b0e - Some seriously cool joojoo - tagging and undoing (cf checkpointing in copilot)
```

---

## Known Issues

### CRITICAL: XML Parsing Crashes

**File**: `code/adapters/strands_factory/config_converter.py`  
**Status**: MODIFIED (uncommitted changes)  
**Problem**: The `create_auto_printer()` function causes XML parsing crashes  
**Temporary Fix**: Using `print_formatted_text` instead of `create_auto_printer()`  

**Code Location**: Lines 90-105 in config_converter.py
```python
# CURRENT WORKAROUND (enabled):
output_printer=(
    print_formatted_text if not self.yacba_config.headless else print
),

# ORIGINAL CODE (disabled due to crashes):
#output_printer=(
#    create_auto_printer() if not self.yacba_config.headless else print
#),
```

**Impact**: Output formatting may be degraded in interactive mode  
**Priority**: HIGH - needs proper fix, not workaround  
**Action Required**: 
1. Investigate why `create_auto_printer()` causes XML parsing crashes
2. Fix the root cause in repl-toolkit or strands-agent-factory
3. Re-enable `create_auto_printer()` once stable
4. Remove workaround comments

---

## Project Structure

```
yacba/
├── yacba                    # Bootstrap launcher script
├── code/                    # Main codebase
│   ├── yacba.py            # Entry point and orchestration
│   ├── config/             # Configuration system (profile-config + dataclass-args)
│   ├── adapters/           # Adapters for strands-factory and repl-toolkit
│   ├── utils/              # Utilities (file, config, logging, session)
│   ├── scripts/            # Maintenance tools (session repair, etc.)
│   ├── tests/              # Test suite
│   └── yacba_types/        # Type definitions
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md     # System architecture (read this!)
│   ├── TAG_SYSTEM.md       # Conversation tagging docs
│   └── ...
├── sample-tool-configs/    # Example tool configurations
├── sample-model-configs/   # Example model configurations
├── sample-python-tools/    # Example Python tools
└── local/                  # Non-public reports (gitignored)
```

---

## Key Technologies

- **Python**: 3.10+ required
- **CLI Generation**: dataclass-args (auto-generates CLI from dataclass)
- **Configuration**: profile-config (profile-based config management)
- **REPL**: repl-toolkit (AsyncREPL for interactive, HeadlessREPL for automation)
- **Agent Framework**: strands-agent-factory → strands-agents
- **Logging**: envlog (Rust RUST_LOG-style syntax via PTHN_LOG)
- **Testing**: pytest

---

## Essential Reading

**Before starting work, read these in order:**

1. **README.md** - User guide, features, usage examples
2. **docs/ARCHITECTURE.md** - System design, data flow, extension points (IMPORTANT!)
3. **CHANGELOG.md** - Recent changes, version history
4. **docs/TAG_SYSTEM.md** - Conversation tagging feature (recent addition)

**Key Architectural Points:**
- YACBA is a **thin wrapper** - core functionality is in strands-agent-factory
- Configuration uses **precedence layers**: DEFAULTS → PROFILE → ENV → --config → CLI
- **Adapter pattern** bridges YACBA ↔ strands-factory ↔ repl-toolkit
- **YacbaConfig** (dataclass) is source of truth for all configuration

---

## Development Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (if needed)
pip install -e .

# Run tests
cd code
python -m pytest tests/ -v

# Run linting
ruff check .
mypy .

# Run YACBA locally
python code/yacba.py -m "litellm:gemini/gemini-2.5-flash"
```

---

## Testing

```bash
cd code

# All tests
pytest

# Specific test file
pytest tests/unit/test_factory.py

# With coverage
pytest --cov=. --cov-report=html

# Verbose
pytest -v
```

**Test Organization**:
- `tests/config/` - Configuration system tests
- `tests/unit/` - Unit tests for components
- `conftest.py` - Fixtures and test configuration

---

## Debugging

```bash
# Enable debug logging (Rust RUST_LOG syntax)
export PTHN_LOG="debug"
python code/yacba.py -m "gpt-4o"

# Fine-grained logging
export PTHN_LOG="error,yacba=info,yacba.config=debug"

# Show resolved configuration
python code/yacba.py --show-config

# List available profiles
python code/yacba.py --list-profiles
```

---

## Configuration System

**Key Files**:
- `code/config/dataclass.py` - YacbaConfig (source of truth)
- `code/config/factory.py` - parse_config() orchestration
- `code/config/arguments.py` - Defaults and environment variables
- `code/adapters/strands_factory/config_converter.py` - YacbaConfig → AgentFactoryConfig

**Precedence** (lowest to highest):
1. ARGUMENT_DEFAULTS
2. Profile file (via profile-config)
3. Environment variables (YACBA_*)
4. --config file
5. CLI arguments

**Meta-Arguments** (not in YacbaConfig):
- `--profile <name>` - Select profile
- `--list-profiles` - List profiles
- `--show-config` - Show resolved config
- `--init-config <path>` - Create sample config

---

## Common Tasks

### Adding a Configuration Option

1. Add field to `YacbaConfig` in `code/config/dataclass.py`
2. Add default to `ARGUMENT_DEFAULTS` in `code/config/arguments.py`
3. (Optional) Add to env vars in `_build_env_vars()`
4. Update converter if needed: `code/adapters/strands_factory/config_converter.py`
5. Update docs: README.md, docs/ARCHITECTURE.md

### Adding a Command

1. Create Action class in `code/adapters/repl_toolkit/actions/`
2. Register in `YacbaActionRegistry`
3. Test in interactive mode

### Adding a Utility

1. Create module in `code/utils/`
2. Add unit tests in `code/tests/unit/`
3. Import where needed

---

## Git Workflow

**IMPORTANT**: NEVER modify repository state (`git add`, `git commit`, `git push`, etc.)  
**ALLOWED**: Read-only operations (`git status`, `git log`, `git diff`)

**Current Branch**: `feature/tagging`  
**Main Branch**: `main` (slightly behind feature branch)

---

## When You're Stuck

1. **Check ARCHITECTURE.md** - Most questions answered there
2. **Check strands-agent-factory** - Core functionality lives there
3. **Enable debug logging** - `export PTHN_LOG="debug"`
4. **Read the tests** - Often show usage examples
5. **Check recent commits** - `git log --oneline -10`

---

## Common Gotchas

1. **Thin Wrapper**: Don't implement agent features in YACBA - they belong in strands-agent-factory
2. **Config Precedence**: CLI args override everything - test with clean environment
3. **@file.txt Loading**: Manually processed in factory.py for profile/env values
4. **Tool Discovery**: Automatic for directories, manual for individual files
5. **Session Storage**: Location depends on session_name (yes/no)
6. **Printer Abstraction**: Different for interactive vs headless mode
7. **XML Parsing Crash**: See Known Issues above - use print_formatted_text for now

---

## Quick Reference

```bash
# Run YACBA
python code/yacba.py -m "gpt-4o"

# Run tests
cd code && pytest

# Check config
python code/yacba.py --show-config

# Enable debug logging
export PTHN_LOG="debug"

# Check git status
git status

# View recent changes
git log --oneline -5

# See what's modified
git diff
```

---

## Contact Points

- **Repository**: https://github.com/bassmanitram/yacba
- **strands-agent-factory**: https://github.com/bassmanitram/strands-agent-factory
- **License**: MIT

---

## Session Continuity

When resuming work:

1. **Check git status** - `git status` to see modified files
2. **Review this doc** - Re-read the Known Issues section
3. **Check recent commits** - `git log --oneline -10`
4. **Review CHANGELOG** - See what changed recently
5. **Run tests** - `cd code && pytest` to verify nothing broken

---

## Notes for Future Sessions

- The XML parsing crash workaround is **temporary** and needs a proper fix
- The tagging feature is recent (feature/tagging branch)
- Configuration system was completely rewritten in v2.0 (profile-config integration)
- YACBA is a thin wrapper - most complexity is in strands-agent-factory
- Always check ARCHITECTURE.md for design decisions and extension points

---

**Remember**: Read ARCHITECTURE.md first thing. It contains the detailed system design, data flows, and extension points. This bootstrap doc is just a quick orientation.
