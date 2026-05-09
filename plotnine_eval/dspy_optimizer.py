from pathlib import Path

import dspy
from dspy.teleprompt import MIPROv2

try:
    from .few_shot_examples import format_few_shot_examples
except ImportError:
    from few_shot_examples import format_few_shot_examples


COMPILED_DSPY_PATH = Path(__file__).resolve().parent / "compiled_plotnine_program.json"

PLOTNINE_RUBRIC = """
Score generated Plotnine code using this rubric:
- Correct grammar-of-graphics path: data -> aes -> geoms/stats -> facets/scales -> labels/themes -> save.
- Prompt faithfulness: requested geoms, columns, transformations, themes, labels, and output path are present.
- Plotnine correctness: code is runnable, uses quoted aes columns, uses factor(...) for categorical numeric variables, and uses after_stat/format_string for computed stat labels.
- Image quality: rendered output should be nonblank and visually consistent with the requested chart type.
- Do not award high scores to code that merely contains matching strings but does not satisfy the chart task.
"""


class GeneratePlotnineCode(dspy.Signature):
    """Generate complete runnable Python code for a Plotnine chart using graph context, few-shot examples, and a judge rubric."""

    task_prompt: str = dspy.InputField(desc="Natural-language chart request.")
    graph_context: str = dspy.InputField(desc="Active grammar-of-graphics graph context for this request.")
    few_shot_examples: str = dspy.InputField(desc="Few-shot examples showing high-quality Plotnine code.")
    rubric: str = dspy.InputField(desc="Evaluation rubric used by the LLM judge.")
    code: str = dspy.OutputField(desc="Only complete runnable Python code. No markdown fences.")


class PlotnineCodeGenerator(dspy.Module):
    def __init__(self):
        self.generate = dspy.ChainOfThought(GeneratePlotnineCode)

    def forward(self, task_prompt: str, graph_context: str):
        return self.generate(
            task_prompt=task_prompt,
            graph_context=graph_context,
            few_shot_examples=format_few_shot_examples(),
            rubric=PLOTNINE_RUBRIC,
        )


def make_trainset(cases, build_graph_context):
    trainset = []
    for case in cases:
        context = build_graph_context(case.id, case.category, case.prompt)
        trainset.append(
            dspy.Example(
                task_prompt=case.prompt,
                graph_context=context["context"],
                case=case,
            ).with_inputs("task_prompt", "graph_context")
        )
    return trainset


def compile_program(cases, build_graph_context, metric, num_trials: int = 5, save_path: Path = COMPILED_DSPY_PATH):
    trainset = make_trainset(cases, build_graph_context)
    optimizer = MIPROv2(
        metric=metric,
        auto="light",
        num_trials=num_trials,
    )
    compiled = optimizer.compile(PlotnineCodeGenerator(), trainset=trainset)
    compiled.save(str(save_path))
    return compiled
