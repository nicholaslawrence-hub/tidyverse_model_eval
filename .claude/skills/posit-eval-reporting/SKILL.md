---
name: posit-eval-reporting
description: Summarize, explain, or document this repository's LLM evaluation outputs. Use when writing README sections, resume descriptions, eval summaries, model comparison notes, JSON report interpretations, or concise explanations of pass rates, per-case checks, generated code, and failure details.
---

# Posit Eval Reporting

Use this skill when turning raw eval machinery or reports into clear writing.

## Reporting Style

Write in a direct, project-specific voice. Avoid generic phrases like "robust framework", "seamless integration", "leveraged cutting-edge", or "end-to-end solution" unless the user specifically asks for resume-style corporate language.

Prefer explaining what the harness actually does:

- prompts a model,
- extracts generated code or skill text,
- runs or judges the output,
- scores concrete checks,
- saves reports that make failures inspectable.

## What To Read

For implementation summaries, read:

- `run_evals.py`,
- `plotnine_eval/plotnine_eval.py`,
- `great_tables_eval/src/pipeline.py`.

For report interpretation, read generated files such as:

- `eval_report.json`,
- `plotnine_eval_report.json`,
- any generated `skills/transit_table/SKILL.md`.

## Output Summary Pattern

When summarizing reports, prefer a compact table:

```markdown
| Suite | Cases | Passed | Average Score | Notes |
|---|---:|---:|---:|---|
| plotnine | 0 | 0 | 0% | No report found |
```

Then add a short paragraph about the most important failure mode or improvement opportunity.

## Resume Wording

Keep resume lines concrete and personal to the project. Mention tools only when they clarify the work.

Good shape:

```text
Built a Python eval harness that prompts an LLM to generate Plotnine code, runs the generated scripts, scores task-specific checks, and writes inspectable JSON reports.
```

For the Great Tables side:

```text
Built a DSPy/LangSmith pipeline that generates and judges reusable Great Tables skills for styled Caltrain timetable workflows.
```

## Caveats To Mention

Mention these when relevant:

- model-backed evals require API keys,
- malformed `cases.json` will stop Plotnine case loading,
- the current DSPy provider/key naming should be checked before running,
- generated plots and reports are runtime artifacts.

