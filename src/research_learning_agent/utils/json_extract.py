import re
import json
from ..logging_utils import get_logger


logger = get_logger("utils.json_extract")


def extract_json(text: str) -> dict | None:
    """
    Parses an LLM response to find and extract a single valid JSON object or list.
    """
    if text is None or not isinstance(text, str):
        return None
    
    # 1. Try to find content inside Markdown code blocks
    code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(code_block_pattern, text)
        
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing Error: {e}")
            return None
    
    # 2. If no code blocks, try to find valid JSON by attempting to parse
    # from each potential JSON start position ({ or [)
    for i, char in enumerate(text):
        if char in '{[':
            # Try to find the matching closing brace/bracket
            start_char = char
            end_char = '}' if char == '{' else ']'
            depth = 0
            end_pos = -1
            
            for j in range(i, len(text)):
                if text[j] == start_char:
                    depth += 1
                elif text[j] == end_char:
                    depth -= 1
                    if depth == 0:
                        end_pos = j + 1
                        break
            
            if end_pos > 0:
                # Extract the potential JSON substring
                json_str = text[i:end_pos].strip()
                # Attempt to parse it
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Not valid JSON, continue searching
                    continue
    
    # No valid JSON found
    return None