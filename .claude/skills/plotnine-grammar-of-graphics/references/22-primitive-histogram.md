# Primitive: Histograms

Use histograms for one-variable distributions.

```python
p = (
    ggplot(df, aes(x='Avg_Daily_Usage_Hours', fill='Gender'))
    + geom_histogram(bins=20, alpha=0.7)
    + facet_wrap('Academic_Level')
    + labs(
        title='Daily Social Media Usage',
        x='Average daily usage hours',
        y='Count',
        fill='Gender'
    )
    + theme_bw()
)
```

Prefer explicit `bins` when the prompt gives one.

Use `fill` for group distribution comparisons and `alpha` when groups overlap.

Eval checks usually look for `geom_histogram`, the target column, `fill`, `facet_`, `labs`, theme, and save behavior.

