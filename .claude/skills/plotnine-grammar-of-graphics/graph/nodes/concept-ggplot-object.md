# concept-ggplot-object

The root object binds data and global mappings.

```python
p = (
    ggplot(df, aes(x='x_col', y='y_col'))
    + geom_point()
    + labs(title='Title')
    + theme_minimal()
)
```

Rules:

- Use `+` to add layers.
- Put shared mappings in global `aes()`.
- Put layer-specific mappings inside the layer.
- Save explicitly in scripts.

