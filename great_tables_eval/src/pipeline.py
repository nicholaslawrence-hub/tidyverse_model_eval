import os
from langsmith import Client
import dspy
from dspy.teleprompt import MIPROv2


client = Client(api_key=os.getenv("LANGCHAIN_API_KEY")) if os.getenv("LANGCHAIN_API_KEY") else None

COMPILED_PATH = "optimized_skill_generator.json"
SKILL_OUTPUT = "skills/transit_table/SKILL.md"
SCORE_THRESHOLD = 0.7


NOTEBOOK_CONTEXT = """
# CSV Structure
- fare_zone: int (1-4, inserted manually)
- Stop: station name string
- Train columns: numbered 601, 603, 605... (odd = local, even = express), values like "6:51a", "7:26a", NaN for skipped stops

# Data loading
caltrain_df = pd.read_csv("caltrain_weekend_northbound.csv")
caltrain_df.insert(0, 'fare_zone', [4]*4 + [3]*6 + [2]*10 + [1]*4)

# GT Table construction
train_columns = caltrain_df.filter(regex=("^6")).columns.tolist()
caltrain_table = (
    GT(caltrain_df)
    .tab_header(title=html('<span style="color: rgb(224,37,33); font-weight: bold; font-size: 40px;">Northbound &ndash;</span>...'))
    .tab_stub('fare_zone')
    .tab_source_note(source_note="Sourced from CalTrain's 01/31/26 weekend schedule.")
    .cols_width(cases={'Stop': '300px'})
    .opt_align_table_header(align='left')
    .cols_align(align='center')
    .tab_style(locations=loc.header(), style=style.css("color: rgb(224,37,33) !important; font-size: 35px !important; font-weight: bold !important;"))
    .tab_style(locations=loc.column_labels(), style=style.css("background-color: black !important; color: white !important; font-size: 16px !important; font-weight: bold !important;"))
    .tab_style(locations=loc.stub(), style=style.css("background-color: rgb(224,37,33) !important; color: white !important; writing-mode: sideways-lr; font-size: 14px !important;"))
    .tab_style(locations=loc.body(), style=style.css("height: 10px !important; border-left: solid #a2a7a8 1px !important; border-right: solid #a2a7a8 1px !important; color: black !important"))
    .tab_options(row_group_as_column=True, row_striping_background_color="#e1e2e2")
    .cols_label(Stop='Train No.', fare_zone='Fare Zone')
    .opt_row_striping()
    .opt_table_outline()
    .opt_table_font(font=google_font('frutiger'))
)
"""

SKILL_TEMPLATE = """
# [Skill Name]

## Description
[When to use this skill]

## Dependencies
[pip packages]

## CSV Schema
[expected columns]

## Step-by-step Instructions
[numbered steps]

## Code Example
[complete working code]

## Notes
[gotchas, edge cases]
"""

# DSPy signatures

class GenerateSkill(dspy.Signature):
    """Generate a complete SKILL.md file for assisting users writing transit timetables using GT, with a CSV source
    Inputs: user_prompt, notebook_context
    Outputs: skill_md
    """ 
 
    user_prompt: str = dspy.InputField(desc="Specifics regarding timetable construction from GT")
    notebook_context: str = dspy.InputField(desc="Reference implementation from a working notebook")
    skill_template: str = dspy.InputField(desc='Template for skill.md output')
    skill_md: str = dspy.OutputField(desc="Complete SKILL.md with description, dependencies, common failure modes, and a working code example using styled Great Tables")


class JudgeSkill(dspy.Signature):
    """Evaluate a SKILL.md file for correctness, coverage, trigger accuracy, and conciseness, and faithfulness to styled timetable design.
    Return a float score between 0.0 and 1.0."""
 
    user_prompt: str = dspy.InputField()
    skill_md: str = dspy.InputField()
    score: float = dspy.OutputField(desc="Composite quality score between 0.0 and 1.0")
    reasoning: str = dspy.OutputField(desc="Brief explanation covering correctness, coverage, trigger accuracy, conciseness, timetable faithfulness")

# DSPy Modules for skill generation and evaluation

class SkillGenerator(dspy.Module):
    def __init__(self):
        self.generate = dspy.ChainOfThought(GenerateSkill)
 
    def forward(self, user_prompt):
        return self.generate(
            user_prompt=user_prompt,
            skill_template=SKILL_TEMPLATE,
            notebook_context=NOTEBOOK_CONTEXT
        )
 
class SkillJudge(dspy.Module):
    def __init__(self):
        self.judge = dspy.ChainOfThought(JudgeSkill)
 
    def forward(self, user_prompt, skill_md):
        return self.judge(user_prompt=user_prompt, skill_md=skill_md)

_judge = SkillJudge()

def skill_metric(example, prediction, trace=None):
    result = _judge(
        user_prompt=example.user_prompt,
        skill_md=prediction.skill_md
    )
    return float(result.score)

# Pulls from langsmith dataset for training prompts for optimization

def load_trainset(dataset_name: str = "transit-skill-train") -> list:
    if not os.getenv("LANGCHAIN_API_KEY"):
        raise RuntimeError("LANGCHAIN_API_KEY must be set to load LangSmith datasets.")
    client = Client(api_key=os.getenv("LANGCHAIN_API_KEY"))
    examples = list(client.list_examples(dataset_name=dataset_name))
    print(f"Loaded {len(examples)} examples from LangSmith")
    return [
        dspy.Example(user_prompt=ex.inputs["prompt"]).with_inputs("user_prompt")
        for ex in examples
    ]

# Compiles using prompts from Langchain database, runs over 10 trials

def compile(dataset_name: str = "transit-skill-prompts", num_trials: int = 10):
    if not dspy.settings.lm:
        raise RuntimeError("DSPy is not configured with an LM. Run through great_tables_eval.py or call dspy.configure first.")
    trainset = load_trainset(dataset_name)
    optimizer = MIPROv2(
        metric=skill_metric, 
        auto="medium", 
        num_trials=num_trials
    )
    compiled = optimizer.compile(SkillGenerator(), trainset=trainset)
    compiled.save(COMPILED_PATH)
    print(f"Saved to {COMPILED_PATH}")
    return compiled
 
def run(user_prompt: str, save_skill: bool = True):
    if not dspy.settings.lm:
        raise RuntimeError("DSPy is not configured with an LM. Run through great_tables_eval.py or call dspy.configure first.")
    generator = SkillGenerator()
    if os.path.exists(COMPILED_PATH):
        generator.load(COMPILED_PATH)
        print(f"Using generator from {COMPILED_PATH}")
 
    result = generator(user_prompt=user_prompt)
    judge_result = _judge(user_prompt=user_prompt, skill_md=result.skill_md)
 
    print(f"\nScore: {judge_result.score:.2f}")
 
    if save_skill:
        if float(judge_result.score) >= SCORE_THRESHOLD:
            os.makedirs(os.path.dirname(SKILL_OUTPUT), exist_ok=True)
            with open(SKILL_OUTPUT, "w") as f:
                f.write(result.skill_md)
            print(f"Skill saved to {SKILL_OUTPUT}")
 
    return result.skill_md, judge_result
 
def eval_dataset(dataset_name: str = "transit-skill-test"):
    if not dspy.settings.lm:
        raise RuntimeError("DSPy is not configured with an LM. Run through great_tables_eval.py or call dspy.configure first.")
    trainset = load_trainset(dataset_name)
    generator = SkillGenerator()
    if os.path.exists(COMPILED_PATH):
        generator.load(COMPILED_PATH)
 
    scores = []
    for ex in trainset:
        result = generator(user_prompt=ex.user_prompt)
        judge_result = _judge(user_prompt=ex.user_prompt, skill_md=result.skill_md)
        score = float(judge_result.score)
        scores.append(score)
        print(f"  [{score:.2f}] {ex.user_prompt}")
    return scores
