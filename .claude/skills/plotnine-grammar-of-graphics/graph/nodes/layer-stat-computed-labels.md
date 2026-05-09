# layer-stat-computed-labels

Use for labels computed by a stat layer, especially bar counts and percentages.

Preferred pattern:

```python
+ geom_text(
    aes(label=after_stat('prop*100'), group=1),
    stat='count',
    nudge_y=0.5,
    format_string='{:.1f}%'
)
```

Do not use f-strings for values computed by Plotnine stats.

