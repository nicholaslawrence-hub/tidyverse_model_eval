# primitive-text

Geom: `geom_text()`

Use for labels. With computed bar labels, pair with `layer-stat-computed-labels`.

```python
+ geom_text(aes(label='label_col'), va='bottom')
```

For stat-computed labels, use `stat='count'`, `after_stat(...)`, and `format_string`.

