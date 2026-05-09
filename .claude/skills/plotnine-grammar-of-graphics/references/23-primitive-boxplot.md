# Primitive: Boxplots

Use boxplots for comparing numeric distributions across groups.

```python
p = (
    ggplot(df, aes(x='factor(cyl)', y='mpg', fill='factor(cyl)'))
    + geom_boxplot()
    + labs(x='Cylinders', y='Miles per gallon')
    + theme_minimal()
)
```

Overlay jitter when individual observations matter:

```python
+ geom_jitter(width=0.15, alpha=0.4)
```

Facet when the prompt asks for repeated group comparisons:

```python
+ facet_wrap('factor(gear)')
```

Eval checks usually look for `geom_boxplot`, optional `geom_jitter`, categorical `factor(...)`, fill/color, facets when requested, theme, and save behavior.

