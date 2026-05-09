FEW_SHOT_EXAMPLES = [
    {
        "name": "scatter_with_trend",
        "prompt": "Create a scatter plot of hp vs mpg, color by cyl as a category, add a linear trend line, and save to output.png.",
        "graph_path": [
            "intent-relationship",
            "concept-ggplot-object",
            "layer-aesthetic-mapping",
            "primitive-point",
            "primitive-smooth",
            "layer-labels-theme",
            "output-save",
        ],
        "code": """from plotnine import *
from plotnine.data import mtcars
import pandas as pd

df = pd.DataFrame(mtcars)
p = (
    ggplot(df, aes(x='hp', y='mpg', color='factor(cyl)'))
    + geom_point(alpha=0.8, size=3)
    + geom_smooth(method='lm', se=False)
    + labs(title='Horsepower vs MPG', x='Horsepower', y='Miles per gallon', color='Cylinders')
    + theme_minimal()
)
p.save('output.png', dpi=150, width=8, height=6)
""",
        "rubric_notes": "Satisfies point primitive, smooth primitive, categorical factor mapping, labels, theme, and output saving.",
    },
    {
        "name": "bar_with_computed_percent_labels",
        "prompt": "Create a bar chart of car counts by cyl with percentage labels and save to output.png.",
        "graph_path": [
            "intent-counts",
            "concept-ggplot-object",
            "layer-aesthetic-mapping",
            "primitive-bar",
            "layer-stat-computed-labels",
            "primitive-text",
            "layer-labels-theme",
            "output-save",
        ],
        "code": """from plotnine import *
from plotnine.data import mtcars
import pandas as pd

df = pd.DataFrame(mtcars)
p = (
    ggplot(df, aes(x='factor(cyl)', fill='factor(cyl)'))
    + geom_bar()
    + geom_text(
        aes(label=after_stat('prop*100'), group=1),
        stat='count',
        nudge_y=0.5,
        format_string='{:.1f}%'
    )
    + labs(title='Cars by Cylinder Count', x='Cylinders', y='Count', fill='Cylinders')
    + theme_classic()
)
p.save('output.png', dpi=150, width=8, height=6)
""",
        "rubric_notes": "Uses computed labels through after_stat and format_string rather than precomputed f-strings.",
    },
    {
        "name": "faceted_histogram",
        "prompt": "Create a histogram of usage hours filled by gender, faceted by academic level, and save to output.png.",
        "graph_path": [
            "intent-distribution",
            "concept-ggplot-object",
            "layer-aesthetic-mapping",
            "primitive-histogram",
            "layer-facets",
            "layer-labels-theme",
            "output-save",
        ],
        "code": """from plotnine import *
import pandas as pd

df = pd.read_csv('example_datasets/Social_media_impact_on_life.csv')
p = (
    ggplot(df, aes(x='Avg_Daily_Usage_Hours', fill='Gender'))
    + geom_histogram(bins=20, alpha=0.7)
    + facet_wrap('Academic_Level')
    + labs(title='Daily Social Media Usage', x='Average daily usage hours', y='Count', fill='Gender')
    + theme_bw()
)
p.save('output.png', dpi=150, width=8, height=6)
""",
        "rubric_notes": "Uses the requested dataset column, histogram primitive, fill aesthetic, facet layer, labels, and saved image.",
    },
]


def format_few_shot_examples() -> str:
    blocks = []
    for ex in FEW_SHOT_EXAMPLES:
        blocks.append(
            f"Example: {ex['name']}\n"
            f"Prompt: {ex['prompt']}\n"
            f"Graph path: {ex['graph_path']}\n"
            f"Rubric notes: {ex['rubric_notes']}\n"
            f"Code:\n```python\n{ex['code']}```"
        )
    return "\n\n".join(blocks)

