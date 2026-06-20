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
