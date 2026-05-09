# intent-trend

Use when the prompt asks for a trend over an ordered or summarized variable.

Signals: line chart, trend by age, time series, grouped mean, overlay point markers.

Primary path:

```text
intent-trend -> primitive-line -> primitive-point? -> layer-aesthetic-mapping -> layer-labels-theme -> output-save
```

Prepare summary data before plotting when the prompt asks for means or grouped values.

