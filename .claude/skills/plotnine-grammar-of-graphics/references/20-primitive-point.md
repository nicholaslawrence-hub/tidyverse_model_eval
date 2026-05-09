# Primitive: Points

Use points for observation-level comparisons between two variables.

```python
p = (
    ggplot(df, aes(x='hp', y='mpg', color='factor(cyl)'))
    + geom_point(alpha=0.8, size=3)
    + labs(x='Horsepower', y='Miles per gallon', color='Cylinders')
    + theme_minimal()
)
```

For dense or grouped plots, use jitter:

```python
+ geom_jitter(width=0.15, alpha=0.4)
```

Eval checks usually look for `geom_point`, quoted `aes()` columns, categorical `factor(...)`, labels, theme, and save behavior.

