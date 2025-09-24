from cli.commands.base_command import BaseCommand
from cli.commands.registry import CommandRegistry
from core.engine import YacbaEngine

class AdaptedCommands(BaseCommand):
	def __init__(self, registry: CommandRegistry, engine: YacbaEngine):
		super().__init__(registry)
		self.engine = engine
		self.agent = self.engine.agent