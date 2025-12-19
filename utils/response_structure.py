from utils.packages import *

def safe_json_loads(llm_text: str) -> dict:
    """
    Extracts and parses JSON from LLM output safely.
    Handles markdown fences and extra text.
    """
    # 1. Strip markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_text)
    if fenced:
        llm_text = fenced.group(1)

    # 2. Trim whitespace
    llm_text = llm_text.strip()

    # 3. Parse JSON
    return json.loads(llm_text)