# balance_app Uplift Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `balance_app` to `uv`-based local dev tooling, add a mocked pytest regression suite + CI, make expense/income categories dynamic with richer transaction UI and three new charts, and implement a flat-average / linear-regression balance projection on the predict page.

**Architecture:** Pure logic (category derivation, monthly aggregation, projection math, auth credential checks) lives in small `utils/*.py` modules with no Streamlit rendering calls, so it's unit-testable with mocked Google Sheets data. `pages/*.py` stay thin: they call into `utils/`, then render with Streamlit. Categories have no new storage — they're derived from existing sheet data plus a seed list.

**Tech Stack:** Python (uv-managed, `>=3.11,<3.13`), Streamlit, pandas, numpy, pydantic, gspread, pytest, GitHub Actions.

## Global Constraints

- Categories have **no new storage** — derived from `DEFAULT_CATEGORIES` ∪ distinct values in the sheet's `Category` column. No "Categories" sheet/tab.
- Tests are **unit tests with a fully mocked Google Sheets layer** — no network, no credentials, no live/integration tests against any real or dev sheet.
- `current_balance` for projections = `Total` value of the most recent row. `current_date` = `pd.Timestamp.now()` (today), never the date of the last transaction.
- `months_between(current_date, target_date)` = whole calendar months: `(target.year - current.year) * 12 + (target.month - current.month)`.
- Projection math uses only `numpy.polyfit` (degree 1) for the regression method — no ML framework, no `sklearn`.
- `run_local.sh` and tests must work against a **separate dev/test Google Sheet**, never the production sheet — this is a user setup concern (local `secrets.toml`), not something the code enforces.
- macOS only — no cross-platform (Windows) run script needed.
- Pin `requires-python = ">=3.11,<3.13"` in `pyproject.toml`.

---

## Task 1: Migrate dependency tooling from poetry to uv

**Files:**
- Modify: `pyproject.toml`
- Delete: `requirments.txt`

**Interfaces:**
- Produces: a `pyproject.toml` that `uv sync` / `uv run` can use directly. No code interfaces (config-only task).

- [ ] **Step 1: Edit `pyproject.toml`**

Replace the entire file content with:

```toml
[project]
name = "balance-app"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11,<3.13"
dependencies = [
    "pandas",
    "numpy",
    "gspread",
    "oauth2client",
    "ipykernel",
    "pydantic",
    "python-dotenv",
    "streamlit",
    "plotly",
    "openpyxl"
]

[tool.uv]
package = false
```

- [ ] **Step 2: Delete the redundant requirements file**

```bash
git rm requirments.txt
```

- [ ] **Step 3: Verify uv can sync the project**

Run: `uv sync`
Expected: Completes without error, creates/updates `.venv/` and `uv.lock` in the repo root.

- [ ] **Step 4: Verify the app's dependencies import correctly under the synced env**

Run: `uv run python -c "import streamlit, pandas, numpy, gspread, oauth2client, pydantic, plotly, openpyxl; print('ok')"`
Expected: prints `ok`

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "Migrate dependency management from poetry to uv"
```

---

## Task 2: Add local run script, secrets template, and updated docs

**Files:**
- Create: `run_local.sh`
- Create: `.streamlit/secrets.toml.example`
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Modify: `README.md`

**Interfaces:**
- Produces: `./run_local.sh` as the documented way to run the app locally. No Python interfaces.

- [ ] **Step 1: Create `run_local.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
    echo "uv is not installed. Install it with:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

if [ ! -f .streamlit/secrets.toml ]; then
    echo "Missing .streamlit/secrets.toml."
    echo "Copy .streamlit/secrets.toml.example to .streamlit/secrets.toml and fill in"
    echo "credentials for your DEV/TEST Google Sheet (not production)."
    exit 1
fi

uv sync
uv run streamlit run home.py
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x run_local.sh
```

- [ ] **Step 3: Create `.streamlit/secrets.toml.example`**

```toml
[credentials]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
universe_domain = "googleapis.com"
sheet = "balance_app_dev"

[passwords]
your_username = "your_password"

[roles]
admin = ["your_username"]
```

- [ ] **Step 4: Verify the example file is structurally valid TOML**

Run: `uv run python -c "import tomllib; tomllib.load(open('.streamlit/secrets.toml.example', 'rb')); print('ok')"`
Expected: prints `ok`

- [ ] **Step 5: Verify `.streamlit/secrets.toml` (the real one) stays gitignored**

Run: `git check-ignore .streamlit/secrets.toml`
Expected: prints `.streamlit/secrets.toml` (confirms it's ignored)

- [ ] **Step 6: Update `CLAUDE.md` Quick Start section**

Replace:
```markdown
## Quick Start

```bash
poetry install              # package-mode = false (this is an app, not a library)
streamlit run home.py
```

Dependencies are also listed in `requirments.txt` (note: intentional filename typo).
```

With:
```markdown
## Quick Start

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # fill in your DEV sheet creds
./run_local.sh
```

`run_local.sh` runs `uv sync` then `streamlit run home.py`. Dependencies live only in
`pyproject.toml` (managed by `uv`); there is no separate requirements file.

Local runs and tests should point at a **separate dev/test Google Sheet** — never your
production data.
```

- [ ] **Step 7: Update `AGENTS.md` with the identical Quick Start change**

Apply the same replacement as Step 6 to `AGENTS.md` (it currently has identical content to `CLAUDE.md`).

- [ ] **Step 8: Add a Quick Start section to `README.md`**

`README.md` is currently empty. Write:

```markdown
# balance_app

Personal finance tracking web app built with Streamlit. Data is stored in Google Sheets.

## Quick Start

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # fill in your DEV sheet creds
./run_local.sh
```

See `CLAUDE.md` for architecture and conventions.
```

- [ ] **Step 9: Commit**

```bash
git add run_local.sh .streamlit/secrets.toml.example CLAUDE.md AGENTS.md README.md
git commit -m "Add local run script, secrets template, and updated quick-start docs"
```

---

## Task 3: Set up pytest and characterize `correct_gs_types`

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_aed_rows.py`

**Interfaces:**
- Produces: `tests/conftest.py::fake_sheet` fixture — a `unittest.mock.MagicMock` standing in for a `gspread` worksheet, with `.get_values()`, `.insert_row()`, `.delete_rows()` available to assert against in later tasks.

- [ ] **Step 1: Add pytest as a dev dependency**

Run: `uv add --dev pytest`
Expected: `pyproject.toml` gains a `[dependency-groups]` section with `dev = ["pytest>=..."]`; `uv.lock` updates.

- [ ] **Step 2: Create empty `tests/__init__.py`**

```python
```

- [ ] **Step 3: Create `tests/conftest.py`**

```python
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_sheet():
    """A stand-in for a gspread Worksheet, with no network calls."""
    return MagicMock()
```

- [ ] **Step 4: Write the failing test for `correct_gs_types`**

Create `tests/test_aed_rows.py`:

```python
import pandas as pd

from utils.aed_rows import correct_gs_types


def test_correct_gs_types_parses_european_numbers():
    df = pd.DataFrame({
        "Date": ["2026-01-15"],
        "Category": ["Supermarket"],
        "Amount": ["1.234,56"],
        "Total": ["2.000,00"],
        "Type": ["0"],
    })

    result = correct_gs_types(df)

    assert result["Amount"].iloc[0] == 1234.56
    assert result["Total"].iloc[0] == 2000.00
    assert result["Type"].iloc[0] == 0
    assert pd.api.types.is_datetime64_any_dtype(result["Date"])


def test_correct_gs_types_parses_plain_integer_amounts():
    df = pd.DataFrame({
        "Date": ["2026-02-01"],
        "Category": ["Fun"],
        "Amount": ["50"],
        "Total": ["1950"],
        "Type": ["1"],
    })

    result = correct_gs_types(df)

    assert result["Amount"].iloc[0] == 50.0
    assert result["Total"].iloc[0] == 1950.0
    assert result["Type"].iloc[0] == 1
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_aed_rows.py -v`
Expected: both tests `PASS` (the function already exists and is correct — these are characterization tests locking in current behavior).

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock tests/__init__.py tests/conftest.py tests/test_aed_rows.py
git commit -m "Add pytest infrastructure and characterization tests for correct_gs_types"
```

---

## Task 4: Characterize `validate_row`, `add_row`, `delete_row`

**Files:**
- Modify: `tests/test_aed_rows.py`

**Interfaces:**
- Consumes: `tests/conftest.py::fake_sheet` fixture (Task 3).
- Consumes: `utils.aed_rows.validate_row(row_data: list) -> Data | None`, `add_row(sheet, new_row: list) -> bool`, `delete_row(sheet, index: int) -> bool` (existing).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_aed_rows.py`:

```python
from utils.aed_rows import add_row, delete_row, validate_row
from utils.schema import Categories


def test_validate_row_accepts_valid_row():
    row = ["2026-03-01", "Fun", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is not None
    assert result.Category == Categories.Fun
    assert result.Amount == 20.00
    assert result.Type == 0


def test_validate_row_rejects_invalid_category():
    row = ["2026-03-01", "NotARealCategory", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is None


def test_add_row_inserts_validated_row_at_position_two(fake_sheet):
    new_row = ["2026-03-01", "Fun", "20.00", "980.00", "0"]

    result = add_row(fake_sheet, new_row)

    assert result is True
    fake_sheet.insert_row.assert_called_once_with(
        ["2026-03-01", "Fun", 20.00, 980.00, 0], 2
    )


def test_add_row_returns_false_for_invalid_row(fake_sheet):
    new_row = ["2026-03-01", "NotARealCategory", "20.00", "980.00", "0"]

    result = add_row(fake_sheet, new_row)

    assert result is False
    fake_sheet.insert_row.assert_not_called()


def test_delete_row_calls_delete_rows_with_given_index(fake_sheet):
    result = delete_row(fake_sheet, 5)

    assert result is True
    fake_sheet.delete_rows.assert_called_once_with(5)
```

Note: `test_validate_row_accepts_valid_row` and `test_add_row_inserts_validated_row_at_position_two`
import `Categories` from `utils.schema` — this still exists at this point in the plan (it's removed
in Task 9). These two tests will be rewritten in Task 9 once categories become plain strings.

- [ ] **Step 2: Run the tests**

Run: `uv run pytest tests/test_aed_rows.py -v`
Expected: all 7 tests (2 from Task 3 + 5 new) `PASS`.

- [ ] **Step 3: Commit**

```bash
git add tests/test_aed_rows.py
git commit -m "Add characterization tests for validate_row, add_row, delete_row"
```

---

## Task 5: Refactor authentication into a testable pure function

**Files:**
- Modify: `utils/authentication.py`
- Create: `tests/test_authentication.py`

**Interfaces:**
- Produces: `utils.authentication.authenticate(username: str, password: str) -> list[str] | None` — returns the user's roles on success, `None` on bad username, bad password, or no assigned role.

- [ ] **Step 1: Write the failing test**

Create `tests/test_authentication.py`:

```python
from unittest.mock import MagicMock, patch

import pytest

from utils.authentication import authenticate


def _mock_secrets(passwords, roles):
    secrets = MagicMock()
    secrets.__getitem__.side_effect = lambda key: {"passwords": passwords}[key] if key == "passwords" else None
    secrets.roles = roles
    return secrets


@patch("utils.authentication.st")
def test_authenticate_returns_roles_for_valid_credentials(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": ["alice"]},
    )

    result = authenticate("alice", "correct-password")

    assert result == ["admin"]


@patch("utils.authentication.st")
def test_authenticate_returns_none_for_wrong_password(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": ["alice"]},
    )

    result = authenticate("alice", "wrong-password")

    assert result is None


@patch("utils.authentication.st")
def test_authenticate_returns_none_for_unknown_username(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": ["alice"]},
    )

    result = authenticate("bob", "anything")

    assert result is None


@patch("utils.authentication.st")
def test_authenticate_returns_none_when_user_has_no_role(mock_st):
    mock_st.secrets = _mock_secrets(
        passwords={"alice": "correct-password"},
        roles={"admin": []},
    )

    result = authenticate("alice", "correct-password")

    assert result is None
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_authentication.py -v`
Expected: `FAIL` with `ImportError: cannot import name 'authenticate' from 'utils.authentication'`

- [ ] **Step 3: Implement `authenticate()` and use it from both forms**

Replace the full content of `utils/authentication.py` with:

```python
import hmac
import streamlit as st


def authenticate(username: str, password: str) -> list[str] | None:
    """Check credentials and return the user's roles, or None if invalid."""
    if username not in st.secrets["passwords"]:
        return None
    if not hmac.compare_digest(password, st.secrets["passwords"][username]):
        return None

    roles = [role for role in st.secrets.roles if username in st.secrets.roles[role]]
    return roles or None


def show_login_widget():
    """Show login widget and return authentication status."""
    with st.sidebar:
        st.header("Login")
        with st.form("login_form", clear_on_submit=False):
            user = st.text_input("Username", type="default", key="username")
            password = st.text_input("Password", type="password", key="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                roles = authenticate(user, password)
                if roles is None:
                    st.error("😕 Invalid username, password, or no role assigned")
                    st.session_state['user'] = None
                    return False

                st.success("Login successful!")
                st.session_state['user'] = {"user": user, "roles": roles}
                return True

    # If the user clicked the login button, show a modal dialog
    if st.session_state.get("show_login", False):
        # Using expander instead of dialog for compatibility
        with st.expander("Login", expanded=True):
            st.subheader("Login")
            with st.form("login_modal"):
                user = st.text_input("Username", type="default", key="modal_username")
                password = st.text_input("Password", type="password", key="modal_password")
                login_clicked = st.form_submit_button("Login")
                cancel = st.form_submit_button("Cancel")

                if cancel:
                    st.session_state["show_login"] = False
                    st.rerun()
                    return False

                if login_clicked:
                    roles = authenticate(user, password)
                    if roles is None:
                        st.error("😕 Invalid username, password, or no role assigned")
                        st.session_state['user'] = None
                        st.session_state["show_login"] = False
                        return False

                    st.success("Login successful!")
                    st.session_state['user'] = {"user": user, "roles": roles}
                    st.session_state["show_login"] = False
                    st.rerun()
                    return True

    return False


def is_authenticated():
    """Check if user is authenticated."""
    return 'user' in st.session_state and st.session_state['user'] is not None


def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'user' not in st.session_state:
        st.session_state['user'] = None
    if 'show_login' not in st.session_state:
        st.session_state['show_login'] = False


def logout():
    """Log out the current user."""
    st.session_state['user'] = None
    st.success("Logged out successfully!")


def auth_sidebar():
    """Add authentication sidebar with login/logout options."""
    initialize_session_state()

    with st.sidebar:
        if is_authenticated():
            st.write(f"Logged in as: **{st.session_state['user']['user']}**")
            if st.button("Logout"):
                logout()
                st.rerun()
        else:
            show_login_widget()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_authentication.py -v`
Expected: all 4 tests `PASS`

- [ ] **Step 5: Commit**

```bash
git add utils/authentication.py tests/test_authentication.py
git commit -m "Extract authenticate() pure function from authentication.py for testability"
```

---

## Task 6: Characterize the current `Data` schema

**Files:**
- Create: `tests/test_schema.py`

**Interfaces:**
- Consumes: `utils.schema.Data`, `utils.schema.Categories` (existing, pre-Task-9 shape).

- [ ] **Step 1: Write the test**

Create `tests/test_schema.py`:

```python
from datetime import datetime

import pytest
from pydantic import ValidationError

from utils.schema import Categories, Data


def test_data_accepts_valid_enum_category():
    data = Data(
        Date=datetime(2026, 1, 1),
        Category=Categories.Fun,
        Amount=20.0,
        Total=980.0,
        Type=0,
    )

    assert data.Category == Categories.Fun


def test_data_rejects_unknown_category_string():
    with pytest.raises(ValidationError):
        Data(
            Date=datetime(2026, 1, 1),
            Category="NotARealCategory",
            Amount=20.0,
            Total=980.0,
            Type=0,
        )
```

- [ ] **Step 2: Run the test**

Run: `uv run pytest tests/test_schema.py -v`
Expected: both tests `PASS` (characterizing current Enum-based behavior, changed in Task 9).

- [ ] **Step 3: Commit**

```bash
git add tests/test_schema.py
git commit -m "Add characterization tests for current Data schema"
```

---

## Task 7: Add GitHub Actions CI workflow

**Files:**
- Create: `.github/workflows/test.yml`

**Interfaces:**
- None (CI config only). Runs whatever `uv run pytest` finds in `tests/` at the time it executes.

- [ ] **Step 1: Create the workflow file**

```yaml
name: Test

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync
      - run: uv run pytest -v
```

- [ ] **Step 2: Verify the YAML parses**

Run: `uv run python -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml')); print('ok')"`
Expected: prints `ok` (if `pyyaml` isn't available, instead just visually confirm the indentation above is exactly as written — no tabs, 2-space indents).

- [ ] **Step 3: Run the full local suite once to confirm what CI will see**

Run: `uv run pytest -v`
Expected: all tests collected so far `PASS`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "Add GitHub Actions CI workflow running pytest on push and PR"
```

---

## Task 8: Add dynamic category derivation and normalization

**Files:**
- Create: `utils/categories.py`
- Create: `tests/test_categories.py`

**Interfaces:**
- Produces: `utils.categories.DEFAULT_CATEGORIES: list[str]`, `get_known_categories(df: pandas.DataFrame) -> list[str]`, `normalize_category(typed_name: str, known_categories: list[str]) -> str`.
- Consumes (Task 9 onward): nothing new — `df['Category']` is read as plain strings, which already works whether `Category` is stored as an Enum's `.value` string or a plain string in the sheet, since `get_values()` always returns raw strings.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_categories.py`:

```python
import pandas as pd

from utils.categories import DEFAULT_CATEGORIES, get_known_categories, normalize_category


def test_get_known_categories_includes_defaults_when_df_empty():
    df = pd.DataFrame({"Category": []})

    result = get_known_categories(df)

    assert set(DEFAULT_CATEGORIES).issubset(set(result))


def test_get_known_categories_includes_new_category_from_data():
    df = pd.DataFrame({"Category": ["Pharmacy", "Pharmacy", "Fun"]})

    result = get_known_categories(df)

    assert "Pharmacy" in result
    assert "Fun" in result


def test_get_known_categories_is_sorted_with_no_duplicates():
    df = pd.DataFrame({"Category": ["Fun", "Fun", "Zzz"]})

    result = get_known_categories(df)

    assert result == sorted(set(result))


def test_normalize_category_strips_whitespace():
    result = normalize_category("  Pharmacy  ", ["Fun"])

    assert result == "Pharmacy"


def test_normalize_category_reuses_existing_casing_case_insensitively():
    result = normalize_category("job", ["Job", "Fun"])

    assert result == "Job"


def test_normalize_category_returns_new_name_unchanged_when_no_match():
    result = normalize_category("Pharmacy", ["Fun", "Job"])

    assert result == "Pharmacy"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_categories.py -v`
Expected: `FAIL` with `ModuleNotFoundError: No module named 'utils.categories'`

- [ ] **Step 3: Implement `utils/categories.py`**

```python
import pandas as pd

DEFAULT_CATEGORIES: list[str] = [
    "Fun",
    "Mprikis",
    "Education",
    "Supermarket",
    "Vodafone",
    "Fuel",
    "Dad",
    "Mom",
    "Gym",
    "Other",
    "Job",
    "Efka",
    "Rent",
    "Subscriptions",
    "Parking",
    "Haircut",
    "Electricity",
    "Water",
    "Me",
    "Family",
    "Vacation",
    "Accountant",
    "Lena",
    "Health",
    "Gifts",
    "Allowance",
    "Building fees",
    "Hobies",
    "Private",
    "MOTOmaintenance/oil/insurance",
]


def get_known_categories(df: pd.DataFrame) -> list[str]:
    """Default categories plus any category already present in the data, sorted."""
    seen_in_data = set(df["Category"].dropna().astype(str)) if "Category" in df else set()
    return sorted(set(DEFAULT_CATEGORIES) | seen_in_data)


def normalize_category(typed_name: str, known_categories: list[str]) -> str:
    """Strip whitespace; reuse an existing category's casing on a case-insensitive match."""
    stripped = typed_name.strip()
    for known in known_categories:
        if known.lower() == stripped.lower():
            return known
    return stripped
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_categories.py -v`
Expected: all 6 tests `PASS`

- [ ] **Step 5: Commit**

```bash
git add utils/categories.py tests/test_categories.py
git commit -m "Add dynamic category derivation and normalization"
```

---

## Task 9: Change `Data.Category` from Enum to plain string

**Files:**
- Modify: `utils/schema.py`
- Modify: `utils/aed_rows.py`
- Modify: `tests/test_schema.py`
- Modify: `tests/test_aed_rows.py`

**Interfaces:**
- Produces: `utils.schema.Data.Category: str` (was `Categories` enum). `utils.schema.Categories` is removed.
- Modifies: `utils.aed_rows.add_row` no longer calls `.value` on the category (plain strings have no `.value`).

- [ ] **Step 1: Update the failing tests in `tests/test_schema.py`**

Replace the full content of `tests/test_schema.py` with:

```python
from datetime import datetime

import pytest
from pydantic import ValidationError

from utils.schema import Data


def test_data_accepts_any_non_empty_category_string():
    data = Data(
        Date=datetime(2026, 1, 1),
        Category="Pharmacy",
        Amount=20.0,
        Total=980.0,
        Type=0,
    )

    assert data.Category == "Pharmacy"


def test_data_rejects_empty_category_string():
    with pytest.raises(ValidationError):
        Data(
            Date=datetime(2026, 1, 1),
            Category="",
            Amount=20.0,
            Total=980.0,
            Type=0,
        )
```

- [ ] **Step 2: Update the failing tests in `tests/test_aed_rows.py`**

In `tests/test_aed_rows.py`, replace:

```python
from utils.aed_rows import add_row, delete_row, validate_row
from utils.schema import Categories


def test_validate_row_accepts_valid_row():
    row = ["2026-03-01", "Fun", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is not None
    assert result.Category == Categories.Fun
    assert result.Amount == 20.00
    assert result.Type == 0


def test_validate_row_rejects_invalid_category():
    row = ["2026-03-01", "NotARealCategory", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is None
```

With:

```python
from utils.aed_rows import add_row, delete_row, validate_row


def test_validate_row_accepts_valid_row():
    row = ["2026-03-01", "Fun", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is not None
    assert result.Category == "Fun"
    assert result.Amount == 20.00
    assert result.Type == 0


def test_validate_row_accepts_brand_new_category():
    row = ["2026-03-01", "Pharmacy", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is not None
    assert result.Category == "Pharmacy"


def test_validate_row_rejects_empty_category():
    row = ["2026-03-01", "", "20.00", "980.00", "0"]

    result = validate_row(row)

    assert result is None
```

Also update `test_add_row_inserts_validated_row_at_position_two` and
`test_add_row_returns_false_for_invalid_row` (the `NotARealCategory` row in the latter is
now a valid category, since any non-empty string is accepted — change it to an empty
category instead):

Replace:

```python
def test_add_row_returns_false_for_invalid_row(fake_sheet):
    new_row = ["2026-03-01", "NotARealCategory", "20.00", "980.00", "0"]

    result = add_row(fake_sheet, new_row)

    assert result is False
    fake_sheet.insert_row.assert_not_called()
```

With:

```python
def test_add_row_returns_false_for_invalid_row(fake_sheet):
    new_row = ["2026-03-01", "", "20.00", "980.00", "0"]

    result = add_row(fake_sheet, new_row)

    assert result is False
    fake_sheet.insert_row.assert_not_called()
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_schema.py tests/test_aed_rows.py -v`
Expected: `FAIL` — `test_data_accepts_any_non_empty_category_string` and
`test_validate_row_accepts_brand_new_category` fail validation against the current Enum;
`test_add_row_inserts_validated_row_at_position_two` fails on
`validated_data.Category.value` once Category is a plain string is not yet true, so this one
still passes for now — confirm via running that the two new/changed cases above fail before
proceeding.

- [ ] **Step 4: Update `utils/schema.py`**

Replace the full content of `utils/schema.py` with:

```python
from pydantic import BaseModel, Field
from datetime import datetime


class Data(BaseModel):
    Date: datetime
    Category: str = Field(min_length=1)
    Amount: float
    Total: float
    Type: int
```

- [ ] **Step 5: Fix `utils/aed_rows.py`'s now-broken `.value` call**

In `utils/aed_rows.py`, replace:

```python
            sheet_row = [
                validated_data.Date.strftime("%Y-%m-%d"),
                validated_data.Category.value,  # Use .value for enum
                validated_data.Amount,
                validated_data.Total,
                validated_data.Type
            ]
```

With:

```python
            sheet_row = [
                validated_data.Date.strftime("%Y-%m-%d"),
                validated_data.Category,
                validated_data.Amount,
                validated_data.Total,
                validated_data.Type
            ]
```

Also update the `validate_row` docstring-adjacent import at the top of `utils/aed_rows.py`:
the line `from utils.schema import Data, Categories` becomes `from utils.schema import Data`
(since `Categories` no longer exists).

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest tests/test_schema.py tests/test_aed_rows.py -v`
Expected: all tests `PASS`

- [ ] **Step 7: Run the full suite to check nothing else broke**

Run: `uv run pytest -v`
Expected: all tests `PASS` (in particular, `tests/test_authentication.py` and
`tests/test_categories.py` are unaffected by this change).

- [ ] **Step 8: Commit**

```bash
git add utils/schema.py utils/aed_rows.py tests/test_schema.py tests/test_aed_rows.py
git commit -m "Change Data.Category from a fixed Enum to a validated plain string"
```

---

## Task 10: Add `compute_monthly_aggregates`

**Files:**
- Create: `utils/forecasting.py`
- Create: `tests/test_forecasting.py`

**Interfaces:**
- Produces: `utils.forecasting.compute_monthly_aggregates(df: pandas.DataFrame) -> pandas.DataFrame` with columns `YearMonth` (str, `"YYYY-MM"`), `Date` (Timestamp, first of month), `Income` (float), `Expenses` (float), `Net` (float) — sorted ascending by `Date`. Input `df` must have `Date` (datetime), `Type` (int, 0=expense/1=income), `Amount` (float) columns, matching the shape `correct_gs_types` produces.

- [ ] **Step 1: Write the failing test**

Create `tests/test_forecasting.py`:

```python
import pandas as pd

from utils.forecasting import compute_monthly_aggregates


def test_compute_monthly_aggregates_sums_income_and_expenses_per_month():
    df = pd.DataFrame({
        "Date": pd.to_datetime([
            "2026-01-05", "2026-01-10", "2026-02-01", "2026-02-15",
        ]),
        "Type": [0, 1, 0, 1],
        "Amount": [100.0, 500.0, 50.0, 600.0],
    })

    result = compute_monthly_aggregates(df)

    jan = result[result["YearMonth"] == "2026-01"].iloc[0]
    feb = result[result["YearMonth"] == "2026-02"].iloc[0]

    assert jan["Expenses"] == 100.0
    assert jan["Income"] == 500.0
    assert jan["Net"] == 400.0
    assert feb["Expenses"] == 50.0
    assert feb["Income"] == 600.0
    assert feb["Net"] == 550.0


def test_compute_monthly_aggregates_sorted_ascending_by_date():
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2026-03-01", "2026-01-01", "2026-02-01"]),
        "Type": [0, 0, 0],
        "Amount": [10.0, 20.0, 30.0],
    })

    result = compute_monthly_aggregates(df)

    assert list(result["YearMonth"]) == ["2026-01", "2026-02", "2026-03"]


def test_compute_monthly_aggregates_handles_month_with_no_income():
    df = pd.DataFrame({
        "Date": pd.to_datetime(["2026-01-01"]),
        "Type": [0],
        "Amount": [75.0],
    })

    result = compute_monthly_aggregates(df)

    assert result.iloc[0]["Income"] == 0.0
    assert result.iloc[0]["Expenses"] == 75.0
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_forecasting.py -v`
Expected: `FAIL` with `ModuleNotFoundError: No module named 'utils.forecasting'`

- [ ] **Step 3: Implement `compute_monthly_aggregates` in `utils/forecasting.py`**

```python
import pandas as pd


def compute_monthly_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """Group transactions into per-month Income/Expenses/Net totals, sorted by date."""
    working = df.copy()
    working["YearMonth"] = working["Date"].dt.strftime("%Y-%m")

    grouped = (
        working.groupby(["YearMonth", "Type"])["Amount"]
        .sum()
        .unstack(fill_value=0.0)
        .reset_index()
    )
    grouped = grouped.rename(columns={0: "Expenses", 1: "Income"})
    for column in ("Expenses", "Income"):
        if column not in grouped:
            grouped[column] = 0.0

    grouped["Net"] = grouped["Income"] - grouped["Expenses"]
    grouped["Date"] = pd.to_datetime(grouped["YearMonth"] + "-01")
    grouped = grouped.sort_values("Date").reset_index(drop=True)

    return grouped[["YearMonth", "Date", "Income", "Expenses", "Net"]]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_forecasting.py -v`
Expected: all 3 tests `PASS`

- [ ] **Step 5: Commit**

```bash
git add utils/forecasting.py tests/test_forecasting.py
git commit -m "Add compute_monthly_aggregates for shared monthly income/expense rollups"
```

---

## Task 11: Dynamic category input in the Add Entry form

**Files:**
- Modify: `pages/interaction.py`

**Interfaces:**
- Consumes: `utils.categories.get_known_categories(df) -> list[str]`, `utils.categories.normalize_category(typed_name, known_categories) -> str` (Task 8).

- [ ] **Step 1: Update the imports and category input in `pages/interaction.py`**

Replace:

```python
from utils.schema import Categories, Data
```

With:

```python
from utils.categories import get_known_categories, normalize_category
```

Replace the Add Entry form's category input:

```python
        date = st.date_input("Select Date")
        category = st.selectbox("Select Category", [cat.value for cat in Categories])
        amount = st.number_input("Enter Amount", min_value=0.01, step=0.01)
```

With:

```python
        date = st.date_input("Select Date")
        known_categories = get_known_categories(df)
        category_choice = st.selectbox("Select Category", known_categories)
        new_category = st.text_input("Or type a new category", value="")
        category = (
            normalize_category(new_category, known_categories)
            if new_category.strip()
            else category_choice
        )
        amount = st.number_input("Enter Amount", min_value=0.01, step=0.01)
```

- [ ] **Step 2: Manually verify in the browser**

Run: `./run_local.sh`

In the running app:
1. Go to the Interaction page, log in, expand "➕ Add Income/Expense".
2. Confirm the category dropdown lists the existing categories.
3. Leave "Or type a new category" blank, submit an entry using the dropdown — confirm it saves with the dropdown's category.
4. Type a brand-new category name (e.g. "Pharmacy") into the new-category field, submit — confirm the entry saves with "Pharmacy", and that reloading the page now shows "Pharmacy" in the dropdown.
5. Type an existing category with different casing (e.g. "job" when "Job" exists) into the new-category field, submit — confirm it saves as "Job" (existing casing), not a second "job" category.

- [ ] **Step 3: Commit**

```bash
git add pages/interaction.py
git commit -m "Add dynamic category input to the Add Entry form"
```

---

## Task 12: Add filters to the transaction table

**Files:**
- Modify: `pages/interaction.py`

**Interfaces:**
- None new — pure Streamlit UI filtering of the already-loaded `df`.

- [ ] **Step 1: Add filter controls above the table**

Replace:

```python
# Display dataframe with CSS blurring if not authenticated
if is_authenticated():
    # Show the current total
    st.subheader(f'Current total: {df.Total.iloc[0]}')

    # Show dataframe
    st.dataframe(df, use_container_width=True)
else:
```

With:

```python
# Filter controls for the transaction table
filter_col1, filter_col2, filter_col3 = st.columns(3)
with filter_col1:
    filter_categories = st.multiselect(
        "Filter by category", sorted(df["Category"].unique()), default=[]
    )
with filter_col2:
    filter_date_range = st.date_input(
        "Filter by date range",
        value=(df["Date"].min().date(), df["Date"].max().date()) if not df.empty else None,
    )
with filter_col3:
    filter_type = st.radio("Filter by type", ["All", "Expense", "Income"], horizontal=True)

filtered_table_df = df.copy()
if filter_categories:
    filtered_table_df = filtered_table_df[filtered_table_df["Category"].isin(filter_categories)]
if isinstance(filter_date_range, tuple) and len(filter_date_range) == 2:
    start, end = (pd.Timestamp(filter_date_range[0]), pd.Timestamp(filter_date_range[1]))
    filtered_table_df = filtered_table_df[
        (filtered_table_df["Date"] >= start) & (filtered_table_df["Date"] <= end)
    ]
if filter_type != "All":
    filtered_table_df = filtered_table_df[
        filtered_table_df["Type"] == (1 if filter_type == "Income" else 0)
    ]

# Display dataframe with CSS blurring if not authenticated
if is_authenticated():
    # Show the current total
    st.subheader(f'Current total: {df.Total.iloc[0]}')

    # Show dataframe
    st.dataframe(filtered_table_df, use_container_width=True)
else:
```

Note: the unauthenticated branch further down still references `df` directly for its blurred
display — leave that branch as-is; filters are a feature for authenticated users viewing
real data, not the blurred public view.

- [ ] **Step 2: Manually verify in the browser**

Run: `./run_local.sh`

In the running app, on the Interaction page (logged in):
1. Confirm the table shows all rows by default.
2. Select one category in the multiselect — confirm the table shows only matching rows.
3. Narrow the date range — confirm the table updates.
4. Switch the type filter to "Income" — confirm only income rows show; switch to "Expense" — confirm only expense rows show.

- [ ] **Step 3: Commit**

```bash
git add pages/interaction.py
git commit -m "Add category, date range, and type filters to the transaction table"
```

---

## Task 13: Add three new charts to the Visualisation page

**Files:**
- Modify: `pages/plots.py`

**Interfaces:**
- Consumes: `utils.forecasting.compute_monthly_aggregates(df) -> pandas.DataFrame` (Task 10).

- [ ] **Step 1: Add the import**

Add to the top of `pages/plots.py`:

```python
from utils.forecasting import compute_monthly_aggregates
```

- [ ] **Step 2: Add the three new charts after the existing visualization block**

At the end of `pages/plots.py`, append:

```python
# --- NEW: Monthly trend charts (use full history, not the date-range filter above) ---
st.divider()
st.subheader("Monthly Trends")

monthly = compute_monthly_aggregates(df)

if not monthly.empty:
    # Monthly income vs expense bars
    income_vs_expense = monthly.melt(
        id_vars=["YearMonth"], value_vars=["Income", "Expenses"],
        var_name="Type", value_name="Amount",
    )
    fig_bars = px.bar(
        income_vs_expense, x="YearMonth", y="Amount", color="Type",
        barmode="group", title="Monthly Income vs Expenses",
    )
    st.plotly_chart(fig_bars, use_container_width=True)

    # Category spending trend over time
    category_monthly = (
        df.assign(YearMonth=df["Date"].dt.strftime("%Y-%m"))
        .groupby(["YearMonth", "Category"])["Amount"]
        .sum()
        .reset_index()
        .sort_values("YearMonth")
    )
    fig_category_trend = px.line(
        category_monthly, x="YearMonth", y="Amount", color="Category",
        title="Category Spending Trend Over Time", markers=True,
    )
    st.plotly_chart(fig_category_trend, use_container_width=True)

    # Net savings per month, colored by surplus/deficit
    net_savings = monthly.copy()
    net_savings["Result"] = net_savings["Net"].apply(
        lambda value: "Surplus" if value >= 0 else "Deficit"
    )
    fig_net = px.bar(
        net_savings, x="YearMonth", y="Net", color="Result",
        color_discrete_map={"Surplus": "green", "Deficit": "red"},
        title="Net Savings per Month",
    )
    st.plotly_chart(fig_net, use_container_width=True)
else:
    st.info("Not enough data yet to show monthly trends.")
```

- [ ] **Step 3: Manually verify in the browser**

Run: `./run_local.sh`

In the running app, on the Visualisation page:
1. Confirm the three new charts render below the existing pie/line charts.
2. Confirm the income-vs-expense bar chart shows grouped bars per month.
3. Confirm the category trend chart shows one line per category.
4. Confirm the net savings chart colors surplus months green and deficit months red.

- [ ] **Step 4: Commit**

```bash
git add pages/plots.py
git commit -m "Add monthly income/expense, category trend, and net savings charts"
```

---

## Task 14: Add flat-average and linear-regression projection functions

**Files:**
- Modify: `utils/forecasting.py`
- Modify: `tests/test_forecasting.py`

**Interfaces:**
- Produces: `utils.forecasting.project_flat_average(monthly_df, current_balance, current_date, target_date) -> dict` and `project_linear_regression(monthly_df, current_balance, current_date, target_date) -> dict`. Both return `{"avg_income": float, "avg_expense": float, "months_ahead": int, "projected_balance": float, "warning": str | None}`, where `avg_income`/`avg_expense` are always the trailing-window mean `Income`/`Expenses` (descriptive stats shown to the user), regardless of which method computed `projected_balance`. Both raise `ValueError("Not enough history to project")` if fewer than 2 months of data exist.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_forecasting.py`:

```python
import numpy as np
import pytest

from utils.forecasting import project_flat_average, project_linear_regression


def _monthly_df(nets, incomes=None, expenses=None):
    n = len(nets)
    incomes = incomes or [1000.0] * n
    expenses = expenses or [1000.0 - net for net in nets]
    dates = pd.date_range("2025-01-01", periods=n, freq="MS")
    return pd.DataFrame({
        "YearMonth": dates.strftime("%Y-%m"),
        "Date": dates,
        "Income": incomes,
        "Expenses": expenses,
        "Net": nets,
    })


def test_project_flat_average_uses_trailing_12_months():
    monthly = _monthly_df(nets=[100.0] * 12, incomes=[500.0] * 12, expenses=[400.0] * 12)
    current_date = pd.Timestamp("2026-01-01")
    target_date = pd.Timestamp("2026-04-01")

    result = project_flat_average(monthly, current_balance=1000.0, current_date=current_date, target_date=target_date)

    assert result["months_ahead"] == 3
    assert result["avg_income"] == pytest.approx(500.0)
    assert result["avg_expense"] == pytest.approx(400.0)
    assert result["projected_balance"] == pytest.approx(1000.0 + 100.0 * 3)


def test_project_flat_average_warns_with_fewer_than_12_months():
    monthly = _monthly_df(nets=[50.0, 50.0, 50.0])
    current_date = pd.Timestamp("2026-01-01")
    target_date = pd.Timestamp("2026-02-01")

    result = project_flat_average(monthly, current_balance=0.0, current_date=current_date, target_date=target_date)

    assert result["warning"] is not None


def test_project_flat_average_raises_with_fewer_than_2_months():
    monthly = _monthly_df(nets=[50.0])
    current_date = pd.Timestamp("2026-01-01")
    target_date = pd.Timestamp("2026-02-01")

    with pytest.raises(ValueError):
        project_flat_average(monthly, current_balance=0.0, current_date=current_date, target_date=target_date)


def test_project_linear_regression_extrapolates_constant_trend():
    # Net is flat at 100/month -> regression slope should be ~0, projecting flat balance growth of 100/month
    monthly = _monthly_df(nets=[100.0] * 12)
    current_date = pd.Timestamp("2026-01-01")
    target_date = pd.Timestamp("2026-03-01")

    result = project_linear_regression(monthly, current_balance=1000.0, current_date=current_date, target_date=target_date)

    assert result["months_ahead"] == 2
    assert result["projected_balance"] == pytest.approx(1000.0 + 100.0 * 2, abs=1.0)


def test_project_linear_regression_raises_with_fewer_than_2_months():
    monthly = _monthly_df(nets=[50.0])
    current_date = pd.Timestamp("2026-01-01")
    target_date = pd.Timestamp("2026-02-01")

    with pytest.raises(ValueError):
        project_linear_regression(monthly, current_balance=0.0, current_date=current_date, target_date=target_date)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_forecasting.py -v`
Expected: `FAIL` with `ImportError: cannot import name 'project_flat_average'`

- [ ] **Step 3: Implement both functions in `utils/forecasting.py`**

Append to `utils/forecasting.py`:

```python
def _months_between(current_date: pd.Timestamp, target_date: pd.Timestamp) -> int:
    return (target_date.year - current_date.year) * 12 + (target_date.month - current_date.month)


def project_flat_average(
    monthly_df: pd.DataFrame,
    current_balance: float,
    current_date: pd.Timestamp,
    target_date: pd.Timestamp,
) -> dict:
    """Project balance using the trailing-12-months average income/expense, as a straight line."""
    if len(monthly_df) < 2:
        raise ValueError("Not enough history to project")

    trailing = monthly_df.tail(12)
    avg_income = trailing["Income"].mean()
    avg_expense = trailing["Expenses"].mean()
    months_ahead = _months_between(current_date, target_date)

    return {
        "avg_income": avg_income,
        "avg_expense": avg_expense,
        "months_ahead": months_ahead,
        "projected_balance": current_balance + (avg_income - avg_expense) * months_ahead,
        "warning": "Fewer than 12 months of history available; projection uses all available data." if len(monthly_df) < 12 else None,
    }


def project_linear_regression(
    monthly_df: pd.DataFrame,
    current_balance: float,
    current_date: pd.Timestamp,
    target_date: pd.Timestamp,
) -> dict:
    """Project balance using a least-squares trend line through trailing-12-months Net."""
    if len(monthly_df) < 2:
        raise ValueError("Not enough history to project")

    trailing = monthly_df.tail(12).reset_index(drop=True)
    x = np.arange(len(trailing))
    slope, intercept = np.polyfit(x, trailing["Net"].to_numpy(), 1)
    months_ahead = _months_between(current_date, target_date)

    projected_monthly_net = slope * (len(trailing) - 1 + months_ahead) + intercept

    return {
        "avg_income": trailing["Income"].mean(),
        "avg_expense": trailing["Expenses"].mean(),
        "months_ahead": months_ahead,
        "projected_balance": current_balance + projected_monthly_net * months_ahead,
        "warning": "Fewer than 12 months of history available; projection uses all available data." if len(monthly_df) < 12 else None,
    }
```

Add `import numpy as np` to the top of `utils/forecasting.py` alongside the existing `import pandas as pd`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_forecasting.py -v`
Expected: all tests `PASS`

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -v`
Expected: all tests across the whole project `PASS`

- [ ] **Step 6: Commit**

```bash
git add utils/forecasting.py tests/test_forecasting.py
git commit -m "Add flat-average and linear-regression balance projection functions"
```

---

## Task 15: Rewrite the Predict page

**Files:**
- Modify: `pages/predict.py`

**Interfaces:**
- Consumes: `utils.forecasting.compute_monthly_aggregates`, `project_flat_average`, `project_linear_regression` (Tasks 10, 14).

- [ ] **Step 1: Replace the full content of `pages/predict.py`**

```python
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.authentication import auth_sidebar, is_authenticated
from utils.connect import connect
from utils.aed_rows import correct_gs_types
from utils.forecasting import compute_monthly_aggregates, project_flat_average, project_linear_regression

auth_sidebar()

st.title("Predict Balance")

if not is_authenticated():
    st.warning("⚠️ This feature requires login to access.")
    st.info("Please log in using the sidebar to access prediction features.")
    st.stop()

sheet = connect()
raw_data = sheet.get_values()
headers = raw_data[0]
values = raw_data[1:]
df = pd.DataFrame(values, columns=headers)
df = correct_gs_types(df)

monthly = compute_monthly_aggregates(df)

if len(monthly) < 2:
    st.warning("Not enough historical data to make a prediction. At least 2 months of data are required.")
    st.stop()

current_balance = df.sort_values("Date", ascending=False).iloc[0]["Total"]
current_date = pd.Timestamp.now()

target_date = st.date_input("Project my balance on this date", value=current_date + pd.DateOffset(months=3))
target_date = pd.Timestamp(target_date)

method = st.radio("Projection method", ["Flat average", "Linear regression"], horizontal=True)

if target_date <= current_date:
    st.warning("Pick a target date in the future.")
    st.stop()

if method == "Flat average":
    result = project_flat_average(monthly, current_balance, current_date, target_date)
else:
    result = project_linear_regression(monthly, current_balance, current_date, target_date)

if result["warning"]:
    st.info(result["warning"])

st.subheader(f"Prediction for {target_date.strftime('%Y-%m-%d')}")
cols = st.columns(4)
with cols[0]:
    st.metric("Avg Income/Month", f"€{result['avg_income']:.2f}")
with cols[1]:
    st.metric("Avg Expense/Month", f"€{result['avg_expense']:.2f}")
with cols[2]:
    st.metric("Months Ahead", result["months_ahead"])
with cols[3]:
    st.metric("Projected Balance", f"€{result['projected_balance']:.2f}")

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=monthly["Date"], y=monthly["Net"].cumsum() + (current_balance - monthly["Net"].cumsum().iloc[-1]),
    mode="lines+markers", name="Historical Balance", line=dict(color="blue"),
))
fig.add_trace(go.Scatter(
    x=[current_date, target_date],
    y=[current_balance, result["projected_balance"]],
    mode="lines+markers", name=f"Projected Balance ({method})",
    line=dict(color="orange", dash="dash"),
))
fig.update_layout(
    title="Balance Projection", xaxis_title="Date", yaxis_title="Balance (€)",
    hovermode="x unified",
)
st.plotly_chart(fig, use_container_width=True)
```

- [ ] **Step 2: Manually verify in the browser**

Run: `./run_local.sh`

In the running app, on the Predict Month page (logged in):
1. Confirm a date picker and a "Flat average" / "Linear regression" toggle appear.
2. Pick a target date a few months out — confirm metrics populate and the chart shows a historical line plus a dashed projected segment.
3. Switch the toggle to "Linear regression" — confirm the projected balance updates.
4. Pick a target date in the past or today — confirm the warning message appears and no crash occurs.
5. Log out and revisit the page — confirm the login-required warning shows instead of the page content.

- [ ] **Step 3: Commit**

```bash
git add pages/predict.py
git commit -m "Implement Predict page with flat-average and linear-regression projections"
```

---

## Task 16: Update CLAUDE.md and AGENTS.md to reflect the finished state

**Files:**
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`

**Interfaces:**
- None (documentation only).

- [ ] **Step 1: Update the Architecture and Gotchas sections**

In both `CLAUDE.md` and `AGENTS.md`, replace:

```markdown
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
```

With:

```markdown
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
```

And replace:

```markdown
## Gotchas

- `connect()` has **no try/except** — Google Sheets connectivity failures cause raw tracebacks.
- `blur_css_helper.py` only blurs with CSS — trivial to bypass via browser devtools.
- `predict.py` is fully commented out and will render a blank page. Either implement or remove from nav.
- `aed_rows.py` has old versions of functions kept as comments — safe to clean up.
- Duplicate login UI code in `authentication.py` (`show_login_widget` has two nearly-identical form blocks).
- `openpyxl` and `ipykernel` are in dependencies but not used in the app code.
```

With:

```markdown
## Gotchas

- `connect()` has **no try/except** — Google Sheets connectivity failures cause raw tracebacks.
- `blur_css_helper.py` only blurs with CSS — trivial to bypass via browser devtools.
- `aed_rows.py` has old versions of functions kept as comments — safe to clean up.
- `openpyxl` and `ipykernel` are in dependencies but not used in the app code.
- Categories have no dedicated storage — `get_known_categories()` derives the list from
  `DEFAULT_CATEGORIES` plus whatever already exists in the sheet's `Category` column.
- Run `./run_local.sh` against a separate dev/test Google Sheet, never production — both
  local dev and the pytest suite assume this.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md AGENTS.md
git commit -m "Update CLAUDE.md and AGENTS.md to reflect uplift changes"
```

---

## Self-Review Notes

- **Spec coverage:** Section 1 → Tasks 1–2. Section 2 → Tasks 3–7. Section 3 → Tasks 8–9, 10 (shared helper), 11–13. Section 4 → Tasks 14–15. Doc wrap-up → Task 16. All spec decisions have a corresponding task.
- **Fixed inline during review:** Task 9 explicitly walks through updating the two tests in `tests/test_aed_rows.py` that depended on the `Categories` enum, since Task 4 wrote them before Task 9 removes the enum — without this, Task 9 would leave failing tests behind.
- **Type consistency:** `get_known_categories` / `normalize_category` signatures in Task 8 match their usage in Task 11. `compute_monthly_aggregates` output columns (`YearMonth`, `Date`, `Income`, `Expenses`, `Net`) match what Tasks 13, 14, and 15 consume. `project_flat_average`/`project_linear_regression`'s returned dict keys (`avg_income`, `avg_expense`, `months_ahead`, `projected_balance`, `warning`) match Task 15's usage.
