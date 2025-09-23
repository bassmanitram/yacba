# Command registry for validation and help generation
from typing import Any
from loguru import logger

from .base_command import BaseCommand, CommandError


COMMAND_REGISTRY = {
    # Help system (special case)
    '/help': {
        'handler': 'cli.commands.help_command.HelpCommand',
		'category': 'General',
        'description': 'Show help information',
        'usage': [
            '/help - Show all available commands',
            '/help <command> - Show detailed help for a specific command'
        ]
    },
    
    # Control commands (handled directly by main loop)
    '/exit': {
        'handler': 'MainLoop',
		'category': 'Control',
        'description': 'Exit the application',
        'usage': ['/exit - Exit YACBA']
    },
    '/quit': {
        'handler': 'MainLoop',
		'category': 'Control',
        'description': 'Exit the application',
        'usage': ['/quit - Exit YACBA']
    }
}

class CommandRegistry:
	"""Utility class for command registry operations."""
	def __init__(self):
		self.commands = COMMAND_REGISTRY
		self.command_cache = {}

	def _load_handler(self, handler_name: str) -> Any:
		"""Dynamically import a command handler class by name.
		
		Args:
			handler_name: Full class path as string (e.g., 'cli.commands.help_command.HelpCommand')
		"""
		module_path, class_name = handler_name.rsplit('.', 1)
		module = __import__(module_path, fromlist=[class_name])
		return getattr(module, class_name)
	
	def _instantiate_handler(self, command: str, handler_class: Any) -> BaseCommand:
		"""
		Instantiate a command handler class.
		
		Args:
			handler_class: The class to instantiate
			
		Returns:
			Instance of the handler class
			
		Raises:
			Any error that instantiation might raise
		"""
		return handler_class()

	def _create_handler(self, handler_class_name: str) -> BaseCommand:
		"""
		Dynamically import and instantiate a command handler class.
		
		Args:
			handler_name: Full class path as string (e.g., 'cli.commands.help_command.HelpCommand')
			
		Returns:
			Instance of the handler class
			
		Raises:
			ImportError if the class cannot be imported
		"""
		handler_class = self._load_handler(handler_class_name)
		if not issubclass(handler_class, BaseCommand):
			raise TypeError(f"Handler {handler_class_name} is not a subclass of BaseCommand")
		return self._instantiate_handler(handler_class)
				
	def add_command(self, command: str, handler: str, category: str, description: str, usage: list) -> None:
		"""
		Add a new command to the registry.
		
		Args:
			command: Command string (e.g., '/mycommand')
			handler: Handler class name
			category: Command category (e.g., 'Info', 'Session')
			description: Short description of the command
			usage: List of usage strings
		"""
		if command in self.commands:
			raise ValueError(f"Command {command} already exists in registry.")
		
		self.commands[command] = {
			'handler': handler,
			'category': category,
			'description': description,
			'usage': usage
		}

	def get_command_help(self, command: str = None) -> str:
		"""
		Get help text for a specific command or all commands.
		
		Args:
			command: Specific command to get help for, or None for all commands
			
		Returns:
			Formatted help text
		"""
		if command and command in self.commands:
			cmd_info = self.commands[command]
			help_text = f"{command}: {cmd_info['description']}\n"
			for usage in cmd_info['usage']:
				help_text += f"  {usage}\n"
			return help_text.strip()
		
		# Return help for all commands
		help_text = "Available commands:\n"
		for cmd, info in self.commands.items():
			help_text += f"  {cmd:<12} - {info['description']}\n"
		
		help_text += "\nUse '/help <command>' for detailed usage information."
		return help_text

	def get_command_handler(self, command: str) -> BaseCommand:
		"""
		Get the handler instance for a specific command.
		
		Args:
			command: Command to get handler for (e.g., '/help')
			
		Returns:
			Handler class name as string
			
		Raises:
			CommandError if command is not found
		"""
		
		if not command.startswith('/'):
			command = f'/{command}'
			
		if not self.validate_command(command):
			raise CommandError(f"Command {command} is not recognized.", command=command)
		
		handler_class = self.commands[command]['handler']

		if handler_class == 'MainLoop':
			# MainLoop commands are handled directly in the main application loop
			return None

		if command in self.command_cache:
			return self.command_cache[handler_class]
				
		handler_instance = self._create_handler(handler_class)
		self.command_cache[command] = handler_instance
		return handler_instance
	
	def validate_command(self, command: str) -> bool:
		"""
		Validate if a command is supported.
		
		Args:
			command: Command to validate (e.g., '/help')
			
		Returns:
			True if command is supported, False otherwise
		"""
		return command in self.commands
	
	def handle_command(self, command: str, args: list) -> None:
		"""
		Handle a command by invoking its handler.
		
		Args:
			command: Command to handle (e.g., '/help')
			args: List of command arguments
			
		Raises:
			CommandError if command is not recognized or handling fails
		"""
		if not command.startswith('/'):
			command = f'/{command}'
			
		if not self.validate_command(command):
			raise CommandError(f"Command {command} is not recognized.", command=command)
		
		try:
			handler = self.get_command_handler(command)
			if handler:
				handler.handle_command(command, args)
		except Exception as e:
			logger.error(f"Error handling command {command}: {e}")
			print(f"Error handling command {command}: {e}")