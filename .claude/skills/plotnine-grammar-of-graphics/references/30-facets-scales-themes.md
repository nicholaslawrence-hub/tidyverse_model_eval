# Facets, Scales, And Themes

Use facets for small multiples.

```python
+ facet_wrap('Academic_Level')
```

Use scales for axis or legend transformations.

```python
+ scale_color_brewer(palette='Set2')
+ scale_y_continuous(labels=lambda x: [f'{v:.0f}%' for v in x])
```

Use labels to make the chart legible.

```python
+ labs(title='Title', x='X label', y='Y label', color='Legend title')
```

Use a base theme first, then targeted overrides.

```python
+ theme_bw()
+ theme(
    axis_title=element_text(face='bold'),
    legend_position='bottom',
    panel_grid_minor=element_blank(),
)
```

Eval checks often look for `facet_`, `labs`, `theme_*`, `theme(`, `element_text`, `element_blank`, and `legend_position`.

