import os
import json
from typing import Any

try:
    from google.genai import types
except Exception:
    types = None

from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.run_python_file import run_python_file
from functions.write_file import write_file


def call_function(function_call_part, verbose: bool = False) -> Any:
    """Invoke one of the available functions based on a FunctionCall-like object.

    - function_call_part: object with .name and .args
    - verbose: whether to print detailed call information

    Returns a types.Content with from_function_response describing the result or error when types is available.
    If types is not available, returns a simple dict with the result.
    """

    # Extract function name
    function_name = getattr(function_call_part, 'name', None)
    raw_args = getattr(function_call_part, 'args', None)

    # Print according to verbose
    if verbose:
        print(f"Calling function: {function_name}({raw_args})")
    else:
        print(f" - Calling function: {function_name}")

    # Parse args: sometimes args are provided as a JSON string
    kwargs = {}
    if raw_args:
        if isinstance(raw_args, str):
            try:
                kwargs = json.loads(raw_args)
            except Exception:
                # fallback: not JSON, leave as empty or attempt eval? keep safe
                kwargs = {}
        elif isinstance(raw_args, dict):
            kwargs = raw_args.copy()

    # Ensure working_directory is injected and cannot be overridden by the LLM
    kwargs['working_directory'] = os.path.join('.', 'calculator')

    # Map function names to actual callables
    function_map = {
        'get_files_info': get_files_info,
        'get_file_content': get_file_content,
        'run_python_file': run_python_file,
        'write_file': write_file,
    }

    if function_name not in function_map:
        err_msg = f"Unknown function: {function_name}"
        if types is not None:
            return types.Content(
                role="tool",
                parts=[
                    types.Part.from_function_response(
                        name=function_name,
                        response={"error": err_msg},
                    )
                ],
            )
        return {"error": err_msg}

    func = function_map[function_name]

    try:
        result = func(**kwargs)
    except Exception as e:
        err_msg = f"Error executing function {function_name}: {e}"
        if types is not None:
            return types.Content(
                role="tool",
                parts=[
                    types.Part.from_function_response(
                        name=function_name,
                        response={"error": err_msg},
                    )
                ],
            )
        return {"error": err_msg}

    # Ensure the response is serializable: wrap into dict
    response_dict = {"result": result}

    if types is not None:
        return types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response=response_dict,
                )
            ],
        )

    return response_dict

