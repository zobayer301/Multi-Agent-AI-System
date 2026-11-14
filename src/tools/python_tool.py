"""
Safe Python Execution Tool for Quantitative & Statistical Analysis.

Enables the Analysis Agent to execute programmatic calculations:
- Calculates statistics, percentages, margins, compound growth, and data aggregation.
- Sandboxed environment with restricted built-in primitives and whitelist imports.
- Captures standard output and expression results.
- Robust exception handling to prevent crashing agent workflows.
"""

import sys
import io
import math
import statistics
import json
import datetime
import logging
from agents import function_tool

logger = logging.getLogger("tools.python_tool")

# Whitelist of modules permitted to be imported
ALLOWED_MODULES = {"math", "statistics", "json", "datetime", "decimal"}


def _safe_import(name, *args, **kwargs):
    """Restricted __import__ allowing only safe mathematical and data libraries."""
    if name in ALLOWED_MODULES:
        return __import__(name, *args, **kwargs)
    raise ImportError(f"Import of module '{name}' is restricted for security reasons.")


# Restricted safe execution environment
SAFE_GLOBALS = {
    "__builtins__": {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "range": range,
        "enumerate": enumerate,
        "zip": zip,
        "map": map,
        "filter": filter,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "print": print,
        "__import__": _safe_import,
    },
    "math": math,
    "statistics": statistics,
    "json": json,
    "datetime": datetime,
}


def execute_python_analysis_fn(code: str) -> str:
    """
    Safely execute a Python snippet to perform quantitative, mathematical, or statistical analysis.

    Use this tool to calculate growth rates, perform statistical aggregations, compute percentages,
    or verify mathematical claims.

    Args:
        code: Python source code snippet to execute. Output results using `print(...)`.

    Returns:
        The printed stdout from the code, or an error description if execution fails.
    """
    cleaned_code = code.strip()
    if not cleaned_code:
        return "Error: Code snippet cannot be empty."

    stdout_buffer = io.StringIO()
    old_stdout = sys.stdout

    try:
        sys.stdout = stdout_buffer
        local_scope = {}
        # Execute code in safe environment
        exec(cleaned_code, SAFE_GLOBALS.copy(), local_scope)

        captured_output = stdout_buffer.getvalue().strip()

        if captured_output:
            return f"Execution Output:\n{captured_output}"
        elif local_scope:
            filtered_vars = {k: v for k, v in local_scope.items() if not k.startswith("_")}
            return f"Execution Completed (Variables: {filtered_vars})"
        else:
            return "Execution completed successfully with no output."

    except Exception as e:
        logger.warning(f"Python execution error: {e}")
        return f"Python Execution Error: {type(e).__name__}: {str(e)}"

    finally:
        sys.stdout = old_stdout


# Decorated OpenAI Agents SDK FunctionTool
execute_python_analysis = function_tool(execute_python_analysis_fn)
