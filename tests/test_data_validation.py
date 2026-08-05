import pandas as pd

from data_loader import (
    add_period_columns,
    validate_ratio_scale_mixing,
    validate_cumulative_data,
)


def test_duplicate_center_month_is_invalid():
    df = pd.DataFrame([
        {"센터명": "A", "평가월": "2026-07-01", "총점": 500},
        {"센터명": "A", "평가월": "2026-07-01", "총점": 510},
    ])

    df = add_period_columns(df)

    is_valid, errors, warnings = validate_cumulative_data(df)

    assert is_valid is False
    assert any("중복" in error for error in errors)


def test_mixed_ratio_scale_is_invalid():
    df = pd.DataFrame([
        {"센터명": "A", "평가월": "2026-07-01", "상담응대율": 0.95},
        {"센터명": "B", "평가월": "2026-07-01", "상담응대율": 96},
    ])

    is_valid, errors = validate_ratio_scale_mixing(df)

    assert is_valid is False
    assert any("혼재" in error for error in errors)


def test_july_data_is_not_flagged_as_month_gap():
    df = pd.DataFrame([
        {"센터명": "A", "평가월": "2026-07-01", "총점": 520},
        {"센터명": "A", "평가월": "2026-08-01", "총점": 650},
    ])

    df = add_period_columns(df)

    is_valid, errors, warnings = validate_cumulative_data(df)

    assert is_valid is True
    assert errors == []
