# Primitive: Lines And Smooths

Use lines for ordered data, time-like data, or grouped summaries.

```python
p = (
    ggplot(df_grouped, aes(x='Age', y='mean_score'))
    + geom_line(color='steelblue', size=1)
    + geom_point(size=2)
    + labs(x='Age', y='Mean mental health score')
    + theme_minimal()
)
```

Use smoothing layers for trend lines over scatter plots.

```python
+ geom_smooth(method='lm', se=False)
```

If multiple groups should get separate lines, map `color` or `group` inside `aes()`.

Eval checks usually look for `geom_line`, `geom_point`, `geom_smooth` when requested, referenced summary columns, labels, and save behavior.

