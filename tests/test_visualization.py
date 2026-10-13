import pandas as pd

from utils.visualization import choose_chart, make_chart_figure


def test_chart_choice_prefers_time_series_for_dates():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5, freq="D"),
        "revenue": [10, 20, 15, 25, 18],
    })

    chart = choose_chart(df, x_col="date", y_col="revenue")
    assert chart == "line"

    figure = make_chart_figure(df, chart, x_col="date", y_col="revenue")
    assert figure is not None


def test_invalid_chart_inputs_are_guarded():
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert choose_chart(df, x_col="missing", y_col="b") == "invalid"
    assert make_chart_figure(df, "invalid", x_col="a", y_col="b") is None
