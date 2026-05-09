import sys
import json
import time
from pathlib import Path

import plotnine_eval as pn_eval

try:
    import great_tables_eval as gt_eval
except ImportError:
    gt_eval = None

GREEN, RED, YELLOW, BOLD, CYAN, RESET = (
    "\033[92m", "\033[91m", "\033[93m", "\033[1m", "\033[96m", "\033[0m"
)


def run_suite(name: str, cases, run_fn, case_ids: list[str] | None = None):
    filtered = [c for c in cases if case_ids is None or c.id in case_ids]
    if not filtered:
        return []

    print(f"\n{BOLD}{CYAN}{'=' * 64}{RESET}")
    print(f"{BOLD}{CYAN}  Suite: {name}  ({len(filtered)} cases){RESET}")
    print(f"{BOLD}{CYAN}{'=' * 64}{RESET}\n")

    results = []
    for case in filtered:
        print(f"  [{case.id}] ...", end="", flush=True)
        t0 = time.perf_counter()
        result = run_fn(case)
        elapsed = time.perf_counter() - t0
        results.append(result)
        icon = f"{GREEN}PASS{RESET}" if result.passed else f"{RED}FAIL{RESET}"
        print(f" {icon}  ({result.score:.0%})  [{elapsed:.1f}s]")

    return results


def print_combined_report(pn_results, gt_results) -> None:
    print(f"\n{BOLD}{'=' * 64}{RESET}")
    print(f"{BOLD}  COMBINED REPORT{RESET}")
    print(f"{BOLD}{'=' * 64}{RESET}\n")

    def suite_line(name, results):
        if not results:
            return f"  {name:<20} --  (skipped)"
        passed = sum(r.passed for r in results)
        total = len(results)
        avg = sum(r.score for r in results) / total
        color = GREEN if passed == total else (YELLOW if passed > 0 else RED)
        return f"  {name:<20} {color}{passed}/{total} passed{RESET}  |  avg score {avg:.0%}"

    print(suite_line("plotnine", pn_results))
    print(suite_line("great-tables", gt_results))

    all_results = pn_results + gt_results
    if all_results:
        grand_passed = sum(r.passed for r in all_results)
        grand_total = len(all_results)
        grand_avg = sum(r.score for r in all_results) / grand_total
        color = GREEN if grand_passed == grand_total else (YELLOW if grand_passed > 0 else RED)
        print(f"\n  {'TOTAL':<20} {color}{grand_passed}/{grand_total} passed{RESET}  |  avg score {grand_avg:.0%}\n")


def save_combined_report(pn_results, gt_results) -> None:
    def serialize(results, tool):
        return [
            {
                "id": r.case_id,
                "tool": tool,
                "category": r.category,
                "score": round(r.score, 3),
                "passed": r.passed,
                "checks": [
                    {"name": c.name, "passed": c.passed, "detail": c.detail}
                    for c in r.check_results
                ],
                "generated_code": r.generated_code,
                "graph_nodes": getattr(r, "graph_nodes", []),
                "prompt_variant": getattr(r, "prompt_variant", None),
                "image_eval": getattr(r, "image_eval", None),
                "llm_judge": getattr(r, "llm_judge", None),
                "vision_judge": getattr(r, "vision_judge", None),
            }
            for r in results
        ]

    all_results = pn_results + gt_results
    report = {
        "model": "claude-sonnet-4-6",
        "summary": {
            "total": len(all_results),
            "passed": sum(r.passed for r in all_results),
            "avg_score": round(sum(r.score for r in all_results) / len(all_results), 3) if all_results else 0,
            "plotnine": {
                "total": len(pn_results),
                "passed": sum(r.passed for r in pn_results),
            },
            "great_tables": {
                "total": len(gt_results),
                "passed": sum(r.passed for r in gt_results),
            },
        },
        "cases": serialize(pn_results, "plotnine") + serialize(gt_results, "great-tables"),
    }
    path = "eval_report.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Combined report saved -> {path}")


def main() -> None:
    args = sys.argv[1:]

    run_plotnine = True
    run_gt = True
    case_ids: list[str] | None = None

    pn_ids = {c.id for c in pn_eval.CASES}
    gt_cases = getattr(gt_eval, "CASES", []) if gt_eval else []
    gt_ids = {c.id for c in gt_cases}

    if args:
        first = args[0].lower().replace("-", "_")
        if first == "plotnine":
            run_gt = False
            case_ids = args[1:] or None
        elif first in ("great_tables", "great-tables"):
            run_plotnine = False
            case_ids = args[1:] or None
        else:
            # Treat all args as case IDs
            case_ids = args
            run_plotnine = any(i in pn_ids for i in case_ids)
            run_gt = any(i in gt_ids for i in case_ids)

    pn_results = []
    gt_results = []

    if run_plotnine:
        pn_case_ids = [i for i in (case_ids or [])] if case_ids else None
        pn_case_ids = [i for i in pn_case_ids if i in pn_ids] if pn_case_ids else None
        pn_results = run_suite("plotnine", pn_eval.CASES, pn_eval.run_eval_case, pn_case_ids)
        if pn_results:
            pn_eval.print_report(pn_results)

    if run_gt:
        gt_case_ids = [i for i in (case_ids or [])] if case_ids else None
        gt_case_ids = [i for i in gt_case_ids if i in gt_ids] if gt_case_ids else None
        if not gt_cases:
            print("\n  great-tables        --  (skipped: use great_tables_eval/great_tables_eval.py)")
        else:
            gt_results = run_suite("great-tables", gt_cases, gt_eval.run_eval_case, gt_case_ids)
        if gt_results and hasattr(gt_eval, "print_report"):
            gt_eval.print_report(gt_results)

    print_combined_report(pn_results, gt_results)
    if pn_results or gt_results:
        save_combined_report(pn_results, gt_results)


if __name__ == "__main__":
    main()
