import os
import sys
import argparse
import json
import time
from google.genai import types
from functions.schemas import available_functions
from functions.call_function import call_function


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


def generate_content(prompt: str, verbose: bool = False):
    """Generate content from the model for the given prompt.

    Returns: (text, prompt_tokens, response_tokens)
    """
    # System prompt to instruct the model about using tools
    system_prompt = """
    You are a helpful AI coding agent.

    When a user asks a question or makes a request, make a function call plan. You can perform the following operations:

    - List files and directories
    - Read file contents
    - Execute Python files with optional arguments
    - Write or overwrite files

    All paths you provide should be relative to the working directory. You do not need to specify the working directory in your function calls as it is automatically injected for security reasons.
    """

    # Build the typed messages list: only the user prompt is included in contents.
    # The system instruction is passed separately via GenerateContentConfig.system_instruction
    messages = [
        types.Content(role="user", parts=[types.Part(text=prompt)]),
    ]

    # Tool-invocation loop: keep calling the model with the full messages list
    # and execute any function calls the model requests until it stops.
    while True:
        # Call the model with retries/backoff to handle transient server-side errors
        max_attempts = 5
        attempt = 0
        while True:
            try:
                response = client.models.generate_content(
                    model='gemini-2.0-flash-001',
                    contents=messages,
                    config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[available_functions]),
                )
                break
            except Exception as e:
                attempt += 1
                # For transient errors (like 503/429), retry with exponential backoff
                if attempt >= max_attempts:
                    # Re-raise the exception after exhausting retries
                    raise
                backoff = 2 ** (attempt - 1)
                if verbose:
                    print(f"Transient error calling model (attempt {attempt}/{max_attempts}): {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                continue

        # Some client implementations return usage_metadata as an attribute or a dict.
        usage = getattr(response, "usage_metadata", None)

        # Append all candidates to the conversation as assistant messages so
        # the model's chosen candidate(s) become part of the message history.
        candidates = getattr(response, 'candidates', None)
        if candidates:
            for cand in candidates:
                cand_content = getattr(cand, 'content', None) or getattr(cand, 'text', None)

                # Normalize candidate content to a plain string. The API may return
                # a nested Content object (with parts) or a dict; ensure we pass
                # a string into types.Part(text=...).
                cand_text = None
                if isinstance(cand_content, str):
                    cand_text = cand_content
                else:
                    # If it's a Content-like object with parts, extract text from parts
                    if hasattr(cand_content, 'parts'):
                        parts_texts = []
                        for p in getattr(cand_content, 'parts') or []:
                            t = getattr(p, 'text', None) or getattr(p, 'content', None)
                            if t is not None:
                                parts_texts.append(t)
                        if parts_texts:
                            cand_text = "\n".join(parts_texts)

                    # As a fallback, JSON-serialize the candidate content
                    if cand_text is None:
                        try:
                            cand_text = json.dumps(cand_content, default=str)
                        except Exception:
                            cand_text = str(cand_content)

                if cand_text:
                    messages.append(types.Content(role="assistant", parts=[types.Part(text=cand_text)]))

        # Check for function calls
        function_calls = getattr(response, 'function_calls', None)

        # If there are function calls, execute the first one and append the tool response
        if function_calls:
            first_call = function_calls[0]
            if verbose:
                print(f"Calling function: {getattr(first_call, 'name', None)}({getattr(first_call, 'args', None)})")

            # Execute the function using our helper
            function_call_result = call_function(first_call, verbose=verbose)

            # Ensure we got a types.Content back
            if not (hasattr(function_call_result, 'parts') and function_call_result.parts):
                raise RuntimeError('Invalid function result returned by call_function')

            # Extract the function response payload
            part = function_call_result.parts[0]
            function_response = getattr(part, 'function_response', None)
            if function_response is None:
                raise RuntimeError('Invalid function result: missing function_response')

            response_payload = getattr(function_response, 'response', None)
            if response_payload is None:
                raise RuntimeError('Invalid function result: missing response payload')

            # Append the tool response as a tool message so the model can continue.
            tool_text = types.Part.from_function_response(name=part.function_response.name, response=response_payload)
            tool_content = types.Content(role="tool", parts=[tool_text])
            messages.append(tool_content)

            # Also append the function response as a user-role message (serialized)
            # so the model sees the function result as part of the conversation.
            user_text = types.Part(text=json.dumps(response_payload))
            user_content = types.Content(role="user", parts=[user_text])
            messages.append(user_content)

            # Loop to call the model again with the updated messages
            continue

        # No function calls requested — break and proceed to extract text and usage
        break

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

    # Extract final text/candidate from the last model response
    text = getattr(response, 'text', None)
    had_text = text is not None
    if text is None:
        candidates = getattr(response, 'candidates', None)
        if candidates and len(candidates) > 0:
            text = getattr(candidates[0], 'content', None) or getattr(candidates[0], 'text', None)

    # Return an extra flag (had_text) that is True when response.text was present
    return (text or ""), prompt_tokens, response_tokens, had_text

def main():
    # Parse command-line arguments: a single positional prompt and an optional --verbose flag.
    parser = argparse.ArgumentParser(description="Generate content from Gemini model.")
    parser.add_argument('prompt', help='The user prompt as a single quoted string')
    parser.add_argument('--verbose', action='store_true', help='Print prompt and token counts')
    args = parser.parse_args()

    prompt = args.prompt

    # Call generate_content repeatedly to allow the agent to iterate on the prompt.
    # Limit to 20 iterations to avoid infinite loops.
    max_iters = 20
    for i in range(max_iters):
        try:
            response_text, prompt_tokens, response_tokens, had_text = generate_content(prompt, verbose=args.verbose)
        except Exception as e:
            print(f"Error during generation: {e}")
            break

        print(f"[Iteration {i+1}]")
        print(response_text)

        if args.verbose:
            # Print the user's prompt and token counts only when verbose is requested.
            print(f'User prompt: "{prompt}"')
            print(f"Prompt tokens: {prompt_tokens}")
            print(f"Response tokens: {response_tokens}")

        # If the model returned a final response in response.text, we're done
        if had_text:
            break


if __name__ == "__main__":
    main()