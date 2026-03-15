import re
import json

def parse_json(text: str) -> any:
    """Strips markdown fences and parses JSON robustly."""
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback if the model included some preamble or trailing text
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            # Handle cases where the model might include "..." inside a list/dict
            json_str = re.sub(r',\s*\.\.\.\s*\]', ']', json_str) # Trailing ... in list
            json_str = re.sub(r',\s*\.\.\.\s*\}', '}', json_str) # Trailing ... in dict
            return json.loads(json_str)
        raise
