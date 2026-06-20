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
pages/interaction.py        # CRUD: view transactions, add, delete
pages/plots.py              # Pie charts (income/expense by category) + line chart (balance)
pages/intro_page.py         # Static landing page
pages/predict.py            # ALL COMMENTED OUT — renders blank page
utils/connect.py            # gspread connection to Google Sheets (no error handling)
utils/aed_rows.py           # Row ops: add_row, delete_row, correct_gs_types
utils/authentication.py     # HMAC-based login via st.session_state, roles, secrets
utils/blur_css_helper.py    # CSS blur for unauthenticated users (NOT real security)
utils/schema.py             # Pydantic: Categories (Enum, ~30 values), Data (BaseModel)
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
- `predict.py` is fully commented out and will render a blank page. Either implement or remove from nav.
- `aed_rows.py` has old versions of functions kept as comments — safe to clean up.
- Duplicate login UI code in `authentication.py` (`show_login_widget` has two nearly-identical form blocks).
- `openpyxl` and `ipykernel` are in dependencies but not used in the app code.
