import pandas as pd

from utils.aed_rows import add_row, correct_gs_types, delete_row, validate_row


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


def test_add_row_inserts_validated_row_at_position_two(fake_sheet):
    new_row = ["2026-03-01", "Fun", "20.00", "980.00", "0"]

    result = add_row(fake_sheet, new_row)

    assert result is True
    fake_sheet.insert_row.assert_called_once_with(
        ["2026-03-01", "Fun", 20.00, 980.00, 0], 2
    )


def test_add_row_returns_false_for_invalid_row(fake_sheet):
    new_row = ["2026-03-01", "", "20.00", "980.00", "0"]

    result = add_row(fake_sheet, new_row)

    assert result is False
    fake_sheet.insert_row.assert_not_called()


def test_delete_row_calls_delete_rows_with_given_index(fake_sheet):
    result = delete_row(fake_sheet, 5)

    assert result is True
    fake_sheet.delete_rows.assert_called_once_with(5)
