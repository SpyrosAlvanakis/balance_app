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
