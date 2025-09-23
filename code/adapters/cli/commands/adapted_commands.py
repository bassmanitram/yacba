from cli.commands.base_command import BaseCommand
from yacba_engine import YacbaEngine

class AdaptedCommands(BaseCommand):
	def __init__(self, engine: YacbaEngine):
		super().__init__()
		self.engine = engine
		self.agent = self.engine.agent

