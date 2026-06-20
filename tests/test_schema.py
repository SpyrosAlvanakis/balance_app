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
