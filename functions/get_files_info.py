import os
import sys
from datetime import datetime
try:
    from google.genai import types
except Exception:
    types = None


def get_files_info(working_directory, directory="."):
    """Return file information for `directory` which must be inside `working_directory`.

    working_directory: base directory (string)
    directory: relative path within working_directory to list (string)

    If the resolved absolute path for `directory` lies outside `working_directory`,
    return the exact error string:
        f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    Otherwise return a list of dicts, one per directory entry, with fields:
      - name: entry name
      - is_dir: True if entry is a directory
      - size: size in bytes (files), 0 for directories
      - mtime: modification time ISO string
      - relpath: path relative to working_directory
    """

    # Build the candidate path by joining the base working_directory and the requested directory
    candidate = os.path.join(working_directory, directory)

    # Resolve symlinks and get absolute paths for robust comparison
    base_real = os.path.realpath(working_directory)
    target_real = os.path.realpath(candidate)

    try:
        # Ensure the target stays within the base directory using commonpath
        common = os.path.commonpath([base_real, target_real])
    except Exception:
        # If paths are on different drives or invalid, treat as outside
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    if common != base_real:
        return f'Error: Cannot list "{directory}" as it is outside the permitted working directory'

    if not os.path.exists(target_real):
        return f'Error: "{directory}" does not exist'

    if not os.path.isdir(target_real):
        return f'Error: "{directory}" is not a directory'

    try:
        names = sorted(os.listdir(target_real))
    except Exception as e:
        return f"Error: {str(e)}"

    lines = []
    for name in names:
        full = os.path.join(target_real, name)
        try:
            stat = os.stat(full)
            is_dir = os.path.isdir(full)
            size = stat.st_size if not is_dir else 0
        except Exception as e:
            return f"Error: {str(e)}"

        lines.append(f"- {name}: file_size={size} bytes, is_dir={is_dir}")

    return "\n".join(lines)


# Function declaration/schema for use by an LLM
if types is not None:
    schema_get_files_info = types.FunctionDeclaration(
        name="get_files_info",
        description="Lists files in the specified directory along with their sizes, constrained to the working directory.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "directory": types.Schema(
                    type=types.Type.STRING,
                    description="The directory to list files from, relative to the working directory. If not provided, lists files in the working directory itself.",
                ),
            },
        ),
    )

    available_functions = types.Tool(
        function_declarations=[
            schema_get_files_info,
        ]
    )
