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
