---
name: plotnine
description: Create statistical visualizations using plotnine (Python's ggplot2). Use when asked to build charts, plots, or visualizations with plotnine, ggplot, or grammar-of-graphics style plots in Python.
triggers:
  - plotnine
  - ggplot in Python
  - grammar of graphics
  - geom_point / geom_bar / geom_line (plotnine)
---

## Overview

plotnine is a Python implementation of the Grammar of Graphics, closely mirroring R's ggplot2.
Every plot is built by **layering** components: data → aesthetics → geometries → scales → facets → coordinates → themes.

## Core Pattern

```python
from plotnine import *

p = (
    ggplot(df, aes(x='col_x', y='col_y'))
    + geom_*()          # geometry (required)
    + scale_*()         # axis/color transformations (optional)
    + facet_*()         # small multiples (optional)
    + coord_*()         # coordinate system (optional)
    + labs()            # title, axis labels (optional)
    + theme_*()         # base theme (optional)
    + theme()           # fine-grained overrides (optional)
)
p.save('output.png', dpi=150, width=8, height=6)
```

## Important Considerations


## Critical Rules

1. **Star import** — `from plotnine import *`. The API is designed for it.
2. **String column names** — `aes(x='mpg')`, never `aes(x=mpg)`.
3. **Categorical variables** — wrap with `factor()` inside `aes`: `aes(fill='factor(cyl)')`.
4. **Stat-computed labels** — use `after_stat('count')` / `after_stat('prop*100')` and `format_string="{:.1f}%"` (not f-strings).
5. **Saving** — assign to `p` then call `p.save(...)`. In scripts, the plot won't render unless saved or `.draw()` is called.
6. **Method chaining** — use `+` operator, not `.` — plotnine uses operator overloading, not method chaining.

## Common Tasks with Examples

### Scatter plot with trend line

```python
from plotnine import *
from plotnine.data import mtcars
import pandas as pd

df = pd.DataFrame(mtcars)
p = (
    ggplot(df, aes(x='wt', y='mpg', color='factor(cyl)'))
    + geom_point(alpha=0.8, size=3)
    + geom_smooth(method='lm', se=False)
    + labs(title='MPG vs Weight', x='Weight (1000 lbs)', y='Miles per Gallon', color='Cylinders')
    + theme_minimal()
)
p.save('output.png', dpi=150)
```

### Bar chart with percentage labels
```python
p = (
    ggplot(df, aes(x='factor(cyl)', fill='factor(cyl)'))
    + geom_bar()
    + geom_text(
        aes(label=after_stat('prop*100'), group=1),
        stat='count',
        nudge_y=0.5,
        format_string="{:.1f}%"
    )
    + labs(x='Cylinders', y='Count')
    + theme_classic()
)
```

### Faceted scatter (small multiples)
```python
from plotnine.data import anscombe_quartet

p = (
    ggplot(anscombe_quartet, aes(x='x', y='y'))
    + geom_point(color='sienna', size=2)
    + geom_smooth(method='lm', se=False, color='steelblue')
    + facet_wrap('dataset')
    + scale_y_continuous(breaks=(4, 8, 12))
    + theme_minimal(11)
)
```

### Histogram with fill grouping
```python
p = (
    ggplot(df, aes(x='value', fill='category'))
    + geom_histogram(bins=20, alpha=0.7, position='dodge')
    + labs(title='Distribution by Group')
    + theme_bw()
)
```

### Boxplot with jitter overlay
```python
p = (
    ggplot(df, aes(x='factor(cyl)', y='mpg', fill='factor(cyl)'))
    + geom_boxplot(outlier_alpha=0)
    + geom_jitter(alpha=0.4, width=0.15)
    + theme_minimal()
)
```

### Line chart (time series / trend)
```python
p = (
    ggplot(df_grouped, aes(x='age', y='mean_score'))
    + geom_line(color='steelblue', size=1)
    + geom_point(size=2)
    + theme_minimal()
)
```

## Themes

| Theme | Style |
|---|---|
| `theme_minimal()` | Clean, light gridlines |
| `theme_bw()` | Black-and-white, classic |
| `theme_classic()` | No grid, axis lines only |
| `theme_tufte()` | Edward Tufte's minimalist |
| `theme_void()` | No axes, background only |

Override any theme property:
```python
+ theme(
    axis_title=element_text(size=12, face='bold'),
    panel_spacing=0.1,
    legend_position='bottom',
)
```

## Scales

```python
+ scale_color_brewer(palette='Set2')     # categorical color palette
+ scale_fill_gradient(low='white', high='steelblue')  # continuous fill
+ scale_x_log10()                        # log-transformed x axis
+ scale_y_continuous(breaks=(0, 25, 50, 75, 100), labels=lambda x: f'{x}%')
```

## Coordinate Systems

```python
+ coord_flip()           # horizontal bars
+ coord_fixed(ratio=1)   # equal x/y scaling
+ coord_fixed(ylim=(0, 100), xlim=(0, 10))
```

## Saving Options

```python
p.save('output.png', dpi=150, width=8, height=6)
p.save('output.pdf')          # vector PDF
p.save('output.svg')          # scalable SVG
```

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `ValueError: Unknown column name` | Column doesn't exist in df | Check `df.columns` — names are case-sensitive |
| `PlotnineError: Aesthetics must be valid column names` | Bare variable in `aes()` | Quote column names: `aes(x='col')` |
| `TypeError: unsupported format_string` | f-string in `geom_text` | Use `format_string="{:.1f}%"` parameter |
| Blank plot in script | Plot not rendered | Call `p.save(...)` or `p.draw()` |
| `after_stat` not recognized | Old plotnine version | Use `stat_count(aes(label=after_stat(...)))` or upgrade |
