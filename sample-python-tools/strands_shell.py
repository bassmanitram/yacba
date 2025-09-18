# shell_tool.py
# This module acts as a simple bridge to expose the pre-built shell tool
# from the strands-agents library to the yacba tool discovery mechanism.

from strands_tools import shell

# The 'shell' object is already a decorated tool. We just need to make it
# available in a module that our configuration can point to.
# We assign it to a new variable name to show that the name in this file
# is what matters for the .tools.json configuration.
local_shell = shell.shell
