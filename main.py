import os
import sys
import argparse
from google.genai import types
from functions.get_files_info import available_functions


# Optional: load environment variables from a .env file if python-dotenv is installed.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # It's fine if dotenv isn't available; environment vars may be set externally.
    pass

try:
    from google import genai
except Exception:
    print("The 'google.genai' client library is required. Install it with 'pip install google-genai' and try again.", file=sys.stderr)
    sys.exit(1)

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)
# messages will be constructed per-request inside generate_content using the prompt


def generate_content(prompt: str):
    """Generate content from the model for the given prompt.

    Returns: (text, prompt_tokens, response_tokens)
    """
    # System prompt to instruct the model about using tools
    system_prompt = """
You are a helpful AI coding agent.

When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

- List files and directories

All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
"""

    # Build the typed messages list: a single user Content with a Part containing the prompt.
    messages = [
        types.Content(role="user", parts=[types.Part(text=prompt)]),
    ]

    # Call the model when the function is invoked so we get a fresh response each run.
    response = client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=messages,
        config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[available_functions]),
    )

    # Some client implementations return usage_metadata as an attribute or a dict.
    usage = getattr(response, "usage_metadata", None)

    if usage is None:
        prompt_tokens = "N/A"
        response_tokens = "N/A"
    else:
        if hasattr(usage, 'prompt_token_count'):
            prompt_tokens = usage.prompt_token_count
        elif isinstance(usage, dict) and 'prompt_token_count' in usage:
            prompt_tokens = usage['prompt_token_count']
        else:
            prompt_tokens = "N/A"

        if hasattr(usage, 'candidates_token_count'):
            response_tokens = usage.candidates_token_count
        elif isinstance(usage, dict) and 'candidates_token_count' in usage:
            response_tokens = usage['candidates_token_count']
        else:
            response_tokens = "N/A"

    # If the LLM made a function call, print it. Otherwise show normal text.
    function_calls = getattr(response, 'function_calls', None)

    text = getattr(response, 'text', None)
    if (not text) and function_calls:
        # Print the first function call's name and args
        first_call = function_calls[0]
        name = getattr(first_call, 'name', None) or first_call.get('name')
        args = getattr(first_call, 'args', None) or first_call.get('args')
        print(f"Calling function: {name}({args})")
        # We still fall through to extract text from candidates if available
    
    if text is None:
        candidates = getattr(response, 'candidates', None)
        if candidates and len(candidates) > 0:
            text = getattr(candidates[0], 'content', None) or getattr(candidates[0], 'text', None)

    return (text or ""), prompt_tokens, response_tokens


def main():
    # Parse command-line arguments: a single positional prompt and an optional --verbose flag.
    parser = argparse.ArgumentParser(description="Generate content from Gemini model.")
    parser.add_argument('prompt', help='The user prompt as a single quoted string')
    parser.add_argument('--verbose', action='store_true', help='Print prompt and token counts')
    args = parser.parse_args()

    prompt = args.prompt
    response_text, prompt_tokens, response_tokens = generate_content(prompt)

    # Print the model response and token counts in the requested format.
    print(response_text)

    if args.verbose:
        # Print the user's prompt and token counts only when verbose is requested.
        print(f'User prompt: "{prompt}"')
        print(f"Prompt tokens: {prompt_tokens}")
        print(f"Response tokens: {response_tokens}")


if __name__ == "__main__":
    main()