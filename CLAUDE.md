# CLAUDE.md — balance_app

## Project Overview

Personal finance tracking web app built with **Streamlit**. Data is stored in **Google Sheets** (not a traditional database).

## Quick Start

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # fill in your DEV sheet creds
./run_local.sh
```

`run_local.sh` runs `uv sync` then `streamlit run home.py`. Dependencies live only in
`pyproject.toml` (managed by `uv`); there is no separate requirements file.

Local runs and tests should point at a **separate dev/test Google Sheet** — never your
production data.

## Architecture

```
home.py                     # Entry point: st.navigation with 4 pages
pages/interaction.py        # CRUD: view/filter transactions, add (dynamic category), delete
pages/plots.py              # Pie charts, monthly trend charts, line chart (balance)
pages/intro_page.py         # Static landing page
pages/predict.py            # Flat-average / linear-regression balance projection
utils/connect.py            # gspread connection to Google Sheets (no error handling)
utils/aed_rows.py           # Row ops: add_row, delete_row, correct_gs_types
utils/authentication.py     # authenticate() pure function + HMAC login UI
utils/blur_css_helper.py    # CSS blur for unauthenticated users (NOT real security)
utils/schema.py             # Pydantic: Data (BaseModel, Category is a plain str)
utils/categories.py         # DEFAULT_CATEGORIES + dynamic category derivation/normalization
utils/forecasting.py        # Monthly aggregation + balance projection math
tests/                      # pytest suite, fully mocked Google Sheets — no network
```

## Key Conventions

- **Google Sheets as DB**: Every page calls `connect()` → `sheet.get_values()` independently. No caching or shared state across pages.
- **European number format**: `correct_gs_types()` converts `1.234,56` → `1234.56` (strips dots, commas→decimals).
- **Row deletion offset**: `delete_row(sheet, row_to_delete + 2)` — the `+2` accounts for 1-indexed sheets + header row. If the DataFrame is sorted/reordered, this will delete the wrong row.
- **Total column**: Computed client-side on insert by reading `df.iloc[0]["Total"]` (latest row). Breaks if rows are inserted out of order or the sheet is edited externally.
- **Auth**: `st.session_state['user']` holds `{"user": username, "roles": [...]}`. Requires `.streamlit/secrets.toml` with `[passwords]`, `[roles]`, and `[credentials]` sections.
- **Modern Streamlit API**: Uses `st.navigation()` + `st.Page()` — NOT the old `pages/` auto-discovery.
- **Hardcoded year range**: `plots.py` has `range(2023, 2027)` — needs manual updating.

## Gotchas

- `connect()` has **no try/except** — Google Sheets connectivity failures cause raw tracebacks.
- `blur_css_helper.py` only blurs with CSS — trivial to bypass via browser devtools.
- `aed_rows.py` has old versions of functions kept as comments — safe to clean up.
- `openpyxl` and `ipykernel` are in dependencies but not used in the app code.
- Categories have no dedicated storage — `get_known_categories()` derives the list from
  `DEFAULT_CATEGORIES` plus whatever already exists in the sheet's `Category` column.
- Run `./run_local.sh` against a separate dev/test Google Sheet, never production — both
  local dev and the pytest suite assume this.
