# Aesthetic Mapping

Use `aes()` for data-driven visual encodings.

```python
aes(x='hp', y='mpg', color='factor(cyl)')
```

Required conventions for this repo:

- quote column names,
- use `factor(...)` for categorical numeric fields,
- map variables inside `aes()`,
- set constants outside `aes()`.

```python
# data-driven color
geom_point(aes(color='factor(cyl)'))

# constant color
geom_point(color='steelblue')
```

Common aesthetics:

| Aesthetic | Use |
|---|---|
| `x`, `y` | position |
| `color` | stroke/line/point color |
| `fill` | area fill for bars, histograms, boxplots |
| `group` | connect or summarize observations as a group |
| `alpha` | transparency |
| `size` | point or line size |
| `label` | text labels |

