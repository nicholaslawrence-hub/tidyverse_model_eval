# intent-counts

Use when the prompt asks for counts by category or percentages of categories.

Signals: bar chart, count, frequency, percentage labels, each cylinder count.

Primary path:

```text
intent-counts -> primitive-bar -> layer-stat-computed-labels? -> primitive-text? -> layer-labels-theme -> output-save
```

Use `geom_bar()` for counts. Use `geom_text(..., stat='count')` with `after_stat(...)` when labels are computed from counts.

