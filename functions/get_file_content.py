import os
from .config import MAX_FILE_CHARS


def get_file_content(working_directory, file_path):
    """Read and return the contents of a file inside working_directory.

    Returns error strings prefixed with 'Error:' on failures.
    """
    # Build the candidate absolute path
    candidate = os.path.join(working_directory, file_path)

    # Resolve real paths to handle symlinks
    base_real = os.path.realpath(working_directory)
    target_real = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([base_real, target_real])
    except Exception:
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

    if common != base_real:
        return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

    # Ensure the target exists and is a regular file
    if not os.path.exists(target_real) or not os.path.isfile(target_real):
        return f'Error: File not found or is not a regular file: "{file_path}"'

    try:
        with open(target_real, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        return f'Error: {str(e)}'

    # Truncate if too long
    if len(content) > MAX_FILE_CHARS:
        truncated = content[:MAX_FILE_CHARS]
        truncated += f"[...File \"{file_path}\" truncated at {MAX_FILE_CHARS} characters]"
        return truncated

    return content
