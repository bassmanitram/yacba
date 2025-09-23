"""
Performance utilities for YACBA.
Provides lazy loading, caching, and performance monitoring capabilities.
"""

import time
import functools
import threading
import hashlib
import json
from pathlib import Path
from collections import OrderedDict
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from loguru import logger

T = TypeVar('T')

class LazyImporter:
    """Thread-safe lazy import manager to reduce startup time."""
    
    def __init__(self):
        self._modules: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def get_module(self, module_name: str, import_func: Callable[[], T]) -> T:
        """Get a module, importing it only when first accessed."""
        if module_name not in self._modules:
            with self._lock:
                if module_name not in self._modules:
                    logger.debug(f"Lazy loading module: {module_name}")
                    self._modules[module_name] = import_func()
        return self._modules[module_name]

class FileSystemCache:
    """
    A two-tier file system cache for expensive operations.
    Uses an in-memory LRU cache for speed and a disk-based cache for persistence.
    """
    
    def __init__(self, cache_dir: str = ".yacba_cache", memory_limit: int = 256):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self._memory_cache: "OrderedDict[str, Any]" = OrderedDict()
        self._memory_cache_max_size = memory_limit
        self._lock = threading.Lock()
    
    def _get_cache_key(self, operation: str, *args, **kwargs) -> str:
        """Generate a cache key for the operation and arguments."""
        # Convert Path objects to strings for consistent hashing
        processed_args = []
        for arg in args:
            if isinstance(arg, Path):
                processed_args.append(str(arg))
            else:
                processed_args.append(arg)
        
        key_data = f"{operation}:{processed_args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, operation: str, *args, **kwargs) -> Optional[Any]:
        """Get cached result if available, checking memory first, then disk."""
        cache_key = self._get_cache_key(operation, *args, **kwargs)
        
        with self._lock:
            # Tier 1: Check memory LRU cache
            if cache_key in self._memory_cache:
                logger.debug(f"Cache hit (memory): {operation}")
                self._memory_cache.move_to_end(cache_key)  # Mark as recently used
                return self._memory_cache[cache_key]
        
        # Tier 2: Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    result = json.load(f)
                
                # Promote from disk to memory cache
                with self._lock:
                    self._memory_cache[cache_key] = result
                    self._memory_cache.move_to_end(cache_key)
                    if len(self._memory_cache) > self._memory_cache_max_size:
                        self._memory_cache.popitem(last=False)  # Evict oldest item

                logger.debug(f"Cache hit (disk, promoted to memory): {operation}")
                return result
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Cache file corrupted, removing: {e}")
                cache_file.unlink(missing_ok=True)
        
        return None
    
    def set(self, operation: str, result: Any, *args, **kwargs):
        """Cache a result to both memory and disk."""
        cache_key = self._get_cache_key(operation, *args, **kwargs)
        
        with self._lock:
            # Store in memory LRU cache
            self._memory_cache[cache_key] = result
            self._memory_cache.move_to_end(cache_key)
            if len(self._memory_cache) > self._memory_cache_max_size:
                self._memory_cache.popitem(last=False)
        
        # Store on disk
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2)
            logger.debug(f"Cached result to memory and disk: {operation}")
        except (TypeError, IOError) as e:
            logger.debug(f"Could not write to disk cache for {operation}: {e}")
    
    def clear(self):
        """Clear all caches (memory and disk)."""
        with self._lock:
            self._memory_cache.clear()
        
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink(missing_ok=True)
        logger.info("Performance cache cleared (memory and disk)")

class PerformanceMonitor:
    """Built-in performance monitoring with statistics."""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        self.counters: Dict[str, int] = {}
        self._lock = threading.Lock()
    
    def time_operation(self, operation_name: str):
        """Context manager to time operations."""
        return self._TimingContext(self, operation_name)
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a performance counter."""
        with self._lock:
            self.counters[counter_name] = self.counters.get(counter_name, 0) + value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            stats = {
                'timings': {},
                'counters': dict(self.counters)
            }
            
            for operation, timings in self.timings.items():
                if timings:
                    stats['timings'][operation] = {
                        'count': len(timings),
                        'total': sum(timings),
                        'average': sum(timings) / len(timings),
                        'min': min(timings),
                        'max': max(timings)
                    }
            
            return stats
    
    def log_stats(self):
        """Log performance statistics."""
        stats = self.get_stats()
        
        if stats['timings']:
            logger.info("Performance Statistics:")
            for operation, timing_stats in stats['timings'].items():
                logger.info(f"  {operation}: {timing_stats['average']:.3f}s avg "
                          f"({timing_stats['count']} calls, "
                          f"{timing_stats['total']:.3f}s total)")
        
        if stats['counters']:
            logger.info("Performance Counters:")
            for counter, value in stats['counters'].items():
                logger.info(f"  {counter}: {value}")
    
    class _TimingContext:
        def __init__(self, monitor: 'PerformanceMonitor', operation_name: str):
            self.monitor = monitor
            self.operation_name = operation_name
            self.start_time: Optional[float] = None
        
        def __enter__(self):
            self.start_time = time.time()
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.start_time is not None:
                duration = time.time() - self.start_time
                with self.monitor._lock:
                    if self.operation_name not in self.monitor.timings:
                        self.monitor.timings[self.operation_name] = []
                    self.monitor.timings[self.operation_name].append(duration)

# Global instances
lazy_importer = LazyImporter()
fs_cache = FileSystemCache()
perf_monitor = PerformanceMonitor()

def cached_operation(operation_name: str):
    """Decorator to cache expensive operations."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_result = fs_cache.get(operation_name, *args, **kwargs)
            if cached_result is not None:
                perf_monitor.increment_counter(f"{operation_name}_cache_hits")
                return cached_result
            
            # Execute and cache result
            with perf_monitor.time_operation(operation_name):
                result = func(*args, **kwargs)
            
            fs_cache.set(operation_name, result, *args, **kwargs)
            perf_monitor.increment_counter(f"{operation_name}_cache_misses")
            return result
        return wrapper
    return decorator

def timed_operation(operation_name: str):
    """Decorator to time operations without caching."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with perf_monitor.time_operation(operation_name):
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Lazy import helpers for heavy dependencies
def lazy_import_strands():
    """Lazy import of strands library."""
    def _import():
        from strands import Agent
        return Agent
    return lazy_importer.get_module('strands_agent', _import)

def lazy_import_mcp():
    """Lazy import of MCP libraries."""
    def _import():
        from strands.tools.mcp import MCPClient
        from mcp import StdioServerParameters
        from mcp.client.stdio import stdio_client
        from mcp.client.streamable_http import streamablehttp_client
        return {
            'MCPClient': MCPClient,
            'StdioServerParameters': StdioServerParameters,
            'stdio_client': stdio_client,
            'streamablehttp_client': streamablehttp_client
        }
    return lazy_importer.get_module('mcp_libs', _import)

def lazy_import_framework_adapters():
    """Lazy import of framework adapters."""
    def _import():
        from adapters import get_framework_adapter
        return get_framework_adapter
    return lazy_importer.get_module('framework_adapters', _import)
