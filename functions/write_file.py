import os


def write_file(working_directory, file_path, content):
    """Write content to file_path inside working_directory.

    Returns an error string starting with 'Error:' on failure, otherwise a success string.
    """
    try:
        candidate = os.path.join(working_directory, file_path)

        base_real = os.path.realpath(working_directory)
        target_real = os.path.realpath(candidate)

        try:
            common = os.path.commonpath([base_real, target_real])
        except Exception:
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        if common != base_real:
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        # Ensure parent directory exists
        parent_dir = os.path.dirname(target_real)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        # Overwrite the file with the provided content
        with open(target_real, 'w', encoding='utf-8') as f:
            f.write(content)

        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'
    except Exception as e:
        return f'Error: {str(e)}'

