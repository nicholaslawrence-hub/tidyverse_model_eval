# grader-plotnine-eval

Use when converting graph expectations into eval checks.

Good checks:

- `executes_without_error`
- `uses_geom_point`, `uses_geom_bar`, etc.
- required column name appears
- `factor(` appears for categorical numeric variables
- `after_stat` and `format_string` appear for computed labels
- `facet_` appears for small multiples
- `labs` appears for labels
- `theme_*` or `theme(` appears for presentation requirements
- `.save(` or `ggsave(` appears for output

Keep each grader attached to a graph node or edge. If a prompt requires a visual behavior, either grade it or mark it as intentionally ungraded.

