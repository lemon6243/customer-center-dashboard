"""
자동 인사이트 생성 v2.7
- 평가 체계: 상/하반기 각 1000점, 2개 반기 평균 911점 = 연간 pass
- 반기 시작월(1월/7월)은 당해 전월이 아닌 작년 동일 월·동일 반기와 비교
- NaN 처리 및 비정상 KPI 변동값 필터링
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import pandas as pd
import numpy as np
from utils.prediction import add_predictions_to_df


# ==================== 상수 정의 ====================

TARGET_TOTAL = 911
PERFECT_TOTAL = 1000
ANNUAL_PASS_TOTAL = TARGET_TOTAL * 2
DANGER_THRESHOLD = 851

MIN_CHANGE_PCT = {
    '상담응대': 3.0, '상담기여': 3.0, '만족도': 3.0, '사용계약': 5.0,
}
MAX_REASONABLE_CHANGE_PCT = 50.0
PROGRESS_TOLERANCE = 8.0
NEAR_TARGET_LOW = 895
NEAR_TARGET_HIGH = 910

MERGED_CENTERS = {
    '퇴계원/별내', '별내/퇴계원',
    '금곡/경기동부', '경기동부/금곡',
    '덕소/양평', '양평/덕소',
}

LAST_YEAR_KPI_MAX = {
    '안전점검': 600, '중점고객': 100, '상담응대': 100, '상담기여': 100, '만족도': 100,
}
THIS_YEAR_KPI_MAX = {
    '안전점검': 550, '중점고객': 100, '사용계약': 50,
    '상담응대': 100, '상담기여': 100, '만족도': 100,
}

SAFETY_MONTHLY_TARGET = {
    1: 15, 2: 30, 3: 45, 4: 60, 5: 75, 6: 90,
    7: 15, 8: 30, 9: 45, 10: 60, 11: 75, 12: 90,
}
HALF_END_MONTHS = {6, 12}
HALF_START_MONTHS = {1, 7}


# ==================== 데이터 클래스 ====================

@dataclass
class Insight:
    icon: str
    title: str
    message: str
    category: str = 'info'
    priority: int = 5
    action: Optional[str] = None


# ==================== 헬퍼 함수 ====================

def _get_half(month: int) -> str:
    return '상반기' if 1 <= month <= 6 else '하반기'

def _get_half_last_month(half: str) -> int:
    return 6 if half == '상반기' else 12

def _to_month_int(month_val) -> int:
    if pd.isna(month_val):
        return 0
    if isinstance(month_val, (int, np.integer)):
        return int(month_val)
    try:
        return pd.to_datetime(month_val).month
    except Exception:
        return 0

def _is_half_end(month_val) -> bool:
    return _to_month_int(month_val) in HALF_END_MONTHS

def _is_half_start(month_val) -> bool:
    return _to_month_int(month_val) in HALF_START_MONTHS

def _normalize_pct(val) -> float:
    """0~1 / 0~100 혼재 대응. NaN은 NaN 유지."""
    if pd.isna(val):
        return np.nan
    v = float(val)
    return v * 100 if v <= 1.0 else v

def _safe_latest_month(df: pd.DataFrame):
    if '평가월' not in df.columns or df.empty:
        return None
    months = pd.to_datetime(df['평가월'], errors='coerce').dropna()
    return None if months.empty else months.max()

def _filter_by_month(df: pd.DataFrame, month) -> pd.DataFrame:
    if month is None or df is None or df.empty or '평가월' not in df.columns:
        return pd.DataFrame(columns=df.columns if isinstance(df, pd.DataFrame) else None)
    month_series = pd.to_datetime(df['평가월'], errors='coerce')
    return df[month_series == pd.Timestamp(month)]

def _filter_same_month_last_year(
    df_last_year: Optional[pd.DataFrame], latest
) -> pd.DataFrame:
    """작년 데이터 중 현재 평가월과 같은 '월'만 반환한다."""
    if (
        df_last_year is None or df_last_year.empty
        or '평가월' not in df_last_year.columns or latest is None
    ):
        return pd.DataFrame()

    target_month = pd.Timestamp(latest).month
    month_series = pd.to_datetime(df_last_year['평가월'], errors='coerce')
    return df_last_year[month_series.dt.month == target_month]

def _needed_for_annual_pass(h1_score: float) -> float:
    return max(ANNUAL_PASS_TOTAL - h1_score, 0)

def _comparison_data(
    df: pd.DataFrame,
    latest,
    prev,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Tuple[pd.DataFrame, str]:
    """
    비교 기준 반환.
    - 1월/7월: 작년 동월(동일 반기)
    - 그 외: 당해 전월
    """
    if _is_half_start(latest):
        return _filter_same_month_last_year(df_last_year, latest), '전년 동월'
    return _filter_by_month(df, prev), '전월'


# ==================== 인사이트 함수 ====================

def insight_overall_score(
    df: pd.DataFrame,
    latest,
    prev,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Insight]:
    """전체 평균: 진행 중에는 현재점수가 아닌 반기말 예측점수로 판정"""
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    avg_current = df_latest["총점"].mean()
    n_centers = len(df_latest)

    # 비교 문구: 1·7월은 전년 동월, 그 외는 같은 반기 전월
    delta_msg = ""
    df_compare, compare_label = _comparison_data(df, latest, prev, df_last_year)

    if not df_compare.empty and "총점" in df_compare.columns:
        compare_avg = df_compare["총점"].mean()
        delta = avg_current - compare_avg
        arrow = "🔺" if delta > 0 else ("🔻" if delta < 0 else "➡️")
        delta_msg = f" ({compare_label} 대비 {arrow} {abs(delta):.1f}점)"

    is_final = _is_half_end(latest)
    month_num = _to_month_int(latest)
    half_label = _get_half(month_num)
    period_month = month_num if month_num <= 6 else month_num - 6

    # 반기 마감: 실제 점수로 판단
    if is_final:
        final_avg = avg_current

        if final_avg >= TARGET_TOTAL:
            category = "success"
            action = f"{half_label} 평균 911점 이상 달성. 연간 pass 안정권입니다."
        elif final_avg >= 895:
            category = "warning"
            action = (
                f"{half_label} 최종 평균 {final_avg:.1f}점. "
                f"911점까지 {TARGET_TOTAL - final_avg:.1f}점 부족합니다."
            )
        else:
            category = "danger"
            action = f"{half_label} 최종 평균이 895점 미만입니다. 원인 분석과 개선계획이 필요합니다."

        return Insight(
            icon="📊",
            title=f"{half_label} 최종 평균 점수",
            message=f"전체 {n_centers}개 센터 평균 **{final_avg:.1f}점**{delta_msg}",
            category=category,
            priority=1,
            action=action,
        )

    # 진행 중: 성과분석과 동일한 예측점수로 판단
    outlook = get_half_outlook(
        df,
        current_month=latest,
        df_last_year=df_last_year,
    )

    avg_forecast = outlook["현실전망"].mean() if not outlook.empty else None

    if avg_forecast is None or pd.isna(avg_forecast):
        category = "info"
        action = "반기 마감 전망 데이터를 계산할 수 없습니다."
        forecast_msg = ""
    else:
        forecast_msg = f" · 반기말 예측 평균 **{avg_forecast:.1f}점**"

        if avg_forecast >= TARGET_TOTAL:
            category = "success"
            action = "현재 페이스 유지 시 반기 목표 911점 달성이 예상됩니다."
        elif avg_forecast >= 895:
            category = "warning"
            action = (
                f"반기말 예측 평균이 {avg_forecast:.1f}점입니다. "
                f"911점까지 {TARGET_TOTAL - avg_forecast:.1f}점 보완이 필요합니다."
            )
        else:
            category = "danger"
            action = (
                f"반기말 예측 평균이 {avg_forecast:.1f}점입니다. "
                "누적형 KPI와 변동형 KPI 개선이 필요합니다."
            )

    return Insight(
        icon="📊",
        title=f"{half_label} {period_month}개월차 평균 점수",
        message=(
            f"전체 {n_centers}개 센터 현재 평균 **{avg_current:.1f}점**"
            f"{delta_msg}{forecast_msg}"
        ),
        category=category,
        priority=1,
        action=action,
    )


def insight_achievers(
    df: pd.DataFrame,
    latest,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Insight]:
    """진행 중에는 예상 반기말 점수 911점 이상 센터를 표시"""
    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    # 마감월: 실제 점수 기준
    if is_final:
        df_latest = _filter_by_month(df, latest)

        if df_latest.empty:
            return None

        achievers = df_latest[df_latest["총점"] >= TARGET_TOTAL].sort_values(
            "총점", ascending=False
        )

        if achievers.empty:
            return None

        n_ach = len(achievers)
        names = ", ".join(achievers["센터명"].head(5).tolist())
        extra = f" 외 {n_ach - 5}개" if n_ach > 5 else ""

        return Insight(
            icon="🏆",
            title=f"🎉 {half_label} 911점 달성 {n_ach}개",
            message=f"**{names}**{extra} 센터가 반기 목표를 달성했습니다.",
            category="success",
            priority=2,
            action="우수 센터의 운영 사례를 다음 반기 운영계획에 공유하세요.",
        )

    # 진행월: 성과분석 공통 예측점수 기준
    outlook = get_half_outlook(
        df,
        current_month=latest,
        df_last_year=df_last_year,
    )

    if outlook.empty:
        return None

    safe = outlook[outlook["안전도"] == "안전"].sort_values(
        "현실전망", ascending=False
    )

    if safe.empty:
        return None

    n_safe = len(safe)
    names = ", ".join(safe["센터명"].head(5).tolist())
    extra = f" 외 {n_safe - 5}개" if n_safe > 5 else ""
    top = safe.iloc[0]

    return Insight(
        icon="🏆",
        title=f"🎯 911점 달성 안전 페이스 {n_safe}개",
        message=(
            f"**{names}**{extra} 센터가 반기말 911점 이상으로 예상됩니다. "
            f"선두: {top['센터명']} **{top['현실전망']:.1f}점 예상**"
        ),
        category="success",
        priority=2,
        action="현재 KPI 관리 수준을 유지하고 우수 운영 사례를 공유하세요.",
    )


def insight_below_target(
    df: pd.DataFrame,
    latest,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Insight]:
    """진행 중에는 현재점수 미달이 아니라 반기말 페이스 위험을 표시"""
    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    # 반기 마감: 실제 총점 기준
    if is_final:
        df_latest = _filter_by_month(df, latest)

        if df_latest.empty:
            return None

        below = df_latest[df_latest["총점"] < TARGET_TOTAL].sort_values("총점")

        if below.empty:
            return None

        n_below = len(below)
        names = ", ".join(below["센터명"].head(3).tolist())
        extra = f" 외 {n_below - 3}개" if n_below > 3 else ""

        return Insight(
            icon="⚠️",
            title=f"{half_label} 911점 미달 {n_below}개",
            message=f"**{names}**{extra} 센터가 반기 목표에 미달했습니다.",
            category="warning" if half_label == "상반기" else "danger",
            priority=3,
            action="센터별 미달 KPI와 개선 우선순위를 점검하세요.",
        )

    # 진행월: 예상 반기말 점수 895점 미만만 위험으로 표시
    outlook = get_half_outlook(
        df,
        current_month=latest,
        df_last_year=df_last_year,
    )

    if outlook.empty:
        return None

    risk = outlook[outlook["안전도"] == "위험"].sort_values("현실전망")

    if risk.empty:
        return None

    n_risk = len(risk)
    names = ", ".join(risk["센터명"].head(3).tolist())
    extra = f" 외 {n_risk - 3}개" if n_risk > 3 else ""
    worst = risk.iloc[0]

    return Insight(
        icon="⚠️",
        title=f"반기 페이스 위험 센터 {n_risk}개",
        message=(
            f"**{names}**{extra} 센터의 반기말 예상점수가 895점 미만입니다. "
            f"최저 예상: {worst['센터명']} **{worst['현실전망']:.1f}점**"
        ),
        category="warning",
        priority=3,
        action="안전점검·중점고객 등 누적형 KPI와 변동형 KPI의 개선 항목을 우선 점검하세요.",
    )


def insight_danger_zone(
    df: pd.DataFrame,
    latest,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Insight]:
    """진행 중에는 반기말 851점 미만 예상 센터만 강한 위험으로 표시"""
    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    # 마감월: 실제점수 기준
    if is_final:
        df_latest = _filter_by_month(df, latest)

        if df_latest.empty:
            return None

        danger = df_latest[df_latest["총점"] < DANGER_THRESHOLD].sort_values("총점")

        if danger.empty:
            return None

        names = ", ".join(danger["센터명"].head(3).tolist())
        extra = f" 외 {len(danger) - 3}개" if len(danger) > 3 else ""

        return Insight(
            icon="🚨",
            title=f"{half_label} 850점 미만 {len(danger)}개",
            message=f"**{names}**{extra} 센터가 850점 미만입니다.",
            category="danger",
            priority=2,
            action="최저 성과 KPI를 중심으로 긴급 개선계획을 수립하세요.",
        )

    # 진행월: 예측 반기말 점수 기준
    outlook = get_half_outlook(
        df,
        current_month=latest,
        df_last_year=df_last_year,
    )

    if outlook.empty:
        return None

    severe = outlook[outlook["현실전망"] < DANGER_THRESHOLD].sort_values("현실전망")

    if severe.empty:
        return None

    names = ", ".join(severe["센터명"].head(3).tolist())
    extra = f" 외 {len(severe) - 3}개" if len(severe) > 3 else ""

    return Insight(
        icon="🚨",
        title=f"반기 마감 851점 미만 전망 {len(severe)}개",
        message=(
            f"**{names}**{extra} 센터의 반기말 예상점수가 "
            f"{DANGER_THRESHOLD}점 미만입니다."
        ),
        category="danger",
        priority=2,
        action="해당 센터는 즉시 원인 진단과 KPI별 회복 목표 설정이 필요합니다.",
    )



def insight_safety_progress(df: pd.DataFrame, latest) -> Optional[Insight]:
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty or '안전점검실점검율' not in df.columns:
        return None

    month = _to_month_int(latest)
    expected = SAFETY_MONTHLY_TARGET.get(month, 0)
    if expected == 0:
        return None

    df_latest = df_latest.copy()
    df_latest['_progress'] = df_latest['안전점검실점검율'].apply(_normalize_pct)
    df_latest = df_latest.dropna(subset=['_progress'])
    if df_latest.empty:
        return None

    is_final, half_label = _is_half_end(latest), _get_half(month)
    if is_final:
        behind = df_latest[df_latest['_progress'] < 90.0].sort_values('_progress')
        if behind.empty:
            return None
        names = ', '.join(behind['센터명'].head(3).tolist())
        extra = f' 외 {len(behind)-3}개' if len(behind) > 3 else ''
        return Insight('🚨', f'안전점검 반기 목표 미달 {len(behind)}개',
                       f'**{names}**{extra} 센터의 반기 실점검율이 90% 미만으로 최종 확정되었습니다.',
                       'danger', 4, f'{half_label} 안전점검 최종 미달. 다음 반기는 초기부터 월별 진척도 관리 필요.')

    threshold = expected - PROGRESS_TOLERANCE
    behind = df_latest[df_latest['_progress'] < threshold].sort_values('_progress')
    if behind.empty:
        return None
    names = ', '.join(behind['센터명'].head(3).tolist())
    extra = f' 외 {len(behind)-3}개' if len(behind) > 3 else ''
    return Insight('⚠️', f'안전점검 진척도 미달 {len(behind)}개',
                   f'**{names}**{extra} 센터의 안전점검 누적률이 {month}월 정상치({expected}%) 대비 {PROGRESS_TOLERANCE:.0f}%p 이상 부족합니다.',
                   'warning', 4, '반기 마지막 달까지 90% 도달을 위해 잔여 점검량을 재분배하세요.')


def _get_kpi_change(
    df: pd.DataFrame, latest, prev, col: str, df_last_year: Optional[pd.DataFrame] = None
) -> Tuple[pd.Series, str]:
    """
    센터별 KPI 변화량.
    1월/7월은 작년 동월, 그 외에는 당해 전월과 비교한다.
    """
    df_latest = _filter_by_month(df, latest)
    df_compare, compare_label = _comparison_data(df, latest, prev, df_last_year)
    if df_latest.empty or df_compare.empty or col not in df_latest.columns or col not in df_compare.columns:
        return pd.Series(dtype=float), compare_label

    latest_vals = df_latest.set_index('센터명')[col].apply(_normalize_pct)
    compare_vals = df_compare.set_index('센터명')[col].apply(_normalize_pct)
    return (latest_vals - compare_vals).dropna(), compare_label


def insight_volatile_kpi_drop(
    df: pd.DataFrame, latest, prev, df_last_year: Optional[pd.DataFrame] = None
) -> Optional[Insight]:
    volatile_cols = {'상담응대': '상담응대율', '상담기여': '상담기여도', '만족도': '고객서비스만족도'}
    findings = []
    comparison_label = '전월'

    for kpi_name, col in volatile_cols.items():
        if col not in df.columns:
            continue
        df_diff, comparison_label = _get_kpi_change(df, latest, prev, col, df_last_year)
        df_diff = df_diff[df_diff.abs() <= MAX_REASONABLE_CHANGE_PCT]
        threshold = MIN_CHANGE_PCT.get(kpi_name, 3.0)
        meaningful_drops = df_diff[df_diff <= -threshold]
        if not meaningful_drops.empty:
            findings.append((kpi_name, len(meaningful_drops), meaningful_drops.idxmin(), meaningful_drops.min()))

    if not findings:
        return None

    msgs = [f'**{kpi}** {cnt}개 센터 (최대 하락: {center} {value:.1f}%p)'
            for kpi, cnt, center, value in findings]
    is_final = _is_half_end(latest)
    return Insight('📉', f'변동형 KPI 의미있는 하락 ({comparison_label} 대비)', ' / '.join(msgs),
                   'warning', 8 if is_final else 5,
                   '반기 확정값입니다. 하락 원인은 다음 반기 시작 전 리뷰 자료로 활용하세요.'
                   if is_final else '하락폭이 큰 센터의 원인을 파악하고 다음 달 회복 계획을 수립하세요.')


def insight_volatile_kpi_rising(
    df: pd.DataFrame, latest, prev, df_last_year: Optional[pd.DataFrame] = None
) -> Optional[Insight]:
    volatile_cols = {'상담응대': '상담응대율', '상담기여': '상담기여도', '만족도': '고객서비스만족도'}
    rising_total, best_kpi, best_center, best_val = 0, None, None, 0
    comparison_label = '전월'

    for kpi_name, col in volatile_cols.items():
        if col not in df.columns:
            continue
        df_diff, comparison_label = _get_kpi_change(df, latest, prev, col, df_last_year)
        df_diff = df_diff[df_diff.abs() <= MAX_REASONABLE_CHANGE_PCT]
        meaningful_rises = df_diff[df_diff >= MIN_CHANGE_PCT.get(kpi_name, 3.0)]
        rising_total += len(meaningful_rises)
        if not meaningful_rises.empty and meaningful_rises.max() > best_val:
            best_val, best_center, best_kpi = meaningful_rises.max(), meaningful_rises.idxmax(), kpi_name

    if rising_total == 0 or best_center is None:
        return None
    return Insight('📈', f'변동형 KPI 상승 모멘텀 {rising_total}건 ({comparison_label} 대비)',
                   f'**{best_center}**의 {best_kpi}가 {best_val:.1f}%p 상승하는 등 회복세가 보입니다.',
                   'success', 6, '상승 요인을 분석해 다른 센터에 확산할 만한 베스트 프랙티스를 도출하세요.')


def insight_near_miss(df: pd.DataFrame, latest) -> Optional[Insight]:
    # 반기 진행 중에는 현재 누적점수로 911/850 위험을 판정하지 않는다.
    if not _is_half_end(latest):
        return None

    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None
    near = df_latest[(df_latest['총점'] >= NEAR_TARGET_LOW) & (df_latest['총점'] < TARGET_TOTAL)].sort_values('총점', ascending=False)
    if near.empty:
        return None

    names = ', '.join(near['센터명'].head(5).tolist())
    extra = f' 외 {len(near)-5}개' if len(near) > 5 else ''
    is_final, half_label = _is_half_end(latest), _get_half(_to_month_int(latest))
    if is_final:
        return Insight('😢', f'{half_label} 911점 근접 미달 {len(near)}개',
                       f'**{names}**{extra} 센터가 911점까지 16점 이내로 근접했으나 미달 확정.',
                       'warning', 5,
                       '하반기에 조금만 끌어올리면 연간 pass 가능한 센터들입니다. 변동형 KPI 1~2개 집중 관리 필요.'
                       if half_label == '상반기' else '연간 근접 미달. 아쉬운 결과. 미달 요인 정밀 분석 필요.')
    return Insight('🎯', f'911점 도달 가능 {len(near)}개',
                   f'**{names}**{extra} 센터가 911점까지 16점 이내로 근접해 있습니다.',
                   'info', 7, '이들 센터에 변동형 KPI 1~2개를 집중 관리하면 목표 달성 가능합니다.')


# ==================== 반기 전망 함수 ====================

def predict_half_total(
    df: pd.DataFrame,
    center: str,
    current_month=None,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Dict]:
    """
    반기 최종점수 전망.

    우선순위
    1) 작년 같은 반기의 '현재월 점수 / 반기 최종점수' 진행률을 이용해 전망
    2) 작년 비교 데이터가 없으면 반기 경과개월 기준 단순 페이스로 전망

    예: 작년 7월 500점, 작년 12월 950점(진행률 52.6%)이고
        올해 7월 530점이면 → 530 / 0.526 = 약 1,000점 전망.
    """
    if df is None or df.empty:
        return None

    current_month = pd.Timestamp(current_month) if current_month is not None else _safe_latest_month(df)
    if current_month is None:
        return None

    cur_month_int = current_month.month
    half = _get_half(cur_month_int)
    half_months = list(range(1, 7)) if half == "상반기" else list(range(7, 13))
    half_last = _get_half_last_month(half)
    elapsed_months = cur_month_int if half == "상반기" else cur_month_int - 6
    remaining = half_last - cur_month_int
    is_final = remaining == 0
    merged_flag = center in MERGED_CENTERS

    # 올해: 현재 반기 데이터만 사용. 6월↔7월 데이터가 절대 섞이지 않게 한다.
    df_c = df[df["센터명"] == center].copy()
    if df_c.empty:
        return None
    df_c["_month_dt"] = pd.to_datetime(df_c["평가월"], errors="coerce")
    df_c = df_c.dropna(subset=["_month_dt"])
    df_c = df_c[
        (df_c["_month_dt"] <= current_month)
        & (df_c["_month_dt"].dt.month.isin(half_months))
    ].sort_values("_month_dt")
    if df_c.empty:
        return None

    current_score = float(df_c["총점"].iloc[-1])
    current_penalty = 0.0
    if "주의경고" in df_c.columns:
        penalty = df_c["주의경고"].iloc[-1]
        current_penalty = float(0 if pd.isna(penalty) else penalty)

    # 작년 같은 센터·같은 반기의 현재월 점수와 반기 마지막 점수
    last_year_reference = None
    last_year_final = None
    progress_ratio = None

    if df_last_year is not None and not df_last_year.empty and not merged_flag:
        df_ly = df_last_year[df_last_year["센터명"] == center].copy()
        if not df_ly.empty:
            df_ly["_month_dt"] = pd.to_datetime(df_ly["평가월"], errors="coerce")
            df_ly = df_ly.dropna(subset=["_month_dt"])
            df_ly = df_ly[df_ly["_month_dt"].dt.month.isin(half_months)].sort_values("_month_dt")

            same_month = df_ly[df_ly["_month_dt"].dt.month == cur_month_int]
            if not same_month.empty:
                last_year_reference = float(same_month["총점"].iloc[-1])

            # 해당 반기의 마지막 월(6월/12월)이 있으면 최종점수로 사용.
            # 아직 없다면 작년 데이터에 존재하는 마지막 월을 참고값으로 사용.
            final_row = df_ly[df_ly["_month_dt"].dt.month == half_last]
            if not final_row.empty:
                last_year_final = float(final_row["총점"].iloc[-1])
            elif not df_ly.empty:
                last_year_final = float(df_ly["총점"].iloc[-1])

            if (
                last_year_reference is not None
                and last_year_final is not None
                and last_year_reference > 0
                and last_year_final > 0
            ):
                ratio = last_year_reference / last_year_final
                # 비정상 데이터 방어: 현재월 진행률은 5~100% 범위만 인정
                if 0.05 <= ratio <= 1.0:
                    progress_ratio = ratio

    if is_final:
        predicted_realistic = current_score
        predicted_optimistic = current_score
        forecast_basis = "반기 확정"
    else:
        # 작년 같은 반기의 누적 진행 패턴이 있으면 가장 신뢰도 높은 전망으로 사용
        if progress_ratio is not None:
            predicted_realistic = min(current_score / progress_ratio, PERFECT_TOTAL)
            forecast_basis = "작년 동일 반기 진행률"
        else:
            # 작년 데이터가 없는 센터는 반기 경과 개월 수 기준으로 환산
            predicted_realistic = min(current_score / max(elapsed_months, 1) * 6, PERFECT_TOTAL)
            forecast_basis = "반기 경과개월 환산"

        # 낙관 전망: 현실 전망보다 낮지 않도록만 처리
        predicted_optimistic = max(predicted_realistic, min(PERFECT_TOTAL, current_score + (PERFECT_TOTAL - current_score) * 0.65))

    # 안전/주의/위험은 '현재 누적점수'가 아니라 '반기 최종 전망'으로 판정한다.
    if is_final:
        safety = "달성" if current_score >= TARGET_TOTAL else ("근접미달" if current_score >= 895 else "미달")
        gap_to_target = TARGET_TOTAL - current_score
    else:
        safety = "안전" if predicted_realistic >= TARGET_TOTAL else ("주의" if predicted_realistic >= 895 else "위험")
        gap_to_target = TARGET_TOTAL - predicted_realistic

    h2_needed = _needed_for_annual_pass(current_score) if is_final and half == "상반기" else None

    return {
        "center": center,
        "half": half,
        "is_final": is_final,
        "current_score": current_score,
        "current_month": cur_month_int,
        "elapsed_months": elapsed_months,
        "remaining_months": remaining,
        "predicted_optimistic": predicted_optimistic,
        "predicted_realistic": predicted_realistic,
        "last_year_reference": last_year_reference,
        "last_year_final": last_year_final,
        "progress_ratio": progress_ratio,
        "forecast_basis": forecast_basis,
        "merged_flag": merged_flag,
        "gap_to_target": gap_to_target,
        "safety_level": safety,
        "current_penalty": current_penalty,
        "h2_needed_for_pass": h2_needed,
    }


def get_half_outlook(
    df: pd.DataFrame,
    current_month=None,
    df_last_year: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    성과분석(overview.py)과 동일한 예측 로직으로 반기 전망 생성.

    공통 예측 기준
    - 누적형 KPI: 반기 진행률 기준 환산
    - 비누적형 KPI: 현재 점수 유지
    - 예측점수: 최대 1,000점
    """
    if df is None or df.empty:
        return pd.DataFrame()

    if current_month is None:
        current_month = _safe_latest_month(df)

    if current_month is None:
        return pd.DataFrame()

    current_month = pd.Timestamp(current_month)
    month_num = current_month.month
    period_month = month_num if month_num <= 6 else month_num - 6
    half_label = _get_half(month_num)
    is_final = period_month >= 6

    df_latest = _filter_by_month(df, current_month).copy()

    if df_latest.empty:
        return pd.DataFrame()

    # ⭐ 성과분석과 동일한 예측 함수 사용
    df_predicted = add_predictions_to_df(df_latest, period_month)

    rows = []

    for _, row in df_predicted.iterrows():
        center = str(row.get("센터명", ""))

        current_score = pd.to_numeric(row.get("총점"), errors="coerce")
        current_score = float(current_score) if pd.notna(current_score) else 0.0

        predicted_score = pd.to_numeric(row.get("예측점수"), errors="coerce")
        predicted_score = float(predicted_score) if pd.notna(predicted_score) else current_score

        # 반기 마감월은 예측점수 = 실제 점수
        final_score = current_score if is_final else predicted_score

        # 진행 중: 예측 반기 마감점수 기준 판정
        if is_final:
            if final_score >= TARGET_TOTAL:
                safety = "달성"
            elif final_score >= 895:
                safety = "근접미달"
            else:
                safety = "미달"
        else:
            if final_score >= TARGET_TOTAL:
                safety = "안전"
            elif final_score >= 895:
                safety = "주의"
            else:
                safety = "위험"

        # 작년 동일 월 참고점수
        last_year_reference = None

        if df_last_year is not None and not df_last_year.empty:
            ly = df_last_year.copy()
            ly["_month_dt"] = pd.to_datetime(ly["평가월"], errors="coerce")

            ly_row = ly[
                (ly["센터명"] == center)
                & (ly["_month_dt"].dt.month == month_num)
            ]

            if not ly_row.empty:
                ly_score = pd.to_numeric(ly_row.iloc[-1].get("총점"), errors="coerce")

                if pd.notna(ly_score):
                    last_year_reference = float(ly_score)

        # 감점
        current_penalty = 0.0

        for col in ["민원대응적정성", "주의경고", "가점"]:
            value = pd.to_numeric(row.get(col, 0), errors="coerce")

            if pd.notna(value):
                current_penalty += float(value)

        result = {
            "센터명": center,
            "현재점수": round(current_score, 1),
            "현실전망": round(final_score, 1),
            # 기존 home.py 호환용: 별도 낙관 전망은 사용하지 않음
            "낙관전망": round(final_score, 1),
            "목표차이": round(TARGET_TOTAL - final_score, 1),
            "안전도": safety,
            "현재감점": round(current_penalty, 1),
            "작년참고": round(last_year_reference, 1) if last_year_reference is not None else None,
            "통합여부": "🆕 통합" if center in MERGED_CENTERS else "",
            "전망근거": (
                "반기 최종 확정"
                if is_final
                else f"성과분석 공통 예측 · 반기 {period_month}/6개월 진행"
            ),
        }

        # 상반기 마감 시: 하반기 만회 필요 점수
        if is_final and half_label == "상반기":
            result["하반기필요점수"] = round(
                _needed_for_annual_pass(current_score),
                1,
            )

        rows.append(result)

    if not rows:
        return pd.DataFrame()

    result_df = pd.DataFrame(rows)

    sort_col = "현재점수" if is_final else "현실전망"

    return result_df.sort_values(
        sort_col,
        ascending=False,
    ).reset_index(drop=True)



def insight_half_strategy(
    df: pd.DataFrame, latest, df_last_year: Optional[pd.DataFrame] = None
) -> Optional[Insight]:
    if _is_half_end(latest):
        return None
    outlook = get_half_outlook(df, latest, df_last_year)
    if outlook.empty:
        return None

    safe = (outlook['안전도'] == '안전').sum()
    caution = (outlook['안전도'] == '주의').sum()
    danger = (outlook['안전도'] == '위험').sum()
    half = _get_half(_to_month_int(latest))
    remaining = _get_half_last_month(half) - _to_month_int(latest)

    if danger:
        category, priority = 'danger', 3
        worst = ', '.join(outlook[outlook['안전도'] == '위험'].head(3)['센터명'].tolist())
        action = f'위험 센터 {danger}개({worst})의 잔여 {remaining}개월 집중 관리 필요'
    elif caution:
        category, priority, action = 'warning', 5, f'주의 센터 {caution}개의 변동형 KPI 회복으로 911점 달성 가능'
    else:
        category, priority, action = 'success', 7, '현재 페이스 유지 시 전 센터 911점 달성 가능'

    return Insight('📅', f'{half} 마감 전망 ({remaining}개월 남음)',
                   f'현실 전망 기준 **안전 {safe}개 / 주의 {caution}개 / 위험 {danger}개** (전체 {len(outlook)}개 센터)',
                   category, priority, action)


# ==================== 메인 통합 함수 ====================

def get_all_insights(
    df: pd.DataFrame, max_count: int = 6, df_last_year: Optional[pd.DataFrame] = None
) -> List[Insight]:
    if df is None or df.empty or '평가월' not in df.columns:
        return []

    months = pd.to_datetime(df['평가월'], errors='coerce').dropna().sort_values().unique()
    if len(months) == 0:
        return []

    latest = pd.Timestamp(months[-1])
    # 1·7월이면 prev=None. 실제 비교는 각 함수가 df_last_year의 동일 월로 수행한다.
    prev = None if _is_half_start(latest) else (pd.Timestamp(months[-2]) if len(months) >= 2 else None)

    candidates = [
        insight_overall_score(df, latest, prev, df_last_year),
        insight_achievers(df, latest, df_last_year),
        insight_below_target(df, latest, df_last_year),
        insight_danger_zone(df, latest, df_last_year),
        insight_safety_progress(df, latest),
        insight_volatile_kpi_drop(df, latest, prev, df_last_year),
        insight_volatile_kpi_rising(df, latest, prev, df_last_year),
        insight_near_miss(df, latest),
        insight_half_strategy(df, latest, df_last_year),
    ]
    valid = [item for item in candidates if item is not None]
    valid.sort(key=lambda item: item.priority)
    return valid[:max_count]


# ==================== 랭킹 함수 ====================

def get_ranking_data(df_latest: pd.DataFrame, n: int = 5, mode: str = 'score') -> Dict:
    if df_latest.empty:
        return {'top': pd.DataFrame(), 'bottom': pd.DataFrame()}

    sorted_df = df_latest.sort_values('총점', ascending=False)
    top = sorted_df.head(n)[['센터명', '총점']].reset_index(drop=True)
    below_target = df_latest[df_latest['총점'] < TARGET_TOTAL].sort_values('총점')
    bottom = below_target.head(n)[['센터명', '총점']].reset_index(drop=True)
    return {'top': top, 'bottom': bottom}


def get_change_ranking(
    df: pd.DataFrame,
    n: int = 5,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    점수 변화 랭킹

    - 1월/7월: 작년 동일 월 비교
    - 그 외 월: 현재 반기 내 직전월 비교
    """
    empty = pd.DataFrame()
    result_empty = {
        'up': empty, 'down': empty,
        'rising': empty, 'falling': empty,
    }

    if df is None or df.empty or '평가월' not in df.columns:
        return result_empty

    work = df.copy()
    work['_month_dt'] = pd.to_datetime(work['평가월'], errors='coerce')
    work = work.dropna(subset=['_month_dt'])

    if work.empty:
        return result_empty

    latest = work['_month_dt'].max()
    latest_month_num = latest.month

    # 최신월 데이터
    df_l = work[
        work['_month_dt'] == latest
    ][['센터명', '총점']].copy()

    if df_l.empty:
        return result_empty

    # 1월/7월: 작년 동월 비교
    if latest_month_num in (1, 7):
        if df_last_year is None or df_last_year.empty:
            return result_empty

        ly = df_last_year.copy()
        ly['_month_dt'] = pd.to_datetime(ly['평가월'], errors='coerce')
        ly = ly.dropna(subset=['_month_dt'])

        df_p = ly[
            ly['_month_dt'].dt.month == latest_month_num
        ][['센터명', '총점']].copy()

    # 그 외: 같은 반기 내 직전 월 비교
    else:
        same_year = work[work['_month_dt'].dt.year == latest.year].copy()

        if latest_month_num <= 6:
            same_half = same_year[same_year['_month_dt'].dt.month.between(1, 6)]
        else:
            same_half = same_year[same_year['_month_dt'].dt.month.between(7, 12)]

        previous_dates = same_half[
            same_half['_month_dt'] < latest
        ]['_month_dt']

        if previous_dates.empty:
            return result_empty

        prev = previous_dates.max()

        df_p = same_half[
            same_half['_month_dt'] == prev
        ][['센터명', '총점']].copy()

    if df_p.empty:
        return result_empty

    df_l = df_l.rename(columns={'총점': '총점_현재'})
    df_p = df_p.rename(columns={'총점': '총점_비교'})

    merged = df_l.merge(df_p, on='센터명', how='inner')

    if merged.empty:
        return result_empty

    merged['변화량'] = merged['총점_현재'] - merged['총점_비교']
    merged['총점'] = merged['총점_현재']
    merged['변화'] = merged['변화량']
    merged['점수변화'] = merged['변화량']
    merged['현재점수'] = merged['총점_현재']
    merged['전월점수'] = merged['총점_비교']

    rising = merged.sort_values('변화량', ascending=False).head(n).reset_index(drop=True)
    falling = merged.sort_values('변화량', ascending=True).head(n).reset_index(drop=True)

    return {
        'up': rising,
        'down': falling,
        'rising': rising,
        'falling': falling,
    }



def get_pace_lag_ranking(
    df: pd.DataFrame,
    n: int = 5,
    df_last_year: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    진행 중인 반기의 페이스 위험 센터.

    성과분석과 동일한 예측점수 기준으로
    반기 최종 예상점수가 895점 미만인 센터만 반환.
    """
    if df is None or df.empty:
        return pd.DataFrame()

    latest = _safe_latest_month(df)

    if latest is None or _is_half_end(latest):
        return pd.DataFrame()

    outlook = get_half_outlook(
        df,
        current_month=latest,
        df_last_year=df_last_year,
    )

    if outlook.empty:
        return pd.DataFrame()

    risk_df = outlook[outlook["안전도"] == "위험"].copy()

    if risk_df.empty:
        return pd.DataFrame()

    risk_df["총점"] = risk_df["현재점수"]
    risk_df["예상점수"] = risk_df["현실전망"]
    risk_df["부족분"] = risk_df["목표차이"]
    risk_df["변화량"] = risk_df["목표차이"]

    return risk_df[
        ["센터명", "총점", "예상점수", "부족분", "변화량"]
    ].sort_values(
        "부족분",
        ascending=False,
    ).head(n).reset_index(drop=True)

    return result_df
