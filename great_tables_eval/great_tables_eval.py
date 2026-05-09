import os
import sys
from pathlib import Path

import dspy
from src.pipeline import compile, run, eval_dataset
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / "config.env")
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if ANTHROPIC_API_KEY:
    dspy.configure(lm=dspy.LM("anthropic/claude-sonnet-4-6", api_key=ANTHROPIC_API_KEY))
elif GEMINI_API_KEY:
    dspy.configure(lm=dspy.LM("gemini/gemini-2.5-pro", api_key=GEMINI_API_KEY))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "help"

    if cmd == "compile":
        compile()
    elif cmd == "run":
        prompt = " ".join(sys.argv[2:])
        if not prompt:
            raise SystemExit('Usage: python great_tables_eval.py run "make a train schedule"')
        run(prompt)
    elif cmd == "eval":
        eval_dataset()
    else:
        print("Usage:")
        print("  python great_tables_eval.py compile")
        print('  python great_tables_eval.py run "make a train schedule"')
        print("  python great_tables_eval.py eval")
