# Primitive: Bars And Text

Use bars for counts or summarized categories.

```python
p = (
    ggplot(df, aes(x='factor(cyl)', fill='factor(cyl)'))
    + geom_bar()
    + labs(x='Cylinders', y='Count', fill='Cylinders')
    + theme_classic()
)
```

For stat-computed labels, prefer `after_stat(...)` and `format_string`.

```python
+ geom_text(
    aes(label=after_stat('prop*100'), group=1),
    stat='count',
    nudge_y=0.5,
    format_string='{:.1f}%'
)
```

Eval checks usually look for `geom_bar`, `geom_text`, `after_stat`, `format_string`, `factor(...)`, labels/theme, and save behavior.

