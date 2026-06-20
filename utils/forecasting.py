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
