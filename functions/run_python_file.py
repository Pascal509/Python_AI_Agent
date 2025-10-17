import os
import subprocess
from typing import List


def run_python_file(working_directory: str, file_path: str, args: List[str] = None) -> str:
    """Run a Python file inside working_directory and return formatted output or error strings.

    - Ensures the target is inside working_directory
    - Ensures the file exists and ends with .py
    - Executes with subprocess.run, timeout=30, captures stdout/stderr
    - Returns formatted string with STDOUT:, STDERR:, and exit code if non-zero
    - On exceptions, returns: Error: executing Python file: {e}
    """
    if args is None:
        args = []

    try:
        candidate = os.path.join(working_directory, file_path)
        base_real = os.path.realpath(working_directory)
        target_real = os.path.realpath(candidate)

        try:
            common = os.path.commonpath([base_real, target_real])
        except Exception:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if common != base_real:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        if not os.path.exists(target_real):
            return f'Error: File "{file_path}" not found.'

        if not file_path.endswith('.py'):
            return f'Error: "{file_path}" is not a Python file.'

        # Build command: use the same python interpreter that's running this script
        cmd = [os.sys.executable, target_real] + args

        completed = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=base_real,
            timeout=30,
            text=True,
        )

        out = completed.stdout or ''
        err = completed.stderr or ''

        if not out and not err:
            return 'No output produced.'

        parts = []
        if out:
            parts.append('STDOUT:\n' + out)
        if err:
            parts.append('STDERR:\n' + err)

        if completed.returncode != 0:
            parts.append(f'Process exited with code {completed.returncode}')

        return '\n'.join(parts)

    except Exception as e:
        return f'Error: executing Python file: {e}'

