import os
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

NOTEBOOK_CONTEXT = """
# CSV Structure
- fare_zone: int (1-4, inserted manually)
- Stop: station name string
- Train columns: numbered 601, 603, 605... (odd = local, even = express), values like "6:51a", "7:26a", NaN for skipped stops

# Data loading
caltrain_df = pd.read_csv("caltrain_weekend_northbound.csv")
caltrain_df.insert(0, 'fare_zone', [4]*4 + [3]*6 + [2]*10 + [1]*4)

# GT Table construction
train_columns = caltrain_df.filter(regex=("^6")).columns.tolist()
caltrain_table = (
    GT(caltrain_df)
    .tab_header(title=html('<span style="color: rgb(224,37,33); font-weight: bold; font-size: 40px;">Northbound &ndash;</span>...'))
    .tab_stub('fare_zone')
    .tab_source_note(source_note="Sourced from CalTrain's 01/31/26 weekend schedule.")
    .cols_width(cases={'Stop': '300px'})
    .opt_align_table_header(align='left')
    .cols_align(align='center')
    .tab_style(locations=loc.header(), style=style.css("color: rgb(224,37,33) !important; font-size: 35px !important; font-weight: bold !important;"))
    .tab_style(locations=loc.column_labels(), style=style.css("background-color: black !important; color: white !important; font-size: 16px !important; font-weight: bold !important;"))
    .tab_style(locations=loc.stub(), style=style.css("background-color: rgb(224,37,33) !important; color: white !important; writing-mode: sideways-lr; font-size: 14px !important;"))
    .tab_style(locations=loc.body(), style=style.css("height: 10px !important; border-left: solid #a2a7a8 1px !important; border-right: solid #a2a7a8 1px !important; color: black !important"))
    .tab_options(row_group_as_column=True, row_striping_background_color="#e1e2e2")
    .cols_label(Stop='Train No.', fare_zone='Fare Zone')
    .opt_row_striping()
    .opt_table_outline()
    .opt_table_font(font=google_font('frutiger'))
)
"""

SKILL_TEMPLATE = """
# [Skill Name]

## Description
[When to use this skill]

## Dependencies
[pip packages]

## CSV Schema
[expected columns]

## Step-by-step Instructions
[numbered steps]

## Code Example
[complete working code]

## Notes
[gotchas, edge cases]
"""

GENERATOR_PROMPT = """You are generating a SKILL.md file for an agentic coding assistant called Claude.
A SKILL.md teaches Claude exactly how to complete a specific coding task.

The user wants help with this task:
<user_prompt>
{user_prompt}
</user_prompt>

Here is a working reference implementation from a Jupyter notebook:
<notebook_context>
{notebook_context}
</notebook_context>

Use this template structure:
<skill_template>
{skill_template}
</skill_template>

Generate a complete, precise SKILL.md that Claude can follow to fulfill the user's request.
The skill should be concrete, include real working code based on the notebook context, and handle NaN values in the schedule.
Output only the SKILL.md content, no preamble.
"""

def generate_skill(user_prompt: str, n_candidates: int = 3) -> list[str]:
    candidates = []
    for i in range(n_candidates):
        message = client.messages.create(
            model="claude-sonnet-4.6",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": GENERATOR_PROMPT.format(
                    user_prompt=user_prompt,
                    notebook_context=NOTEBOOK_CONTEXT,
                    skill_template=SKILL_TEMPLATE,
                )
            }]
        )
        candidates.append(message.content[0].text)
        print(f"Generated candidate {i+1}/{n_candidates}")
    return candidates