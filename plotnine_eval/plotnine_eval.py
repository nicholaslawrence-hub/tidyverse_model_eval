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

client = anthropic.Anthropic()

PLOTNINE_SYSTEM = """You are a Python data visualization expert specializing in the Python visualization library plotnine, developed by Posit.
When given a task, respond with ONLY valid, complete, runnable Python code. 

Rules you must follow:
- `from plotnine import *` at the top (always star-import)
- Column names in aes() must be quoted strings: aes(x='col'), never aes(x=col)
- Categorical variables: wrap in factor() inside aes — aes(fill='factor(cyl)')
- Stat-computed text labels: use after_stat() and format_string parameter, not f-strings    
- Use Pandas for data manipulation and import pd.df into plotnine for visualizations 
"""

# ─── Data structures ──────────────────────────────────────────────────────────

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

    @property
    def score(self) -> float:
        if not self.check_results:
            return 0.0
        return sum(c.passed for c in self.check_results) / len(self.check_results)

    @property
    def passed(self) -> bool:
        return self.score >= 0.7


# ─── Utilities ────────────────────────────────────────────────────────────────

def extract_code(text):
    match = re.search(r"```(?:python)?\n?(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


def run_code(code: str, timeout: int = 45) -> tuple[int, str, str]:
    """Write code to a temp file, execute it, return (returncode, stdout, stderr)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=".") as f:
        f.write(code)
        tmp = f.name
    try:
        result = subprocess.run(
            [sys.executable, tmp],
            capture_output=True, text=True, timeout=timeout, cwd="."
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TimeoutExpired after 45s"
    finally:
        os.unlink(tmp)
        Path("output.png").unlink(missing_ok=True)

def ask_claude(prompt: str) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": PLOTNINE_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_code(response.content[0].text)


# ─── Grader helpers ───────────────────────────────────────────────────────────

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


# ─── Eval cases ───────────────────────────────────────────────────────────────

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


def load_cases(path: str = "cases.json") -> list[EvalCase]:
    with open(path) as f:
        return [EvalCase(**c, graders=GRADERS.get(c["id"], [])) for c in json.load(f)]


CASES = load_cases()

CASES_BY_ID = {c.id: c for c in CASES}

def run_eval_case(case: EvalCase) -> EvalResult:
    code = ask_claude(case.prompt)
    rc, stdout, stderr = run_code(code)

    check_results = []
    for name, grader_fn in case.graders:
        passed, detail = grader_fn(code, rc, stdout, stderr)
        check_results.append(CheckResult(name=name, passed=passed, detail=detail))

    return EvalResult(
        case_id=case.id,
        category=case.category,
        prompt=case.prompt,
        generated_code=code,
        check_results=check_results,
    )


def print_report(results: list[EvalResult]) -> None:
    GREEN, RED, YELLOW, BOLD, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[0m"

    print(f"\n{BOLD}{'─' * 32}{RESET}")
    print(f"{BOLD}  plotnine Eval Report{RESET}")
    print(f"{BOLD}{'─' * 32}{RESET}\n")

    by_category: dict[str, list[EvalResult]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    for cat, cat_results in by_category.items():
        print(f"{BOLD}[{cat}]{RESET}")
        for r in cat_results:
            word = f"{GREEN}PASS{RESET}" if r.passed else f"{RED}FAIL{RESET}"
            print(f"  {word} {r.case_id}  ({r.score:.0%})")
            for c in r.check_results:
                sym = f"{GREEN}✓{RESET}" if c.passed else f"{RED}✗{RESET}"
                detail = f"  {YELLOW}→ {c.detail}{RESET}" if c.detail else ""
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
            }
            for r in results
        ],
    }
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved → {path}")


def main(case_ids: list[str] | None = None) -> None:
    cases = [CASES_BY_ID[cid] for cid in case_ids] if case_ids else CASES

    print(f"Running {len(cases)} plotnine eval case(s)...")
    results = []
    for case in cases:
        print(f"  [{case.id}] ...", end="", flush=True)
        result = run_eval_case(case)
        results.append(result)
        icon = "✓" if result.passed else "✗"
        print(f" {icon}  ({result.score:.0%})")

    print_report(results)
    save_report(results)


if __name__ == "__main__":
    ids = sys.argv[1:] or None
    if ids and any(i not in CASES_BY_ID for i in ids):
        unknown = [i for i in ids if i not in CASES_BY_ID]
        print(f"Unknown case ids: {unknown}")
        print(f"Available: {list(CASES_BY_ID.keys())}")
        sys.exit(1)
    main(ids)
