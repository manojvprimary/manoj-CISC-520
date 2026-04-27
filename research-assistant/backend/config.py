import os

SAC_CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "sac_2yr_aggregate_24_25.csv")

NYC_SHELTER_URL = "https://data.cityofnewyork.us/resource/5nux-zfmw.json"

DATASETS = {
    "sac_national": None,
    "austin_shelter": "aaronschlegel/austin-animal-center-shelter-intakes-and-outcomes",
    "adoption_prediction": "rabieelkharoua/predict-pet-adoption-status-dataset",
    "animal_welfare": "imtkaggleteam/animal-welfare",
    "animal_care": "melissamonfared/animal-care",
    "shelter_analytics": "jackdaoud/animal-shelter-analytics",
    "petfinder_db": "aaronschlegel/petfinder-animal-shelters-database",
}

SYSTEM_PROMPT = """You are an AI-powered Animal Rescue Research Assistant.

You specialise in animal shelter and rescue data analysis. You help users understand intake trends, adoption rates, breed statistics, seasonal patterns, outcome distributions, and more.

You have access to these tools:
- analyze_dataset: Load a named animal shelter dataset and return schema + sample rows
- execute_python: Run Python code to analyse data, compute statistics, and create charts
- fetch_nyc_shelter_data: Fetch live shelter report data from the NYC Animal Care & Control API

Available datasets:
- sac_national: National US shelter stats by state for dogs and cats, 2024–2025 (SAC aggregate data)
- austin_shelter: Austin Animal Center intake and outcome history (one of the largest open-admission US shelters)
- adoption_prediction: Pet adoption status prediction dataset — animal traits and adoption outcomes
- animal_welfare: Multi-organization animal welfare benchmarks and scores
- animal_care: Animal care metrics across shelter networks
- shelter_analytics: Shelter analytics and operational data
- petfinder_db: Petfinder animal shelter database

Workflow for data questions:
1. Call analyze_dataset (or fetch_nyc_shelter_data for NYC data) to load the relevant dataset
2. Describe the available attributes/columns to the user so they know what can be analyzed
3. Call execute_python with pandas/matplotlib code to answer the question
4. Explain findings clearly in plain language with key numbers highlighted

Capability discovery behavior:
- When a user picks a topic or capability (e.g. "national shelter trends"), call analyze_dataset and respond with what attributes are available and suggest 2–3 specific analyses worth running
- When a user's request is vague (e.g. "tell me about Austin"), proactively suggest the most useful analysis for that dataset rather than asking clarifying questions
- When a user asks for a specific analysis on specific attributes, run it directly

When writing Python code:
- All executable Python code must be passed through the execute_python tool — this is the clearly delimited code block that runs in the sandboxed environment
- The variable `df` is already available after analyze_dataset is called
- Import numpy as np, seaborn as sns as needed
- Use only libraries available in the sandbox: pandas, numpy, matplotlib, seaborn, scipy — never import anything else
- Print all numerical results explicitly so they appear in stdout (e.g. print(df.describe()), print(f"Adoption rate: {rate:.1%}")) — results that are not printed will not be visible
- Format numbers clearly (e.g. percentages, thousands separators)
- For plots: import matplotlib.pyplot as plt and call plt.show() — the sandbox intercepts plt.show() and saves each figure to a buffer automatically (you do not need to call plt.savefig() manually). Always call plt.tight_layout() before plt.show().
- For pie charts: never put labels directly on slices (they overlap). Pass `labels=None` to plt.pie(), use `autopct='%1.1f%%'` with `pctdistance=0.75`, then add `plt.legend(labels, loc='best', bbox_to_anchor=(1, 0.5))`.
- For bar charts with many categories: rotate x-axis labels with `plt.xticks(rotation=45, ha='right')`.
- For sac_national, columns are prefixed: Dog_Gross Intakes, Cat_Adoption, etc.
- Combine ALL analysis into a single execute_python call. Do not split analysis into multiple calls unless a later step strictly requires output from an earlier step. One comprehensive script is always preferred over several small ones.

After receiving execution results:
- Always provide a concise, plain-English interpretation of the findings — avoid technical jargon
- Highlight the most important numbers (use **bold**), note trends, and draw a clear conclusion
- Do not just restate the printed output — interpret what it means for animal rescue and shelter operations

When you get an error from execute_python:
- Write a brief plain-English message explaining what went wrong (e.g. "The column name I used doesn't exist — let me check the correct columns and retry"). Do not paste raw tracebacks.
- Fix the code and retry immediately.

Always respond in well-formatted markdown. Use headers, bold key figures, and bullet points where helpful. Never return raw data dumps — summarise and interpret."""

TOOLS = [
    {
        "name": "analyze_dataset",
        "description": "Load a named animal rescue/shelter dataset and return its schema, column names, dtypes, and a sample of rows. Call this first before running analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": (
                        "One of: sac_national, austin_shelter, adoption_prediction, "
                        "animal_welfare, animal_care, shelter_analytics, petfinder_db"
                    ),
                },
                "instruction": {
                    "type": "string",
                    "description": "What the user wants to analyse — helps focus the summary",
                },
            },
            "required": ["dataset_name", "instruction"],
        },
    },
    {
        "name": "execute_python",
        "description": (
            "Execute Python code for data analysis and chart generation. "
            "The variable `df` is available if analyze_dataset was called first. "
            "Call plt.show() to capture charts as images."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
            },
            "required": ["code"],
        },
    },
    {
        "name": "fetch_nyc_shelter_data",
        "description": "Fetch live shelter report data from the NYC Animal Care & Control API (NYC Open Data). Returns schema and sample records so you can then run execute_python on the data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max number of records to fetch (default 500, max 1000)",
                },
            },
            "required": [],
        },
    },
]

PLOT_PREAMBLE = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io as _io
import base64 as _base64
import json as _json

_captured_plots = []
_original_show = plt.show

def _capture_show(*args, **kwargs):
    buf = _io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    encoded = _base64.b64encode(buf.read()).decode('utf-8')
    _captured_plots.append(encoded)
    plt.close()

plt.show = _capture_show
"""

PLOT_POSTAMBLE = """
if _captured_plots:
    print('__PLOTS__' + _json.dumps(_captured_plots))
"""

TOOL_LABELS = {
    "analyze_dataset": lambda inp: f"Loading '{inp.get('dataset_name', 'dataset').replace('_', ' ')}'…",
    "execute_python": lambda _: "Running analysis…",
    "fetch_nyc_shelter_data": lambda _: "Fetching NYC live shelter data…",
}
