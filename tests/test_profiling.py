import pandas as pd

from utils.profiling import summarize_dataset


def test_profile_contains_expected_sections():
    df = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-02", None],
            "sales": [10, 15, 20],
            "segment": ["A", "B", "A"],
        }
    )

    profile = summarize_dataset(df)
    assert profile["row_count"] == 3
    assert profile["column_count"] == 3
    assert "missing_values" in profile
    assert profile["dtypes"]["sales"] == "int64"
    assert profile["categorical_columns"] == ["segment"]
