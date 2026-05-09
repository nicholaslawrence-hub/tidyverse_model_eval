# intent-relationship

Use when the prompt asks how two quantitative variables relate.

Signals: scatter plot, relationship, correlation, x versus y, compare horsepower and mpg.

Primary path:

```text
intent-relationship -> primitive-point -> layer-aesthetic-mapping -> primitive-smooth? -> layer-labels-theme -> output-save
```

Usually maps `x` and `y` to numeric columns. Add `color='factor(...)'` when a categorical grouping is requested.

