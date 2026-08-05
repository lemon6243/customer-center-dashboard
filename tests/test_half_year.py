import pandas as pd

from utils.half_year import (
    get_half,
    get_period_month,
    is_half_start,
    is_half_end,
    get_period_info,
    filter_current_half,
    get_comparison_data,
)


def _df(rows):
    """테스트용 데이터프레임 생성"""
    return pd.DataFrame(rows)


def test_half_classification():
    assert get_half("2026-01-01") == "상반기"
    assert get_half("2026-06-01") == "상반기"
    assert get_half("2026-07-01") == "하반기"
    assert get_half("2026-12-01") == "하반기"


def test_period_month_resets_in_july():
    assert get_period_month("2026-01-01") == 1
    assert get_period_month("2026-06-01") == 6
    assert get_period_month("2026-07-01") == 1
    assert get_period_month("2026-12-01") == 6


def test_half_start_and_end_months():
    assert is_half_start("2026-01-01") is True
    assert is_half_start("2026-07-01") is True
    assert is_half_start("2026-06-01") is False
    assert is_half_start("2026-12-01") is False

    assert is_half_end("2026-06-01") is True
    assert is_half_end("2026-12-01") is True
    assert is_half_end("2026-07-01") is False
    assert is_half_end("2026-01-01") is False


def test_period_info_for_july():
    info = get_period_info("2026-07-01")

    assert info["half"] == "하반기"
    assert info["period_month"] == 1
    assert info["is_half_start"] is True
    assert info["is_half_end"] is False
    assert info["progress_rate"] == 1 / 6
    assert info["period_text"] == "하반기 1개월차"


def test_filter_current_half_does_not_connect_june_to_july():
    df = _df([
        {"평가월": "2026-01-01", "센터명": "A", "총점": 500},
        {"평가월": "2026-06-01", "센터명": "A", "총점": 930},
        {"평가월": "2026-07-01", "센터명": "A", "총점": 520},
        {"평가월": "2026-08-01", "센터명": "A", "총점": 650},
    ])

    result = filter_current_half(df, "2026-08-01")
    months = pd.to_datetime(result["평가월"]).dt.month.tolist()

    assert months == [7, 8]
    assert 6 not in months


def test_july_compares_with_last_year_same_month_not_june():
    current_df = _df([
        {"평가월": "2026-06-01", "센터명": "A", "총점": 940},
        {"평가월": "2026-07-01", "센터명": "A", "총점": 530},
    ])

    last_year_df = _df([
        {"평가월": "2025-06-01", "센터명": "A", "총점": 920},
        {"평가월": "2025-07-01", "센터명": "A", "총점": 500},
    ])

    compare_df, label, compare_month = get_comparison_data(
        current_df,
        "2026-07-01",
        last_year_df,
    )

    assert label == "전년 동월"
    assert compare_month == pd.Timestamp("2025-07-01")
    assert len(compare_df) == 1
    assert compare_df.iloc[0]["총점"] == 500


def test_august_compares_with_july_in_same_half():
    current_df = _df([
        {"평가월": "2026-06-01", "센터명": "A", "총점": 940},
        {"평가월": "2026-07-01", "센터명": "A", "총점": 530},
        {"평가월": "2026-08-01", "센터명": "A", "총점": 650},
    ])

    compare_df, label, compare_month = get_comparison_data(
        current_df,
        "2026-08-01",
    )

    assert label == "전월"
    assert compare_month == pd.Timestamp("2026-07-01")
    assert len(compare_df) == 1
    assert compare_df.iloc[0]["총점"] == 530


def test_january_compares_with_last_year_january_not_december():
    current_df = _df([
        {"평가월": "2025-12-01", "센터명": "A", "총점": 940},
        {"평가월": "2026-01-01", "센터명": "A", "총점": 510},
    ])

    last_year_df = _df([
        {"평가월": "2025-01-01", "센터명": "A", "총점": 490},
        {"평가월": "2025-12-01", "센터명": "A", "총점": 940},
    ])

    compare_df, label, compare_month = get_comparison_data(
        current_df,
        "2026-01-01",
        last_year_df,
    )

    assert label == "전년 동월"
    assert compare_month == pd.Timestamp("2025-01-01")
    assert compare_df.iloc[0]["총점"] == 490

