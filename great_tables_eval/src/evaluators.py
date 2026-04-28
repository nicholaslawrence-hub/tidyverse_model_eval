import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

JUDGE_PROMPT = """You are evaluating a SKILL.md file generated for an agentic coding assistant.

The original user prompt was:
<user_prompt>
{user_prompt}
</user_prompt>

The generated skill file is:
<skill>
{skill}
</skill>

Score this skill on each dimension from 1-5 and explain why.

Return ONLY valid JSON in this exact format:
{{
  "coverage": {{"score": <int>, "reasoning": "<str>"}},
  "correctness": {{"score": <int>, "reasoning": "<str>"}},
  "trigger_accuracy": {{"score": <int>, "reasoning": "<str>"}},
  "conciseness": {{"score": <int>, "reasoning": "<str>"}},
  "composite": <float>
}}

Dimensions:
- coverage (1-5): Does the skill fully address what the user asked for?
- correctness (1-5): Is the great_tables API usage valid and would the code actually run?
- trigger_accuracy (1-5): Would an LLM router correctly invoke this skill for relevant prompts?
- conciseness (1-5): Is it tight and actionable, not bloated?
- composite: weighted average — (coverage*0.3 + correctness*0.35 + trigger_accuracy*0.2 + conciseness*0.15)
"""

def judge_skill(user_prompt: str, skill: str) -> dict:
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": JUDGE_PROMPT.format(user_prompt=user_prompt, skill=skill)
        }]
    )
    raw = message.content[0].text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)

def score_candidates(user_prompt: str, candidates: list[str]) -> list[dict]:
    results = []
    for i, candidate in enumerate(candidates):
        print(f"Judging candidate {i+1}/{len(candidates)}...")
        scores = judge_skill(user_prompt, candidate)
        results.append({"candidate_index": i, "scores": scores, "skill": candidate})
    return results

def pick_best(results: list[dict]) -> dict:
    return max(results, key=lambda r: r["scores"]["composite"])