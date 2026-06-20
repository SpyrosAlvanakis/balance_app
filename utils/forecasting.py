import numpy as np
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
