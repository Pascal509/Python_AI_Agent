try:
    from google.genai import types
except Exception:
    types = None

# Import individual schema_* declarations from their modules if present
schema_get_files_info = None
schema_get_file_content = None
schema_run_python_file = None
schema_write_file = None

try:
    from functions.get_files_info import schema_get_files_info as _s1
    schema_get_files_info = _s1
except Exception:
    pass

try:
    from functions.get_file_content import schema_get_file_content as _s2
    schema_get_file_content = _s2
except Exception:
    pass

try:
    from functions.run_python_file import schema_run_python_file as _s3
    schema_run_python_file = _s3
except Exception:
    pass

try:
    from functions.write_file import schema_write_file as _s4
    schema_write_file = _s4
except Exception:
    pass

if types is not None:
    decls = []
    for s in (schema_get_files_info, schema_get_file_content, schema_run_python_file, schema_write_file):
        if s is not None:
            decls.append(s)

    if decls:
        available_functions = types.Tool(function_declarations=decls)
    else:
        available_functions = None
else:
    available_functions = None
