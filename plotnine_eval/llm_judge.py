import base64
import json
import os
import re
from pathlib import Path

import anthropic


JUDGE_MODEL = os.getenv("PLOTNINE_JUDGE_MODEL", "claude-sonnet-4-5")

JUDGE_RUBRIC = """
Evaluate the generated Plotnine answer as a chart-building artifact, not as a string-matching exercise.

Score 0.0 to 1.0 using:
- Prompt faithfulness: chart type, columns, grouping, labels, theme, facets, and save path match the request.
- Grammar-of-graphics correctness: data, aes mappings, geoms/stats, facets/scales, labels/themes, and output saving are composed correctly.
- Plotnine-specific correctness: columns are quoted in aes(), categorical numeric variables use factor(...), stat labels use after_stat(...) and format_string, and the code is runnable.
- Evidence from deterministic checks: use these checks as supporting evidence, but do not let token presence alone override the actual task.
- For image judging: verify that the rendered chart visually matches the requested primitive, encodings, labels, and layout.

Return only JSON:
{
  "score": 0.0,
  "passed": false,
  "reasoning": "...",
  "strengths": ["..."],
  "failures": ["..."]
}
"""


def require_judge_key() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY is required because LLM-as-a-judge is mandatory for Plotnine evals.")


def _json_from_text(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    raw = match.group(0) if match else text
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"score": 0.0, "passed": False, "reasoning": f"Judge returned non-JSON: {text[:300]}"}


def judge_code(prompt: str, code: str, graph_nodes: list[str], check_summary: list[dict]) -> dict:
    require_judge_key()
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=700,
        system=(
            "You are a strict evaluator for Plotnine code.\n\n"
            f"{JUDGE_RUBRIC}"
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    "Evaluate whether this generated Plotnine code satisfies the prompt and the active "
                    "grammar graph nodes.\n\n"
                    f"Prompt:\n{prompt}\n\n"
                    f"Active graph nodes:\n{graph_nodes}\n\n"
                    f"Deterministic checks:\n{json.dumps(check_summary, indent=2)}\n\n"
                    f"Generated code:\n```python\n{code}\n```"
                ),
            }
        ],
    )
    return _json_from_text(response.content[0].text)


def judge_image(prompt: str, image_path: str | Path, graph_nodes: list[str]) -> dict:
    require_judge_key()
    path = Path(image_path)
    image_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=700,
        system=(
            "You are a strict visual evaluator for Plotnine chart images.\n\n"
            f"{JUDGE_RUBRIC}"
        ),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Evaluate whether this chart image visually satisfies the prompt and active grammar "
                            f"nodes.\n\nPrompt:\n{prompt}\n\nActive graph nodes:\n{graph_nodes}"
                        ),
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64,
                        },
                    },
                ],
            }
        ],
    )
    return _json_from_text(response.content[0].text)
