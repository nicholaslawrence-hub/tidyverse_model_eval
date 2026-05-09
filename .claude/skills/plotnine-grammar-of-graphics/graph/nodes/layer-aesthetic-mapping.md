# layer-aesthetic-mapping

Aesthetic mappings connect dataframe columns to visual channels.

Rules:

- Quote columns: `aes(x='mpg')`.
- Use constants outside `aes()`: `geom_point(color='steelblue')`.
- Use variables inside `aes()`: `aes(color='factor(cyl)')`.
- Use `factor(...)` when numeric values represent categories.

Channels:

```text
x, y, color, fill, group, alpha, size, shape, linetype, label
```

