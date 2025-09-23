import importlib
import os
from typing import Any, Callable, Dict, Optional

from yacba_types.tools import ToolCreationResult
from .base_adapter import ToolAdapter
from loguru import logger

def _load_module_attribute(
    base_module: str,
    attribute: str,
    package_path: Optional[str] = None,
    base_path: Optional[str] = None,
) -> Callable:
    """
    Dynamically loads a attribute, using a specific directory as the root if provided.

    Args:
        base_module: The first part of the module's dotted path (e.g., 'my_app.lib').
        attribute: The second part of the path, including submodules and the
                  attribute name (e.g., 'utils.helpers.my_func').
        package_path: (Optional) The relative path to a directory that should be
                      treated as the root for the import. If None, Python's
                      standard import search paths (sys.path) are used.
		base_path: (Optional) The base directory to resolve package_path against.
    Returns:
        A reference to the dynamically loaded attribute.
    """
    # 1. Combine the inputs into a full dotted path and separate module from attribute
    full_attribute_path = f"{base_module}.{attribute}"
    try:
        full_module_path, attribute_name = full_attribute_path.rsplit('.', 1)
        logger.debug(f"Loading attribute '{attribute_name}' from module '{full_module_path}' (package_path='{base_path}, package_path='{package_path}')")
    except ValueError as e:
        raise ValueError(f"Invalid path '{full_attribute_path}'.") from e

    # 2. Decide which loading strategy to use
    if package_path:
        # --- SCENARIO 1: Custom path is provided ---
        # Translate dotted module path to a relative file path
        relative_file_path = full_module_path.replace('.', os.path.sep) + '.py'
        absolute_file_path = os.path.join(base_path or "", package_path, relative_file_path)

        if not os.path.isfile(absolute_file_path):
            raise FileNotFoundError(f"Module file not found at: {absolute_file_path}")

        # Load the module directly from its file path without using sys.path
        spec = importlib.util.spec_from_file_location(full_module_path, absolute_file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load module from {absolute_file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    else:
        # --- SCENARIO 2: Default behavior ---
        # Use Python's standard import mechanism, which searches sys.path
        try:
            module = importlib.import_module(full_module_path)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                f"Module '{full_module_path}' not found in standard Python paths."
            ) from e
    # 3. Retrieve the attribute from the loaded module
    try:
        attribute_ref = getattr(module, attribute_name)
    except AttributeError as e:
        raise AttributeError(
            f"Attribute '{attribute_name}' not found in module '{full_module_path}'."
        ) from e

    return attribute_ref

class PythonToolAdapter(ToolAdapter):
    """Adapter for creating tools from local or installed Python modules."""
    def create(self, config: Dict[str, Any]) -> ToolCreationResult:
        """Creates a tool or tools based on the provided configuration."""
        tool_id, module_path, package_path, func_names, src_file = (config.get(k) for k in ["id", "module_path", "package_path", "functions", "source_file"])
        if not all([tool_id, module_path, func_names, src_file]):
            logger.warning(f"Python tool config is missing required fields. Skipping.")
            return ToolCreationResult(
                tools=[],
                requested_functions=func_names or [],
                found_functions=[],
                missing_functions=func_names or [],
                error="Missing required configuration fields"
            )
        source_dir = os.path.dirname(os.path.abspath(src_file))
        try:
            loaded_tools = []
            found_functions = []
            missing_functions = []
            
            # Look for the specific function names requested in the config
            for func_spec in func_names:
                if not isinstance(func_spec, str):
                    logger.warning(f"Function spec '{func_spec}' is not a string in tool config '{tool_id}'. Skipping.")
                    missing_functions.append(str(func_spec))
                    continue
                obj = None
                try:
                    obj = _load_module_attribute(module_path, func_spec, package_path, source_dir)
                except (ImportError, AttributeError, FileNotFoundError) as e:
                    logger.warning(f"Error loading function '{func_spec}' from module '{module_path}' (package_path '{package_path}')): {e}")
                    missing_functions.append(func_spec)
                    continue
                    
                # Accept any callable object - removed tool_spec check as it's unreliable
                if callable(obj):
                    # Clean up the tool name to remove path prefixes
                    clean_function_name = func_spec.split('.')[-1]
                    
                    # If the object has a tool_spec, update it with clean name
                    if hasattr(obj, 'tool_spec') and isinstance(obj.tool_spec, dict):
                        if 'name' in obj.tool_spec:
                            original_name = obj.tool_spec['name']
                            obj.tool_spec['name'] = clean_function_name
                            logger.debug(f"Renamed tool from '{original_name}' to '{clean_function_name}'")
                    
                    loaded_tools.append(obj)
                    found_functions.append(func_spec)
                    logger.debug(f"Successfully loaded callable '{func_spec}' as '{clean_function_name}' from module '{module_path}'")
                else:
                    logger.warning(f"Object '{func_spec}' in module '{module_path}' is not callable. Skipping.")
                    missing_functions.append(func_spec)
            
            logger.info(f"Successfully loaded {len(loaded_tools)} tools from Python module: {tool_id}")
            return ToolCreationResult(
                tools=loaded_tools,
                requested_functions=func_names,
                found_functions=found_functions,
                missing_functions=missing_functions,
                error=None
            )
        except Exception as e:
            logger.error(f"Failed to extract tools from Python module '{tool_id}': {e}")
            return ToolCreationResult(
                tools=[],
                requested_functions=func_names,
                found_functions=[],
                missing_functions=func_names,
                error=str(e)
            )

