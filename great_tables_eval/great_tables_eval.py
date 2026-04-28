import os
import sys
from src.pipeline import run_pipeline, run_eval_on_dataset

if __name__ == "__main__":
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        run_pipeline(prompt, save_skill=True)
    else:
        run_eval_on_dataset("transit-skill-prompts")