#!/usr/bin/env python3
"""
Utility to launch the current file as a module based on its path relative to the workspace.
"""

import sys
import runpy
import os


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: launch_current_module.py <script_path> [args...]")
        sys.exit(1)

    script_path = sys.argv[1]
    abs_path = os.path.abspath(script_path)
    # Determine workspace root (current working directory)
    wd = os.getcwd()
    if abs_path.startswith(wd + os.sep):
        rel = abs_path[len(wd) + 1 :]
    else:
        rel = abs_path
    # Strip .py extension and convert path separators to dots
    if rel.lower().endswith(".py"):
        rel = rel[:-3]
    module_path = rel.replace(os.sep, ".")

    if module_path.startswith("src."):
        module_path = module_path[4:]
    if module_path.endswith(".__main__"):
        module_path = module_path[:-9]

    while ".src." in module_path:
        start_index = module_path.find(".src.")
        module_path = module_path[start_index + 4 :]

    # Pass through any remaining args to the module
    sys.argv = sys.argv[2:]
    # Run as module
    runpy.run_module(module_path, run_name="__main__")


if __name__ == "__main__":
    main()
