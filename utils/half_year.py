"""
반기(상반기/하반기) 공통 유틸리티
"""

from typing import Optional, Tuple
import pandas as pd


HALF_START_MONTHS = {1, 7}
HALF_END_MONTHS = {6, 12}


def to_month_int(month_val) -> int:
    """날짜/문자열/정수에서 월(1~12)을 안전하게 추출"""
    if month_val is None or pd.isna(month_val):
        return 0

    if isinstance(month_val, int):
        return month_val if 1 <= month_val <= 12 else 0

    try:
        return pd.Timestamp(month_val).month
    except Exception:
        return 0


def get_half(month_val) -> str:
    """평가월 → 상반기/하반기"""
    month = to_month_int(month_val)
    return "상반기" if 1 <= month <= 6 else "하반기"


def get_half_months(month_val) -> list[int]:
    """해당 월이 속한 반기의 월 목록"""
    return list(range(1, 7)) if get_half(month_val) == "상반기" else list(range(7, 13))


def get_half_last_month(month_val) -> int:
    """해당 월이 속한 반기의 마감월"""
    return 6 if get_half(month_val) == "상반기" else 12


def get_period_month(month_val) -> int:
    """반기 내 진행월: 1월/7월=1, 6월/12월=6"""
    month = to_month_int(month_val)

    if 1 <= month <= 6:
        return month
    if 7 <= month <= 12:
        return month - 6

    return 0


def is_half_start(month_val) -> bool:
    """1월 또는 7월인지"""
    return to_month_int(month_val) in HALF_START_MONTHS


def is_half_end(month_val) -> bool:
    """6월 또는 12월인지"""
    return to_month_int(month_val) in HALF_END_MONTHS


def get_period_info(month_val) -> dict:
    """반기 공통 정보"""
    month_dt = pd.Timestamp(month_val)
    month = month_dt.month
    half = get_half(month)
    period_month = get_period_month(month)

    return {
        "current_month": month,
        "year": month_dt.year,
        "half": half,
        "is_first_half": half == "상반기",
        "is_half_start": is_half_start(month),
        "is_half_end": is_half_end(month),
        "period_month": period_month,
        "progress_rate": period_month / 6,
        "period_text": f"{half} {period_month}개월차",
    }


def get_latest_month(df: pd.DataFrame):
    """데이터의 최신 평가월 반환"""
    if df is None or df.empty or "평가월" not in df.columns:
        return None

    months = pd.to_datetime(df["평가월"], errors="coerce").dropna()
    return None if months.empty else months.max()


def filter_by_month(df: pd.DataFrame, month_val) -> pd.DataFrame:
    """특정 평가월 데이터 반환"""
    if df is None or df.empty or "평가월" not in df.columns or month_val is None:
        return pd.DataFrame()

    months = pd.to_datetime(df["평가월"], errors="coerce")
    return df[months == pd.Timestamp(month_val)].copy()


def filter_current_half(df: pd.DataFrame, latest_month=None) -> pd.DataFrame:
    """최신 평가월과 동일 연도·동일 반기 데이터만 반환"""
    if df is None or df.empty or "평가월" not in df.columns:
        return pd.DataFrame()

    if latest_month is None:
        latest_month = get_latest_month(df)

    if latest_month is None:
        return pd.DataFrame()

    latest_month = pd.Timestamp(latest_month)
    half_months = get_half_months(latest_month)

    work = df.copy()
    work["_month_dt"] = pd.to_datetime(work["평가월"], errors="coerce")
    work = work.dropna(subset=["_month_dt"])

    result = work[
        (work["_month_dt"].dt.year == latest_month.year)
        & (work["_month_dt"].dt.month.isin(half_months))
    ].copy()

    return result.drop(columns="_month_dt")


def filter_same_month_last_year(
    df_last_year: Optional[pd.DataFrame],
    latest_month,
) -> pd.DataFrame:
    """작년 동일 월 데이터 반환"""
    if (
        df_last_year is None
        or df_last_year.empty
        or "평가월" not in df_last_year.columns
        or latest_month is None
    ):
        return pd.DataFrame()

    latest_month = pd.Timestamp(latest_month)

    work = df_last_year.copy()
    work["_month_dt"] = pd.to_datetime(work["평가월"], errors="coerce")
    work = work.dropna(subset=["_month_dt"])

    result = work[
        (work["_month_dt"].dt.year == latest_month.year - 1)
        & (work["_month_dt"].dt.month == latest_month.month)
    ].copy()

    return result.drop(columns="_month_dt")


def get_comparison_data(
    df: pd.DataFrame,
    latest_month,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, str, Optional[pd.Timestamp]]:
    """
    비교 데이터 반환
    - 1월/7월: 전년 동월
    - 그 외: 같은 반기 내 직전 월
    """
    if latest_month is None:
        return pd.DataFrame(), "", None

    latest_month = pd.Timestamp(latest_month)

    if is_half_start(latest_month):
        compare_df = filter_same_month_last_year(df_last_year, latest_month)
        compare_month = pd.Timestamp(
            year=latest_month.year - 1,
            month=latest_month.month,
            day=1,
        )
        return compare_df, "전년 동월", compare_month

    current_half_df = filter_current_half(df, latest_month)

    if current_half_df.empty:
        return pd.DataFrame(), "전월", None

    month_series = pd.to_datetime(current_half_df["평가월"], errors="coerce")
    previous_months = month_series[month_series < latest_month]

    if previous_months.empty:
        return pd.DataFrame(), "전월", None

    compare_month = previous_months.max()
    compare_df = filter_by_month(current_half_df, compare_month)

    return compare_df, "전월", pd.Timestamp(compare_month)


def month_label(month_val) -> Optional[str]:
    """YYYY년 MM월 형식"""
    if month_val is None:
        return None

    try:
        return pd.Timestamp(month_val).strftime("%Y년 %m월")
    except Exception:
        return None
