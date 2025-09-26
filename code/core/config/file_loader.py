"""
Configuration file handling for YACBA.

Supports YAML configuration files with profiles, inheritance, and template variables.
Maintains full backward compatibility with existing CLI arguments.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from string import Template
from loguru import logger

from yacba_types.base import PathLike


@dataclass
class ConfigProfile:
    """Represents a single configuration profile."""
    name: str
    settings: Dict[str, Any] = field(default_factory=dict)
    inherits: Optional[str] = None
    
    def resolve_inheritance(self, profiles: Dict[str, 'ConfigProfile']) -> Dict[str, Any]:
        """Resolve inheritance chain and return merged settings."""
        if not self.inherits:
            return self.settings.copy()
        
        if self.inherits not in profiles:
            logger.warning(f"Profile '{self.name}' inherits from unknown profile '{self.inherits}'")
            return self.settings.copy()
        
        # Recursively resolve parent settings
        parent_settings = profiles[self.inherits].resolve_inheritance(profiles)
        
        # Merge parent settings with own settings (own settings take precedence)
        merged = parent_settings.copy()
        merged.update(self.settings)
        return merged


@dataclass 
class ConfigFile:
    """Represents a complete configuration file."""
    file_path: Optional[Path] = None
    default_profile: Optional[str] = None
    profiles: Dict[str, ConfigProfile] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    
    def get_profile_settings(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """Get resolved settings for a specific profile."""
        # Use specified profile, or default profile, or anonymous profile
        target_profile = profile_name or self.default_profile
        
        if target_profile and target_profile in self.profiles:
            # Get resolved profile settings
            profile_settings = self.profiles[target_profile].resolve_inheritance(self.profiles)
        else:
            if target_profile:
                logger.warning(f"Profile '{target_profile}' not found, using defaults")
            profile_settings = {}
        
        # Merge defaults with profile settings (profile takes precedence)
        merged = self.defaults.copy()
        merged.update(profile_settings)
        return merged


class ConfigFileLoader:
    """Loads and parses YACBA configuration files."""
    
    CONFIG_SEARCH_PATHS = [
        "./.yacba/config.yaml",
        "./.yacba/config.yml", 
        "./yacba.config.yaml",
        "./yacba.config.yml",
        "~/.yacba/config.yaml",
        "~/.yacba/config.yml"
    ]
    
    @classmethod
    def discover_config_file(cls, explicit_path: Optional[PathLike] = None) -> Optional[Path]:
        """
        Discover configuration file using search hierarchy.
        
        Args:
            explicit_path: Explicit config file path (highest priority)
            
        Returns:
            Path to config file or None if not found
        """
        if explicit_path:
            path = Path(explicit_path).expanduser().resolve()
            if path.exists():
                return path
            else:
                logger.warning(f"Explicit config file not found: {path}")
                return None
        
        # Search standard locations
        for search_path in cls.CONFIG_SEARCH_PATHS:
            path = Path(search_path).expanduser().resolve()
            if path.exists() and path.is_file():
                logger.debug(f"Found config file: {path}")
                return path
        
        logger.debug("No configuration file found")
        return None
    
    @classmethod
    def load_config_file(cls, config_path: PathLike) -> ConfigFile:
        """
        Load and parse a configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Parsed ConfigFile object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
            ValueError: If config file has invalid structure
        """
        path = Path(config_path).expanduser().resolve()
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file {path}: {e}")
        
        return cls._parse_config_data(raw_data, path)
    
    @classmethod 
    def _parse_config_data(cls, data: Dict[str, Any], file_path: Path) -> ConfigFile:
        """Parse raw configuration data into ConfigFile object."""
        config = ConfigFile(file_path=file_path)
        
        # Extract default profile
        config.default_profile = data.get('default_profile')
        
        # Extract global defaults
        config.defaults = data.get('defaults', {})
        
        # Parse profiles
        profiles_data = data.get('profiles', {})
        for profile_name, profile_data in profiles_data.items():
            if not isinstance(profile_data, dict):
                logger.warning(f"Invalid profile data for '{profile_name}', skipping")
                continue
            
            # Extract inheritance
            inherits = profile_data.pop('inherits', None)
            
            # Create profile
            profile = ConfigProfile(
                name=profile_name,
                settings=profile_data,
                inherits=inherits
            )
            config.profiles[profile_name] = profile
        
        return config
    
    @classmethod
    def substitute_variables(cls, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute template variables in configuration settings.
        
        Supports variables like ${HOME}, ${PROJECT_NAME}, etc.
        """
        # Get environment variables for substitution
        env_vars = os.environ.copy()
        
        # Add some commonly used variables
        env_vars.setdefault('PROJECT_NAME', Path.cwd().name)
        env_vars.setdefault('USER_HOME', str(Path.home()))
        
        return cls._substitute_recursive(settings, env_vars)
    
    @classmethod
    def _substitute_recursive(cls, obj: Any, env_vars: Dict[str, str]) -> Any:
        """Recursively substitute variables in nested structures."""
        if isinstance(obj, str):
            try:
                template = Template(obj)
                return template.safe_substitute(env_vars)
            except (ValueError, KeyError) as e:
                logger.warning(f"Variable substitution failed for '{obj}': {e}")
                return obj
        elif isinstance(obj, dict):
            return {k: cls._substitute_recursive(v, env_vars) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [cls._substitute_recursive(item, env_vars) for item in obj]
        else:
            return obj


class ConfigManager:
    """Manages configuration loading and merging for YACBA."""
    
    def __init__(self):
        self.config_file: Optional[ConfigFile] = None
        self.current_profile: Optional[str] = None
    
    def load_config(self, 
                   config_path: Optional[PathLike] = None,
                   profile: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration with full precedence handling.
        
        Args:
            config_path: Explicit config file path
            profile: Profile name to use
            
        Returns:
            Merged configuration settings
        """
        # Discover and load config file
        discovered_path = ConfigFileLoader.discover_config_file(config_path)
        
        if discovered_path:
            try:
                self.config_file = ConfigFileLoader.load_config_file(discovered_path)
                self.current_profile = profile
                logger.info(f"Loaded configuration from: {discovered_path}")
                
                # Get profile settings
                settings = self.config_file.get_profile_settings(profile)
                
                # Substitute template variables
                settings = ConfigFileLoader.substitute_variables(settings)
                
                return settings
                
            except Exception as e:
                logger.error(f"Failed to load config file {discovered_path}: {e}")
                return {}
        else:
            logger.debug("No configuration file found, using defaults")
            return {}
    
    def list_profiles(self) -> List[str]:
        """List available profiles from loaded config file."""
        if not self.config_file:
            return []
        return list(self.config_file.profiles.keys())
    
    def get_resolved_config(self, profile: Optional[str] = None) -> Dict[str, Any]:
        """Get resolved configuration for debugging purposes.""" 
        if not self.config_file:
            return {}
        
        target_profile = profile or self.current_profile
        return self.config_file.get_profile_settings(target_profile)
    
    def create_sample_config(self, output_path: PathLike) -> None:
        """Create a sample configuration file."""
        sample_config = {
            'default_profile': 'development',
            'defaults': {
                'conversation_manager': 'sliding_window',
                'window_size': 40,
                'max_files': 10
            },
            'profiles': {
                'development': {
                    'model': 'litellm:gemini/gemini-1.5-flash',
                    'system_prompt': 'You are a helpful development assistant with access to tools.',
                    'tool_configs': ['~/.yacba/tools/', './tools/'],
                    'show_tool_use': True
                },
                'production': {
                    'model': 'openai:gpt-4',
                    'system_prompt': 'file://~/.yacba/prompts/production.txt',
                    'tool_configs': ['~/.yacba/tools/production/'],
                    'show_tool_use': False,
                    'conversation_manager': 'summarizing',
                    'session': 'prod-session'
                },
                'coding': {
                    'inherits': 'development',
                    'model': 'anthropic:claude-3-sonnet',
                    'system_prompt': 'You are an expert programmer with access to development tools.',
                    'tool_configs': ['~/.yacba/tools/dev/', './project-tools/'],
                    'files': ['README.md', 'src/**/*.py'],
                    'max_files': 50
                }
            }
        }
        
        output_path = Path(output_path).expanduser().resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(sample_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created sample configuration file: {output_path}")