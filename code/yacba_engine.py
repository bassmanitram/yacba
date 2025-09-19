"""
Core engine for YACBA .
Contains the core, reusable logic for the YACBA agent with lazy loading and caching.
"""

import os
from typing import List, Optional
from contextlib import ExitStack
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

# Import focused types
from yacba_types.models import Agent, Model, FrameworkAdapter
from yacba_types.tools import Tool, ToolLoadResult
from yacba_types.content import Message
from yacba_config import YacbaConfig
from model_loader import StrandsModelLoader
from custom_handler import SilentToolUseCallbackHandler

# Import optimized components
from performance_utils import (
    lazy_import_strands, lazy_import_framework_adapters, 
    timed_operation, perf_monitor, fs_cache
)
from tool_factory import ToolFactory


class YacbaEngine:
    """
    Core engine for YACBA .
    
    Features:
    - Lazy loading of heavy dependencies
    - Caching of expensive operations
    - Performance monitoring and statistics
    - Parallel tool initialization
    - Memory-efficient resource management
    
    Focused on YACBA's responsibilities:
    - Configuration management and validation
    - Tool configuration and connection (not execution)
    - Model selection and framework adaptation
    - Agent orchestration and lifecycle management
    """
    
    def __init__(self, config: YacbaConfig, initial_messages: Optional[List[Message]] = None):
        self.config = config
        self.initial_messages = initial_messages or []
        self.agent: Optional[Agent] = None
        self.loaded_tools: List[Tool] = []
        self.framework_adapter: Optional[FrameworkAdapter] = None
        self._exit_stack = ExitStack()
        self._tool_factory = ToolFactory(self._exit_stack)
        
        # Performance tracking
        perf_monitor.increment_counter("engine_initializations")
        logger.debug("YacbaEngine initialized with performance monitoring.")

    @timed_operation("tool_initialization")
    def _initialize_all_tools(self) -> List[Tool]:
        """
        Uses a thread pool to initialize all configured tools in parallel with performance monitoring.
        YACBA handles configuration and connection, strands handles execution.
        
        Returns:
            List of successfully loaded tools
        """
        all_tools: List[Tool] = []
        all_errors: List[str] = []
        
        # Filter out disabled tools early
        enabled_configs = [
            config for config in self.config.tool_configs
            if not config.get("disabled", False)
        ]
        
        if not enabled_configs:
            logger.info("No enabled tool configurations found.")
            return []
        
        logger.info(f"Initializing {len(enabled_configs)} tool configurations in parallel...")
        
        with ThreadPoolExecutor(max_workers=min(4, len(enabled_configs))) as executor:
            # Submit tool loading tasks
            future_to_config = {
                executor.submit(self._tool_factory.create_tools, config): config
                for config in enabled_configs
            }

            # Collect results with progress tracking
            completed = 0
            for future in as_completed(future_to_config):
                config = future_to_config[future]
                tool_id = config.get("id", "unknown-tool")
                completed += 1
                
                try:
                    result: ToolLoadResult = future.result()
                    all_tools.extend(result["tools"])
                    all_errors.extend(result["errors"])
                    
                    if result["tools"]:
                        logger.info(f"[{completed}/{len(enabled_configs)}] Successfully loaded {len(result['tools'])} tools from config '{tool_id}'")
                        perf_monitor.increment_counter("successful_tool_loads")
                    if result["errors"]:
                        logger.warning(f"[{completed}/{len(enabled_configs)}] Errors loading tools from config '{tool_id}': {result['errors']}")
                        perf_monitor.increment_counter("tool_load_errors", len(result["errors"]))
                        
                except Exception as e:
                    error_msg = f"Exception initializing tool '{tool_id}': {e}"
                    logger.error(error_msg)
                    all_errors.append(error_msg)
                    perf_monitor.increment_counter("tool_load_exceptions")
        
        if all_errors:
            logger.warning(f"Tool loading completed with {len(all_errors)} errors")
        
        logger.info(f"Total tools loaded: {len(all_tools)}")
        perf_monitor.increment_counter("total_tools_loaded", len(all_tools))
        return all_tools

    @timed_operation("model_initialization")
    def _initialize_model_and_framework(self) -> bool:
        """
        Initialize the model and framework adapter with lazy loading.
        YACBA handles model selection, strands handles execution.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load model using YACBA's model loader
            loader = StrandsModelLoader()
            result = loader.create_model(self.config.model_string, self.config.model_config)
            
            if not result["success"]:
                logger.error(f"Failed to load model: {result['error']}")
                perf_monitor.increment_counter("model_load_failures")
                return False
            
            model: Model = result["model"]
            logger.info(f"Model loaded successfully: {self.config.model_string}")
            perf_monitor.increment_counter("successful_model_loads")
            
            # Get framework adapter with lazy loading
            get_framework_adapter = lazy_import_framework_adapters()
            self.framework_adapter = get_framework_adapter(model)
            self.loaded_tools = self.framework_adapter.adapt_tools(self.loaded_tools, self.config.model_string)
            
            logger.info(f"Framework adapter initialized: {type(self.framework_adapter).__name__}")
            perf_monitor.increment_counter("framework_adapter_initializations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize model and framework: {e}")
            perf_monitor.increment_counter("model_framework_errors")
            return False

    @timed_operation("agent_creation")
    def _create_agent(self) -> bool:
        """
        Create the strands agent with lazy loading.
        YACBA handles configuration, strands handles execution.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Lazy import strands Agent
            Agent = lazy_import_strands()
            
            # Create callback handler
            handler = SilentToolUseCallbackHandler(show_tool_use=self.config.show_tool_use)
            
            self.agent = Agent(
                tools=self.loaded_tools, 
                model=self.framework_adapter.model,
                system_prompt=self.config.system_prompt,
                callback_handler=handler
            )
            
            logger.info("Agent created successfully")
            perf_monitor.increment_counter("agent_creations")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            perf_monitor.increment_counter("agent_creation_errors")
            return False

    @timed_operation("engine_startup")
    def startup(self) -> bool:
        """
        Initialize the engine with all components and performance monitoring.
        
        Returns:
            True if startup successful, False otherwise
        """
        logger.info("Starting optimized YACBA engine...")
        startup_start_time = perf_monitor.time_operation("total_startup")
        startup_start_time.__enter__()
        
        try:
            # Step 1: Initialize tools in parallel
            logger.info("Step 1/3: Initializing tools...")
            self.loaded_tools = self._initialize_all_tools()
            
            # Step 2: Initialize model and framework
            logger.info("Step 2/3: Initializing model and framework...")
            if not self._initialize_model_and_framework():
                return False
            
            # Step 3: Create agent
            logger.info("Step 3/3: Creating agent...")
            if not self._create_agent():
                return False
            
            logger.info("✅ YACBA engine startup completed successfully!")
            perf_monitor.increment_counter("successful_startups")
            
            # Log performance statistics
            if logger.level("DEBUG").no >= logger._core.min_level:
                perf_monitor.log_stats()
            
            return True
            
        except Exception as e:
            logger.error(f"Engine startup failed: {e}")
            perf_monitor.increment_counter("startup_failures")
            return False
        finally:
            startup_start_time.__exit__(None, None, None)

    def shutdown(self):
        """Clean up resources and log final performance statistics."""
        logger.info("Shutting down YACBA engine...")
        
        with perf_monitor.time_operation("engine_shutdown"):
            try:
                # Close the exit stack to clean up all resources
                self._exit_stack.close()
                
                # Clear references
                self.agent = None
                self.framework_adapter = None
                self.loaded_tools.clear()
                
                logger.info("Engine shutdown completed")
                perf_monitor.increment_counter("clean_shutdowns")
                
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
                perf_monitor.increment_counter("shutdown_errors")
            finally:
                # Log final performance statistics
                logger.info("Final Performance Statistics:")
                perf_monitor.log_stats()

    def is_ready(self) -> bool:
        """Check if the engine is ready for use."""
        return (
            self.agent is not None and 
            self.framework_adapter is not None and 
            len(self.loaded_tools) > 0
        )

    def get_tool_count(self) -> int:
        """Get the number of loaded tools."""
        return len(self.loaded_tools)

    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if self.framework_adapter and hasattr(self.framework_adapter, 'model'):
            return {
                'model_string': self.config.model_string,
                'framework': type(self.framework_adapter).__name__,
                'tools_count': len(self.loaded_tools)
            }
        return {}

    def get_performance_stats(self) -> dict:
        """Get current performance statistics."""
        return perf_monitor.get_stats()

    def clear_performance_cache(self):
        """Clear the performance cache."""
        fs_cache.clear()
        logger.info("Performance cache cleared")


# Maintain backward compatibility
YacbaEngine = YacbaEngine
