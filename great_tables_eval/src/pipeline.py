import os
from langsmith import Client
from langsmith.schemas import Run, Example
from src.generator import generate_skill
from src.evaluators import score_candidates, pick_best

langsmith_client = Client(api_key=os.getenv("LANGCHAIN_API_KEY"))

def run_pipeline(user_prompt: str, save_skill: bool = True) -> dict:
    print(f"\nPrompt: {user_prompt}\n")

    candidates = generate_skill(user_prompt, n_candidates=3)
    results = score_candidates(user_prompt, candidates)
    best = pick_best(results)

    print(f"\nBest candidate: #{best['candidate_index']+1}")
    print(f"Composite score: {best['scores']['composite']:.2f}")
    for dim, val in best['scores'].items():
        if dim != 'composite':
            print(f"  {dim}: {val['score']}/5 — {val['reasoning']}")

    if save_skill and best['scores']['composite'] >= 3.5:
        path = "skills/transit_table/SKILL.md"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(best['skill'])
        print(f"\nSkill saved to {path}")
    elif save_skill:
        print(f"\nSkill not saved — composite score {best['scores']['composite']:.2f} below threshold 3.5")

    return best

def run_eval_on_dataset(dataset_name: str = "transit-skill-prompts"):
    examples = list(langsmith_client.list_examples(dataset_name=dataset_name))

    all_results = []
    for ex in examples:
        prompt = ex.inputs["prompt"]
        result = run_pipeline(prompt, save_skill=False)
        all_results.append({"prompt": prompt, "result": result})

    scores = [r["result"]["scores"]["composite"] for r in all_results]
    print(f"\n=== Eval Summary ===")
    print(f"Mean composite score: {sum(scores)/len(scores):.2f}")
    print(f"Min: {min(scores):.2f} | Max: {max(scores):.2f}")
    return all_results