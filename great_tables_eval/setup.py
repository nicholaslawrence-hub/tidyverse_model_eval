import os
from langsmith import Client
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

API_KEY = os.getenv('LANGCHAIN_API_KEY')
DATASET_NAME = os.getenv('LANGCHAIN_PROJECT')

print(API_KEY)

client = Client(api_key=API_KEY)

prompts = [
    "make a great_tables schedule from this CSV",
    "format my Caltrain data into a styled route table",
    "I have a transit CSV, build me a weekly schedule table",
    "Help me create a route table with illustrations for a commuter rail.",
    "Design and write a styled timetable with the CSV attached.",
    "build a great_tables HTML table showing train departure times by route",
    "my CSV has caltrain stops and times, make it into a schedule",
    "generate a styled timetable grouped by weekday vs weekend",
    "take this transit CSV and produce a great_tables summary by station"
]

def main():
 
    dataset = client.create_dataset(
        DATASET_NAME,
        description="User prompts for transit route table skill generation eval"
    )
    print(f"Created dataset: {dataset.name}")
 
    client.create_examples(
        inputs=[{"prompt": p} for p in prompts],
        dataset_name=DATASET_NAME,
    )
    print(f"Pushed {len(prompts)} examples to LangSmith")
 
if __name__ == "__main__":
    main()