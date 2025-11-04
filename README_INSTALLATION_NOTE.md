# YACBA Installation Notes

## Important: strands-agent-factory Installation

**strands-agent-factory is NOT available on PyPI** and must be installed from GitHub.

### Why GitHub-Only?

From strands-agent-factory documentation:
> This package is distributed directly from GitHub releases and repository rather than PyPI due to copyright considerations.

### Installation Methods

#### Method 1: From requirements.txt (Recommended)

The `requirements.txt` already specifies the correct GitHub installation:

```bash
# Clone YACBA
git clone https://github.com/your-username/yacba.git
cd yacba/code

# Install all dependencies (including strands-agent-factory from GitHub)
pip install -r requirements.txt
```

The requirements.txt contains:
```txt
repl-toolkit>=1.1.0
strands-agent-factory @ git+https://github.com/JBarmentlo/strands-agent-factory.git@v1.1.0
```

#### Method 2: Manual GitHub Installation

```bash
# Install specific release (recommended for stability)
pip install "git+https://github.com/bassmanitram/strands-agent-factory.git@v1.1.0"

# Or install from GitHub release wheel (faster, no git required)
pip install "https://github.com/bassmanitram/strands-agent-factory/releases/download/v1.1.0/strands_agent_factory-1.1.0-py3-none-any.whl"
```

#### Method 3: With Provider Extras

```bash
# Install with specific AI provider support
pip install "strands-agent-factory[anthropic,openai] @ git+https://github.com/bassmanitram/strands-agent-factory.git@v1.1.0"

# Install with all providers
pip install "strands-agent-factory[all-providers] @ git+https://github.com/bassmanitram/strands-agent-factory.git@v1.1.0"
```

### What Gets Installed

When you run `pip install -r requirements.txt`, pip will:

1. Install PyPI packages normally (anthropic, litellm, dataclass-args, etc.)
2. Clone strands-agent-factory from GitHub and install it
3. Install all other dependencies

**No additional steps needed** - just use `pip install -r requirements.txt` as documented.

### Requirements Breakdown

```txt
# PyPI packages (installed normally)
anthropic
prompt_toolkit
litellm
profile-config>=1.1.0
dataclass-args>=1.0.1
pyyaml
repl-toolkit>=1.1.0
strands-agents

# GitHub-only packages (installed from git repositories)
strands-agent-factory @ git+https://github.com/JBarmentlo/strands-agent-factory.git@v1.1.0
```

### Prerequisites

To install from GitHub, you need:
- **Git**: Must be installed and accessible in PATH
- **Internet access**: To clone from GitHub
- **GitHub access**: Public repositories require no authentication

Check git installation:
```bash
git --version
```

If git is not installed:
```bash
# Ubuntu/Debian
sudo apt-get install git

# macOS
brew install git

# Windows
# Download from https://git-scm.com/download/win
```

### Docker Installation

When using Docker, ensure git is available:

```dockerfile
FROM python:3.11-slim

# Install git (required for pip to install from GitHub)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install YACBA dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Rest of your Dockerfile
```

### Troubleshooting

#### "git: command not found"
Install git as shown above.

#### "Repository not found" or 403 errors
- Check internet connectivity
- Verify GitHub is accessible
- Try with HTTPS if SSH fails

#### Rate limiting
GitHub may rate limit anonymous requests. Usually not an issue for small teams.

#### Version pinning
The requirements.txt pins to `@v1.1.0` for stability. To update:

```bash
# Update to latest release
pip install --upgrade "git+https://github.com/bassmanitram/strands-agent-factory.git@v1.2.0"

# Update requirements.txt
strands-agent-factory @ git+https://github.com/JBarmentlo/strands-agent-factory.git@v1.2.0
```

### Why This Matters

- **Installation process**: Cannot use `pip install strands-agent-factory` alone
- **Dependency management**: Must use git URLs in requirements files
- **CI/CD**: Ensure git is available in build environments
- **Docker**: Include git in Docker images
- **Offline installation**: Requires pre-downloaded wheels or git bundles

### More Information

For complete strands-agent-factory installation documentation:
- Repository: https://github.com/bassmanitram/strands-agent-factory
- Installation Guide: `/home/jbartle9/tmp/strands-agent-factory/GITHUB_INSTALLATION.md`
- Releases: https://github.com/bassmanitram/strands-agent-factory/releases
