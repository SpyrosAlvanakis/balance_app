# balance_app

A personal finance tracker built with [Streamlit](https://streamlit.io/). Every expense and
income entry is stored as a row in a Google Sheet, which acts as the app's database — there's
no separate backend or SQL database to run.

## Features

- **Track income and expenses** — add entries with a date, category, amount, and type
  (income/expense), and delete entries you no longer want.
- **Dynamic categories** — pick from existing categories or type a brand-new one on the fly;
  it becomes available going forward without any code change.
- **Filterable transaction table** — narrow the view by category, date range, or type.
- **Visualizations** — category breakdown pie charts, a running balance line chart, monthly
  income-vs-expense bars, category spending trends over time, and a net savings (surplus vs.
  deficit) chart.
- **Balance prediction** — project your future balance out to a date you choose, using either
  a simple trailing 12-month average or a linear regression trend line.
- **Login-gated** — unauthenticated visitors see a blurred preview of the data; logging in
  unlocks full detail and the ability to add/delete entries.

## Project structure

```text
home.py                     # Entry point — defines navigation across the 4 pages below
pages/
  intro_page.py             # Landing page
  interaction.py            # View/filter transactions, add new entries, delete entries
  plots.py                  # All charts and visualizations
  predict.py                # Balance projection (flat average / linear regression)
utils/
  connect.py                # Connects to the Google Sheet via a service account
  aed_rows.py                # Row validation, insertion, deletion, and type coercion
  schema.py                  # Pydantic schema for a transaction row
  categories.py              # Derives the known category list from existing data
  forecasting.py             # Monthly aggregation and balance projection math
  authentication.py          # Login/logout, session state, credential checks
  blur_css_helper.py         # CSS blur applied to data when not logged in
tests/                       # pytest suite (mocked Google Sheets — no network required)
.streamlit/
  secrets.toml.example        # Template for your local secrets.toml (see Setup below)
run_local.sh                  # Convenience script to set up and launch the app locally
```

## Setup

### Requirements

- Python 3.11 or 3.12
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management
- A Google Cloud service account with access to the Sheets and Drive APIs, and a Google Sheet
  it can read/write

### 1. Get Google Sheets API credentials

You'll need a service account JSON key with access to the Google Sheets and Drive APIs. Use
the [official setup guide for the `gspread` library](https://docs.gspread.org/en/latest/oauth2.html)
(which this project uses to talk to Google Sheets) to create one.

Share your target Google Sheet with the service account's email address once it's created.

### 2. Configure secrets

Copy the example secrets file and fill in your service account credentials, the name of your
Google Sheet, and your app login credentials:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` to fill in the `[credentials]`, `[passwords]`, and `[roles]`
sections.

### 3. Run it

```bash
./run_local.sh
```

This installs dependencies with `uv` and launches the app with `streamlit run home.py`. The
app will be available at `http://localhost:8501`.

### Running tests

```bash
uv sync
uv run pytest -v
```

The test suite mocks the Google Sheets connection entirely, so it runs without any
credentials or network access.
