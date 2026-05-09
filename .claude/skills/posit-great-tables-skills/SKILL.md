---
name: posit-great-tables-skills
description: Work on this repository's Great Tables and DSPy skill-generation pipeline. Use when modifying great_tables_eval.py, src/pipeline.py, setup.py, Caltrain timetable prompts, LangSmith datasets, DSPy MIPROv2 optimization, generated SKILL.md files, or Great Tables transit schedule evaluation.
---

# Posit Great Tables Skills

Use this skill for the `great_tables_eval` part of the project.

## Workflow

1. Read `great_tables_eval/src/pipeline.py` before changing the generator, judge, metric, or save behavior.
2. Check `great_tables_eval/great_tables_eval.py` for the CLI entrypoints: `compile`, `run`, and `eval`.
3. Treat `NOTEBOOK_CONTEXT` as the project's reference implementation for styled Caltrain timetable output.
4. Keep the generated skill focused on repeatable Great Tables timetable construction, not general table advice.
5. Preserve the score threshold behavior unless the user asks to change acceptance criteria.

## Pipeline Shape

The pipeline has three main pieces:

- `SkillGenerator`: generates a complete `SKILL.md` from a user prompt, template, and notebook context.
- `SkillJudge`: scores the generated skill for correctness, coverage, trigger accuracy, concision, and timetable faithfulness.
- `MIPROv2`: compiles the generator from LangSmith examples.

Generated skills are saved to `skills/transit_table/SKILL.md` only when the judge score is at least `SCORE_THRESHOLD`.

## LangSmith Dataset Work

Use `great_tables_eval/setup.py` when preparing the prompt datasets. Keep train and test prompts distinct, and make sure dataset names in code and environment variables line up.

Watch for small string-concatenation mistakes in prompt lists, especially adjacent string literals without commas.

## Environment Notes

The current code reads:

- `LANGCHAIN_API_KEY` for LangSmith,
- `LANGCHAIN_PROJECT` in `setup.py`,
- `GEMINI_API_KEY` while configuring a DSPy LM string that names an Anthropic model.

If authentication fails, inspect the provider/key pairing before changing model logic.

## Useful Commands

From `great_tables_eval`:

```bash
python great_tables_eval.py compile
python great_tables_eval.py run "make a commuter rail timetable from this CSV"
python great_tables_eval.py eval
python setup.py
```

## Great Tables Timetable Expectations

The reference schedule emphasizes:

- fare zones as a stub/grouping signal,
- train-number columns,
- skipped stops represented by missing values,
- strong header styling,
- row striping,
- official schedule-like typography and spacing,
- source notes and clear labels.

