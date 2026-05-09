# Plotnine Graph Traversal

This graph models Plotnine knowledge as connected nodes. Do not read every node by default. Walk the graph.

## Node Types

| Type | Meaning |
|---|---|
| `intent` | What the user wants to show: relationship, count, distribution, group comparison, trend. |
| `concept` | Grammar-of-graphics structure: ggplot object, layer stack. |
| `primitive` | Plotting geom: point, bar, histogram, boxplot, line, smooth, text. |
| `layer` | Cross-cutting layer: aesthetics, stat labels, facets, scales, labels/themes. |
| `output` | Save/draw behavior. |
| `grader` | Eval checks that correspond to graph nodes. |

## Edge Types

| Edge | Meaning |
|---|---|
| `requires` | The target node is necessary for the source node to work. |
| `uses` | The source commonly uses the target. |
| `maps_to` | The intent maps to a primitive or layer. |
| `pairs_with` | Nodes commonly appear together. |
| `constrains` | The source controls how the target should be written. |
| `graded_by` | The target grader should check the source behavior. |

## Traversal Recipe

1. Identify chart intent from the prompt.
2. Load the matching `intent-*` node.
3. Follow `maps_to` to primitives.
4. Follow `requires` to `concept-ggplot-object`, `layer-aesthetic-mapping`, and `output-save`.
5. Follow `pairs_with` for overlays such as point + smooth or boxplot + jitter.
6. Follow `uses` for facets, scales, labels, themes, or stat-computed labels.
7. Follow `graded_by` when editing eval cases or graders.

## Active Paths

Relationship:

```text
intent-relationship -> primitive-point -> primitive-smooth -> layer-aesthetic-mapping -> layer-labels-theme -> output-save
```

Counts:

```text
intent-counts -> primitive-bar -> layer-stat-computed-labels -> primitive-text -> layer-labels-theme -> output-save
```

Distribution:

```text
intent-distribution -> primitive-histogram -> layer-facets -> layer-labels-theme -> output-save
```

Group comparison:

```text
intent-group-comparison -> primitive-boxplot -> primitive-jitter -> layer-aesthetic-mapping -> layer-labels-theme -> output-save
```

Trend over ordered data:

```text
intent-trend -> primitive-line -> primitive-point -> layer-aesthetic-mapping -> layer-labels-theme -> output-save
```

