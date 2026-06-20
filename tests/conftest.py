from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_sheet():
    """A stand-in for a gspread Worksheet, with no network calls."""
    return MagicMock()
