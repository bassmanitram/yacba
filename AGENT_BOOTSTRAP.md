# yacba - Agent Bootstrap

**Purpose**: CLI wrapper for AI chatbot agents with profile-based configuration
**Type**: Application
**Language**: Python 3.10+
**Repository**: https://github.com/bassmanitram/yacba

---

## What You Need to Know

**This is**: A thin CLI wrapper that combines profile-config, dataclass-args, repl-toolkit, and strands-agent-factory into a complete chatbot application. It provides command-line interface, profile-based configuration (dev/prod profiles), interactive REPL, session management, and tool integration. Think of it as glue code that assembles other libraries into a cohesive chatbot.

**Architecture in one sentence**: Configuration assembly (profile-config + dataclass-args + env + CLI) → Factory adapter (YacbaConfig → AgentFactoryConfig) → REPL adapter (AsyncREPL actions) → strands-agent-factory (actual agent).

**The ONE constraint that must not be violated**: YACBA must remain a thin wrapper - core functionality belongs in upstream libraries (strands-agent-factory, repl-toolkit, profile-config, dataclass-args), not here.

---

## Mental Model

- This is **configuration orchestration** - YACBA's job is to assemble config from multiple sources and pass it to strands-agent-factory
- **Precedence layers**: DEFAULTS → Profile file → Environment vars → --config file → CLI args (5 layers!)
- **Adapter pattern** translates between libraries: YacbaConfig ↔ AgentFactoryConfig, YacbaConfig ↔ REPL actions
- **Most logic lives elsewhere** - strands-agent-factory does agent work, repl-toolkit does UI, profile-config does config discovery
- YACBA's **unique contribution** is the tagging/undo system (conversation checkpointing)

---

## Codebase Organization

```
code/
├── yacba.py                      # Entry point: orchestrates config → factory → REPL
├── config/                       # Configuration system
│   ├── dataclass.py             # YacbaConfig - single source of truth
│   ├── factory.py               # parse_config() - assembles from all sources
│   └── arguments.py             # Defaults and environment variable mapping
├── adapters/                     # Bridges between libraries
│   ├── strands_factory/         # YacbaConfig → AgentFactoryConfig
│   │   └── config_converter.py # Conversion logic
│   └── repl_toolkit/            # REPL actions for chatbot commands
│       └── actions/             # Tag, undo, clear, file upload actions
├── utils/                        # Utilities
│   ├── file.py                  # File upload handling
│   ├── session.py               # Session state management
│   └── logging.py               # envlog integration
├── yacba_types/                  # Type definitions
└── tests/                        # Test suite
```

**Navigation Guide**:

| When you need to... | Start here | Why |
|---------------------|------------|-----|
| Add configuration option | `config/dataclass.py` → YacbaConfig | Single source of truth |
| Change config precedence | `config/factory.py` → parse_config() | Where layers assemble |
| Add REPL command | `adapters/repl_toolkit/actions/` | Create new action class |
| Modify agent creation | `adapters/strands_factory/config_converter.py` | YacbaConfig → AgentFactoryConfig translation |
| Fix tagging/undo | `adapters/repl_toolkit/actions/tag*.py` | Conversation checkpointing logic |

**Entry points**:
- Main execution: `yacba.py` → `main()` - Config assembly → Factory creation → REPL startup
- Tests: `tests/config/` and `tests/unit/` - Configuration and component tests
- Configuration: `~/.yacba/config.yaml` - Profile-based config discovery

---

## Critical Invariants

These rules MUST be maintained:

1. **YacbaConfig is single source of truth**: All configuration flows through this dataclass
   - **Why**: Prevents configuration drift, ensures all sources merge consistently
   - **Breaks if violated**: Config values bypass precedence, become hardcoded, can't be overridden
   - **Enforced by**: Architecture - all adapters consume YacbaConfig, nothing bypasses it

2. **Thin wrapper principle**: Core functionality must not live in YACBA
   - **Why**: YACBA is glue, not engine - functionality belongs in upstream libraries
   - **Breaks if violated**: Code duplication, harder to maintain, other projects can't reuse
   - **Enforced by**: Code review, architectural discipline

3. **Adapter isolation**: Adapters must not depend on each other
   - **Why**: strands_factory adapter and repl_toolkit adapter are independent concerns
   - **Breaks if violated**: Coupling increases, harder to update libraries independently
   - **Enforced by**: Module imports - adapters only import their target library

---

## Non-Obvious Behaviors & Gotchas

Things that surprise people:

1. **@file.txt loading happens during config parsing, not factory init**:
   - **Why it's this way**: config/factory.py manually processes @file.txt in profile and env values
   - **Common mistake**: Expecting strands-agent-factory to handle it (it does for CLI args, not for profile/env)
   - **Correct approach**: YACBA pre-processes @file.txt before passing to factory

2. **response_prefix must be pre-formatted to prevent XML parsing crashes**:
   - **Why**: create_auto_printer() in strands-agent-factory can crash on certain prefixes
   - **Watch out for**: Raw prefixes with angle brackets or special chars
   - **Pattern**: config_converter.py calls auto_format() on response_prefix before passing to factory (line 89)

3. **Session storage location depends on session_name presence**:
   - **Why**: Named sessions go to `~/.yacba/sessions/{name}/`, unnamed to temp directory
   - **Pattern**: session_name=None → ephemeral, session_name="foo" → persistent
   - **Gotcha**: Clearing unnamed sessions is different from clearing named sessions

4. **Tagging/undo is YACBA-specific, not in strands-agent-factory**:
   - **Why**: This is unique YACBA feature, uses truncate_messages_to() under the hood
   - **Watch out for**: Feature requires strands-agent-factory v1.3.0+ (added truncate support)
   - **Correct approach**: YACBA action calls agent_proxy.truncate_messages_to(tag_position)

---

## Architecture Decisions

**Why five-layer configuration precedence?**
- **Trade-off**: Complex but maximizes flexibility (system defaults → user profile → environment → deployment config → runtime args)
- **Alternative considered**: Fewer layers (just CLI and profile)
- **Why five layers**: Enables system-wide defaults, user preferences, environment-specific, deployment overrides, runtime testing

**Why separate adapters for strands_factory and repl_toolkit?**
- **Trade-off**: More code but clean separation of concerns
- **Alternative considered**: Single adapter module
- **Why separate**: Each library has different config shape, independent update cycles, no coupling

**Why use profile-config instead of simple config file?**
- **Trade-off**: Dependency on another library but gets hierarchical discovery, inheritance, interpolation
- **Alternative considered**: Simple YAML loading with PyYAML
- **Implications**: Config files discovered automatically, profiles enable dev/prod separation, variable interpolation works

---

## Key Patterns & Abstractions

**Pattern 1: Configuration Assembly Pipeline**
- **Used for**: Merging five configuration sources in correct precedence order
- **Structure**: DEFAULTS → profile-config.resolve() → env vars → --config file → CLI args
- **Examples in code**: `config/factory.py` → `parse_config()` orchestrates this pipeline

**Pattern 2: Adapter Pattern (Library Bridge)**
- **Used for**: Translating YACBA config to library-specific config
- **Structure**: YacbaConfig → converter → LibraryConfig (AgentFactoryConfig, REPL actions)
- **Why**: YACBA config is user-facing (combined options), library configs are implementation-specific

**Pattern 3: Action-Based Commands**
- **Used for**: REPL commands (tag, undo, clear, upload)
- **Structure**: Each command is Action class with handle() method
- **Examples in code**: `adapters/repl_toolkit/actions/` - one file per command

**Anti-pattern to avoid: Implementing agent logic in YACBA**
- **Don't do this**: Adding message processing, tool handling, session management to YACBA
- **Why it fails**: Violates thin wrapper principle, duplicates strands-agent-factory
- **Instead**: Add features to strands-agent-factory, use them from YACBA

---

## State & Data Flow

**State management**:
- **Persistent state**: Session files (via strands-agent-factory FileSessionManager), config profiles
- **Runtime state**: AgentProxy instance, REPL state, tag positions for undo
- **No state here**: Configuration parsing is stateless (config sources → YacbaConfig instance)

**Data flow**:
```
CLI args + Profile + Env → parse_config() → YacbaConfig
                                               ↓
                           ConfigConverter → AgentFactoryConfig
                                               ↓
                        AgentFactory → AgentProxy → strands Agent
                                               ↓
                          AsyncREPL wraps agent → User interaction
                                               ↓
                      Actions (tag/undo/clear) → Modify conversation state
```

**Critical paths**: Configuration must flow through YacbaConfig - bypassing it breaks precedence and loses validation.

---

## Integration Points

**This project depends on** (upstream):
- **strands-agent-factory**: Agent creation and management, tightly coupled (core functionality)
- **repl-toolkit**: Terminal UI, tightly coupled (user interface)
- **profile-config**: Config discovery, tightly coupled (configuration system)
- **dataclass-args**: CLI generation, tightly coupled (argument parsing)
- **envlog**: Logging configuration, loosely coupled (convenience feature)

**Projects that depend on this** (downstream):
- **Your chatbot usage**: End-user application

**Related projects** (siblings):
- **strands-chatbot** (in strands-agent-factory): Similar tool, less features, different architecture

---

## Configuration Philosophy

**What's configurable**: Everything about agent behavior, REPL appearance, session storage, tool loading

**What's hardcoded**:
- Five-layer precedence order (changing would break predictability)
- Adapter interfaces (YacbaConfig structure)
- Core command set (/tag, /undo, /clear, /upload)

**The trap**: Putting configuration in wrong layer - system defaults go in arguments.py, user preferences go in profile, environment-specific in ENV vars, testing overrides in CLI args.

---

## Testing Strategy

**What we test**:
- **Config assembly**: Precedence layers work correctly, overrides apply in order
- **Adapters**: YacbaConfig correctly converts to library configs
- **Configuration validation**: Invalid configs rejected

**What we don't test**:
- **Upstream library functionality**: Trust strands-agent-factory, repl-toolkit work
- **End-to-end chatbot**: Would require actual LLM calls (too expensive, flaky)

**Test organization**: `tests/config/` for configuration, `tests/unit/` for components. Use mocks for upstream libraries.

**Mocking strategy**: Mock strands-agent-factory components, mock repl-toolkit when testing actions, use real config objects.

---

## Common Problems & Diagnostic Paths

**Symptom**: Configuration not loading from profile
- **Most likely cause**: Profile file not in expected location (`~/.yacba/config.yaml`)
- **Check**: Use `--show-config` flag to see resolved configuration
- **Fix**: Create profile file or use `--profile` to specify different profile

**Symptom**: Tagging/undo not working
- **Likely cause**: Using strands-agent-factory version < 1.3.0 (truncate_messages_to added in 1.3.0)
- **Diagnostic**: Check strands-agent-factory version with `pip show strands-agent-factory`
- **Solution**: Upgrade to strands-agent-factory 1.3.0+

**Symptom**: XML parsing crash with certain response prefixes
- **Why it happens**: Fixed - response_prefix now pre-formatted with auto_format()
- **Diagnostic**: Check config_converter.py line 89 uses auto_format()
- **Prevention**: Already handled, but be careful with special chars in response_prefix config

---

## Modification Patterns

**To add configuration option**:
1. Add field to YacbaConfig in `config/dataclass.py`
2. Add default in `config/arguments.py` → ARGUMENT_DEFAULTS
3. Update adapter if needed: `adapters/strands_factory/config_converter.py`
4. Add tests in `tests/config/`

**To add REPL command**:
1. Create action class in `adapters/repl_toolkit/actions/my_command.py`
2. Import and register in action setup
3. Implement handle() method using ActionContext
4. Add tests mocking the action behavior

**To change config precedence**:
1. **Don't do this without strong reason** - breaks user expectations
2. If necessary: modify `config/factory.py` → parse_config() merge order
3. Update all tests that assume current precedence
4. Document as breaking change (major version bump)

---

## When to Update This Document

Update this bootstrap when:
- [x] Configuration precedence changes (layers added/removed/reordered)
- [x] Major upstream library integration changes (replace strands-agent-factory, etc.)
- [x] Adapter pattern changes (new adapter added, interface changes)
- [x] Thin wrapper principle violated (core logic added to YACBA)

Don't update for:
- ❌ New configuration options (extend YacbaConfig)
- ❌ New REPL commands (extend action system)
- ❌ Bug fixes in adapters or config parsing
- ❌ Dependency version updates

---

**Last Updated**: 2025-12-03
**Last Architectural Change**: v2.0.0 - Complete rewrite with profile-config integration (5-layer precedence)
