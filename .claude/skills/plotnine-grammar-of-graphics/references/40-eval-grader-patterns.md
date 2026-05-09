# Eval Grader Patterns

An eval case should align three things:

1. The natural-language prompt.
2. The generated Plotnine code behavior.
3. The grader checks.

Good grader signals are objective:

- code executes,
- expected geom appears,
- expected column appears,
- categorical mapping uses `factor(...)`,
- stat labels use `after_stat(...)` and `format_string`,
- plot is saved,
- requested theme/facet/labels are present.

Keep superficial string checks tied to real failure modes. For example, checking for `factor(` is useful when the model often treats numeric categories as continuous.

When adding a case, update `GRADERS` in `plotnine_eval.py` and add a matching object in `cases.json`.

