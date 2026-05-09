# layer-labels-theme

Labels and themes make the chart readable and often appear in eval checks.

```python
+ labs(title='Daily Usage', x='Hours', y='Count', fill='Gender')
+ theme_bw()
+ theme(axis_title=element_text(face='bold'))
```

Use a base theme such as `theme_minimal()`, `theme_bw()`, `theme_classic()`, or `theme_light()`.

Use `theme(...)` only for targeted overrides.

