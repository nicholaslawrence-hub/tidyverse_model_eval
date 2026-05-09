---
name: posit-repository
description: Orient an agent inside this Posit evaluation repository before working on Plotnine or Great Tables. Use when the task involves repo structure, choosing the right eval subsystem, understanding how run_evals.py relates to plotnine_eval and great_tables_eval, or deciding which project skill/reference to load next.
---

# Posit Repository

Start here for repository-level orientation. This skill is the top of the project hierarchy.

## Map

```text
posit_project/
+-- run_evals.py                    # combined entrypoint; Plotnine case runner plus Great Tables skip notice
+-- plotnine_eval/                  # grammar-of-graphics eval suite
|   +-- cases.json                  # natural-language chart tasks
|   +-- plotnine_eval.py            # model call, generated code execution, graders, report writer
|   +-- plotnine_skill/             # earlier Plotnine skill/reference material
+-- great_tables_eval/              # DSPy/LangSmith skill-generation pipeline
|   +-- great_tables_eval.py        # Great Tables CLI
|   +-- src/pipeline.py             # DSPy generator, judge, optimizer, LangSmith loader
+-- example_datasets/               # CSV inputs used by eval cases
+-- .claude/skills/                 # project-local agent skills
```

## Routing

Use `plotnine-grammar-of-graphics` when the task is about Plotnine chart construction, chart eval cases, aesthetic mappings, geoms, stats, scales, facets, themes, or generated visualization code.

Use `posit-great-tables-skills` only when the task is about the Great Tables/DSPy/LangSmith pipeline. That branch is separate from the Plotnine grammar-of-graphics hierarchy.

Use `posit-eval-reporting` when the task is mainly explaining reports, writing README material, or turning eval behavior into resume/project language.

## Repository Rules

When working on Plotnine evals, keep the eval case, generated-code expectation, and grader checks aligned. Do not add a prompt requirement without a corresponding grader when the requirement is important.

When changing paths, remember generated Plotnine scripts run from the repository root so they can load `example_datasets/...`.

When running model-backed commands, expect API keys and network access to be required.

