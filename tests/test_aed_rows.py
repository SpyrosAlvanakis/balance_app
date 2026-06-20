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
