# balance_app uplift — design

Date: 2026-06-20

## Context

`balance_app` is a small Streamlit personal-finance tracker. Google Sheets is the only
datastore (`utils/connect.py`), reached fresh on every page load with no caching, no error
handling, and no mocking layer. Categories are a hardcoded Python `Enum`
(`utils/schema.py`). `pages/predict.py` is entirely commented out.

This uplift covers four independent sub-projects, built in this order because each later
one benefits from infrastructure the earlier ones establish (local dev → safe place to test
→ a mocked test harness → feature work that the harness immediately covers):

1. Local dev tooling (`uv`, a run script, a local secrets template)
2. A pytest suite + CI safety net
3. Dynamic categories + richer transaction UI + new charts
4. A linear-projection predict page

## Section 1 — Local dev tooling

**Problem:** secrets only exist in the deployed Streamlit Cloud app, not locally. There's
no local secrets file, so `connect()` would crash immediately on a local run. Also, `poetry`
isn't installed on this machine, and the project's two dependency manifests
(`pyproject.toml`, `requirments.txt`) are fully duplicated.

**Decisions:**

- Use a **separate dev/test Google Sheet** (a duplicate of the production sheet, shared
  with the same service account) for all local runs and tests. Production data is never
  touched by local experimentation.
- Switch tooling from `poetry` to `uv`. `pyproject.toml`'s existing `[project]` table is
  already PEP 621 / uv-compatible — replace `[tool.poetry]\npackage-mode = false` with
  `[tool.uv]\npackage = false`.
- Delete `requirments.txt` — its contents are already fully duplicated in
  `pyproject.toml`'s `dependencies`, so `pyproject.toml` becomes the single source of truth.
- Pin `requires-python = ">=3.11,<3.13"`. The system Python is 3.14; some dependencies
  (`oauth2client`, `gspread`) are old enough that 3.14 compatibility is a real risk. `uv`
  will download and manage a matching interpreter automatically, so this doesn't require
  the user to install anything by hand.
- Add `run_local.sh` (repo root, executable):
  1. Checks `uv` is on `PATH`; if not, prints the install command and exits.
  2. Checks `.streamlit/secrets.toml` exists; if not, prints a pointer to
     `.streamlit/secrets.toml.example` and exits (rather than letting it crash inside
     `connect()` with a raw traceback).
  3. Runs `uv sync && uv run streamlit run home.py`.
- Add `.streamlit/secrets.toml.example`: same `[credentials]` / `[passwords]` / `[roles]`
  structure as production secrets, placeholder values only. `.streamlit/secrets.toml` is
  already gitignored (confirmed), so the real file is never committed.
- Update the Quick Start section in `CLAUDE.md`, `AGENTS.md`, and `README.md` to describe
  the `uv` + `run_local.sh` workflow instead of `poetry`.

## Section 2 — Test suite + CI

**Problem:** there's no regression safety net. Several modules currently mix Streamlit
rendering with logic in a way that's hard to unit test (e.g. `authentication.py`'s two
near-duplicate login form blocks call `st.session_state` assignment inline with form
rendering).

**Decisions:**

- Tests are **unit tests with a fully mocked Google Sheets layer** — no network, no
  credentials required, runs anywhere including CI, sub-second. No live/integration tests
  against the dev sheet (deferred — not needed for the stated goal of catching logic
  regressions).
- Refactor `utils/authentication.py`: extract `authenticate(username, password) -> list[str]
  | None` as a pure function (looks up `st.secrets["passwords"]` / `st.secrets.roles`,
  returns roles or `None`). Both the sidebar form and the modal form call this one function
  instead of duplicating the password/role-check logic. This is a necessary testability
  change and incidentally resolves the documented duplication gotcha.
- New `tests/` directory (pytest):
  - `test_aed_rows.py` — `correct_gs_types` European-number parsing edge cases;
    `validate_row` valid/invalid rows; `add_row`/`delete_row` against a fake `sheet` object
    (asserting the right calls happen, e.g. `insert_row(..., 2)`, `delete_rows(index)`).
  - `test_schema.py` — `Data` Pydantic model validation, including the new plain-`str`
    `Category` field (non-empty, after Section 3's schema change).
  - `test_categories.py` — `get_known_categories` and `normalize_category` (Section 3).
  - `test_forecasting.py` — `compute_monthly_aggregates`, `project_flat_average`,
    `project_linear_regression` (Section 4), using small synthetic DataFrames with known
    expected outputs.
  - `test_authentication.py` — `authenticate()` against mocked `st.secrets`.
- Add `pytest` as a `uv` dev-dependency group (`uv add --dev pytest`).
- Add `.github/workflows/test.yml` using `astral-sh/setup-uv`, running `uv sync` then
  `uv run pytest` on push and pull request. Free on this public repo.

## Section 3 — Dynamic categories + UI/graph enhancements

**Problem:** categories are a fixed `Enum` (`utils/schema.py`); adding a new spending
category currently requires a code change. The transaction table has no filtering. Charts
are limited to category pie charts and a single balance-over-time line.

**Decisions:**

- New `utils/categories.py`:
  - `DEFAULT_CATEGORIES: list[str]` — the current ~30 names, as a plain list (replaces the
    `Categories` Enum as the seed/default set).
  - `get_known_categories(df: pd.DataFrame) -> list[str]` — `DEFAULT_CATEGORIES` union
    distinct values from `df['Category']`, sorted. No new storage: a brand-new category
    becomes "known" the moment a row using it exists in the sheet.
  - `normalize_category(typed_name: str, known_categories: list[str]) -> str` — strips
    whitespace; if it case-insensitively matches an existing known category, returns that
    category's existing casing (prevents "Job" / "job" from becoming two categories).
- `utils/schema.py`: remove the `Categories` Enum. `Data.Category` becomes a plain `str`
  with `min_length=1` validation (post-strip).
- `pages/interaction.py` — Add Entry form: keep the existing selectbox (populated via
  `get_known_categories(df)`), add a text input below it, "Or type a new category". If
  non-empty after `normalize_category`, that value is used instead of the selectbox
  selection. No separate "register category" step — using a new category in a submitted
  entry is how it gets added.
- `pages/interaction.py` — transaction table: add filter controls above the dataframe
  (category multiselect, date range, type radio — same filtering pattern already used in
  `plots.py`) so the table isn't just the full unfiltered dump.
- `pages/plots.py` — three new charts, all built on a shared
  `compute_monthly_aggregates(df)` helper (added to `utils/forecasting.py` in Section 4, so
  Section 3's charts and Section 4's projections share one aggregation implementation):
  - Monthly income vs. expense grouped bar chart.
  - Category spending trend over time (one line per category, by month).
  - Net savings per month (bar chart, green for surplus / red for deficit).

## Section 4 — Predict page

**Problem:** `pages/predict.py` is fully commented out, so the "Predict Month" nav entry
renders a blank page.

**Decisions:**

- New `utils/forecasting.py`:
  - `compute_monthly_aggregates(df: pd.DataFrame) -> pd.DataFrame` — groups transactions by
    year-month into `Income` / `Expenses` / `Net` columns, sorted by date. Shared with
    Section 3's new charts.
  - `project_flat_average(monthly_df, current_balance, current_date, target_date) ->
    pd.DataFrame` — averages `Income` and `Expenses` over the trailing 12 months (or fewer,
    if less history exists), projects `current_balance + (avg_income - avg_expense) *
    months_between(current_date, target_date)` as a straight line to the target date.
  - `project_linear_regression(monthly_df, current_balance, current_date, target_date) ->
    pd.DataFrame` — fits a least-squares line (`numpy.polyfit`, degree 1) through the
    trailing-12-months `Net` values and extrapolates to the target date.
  - `current_balance` is the `Total` value of the most recent row in the sheet (the latest
    known running balance). `current_date` is "today" (`pd.Timestamp.now()`), not the date
    of the last transaction — the projection always starts counting from today, so it stays
    correct even if the most recent entry is a few days old. `months_between` is whole
    calendar months: `(target.year - current.year) * 12 + (target.month - current.month)`.
  - Both raise/short-circuit with a clear "not enough data" signal if fewer than 2 months
    of history exist; both emit a warning flag if fewer than 12 months exist (still compute,
    just with less data).
- `pages/predict.py` rewritten (currently fully commented out):
  - Login-gated via `is_authenticated()` / `st.stop()`, consistent with the app's existing
    security model for sensitive data pages.
  - A `st.date_input` for the target date.
  - A toggle (`st.radio`) between "Flat average" (default) and "Linear regression"
    projection methods.
  - Metrics row: projected income/month, expenses/month, net/month, and projected balance
    on the target date.
  - A chart: historical monthly `Net`/running balance as a solid line, projected values as
    a dashed line extending from today to the target date, using whichever method is
    selected.
  - A warning banner if fewer than 12 months of history exist.

## Out of scope (explicitly deferred)

- Live/integration tests against the real or dev Google Sheet.
- A separate "Categories" sheet/tab as canonical storage.
- Any actual forecasting model (ARIMA, ML, etc.) — only flat-average and least-squares
  linear regression, both explicitly requested as lightweight, non-"model" approaches.
- Cross-platform run script (Windows) — user is on macOS only.
- Fixing unrelated pre-existing issues not touched by this work (e.g. `connect()`'s missing
  try/except, CSS-only blur bypassability) — noted in `CLAUDE.md`'s Gotchas already, not
  part of this uplift.
