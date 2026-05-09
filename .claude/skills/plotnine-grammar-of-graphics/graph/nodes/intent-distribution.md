# intent-distribution

Use when the prompt asks for the distribution of one numeric variable.

Signals: histogram, distribution, bins, filled by group, faceted by group.

Primary path:

```text
intent-distribution -> primitive-histogram -> layer-aesthetic-mapping -> layer-facets? -> layer-labels-theme -> output-save
```

Map the measured variable to `x`. Map comparison groups to `fill` when requested.

