"""
Automated evals for plotnine skill.

Each case asks Claude to generate plotnine code for a specific task, executes
it in a subprocess, then grades the result against objective criteria.

Usage:
    python plotnine_eval.py                  # run all cases
    python plotnine_eval.py scatter_trend    # run one case by id
"""

import anthropic
from dataclasses import dataclass, field
import numpy as np 
import os
import statistics 
import re 
import sys 
import tempfile 
import json
import subprocess 
from pathlib import Path

try:
    from .graph_context import build_graph_context
    from .image_eval import evaluate_image
    from .llm_judge import JUDGE_RUBRIC, judge_code, judge_image, require_judge_key
    from .few_shot_examples import format_few_shot_examples
    from .dspy_optimizer import COMPILED_DSPY_PATH, PlotnineCodeGenerator, compile_program
except ImportError:
    from graph_context import build_graph_context
    from image_eval import evaluate_image
    from llm_judge import JUDGE_RUBRIC, judge_code, judge_image, require_judge_key
    from few_shot_examples import format_few_shot_examples
    from dspy_optimizer import COMPILED_DSPY_PATH, PlotnineCodeGenerator, compile_program

import dspy


client = anthropic.Anthropic()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = Path(__file__).resolve().parent / "cases.json"
OUTPUT_PATH = PROJECT_ROOT / "output.png"

PLOTNINE_SYSTEM = """You are a Python data visualization expert specializing in the Python visualization library plotnine, developed by Posit.
When given a task, respond with ONLY valid, complete, runnable Python code. 

Rules you must follow:
- `from plotnine import *` at the top (always star-import)
- Column names in aes() must be quoted strings: aes(x='col'), never aes(x=col)
- Categorical variables: wrap in factor() inside aes - aes(fill='factor(cyl)')
- Stat-computed text labels: use after_stat() and format_string parameter, not f-strings    
- Use Pandas for data manipulation and import pd.df into plotnine for visualizations 
"""

GRAPH_PROMPT_APPENDIX = """Use the provided grammar-of-graphics knowledge graph as procedural guidance.
Follow the active path from intent to ggplot object, aesthetic mappings, graphical primitives, presentation layers, and output saving.
"""

STRICT_PROMPT_APPENDIX = """Be conservative and literal. If the prompt names a geom, theme, facet, label, or save path, include it exactly.
Return only runnable Python code.
"""

PROMPT_VARIANTS = {
    "baseline": "",
    "graph": GRAPH_PROMPT_APPENDIX,
    "graph_strict": f"{GRAPH_PROMPT_APPENDIX}\n{STRICT_PROMPT_APPENDIX}",
}

# Data structures

class CheckResult:
    def __init__(self, name: str, passed: bool, detail: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail 

@dataclass
class EvalCase:
    id: str
    category: str
    prompt: str
    # Each grader: (name, fn(code, returncode, stdout, stderr) -> (bool, detail_str))
    graders: list = field(default_factory=list)


@dataclass
class EvalResult:
    case_id: str
    category: str
    prompt: str
    generated_code: str
    check_results: list = field(default_factory=list)
    graph_nodes: list[str] = field(default_factory=list)
    prompt_variant: str = "graph"
    image_eval: dict | None = None
    llm_judge: dict | None = None
    vision_judge: dict | None = None

    @property
    def score(self) -> float:
        if self.llm_judge:
            code_score = float(self.llm_judge.get("score", 0.0))
            vision_score = float(self.vision_judge.get("score", 0.0)) if self.vision_judge else 0.0
            image_score = 1.0 if self.image_eval and self.image_eval.get("passed") else 0.0
            return (0.5 * code_score) + (0.35 * vision_score) + (0.15 * image_score)
        return 0.0

    @property
    def passed(self) -> bool:
        llm_passed = bool(self.llm_judge and (self.llm_judge.get("passed") or float(self.llm_judge.get("score", 0)) >= 0.7))
        image_passed = bool(self.image_eval and self.image_eval.get("passed"))
        vision_passed = bool(self.vision_judge and (self.vision_judge.get("passed") or float(self.vision_judge.get("score", 0)) >= 0.7))
        return llm_passed and image_passed and vision_passed


# Utilities

@dataclass
class RunResult:
    returncode: int
    stdout: str
    stderr: str
    output_path: Path

def extract_code(text):
    match = re.search(r"```(?:python)?\n?(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def run_code(code: str, timeout: int = 45) -> RunResult:
    """Write code to a temp file, execute it, return (returncode, stdout, stderr)."""
    OUTPUT_PATH.unlink(missing_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=PROJECT_ROOT) as f:
        f.write(code)
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=timeout, cwd=PROJECT_ROOT
        )
        return RunResult(result.returncode, result.stdout, result.stderr, OUTPUT_PATH)
    except subprocess.TimeoutExpired:
        return RunResult(-1, "", "TimeoutExpired after 45s", OUTPUT_PATH)
    finally:
        os.unlink(tmp)


def build_system_prompt(graph_context: dict | None = None, variant: str = "graph") -> str:
    appendix = PROMPT_VARIANTS.get(variant, PROMPT_VARIANTS["graph"])
    if not graph_context or variant == "baseline":
        return f"{PLOTNINE_SYSTEM}\n{appendix}".strip()

    return (
        f"{PLOTNINE_SYSTEM}\n\n"
        f"{appendix}\n\n"
        f"Few-shot examples:\n{format_few_shot_examples()}\n\n"
        f"Judge rubric:\n{JUDGE_RUBRIC}\n\n"
        f"Active grammar graph nodes: {graph_context['active_nodes']}\n\n"
        f"Graph context:\n{graph_context['context']}"
    ).strip()


def ask_claude(prompt: str, graph_context: dict | None = None, variant: str = "graph") -> str:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": build_system_prompt(graph_context, variant),
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_code(response.content[0].text)


def configure_dspy_lm() -> None:
    if dspy.settings.lm:
        return
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is required for DSPy Plotnine optimization.")
    model = os.getenv("PLOTNINE_DSPY_MODEL", "anthropic/claude-sonnet-4-5")
    dspy.configure(lm=dspy.LM(model, api_key=api_key))


def ask_dspy(prompt: str, graph_context: dict) -> str:
    configure_dspy_lm()
    generator = PlotnineCodeGenerator()
    if COMPILED_DSPY_PATH.exists():
        generator.load(str(COMPILED_DSPY_PATH))
    result = generator(task_prompt=prompt, graph_context=graph_context["context"])
    return extract_code(result.code)


# Grader helpers

def check_executes(code, rc, out, err):
    passed = rc == 0
    detail = (err.strip()[-300:] if err.strip() else "") if not passed else ""
    return passed, detail


def check_uses(token: str):
    def _check(code, rc, out, err):
        passed = token in code
        return passed, f"'{token}' not found in generated code" if not passed else ""
    return _check


def check_saves_plot(code, rc, out, err):
    passed = ".save(" in code or "ggsave(" in code
    return passed, "No .save() or ggsave() call found" if not passed else ""


def check_uses_factor(code, rc, out, err):
    passed = "factor(" in code
    return passed, "Categorical column not wrapped in factor()" if not passed else ""


def check_aes_string_cols(code, rc, out, err):
    """Verify aes() arguments use quoted strings, not bare names."""
    for call in re.findall(r"aes\((.+?)\)", code, re.DOTALL):
        if re.search(r"=\s*[a-zA-Z_][a-zA-Z_0-9]*\b(?!\s*['\"])", call):
            return False, "aes() may contain unquoted column references"
    return True, ""


def check_contains_column(col: str):
    def _check(code, rc, out, err):
        passed = col in code
        return passed, f"Column '{col}' not referenced in code" if not passed else ""
    return _check


def check_image_created(image_info):
    def _check(code, rc, out, err):
        return image_info.passed, image_info.detail
    return _check


def check_llm_judge_result(judge_result):
    def _check(code, rc, out, err):
        passed = bool(judge_result.get("passed", False)) or float(judge_result.get("score", 0)) >= 0.7
        detail = judge_result.get("reasoning", "")
        return passed, detail
    return _check


def check_vision_judge_result(judge_result):
    def _check(code, rc, out, err):
        passed = bool(judge_result.get("passed", False)) or float(judge_result.get("score", 0)) >= 0.7
        detail = judge_result.get("reasoning", "")
        return passed, detail
    return _check


# Eval cases

GRADERS: dict[str, list] = {
    "scatter_trend": [
        ("executes_without_error", check_executes),
        ("uses_geom_point", check_uses("geom_point")),
        ("uses_geom_smooth", check_uses("geom_smooth")),
        ("cyl_as_factor", check_uses_factor),
        ("saves_plot", check_saves_plot),
        ("uses_theme_minimal", check_uses("theme_minimal")),
        ("has_axis_labels", check_uses("labs")),
    ],
    "bar_pct_labels": [
        ("executes_without_error", check_executes),
        ("uses_geom_bar", check_uses("geom_bar")),
        ("uses_geom_text", check_uses("geom_text")),
        ("uses_after_stat", check_uses("after_stat")),
        ("uses_format_string", check_uses("format_string")),
        ("cyl_as_factor", check_uses_factor),
        ("uses_theme_classic", check_uses("theme_classic")),
        ("saves_plot", check_saves_plot),
    ],
    "histogram_social": [
        ("executes_without_error", check_executes),
        ("uses_geom_histogram", check_uses("geom_histogram")),
        ("references_correct_column", check_contains_column("Avg_Daily_Usage_Hours")),
        ("uses_fill", check_uses("fill")),
        ("uses_facet", check_uses("facet_")),
        ("uses_labs", check_uses("labs")),
        ("uses_theme_bw", check_uses("theme_bw")),
        ("saves_plot", check_saves_plot),
    ],
    "boxplot_jitter": [
        ("executes_without_error", check_executes),
        ("uses_geom_boxplot", check_uses("geom_boxplot")),
        ("uses_geom_jitter", check_uses("geom_jitter")),
        ("cyl_as_factor", check_uses_factor),
        ("uses_color_fill", lambda c, *_: ("fill" in c or "color" in c, "")),
        ("saves_plot", check_saves_plot),
    ],
    "facet_wrap_boxplot": [
        ("executes_without_error", check_executes),
        ("uses_geom_boxplot", check_uses("geom_boxplot")),
        ("uses_facet_wrap", check_uses("facet_wrap")),
        ("cyl_as_factor", check_uses_factor),
        ("uses_theme_light", check_uses("theme_light")),
        ("uses_labs_or_ggtitle", lambda c, *_: ("labs" in c or "ggtitle" in c, "No title or labels found")),
        ("saves_plot", check_saves_plot),
    ],
    "line_grouped": [
        ("executes_without_error", check_executes),
        ("uses_geom_line", check_uses("geom_line")),
        ("uses_geom_point", check_uses("geom_point")),
        ("references_mental_health", check_contains_column("Mental_Health_Score")),
        ("uses_labs", check_uses("labs")),
        ("saves_plot", check_saves_plot),
    ],
    "custom_theme": [
        ("executes_without_error", check_executes),
        ("uses_geom_point", check_uses("geom_point")),
        ("uses_theme_bw", check_uses("theme_bw")),
        ("uses_theme_override", check_uses("theme(")),
        ("hides_legend", lambda c, *_: ("legend_position" in c, "legend not hidden")),
        ("uses_element_text", check_uses("element_text")),
        ("saves_plot", check_saves_plot),
    ],
}


def load_cases(path: str | Path = CASES_PATH) -> list[EvalCase]:
    with open(path) as f:
        return [EvalCase(**c, graders=GRADERS.get(c["id"], [])) for c in json.load(f)]


CASES = load_cases()

CASES_BY_ID = {c.id: c for c in CASES}

def evaluate_generated_code(case: EvalCase, code: str, graph_context: dict, prompt_variant: str) -> EvalResult:
    run_result = run_code(code)
    image_info = evaluate_image(run_result.output_path)

    check_results = []
    for name, grader_fn in case.graders:
        passed, detail = grader_fn(code, run_result.returncode, run_result.stdout, run_result.stderr)
        check_results.append(CheckResult(name=name, passed=passed, detail=detail))

    passed, detail = check_image_created(image_info)(code, run_result.returncode, run_result.stdout, run_result.stderr)
    check_results.append(CheckResult(name="image_nonblank", passed=passed, detail=detail))

    summary = [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in check_results]
    llm_result = judge_code(case.prompt, code, graph_context["active_nodes"], summary)
    passed, detail = check_llm_judge_result(llm_result)(code, run_result.returncode, run_result.stdout, run_result.stderr)
    check_results.append(CheckResult(name="llm_judge", passed=passed, detail=detail))

    vision_result = None
    if image_info.exists and image_info.passed:
        vision_result = judge_image(case.prompt, run_result.output_path, graph_context["active_nodes"])
        passed, detail = check_vision_judge_result(vision_result)(code, run_result.returncode, run_result.stdout, run_result.stderr)
        check_results.append(CheckResult(name="vision_judge", passed=passed, detail=detail))
    else:
        check_results.append(CheckResult(name="vision_judge", passed=False, detail="vision judge could not run because no valid image was produced"))

    run_result.output_path.unlink(missing_ok=True)

    return EvalResult(
        case_id=case.id,
        category=case.category,
        prompt=case.prompt,
        generated_code=code,
        check_results=check_results,
        graph_nodes=graph_context["active_nodes"],
        prompt_variant=prompt_variant,
        image_eval=image_info.__dict__,
        llm_judge=llm_result,
        vision_judge=vision_result,
    )


def run_eval_case(case: EvalCase, prompt_variant: str = "graph", backend: str = "anthropic") -> EvalResult:
    require_judge_key()
    graph_context = build_graph_context(case.id, case.category, case.prompt)
    if backend == "dspy":
        code = ask_dspy(case.prompt, graph_context)
        return evaluate_generated_code(case, code, graph_context, "dspy")
    code = ask_claude(case.prompt, graph_context=graph_context, variant=prompt_variant)
    return evaluate_generated_code(case, code, graph_context, prompt_variant)


def dspy_metric(example, prediction, trace=None):
    case = getattr(example, "case", None)
    if case is None:
        return 0.0
    graph_context = build_graph_context(case.id, case.category, case.prompt)
    result = evaluate_generated_code(case, extract_code(prediction.code), graph_context, "dspy_candidate")
    judge_score = float(result.llm_judge.get("score", 0)) if result.llm_judge else 0.0
    vision_score = float(result.vision_judge.get("score", 0)) if result.vision_judge else 0.0
    image_score = 1.0 if result.image_eval and result.image_eval.get("passed") else 0.0
    non_judge_checks = [c for c in result.check_results if c.name not in {"llm_judge", "vision_judge"}]
    deterministic_score = sum(c.passed for c in non_judge_checks) / max(1, len(non_judge_checks))
    return (0.45 * judge_score) + (0.35 * vision_score) + (0.1 * image_score) + (0.1 * deterministic_score)


def optimize_with_dspy(cases: list[EvalCase], num_trials: int = 5):
    require_judge_key()
    configure_dspy_lm()
    return compile_program(cases, build_graph_context, dspy_metric, num_trials=num_trials)


def optimize_prompt_variants(cases: list[EvalCase], variants: list[str] | None = None) -> dict:
    variants = variants or list(PROMPT_VARIANTS)
    report = {"variants": {}, "best_variant": None}

    for variant in variants:
        results = []
        for case in cases:
            result = run_eval_case(case, prompt_variant=variant)
            results.append(result)
        avg = sum(r.score for r in results) / len(results) if results else 0
        report["variants"][variant] = {
            "avg_score": round(avg, 3),
            "passed": sum(r.passed for r in results),
            "total": len(results),
            "results": results,
        }

    report["best_variant"] = max(report["variants"], key=lambda v: report["variants"][v]["avg_score"])
    return report


def print_report(results: list[EvalResult]) -> None:
    GREEN, RED, YELLOW, BOLD, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"

    print(f"\n{BOLD}{'-' * 32}{RESET}")
    print(f"{BOLD}  plotnine Eval Report{RESET}")
    print(f"{BOLD}{'-' * 32}{RESET}\n")

    by_category: dict[str, list[EvalResult]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    for cat, cat_results in by_category.items():
        print(f"{BOLD}[{cat}]{RESET}")
        for r in cat_results:
            word = f"{GREEN}PASS{RESET}" if r.passed else f"{RED}FAIL{RESET}"
            print(f"  {word} {r.case_id}  ({r.score:.0%})")
            for c in r.check_results:
                sym = f"{GREEN}PASS{RESET}" if c.passed else f"{RED}FAIL{RESET}"
                detail = f"  {YELLOW}-> {c.detail}{RESET}" if c.detail else ""
                print(f"      {sym} {c.name}{detail}")
        print()

    total = len(results)
    passed_count = sum(r.passed for r in results)
    median_score = statistics.median(r.score for r in results) if total else 0
    avg_score = sum(r.score for r in results) / total if total else 0
    print(f"{BOLD}Summary of Test Cases: {passed_count}/{total} total cases passed.{RESET}\n Average Eval Score: {avg_score:.0%}{RESET}\n Median Score: {median_score:.0%}")


def save_report(results: list[EvalResult], path: str = "plotnine_eval_report.json") -> None:
    report = {
        "tool": "plotnine",
        "model": "claude-sonnet-4-6",
        "summary": {
            "total": len(results),
            "passed": sum(r.passed for r in results),
            "avg_score": round(sum(r.score for r in results) / len(results), 3) if results else 0,
            "median_score": round(statistics.median(r.score for r in results), 3) if results else 0
        },
        "cases": [
            {
                "id": r.case_id,
                "category": r.category,
                "score": round(r.score, 3),
                "passed": r.passed,
                "checks": [
                    {"name": c.name, "passed": c.passed, "detail": c.detail}
                    for c in r.check_results
                ],
                "generated_code": r.generated_code,
                "graph_nodes": r.graph_nodes,
                "prompt_variant": r.prompt_variant,
                "image_eval": r.image_eval,
                "llm_judge": r.llm_judge,
                "vision_judge": r.vision_judge,
            }
            for r in results
        ],
    }
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved -> {path}")


def save_optimization_report(report: dict, path: str = "plotnine_prompt_optimization_report.json") -> None:
    serializable = {
        "best_variant": report["best_variant"],
        "variants": {
            variant: {
                "avg_score": data["avg_score"],
                "passed": data["passed"],
                "total": data["total"],
                "cases": [
                    {
                        "id": r.case_id,
                        "score": round(r.score, 3),
                        "passed": r.passed,
                        "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in r.check_results],
                        "graph_nodes": r.graph_nodes,
                    }
                    for r in data["results"]
                ],
            }
            for variant, data in report["variants"].items()
        },
    }
    with open(path, "w") as f:
        json.dump(serializable, f, indent=2)
    print(f"Optimization report saved -> {path}")


def main(
    case_ids: list[str] | None = None,
    optimize: bool = False,
    prompt_variant: str = "graph",
    backend: str = "anthropic",
    dspy_optimize: bool = False,
    num_trials: int = 5,
) -> None:
    cases = [CASES_BY_ID[cid] for cid in case_ids] if case_ids else CASES

    if dspy_optimize:
        print(f"Compiling DSPy Plotnine generator over {len(cases)} case(s) with {num_trials} trial(s)...")
        optimize_with_dspy(cases, num_trials=num_trials)
        print(f"Saved compiled DSPy program -> {COMPILED_DSPY_PATH}")
        return

    if optimize:
        print(f"Optimizing prompt variants across {len(cases)} plotnine eval case(s)...")
        report = optimize_prompt_variants(cases)
        for variant, data in report["variants"].items():
            print(f"  {variant:<12} {data['passed']}/{data['total']} passed | avg {data['avg_score']:.0%}")
        print(f"Best variant: {report['best_variant']}")
        save_optimization_report(report)
        return

    print(f"Running {len(cases)} plotnine eval case(s)...")
    results = []
    for case in cases:
        print(f"  [{case.id}] ...", end="", flush=True)
        result = run_eval_case(case, prompt_variant=prompt_variant, backend=backend)
        results.append(result)
        icon = "PASS" if result.passed else "FAIL"
        print(f" {icon}  ({result.score:.0%})")

    print_report(results)
    save_report(results)


if __name__ == "__main__":
    args = sys.argv[1:]
    optimize = "--optimize" in args
    dspy_optimize = "--dspy-optimize" in args
    args = [arg for arg in args if arg not in {"--optimize", "--dspy-optimize"}]
    prompt_variant = "graph"
    backend = "anthropic"
    num_trials = 5
    for arg in list(args):
        if arg.startswith("--variant="):
            prompt_variant = arg.split("=", 1)[1]
            args.remove(arg)
        elif arg.startswith("--backend="):
            backend = arg.split("=", 1)[1]
            args.remove(arg)
        elif arg.startswith("--trials="):
            num_trials = int(arg.split("=", 1)[1])
            args.remove(arg)
    ids = args or None
    if ids and any(i not in CASES_BY_ID for i in ids):
        unknown = [i for i in ids if i not in CASES_BY_ID]
        print(f"Unknown case ids: {unknown}")
        print(f"Available: {list(CASES_BY_ID.keys())}")
        sys.exit(1)
    main(
        ids,
        optimize=optimize,
        prompt_variant=prompt_variant,
        backend=backend,
        dspy_optimize=dspy_optimize,
        num_trials=num_trials,
    )
