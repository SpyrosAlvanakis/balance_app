import pandas as pd

from utils.categories import DEFAULT_CATEGORIES, get_known_categories, normalize_category


def test_get_known_categories_includes_defaults_when_df_empty():
    df = pd.DataFrame({"Category": []})

    result = get_known_categories(df)

    assert set(DEFAULT_CATEGORIES).issubset(set(result))


def test_get_known_categories_includes_new_category_from_data():
    df = pd.DataFrame({"Category": ["Pharmacy", "Pharmacy", "Fun"]})

    result = get_known_categories(df)

    assert "Pharmacy" in result
    assert "Fun" in result


def test_get_known_categories_is_sorted_with_no_duplicates():
    df = pd.DataFrame({"Category": ["Fun", "Fun", "Zzz"]})

    result = get_known_categories(df)

    assert result == sorted(set(result))


def test_normalize_category_strips_whitespace():
    result = normalize_category("  Pharmacy  ", ["Fun"])

    assert result == "Pharmacy"


def test_normalize_category_reuses_existing_casing_case_insensitively():
    result = normalize_category("job", ["Job", "Fun"])

    assert result == "Job"


def test_normalize_category_returns_new_name_unchanged_when_no_match():
    result = normalize_category("Pharmacy", ["Fun", "Job"])

    assert result == "Pharmacy"
