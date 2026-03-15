import re
import json

def parse_json(text: str) -> any:
    """Strips markdown fences and parses JSON robustly."""
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback if the model included some preamble
        match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise
