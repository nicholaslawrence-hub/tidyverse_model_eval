# output-save

Scripts and eval cases must save the plot explicitly.

```python
p.save('output.png', dpi=150, width=8, height=6)
```

Eval graders check for `.save(` or `ggsave(`.

Generated test scripts clean up `output.png` after execution.

