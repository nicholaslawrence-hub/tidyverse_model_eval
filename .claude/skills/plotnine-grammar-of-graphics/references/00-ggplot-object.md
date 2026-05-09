# ggplot Object

The Plotnine object starts with data and optional global aesthetic mappings.

```python
from plotnine import *

p = (
    ggplot(df, aes(x='x_col', y='y_col'))
    + geom_point()
    + labs(title='Title', x='X label', y='Y label')
    + theme_minimal()
)
p.save('output.png', dpi=150, width=8, height=6)
```

Use `+` to add layers. Plotnine is not a method-chain API.

Global `aes()` applies to every layer unless a layer supplies its own mapping.

Keep layer order intentional: base primitive first, annotation or overlay second, scales/facets/themes later.

