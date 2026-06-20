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
