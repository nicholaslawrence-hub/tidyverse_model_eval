# Posit Evaluation Harness

I built this project to test whether an LLM can reliably produce useful Python code for Posit-style visualization and table workflows. Instead of reading a model response and guessing whether it is good, the harness asks the model to generate code, runs that code, and checks the result against concrete expectations.

There are two connected pieces:

- `plotnine_eval` focuses on chart generation. It asks for Plotnine visualizations, executes the generated Python, and scores whether the result used the right geoms, labels, themes, faceting, categorical handling, and save behavior.
- `great_tables_eval` focuses on table-generation skills. It uses DSPy and LangSmith to generate, optimize, and judge a `SKILL.md` file for building styled Great Tables transit schedules.

The goal was to make model evaluation feel closer to software testing: specific tasks, reproducible checks, and reports that make failures easier to understand.

## Project Structure

```text
.
+-- run_evals.py
+-- scripts/
|   +-- install_skills.ps1
+-- .claude/
|   +-- skills/
|       +-- posit-repository/
|       +-- plotnine-grammar-of-graphics/
|       |   +-- graph/
|       |       +-- graph.json
|       |       +-- traversal.md
|       |       +-- nodes/
|       +-- posit-great-tables-skills/
|       +-- posit-eval-reporting/
+-- example_datasets/
|   +-- Social_media_impact_on_life.csv
|   +-- caltrain_weekend_northbound.csv
+-- plotnine_eval/
|   +-- plotnine_eval.py
|   +-- cases.json
|   +-- plotnine_skill/
|       +-- plotnine_skill.md
|       +-- references/
+-- great_tables_eval/
    +-- great_tables_eval.py
    +-- setup.py
    +-- src/
    |   +-- pipeline.py
    +-- test/
```

## What It Does

The Plotnine side behaves like a small code runner and grader. Each case has a natural language prompt, the model returns Python, and the evaluator runs that Python in a temporary file. A case passes when enough of its task-specific checks succeed.

The Plotnine evaluator now also uses the grammar-of-graphics skill graph during generation. Each case is mapped to graph nodes such as `intent-relationship`, `primitive-point`, `layer-aesthetic-mapping`, and `grader-plotnine-eval`; that active path becomes prompt context for the model and report metadata for the eval.

The Great Tables side is more about skill generation. It uses a working Caltrain timetable example as reference context, then asks DSPy to produce a reusable skill for similar table-building tasks. A judge model scores the generated skill for correctness, coverage, trigger accuracy, concision, and faithfulness to the original timetable design.

The included datasets give the evals something real to work with: social-media usage data for visualization tasks and a Caltrain schedule CSV for styled transit-table generation.

## Agent Skills

This repo includes three project skills under `.claude/skills`, which Claude Code can discover when the project is open:

| Skill | Use It For |
|---|---|
| `posit-repository` | Starting point for repo navigation and choosing the right subsystem. |
| `plotnine-grammar-of-graphics` | Plotnine chart construction and eval work organized as a typed knowledge graph of intents, grammar concepts, primitives, layers, outputs, and graders. |
| `posit-great-tables-skills` | Working on the DSPy/LangSmith Great Tables skill-generation pipeline. |
| `posit-eval-reporting` | Summarizing eval reports, writing project descriptions, or turning results into resume/README language. |

The Plotnine skill has an explicit graph in `.claude/skills/plotnine-grammar-of-graphics/graph/graph.json`. Agents start from an intent node, such as `intent-relationship` or `intent-counts`, then follow typed edges into grammar concepts, aesthetics, geoms, presentation layers, output saving, and grader checks.

To make the same skills available globally in Codex or Claude Code, run:

```powershell
.\scripts\install_skills.ps1 -Target Both
```

Use `-Target Codex` or `-Target Claude` if you only want one tool. Restart the tool afterward so it reloads available skills.

## Requirements

Use Python 3.10+ and install the core dependencies:

```bash
pip install anthropic dspy-ai langsmith python-dotenv plotnine pandas numpy great-tables
```

Depending on your local Plotnine stack, you may also need plotting backends used by Matplotlib.

## Environment Variables

Create a `.env` file or export the required API keys before running model-backed evals:

```bash
ANTHROPIC_API_KEY=your_anthropic_key
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=your_langsmith_project
GEMINI_API_KEY=your_model_provider_key_if_used_by_dspy_config
```

Notes:

- `plotnine_eval/plotnine_eval.py` uses the Anthropic SDK directly.
- `great_tables_eval/great_tables_eval.py` configures DSPy with an Anthropic model string and reads the API key from `GEMINI_API_KEY` in the current code.
- LangSmith is used for storing and loading Great Tables prompt datasets.

## Usage

### Run All Evals

From the repository root:

```bash
python run_evals.py
```

This runs both evaluation suites when available and writes a combined report to:

```text
eval_report.json
```

### Run Only Plotnine Evals

```bash
python run_evals.py plotnine
```

Run a specific Plotnine case:

```bash
python run_evals.py plotnine scatter_trend
```

You can also run the Plotnine evaluator directly:

```bash
cd plotnine_eval
python plotnine_eval.py
python plotnine_eval.py scatter_trend
```

The direct Plotnine runner writes:

```text
plotnine_eval_report.json
```

Legacy static prompt variants can still be compared with:

```bash
cd plotnine_eval
python plotnine_eval.py --optimize
```

This runs the configured prompt variants, currently `baseline`, `graph`, and `graph_strict`, then writes:

```text
plotnine_prompt_optimization_report.json
```

The main Plotnine eval path now requires LLM-as-a-judge. Set:

```bash
ANTHROPIC_API_KEY=your_anthropic_key
PLOTNINE_JUDGE_MODEL=claude-sonnet-4-5
```

The code judge scores generated code against the prompt, deterministic checks, and active graph path. The vision judge scores the rendered `output.png` against the same prompt and graph path. Local image evaluation also checks that `output.png` exists, has reasonable dimensions, and is not blank.

DSPy prompt optimization is available through:

```bash
cd plotnine_eval
python plotnine_eval.py --dspy-optimize --trials=5
python plotnine_eval.py --backend=dspy scatter_trend
```

The DSPy program receives the task prompt, active graph context, few-shot examples, and the same judge rubric used by the evaluator. `MIPROv2` compiles the generator against a metric that combines LLM code judging, LLM vision judging, local image evaluation, and deterministic checks.

### Run Great Tables Workflows

From `great_tables_eval`:

```bash
python great_tables_eval.py compile
python great_tables_eval.py run "make a commuter rail timetable from this CSV"
python great_tables_eval.py eval
```

Commands:

- `compile`: loads LangSmith training prompts and optimizes the DSPy skill generator.
- `run`: generates and judges a Great Tables skill for a supplied prompt.
- `eval`: evaluates generated skills against the LangSmith test dataset.

### Create LangSmith Train/Test Datasets

From `great_tables_eval`:

```bash
python setup.py
```

This shuffles a small prompt set, splits it into train/test groups, and uploads examples to LangSmith.

## Evaluation Design

### Plotnine

Each Plotnine case contains:

- a natural language prompt,
- a category,
- a case ID,
- a set of grader functions.

The evaluator sends the prompt to the model, extracts code from the response, runs it locally, and assigns a score based on the fraction of checks passed. A case passes when its score is at least `0.7`.

Example checks include:

- generated code executes without error,
- required geoms are present,
- categorical variables are wrapped in `factor()`,
- `aes()` references use quoted column names,
- plot labels and themes are included,
- output is saved to `output.png`,
- rendered image output exists and is nonblank,
- LLM code judge and LLM vision judge pass.

### Great Tables

The Great Tables workflow defines DSPy signatures for:

- generating a complete `SKILL.md` file from a user prompt,
- judging the generated skill for quality and faithfulness,
- compiling the generator with `MIPROv2`,
- evaluating generated skills over a LangSmith dataset.

The reference context focuses on a styled Caltrain northbound weekend schedule with fare zones, train columns, skipped-stop handling, row striping, official schedule styling, and Great Tables formatting conventions.

## Outputs

| Output | Created By | What It Contains |
|---|---|---|
| `eval_report.json` | `python run_evals.py` | Combined Plotnine and Great Tables results, including pass counts, average score, check results, and generated code. |
| `plotnine_eval_report.json` | `python plotnine_eval.py` | Plotnine-only case results with per-check pass/fail details and generated Python. |
| `output.png` | Generated Plotnine scripts | Temporary chart output used to confirm that generated visualization code saves a plot. |
| `optimized_skill_generator.json` | `python great_tables_eval.py compile` | A compiled DSPy generator produced from LangSmith training prompts. |
| `skills/transit_table/SKILL.md` | `python great_tables_eval.py run ...` | A generated Great Tables skill, saved only when the judge score meets the configured threshold. |

These files make it easier to see not just whether a model succeeded, but how it succeeded or where it fell apart.

## Known Notes

- The current `plotnine_eval/cases.json` should be validated before running all Plotnine cases; malformed JSON will prevent case loading.
- The Great Tables DSPy configuration currently reads `GEMINI_API_KEY` while specifying an Anthropic model through DSPy.
- Some generated artifacts, such as `eval_report.json`, `plotnine_eval_report.json`, `output.png`, optimized DSPy JSON files, and generated `skills/` outputs, are runtime artifacts and are not required to understand the source project.

## Resume Version

| Version | Description |
|---|---|
| Short | Built a Python evaluation harness that tests LLM-generated Plotnine and Great Tables workflows by running generated code, scoring task-specific checks, and saving structured reports. |
| More technical | Created an LLM eval system for Posit-style data workflows, with executable Plotnine chart-generation tests, custom grader functions, JSON reporting, and a DSPy/LangSmith pipeline for optimizing Great Tables skill generation. |
| More personal | Built a project that turns messy model responses into something measurable: prompts go in, generated visualization or table code runs, and the harness reports exactly what worked and what failed. |
