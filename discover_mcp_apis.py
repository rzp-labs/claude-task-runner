#!/usr/bin/env python3
"""Discover MCP module APIs for accurate test writing."""

import inspect
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def discover_module_apis(module_name):
    """Discover all public APIs in a module."""
    print(f"\n{'='*60}")
    print(f"Module: {module_name}")
    print('='*60)
    
    try:
        # Import the module
        module = __import__(module_name, fromlist=[''])
        
        # Check for __all__ attribute
        if hasattr(module, '__all__'):
            print(f"\n__all__ exports: {module.__all__}")
        
        # Get all members
        members = inspect.getmembers(module)
        
        # Separate by type
        functions = []
        classes = []
        constants = []
        
        for name, obj in members:
            if name.startswith('_'):
                continue
                
            if inspect.isfunction(obj):
                functions.append((name, obj))
            elif inspect.isclass(obj):
                classes.append((name, obj))
            elif not inspect.ismodule(obj) and not inspect.isbuiltin(obj):
                constants.append((name, obj))
        
        # Print functions
        if functions:
            print("\nFunctions:")
            for name, func in functions:
                sig = inspect.signature(func)
                print(f"  - {name}{sig}")
                if func.__doc__:
                    first_line = func.__doc__.strip().split('\n')[0]
                    print(f"    {first_line}")
        
        # Print classes
        if classes:
            print("\nClasses:")
            for name, cls in classes:
                print(f"  - {name}")
                if cls.__doc__:
                    first_line = cls.__doc__.strip().split('\n')[0]
                    print(f"    {first_line}")
                
                # Show class methods
                methods = inspect.getmembers(cls, predicate=inspect.isfunction)
                public_methods = [(n, m) for n, m in methods if not n.startswith('_')]
                if public_methods:
                    for method_name, method in public_methods:
                        if method_name != '__init__':
                            sig = inspect.signature(method)
                            print(f"      .{method_name}{sig}")
        
        # Print constants
        if constants:
            print("\nConstants/Variables:")
            for name, value in constants:
                print(f"  - {name}: {type(value).__name__}")
        
    except Exception as e:
        print(f"Error importing {module_name}: {e}")

# Discover MCP modules
mcp_modules = [
    'task_runner.mcp.mcp_server',
    'task_runner.mcp.schema',
    'task_runner.mcp.server',
    'task_runner.mcp.wrapper',
]

for module in mcp_modules:
    discover_module_apis(module)