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
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    avg = df_latest['총점'].mean()
    n_centers = len(df_latest)

    delta_msg = ''
    df_compare, compare_label = _comparison_data(df, latest, prev, df_last_year)
    if not df_compare.empty and '총점' in df_compare.columns:
        compare_avg = df_compare['총점'].mean()
        delta = avg - compare_avg
        arrow = '🔺' if delta > 0 else ('🔻' if delta < 0 else '➡️')
        delta_msg = f' ({compare_label} 대비 {arrow} {abs(delta):.1f}점)'

    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    if avg >= TARGET_TOTAL:
        category = 'success'
        action = (
            f'{half_label} 평균 911점 이상 달성. 현재 페이스면 연간 pass 안정권입니다.'
            if is_final else
            '현재 페이스 유지하며 우수 센터의 성공 요인을 확산해 보세요.'
        )
    elif avg >= 880:
        category = 'info'
        if is_final and half_label == '상반기':
            action = (
                f'{half_label} 평균 {avg:.1f}점. 연간 pass(평균 911점)를 위해 '
                f'**하반기 평균 {_needed_for_annual_pass(avg):.0f}점** 필요.'
            )
        elif is_final:
            action = f'{half_label} 최종 평균 {avg:.1f}점. 연간 종료. 개선 계획 필요.'
        else:
            action = f'전체 평균 911점까지 {TARGET_TOTAL - avg:.0f}점 부족.'
    else:
        category = 'warning'
        if is_final and half_label == '상반기':
            action = (
                f'{half_label} 평균 {avg:.1f}점(880점 미만). 연간 pass 위해 '
                f'하반기 평균 **{_needed_for_annual_pass(avg):.0f}점** 필요 — 강력한 회복 전략 시급.'
            )
        elif is_final:
            action = f'{half_label} 최종 평균이 880점 미만입니다. 근본 원인 분석 필요.'
        else:
            action = '평균이 880점 미만입니다. 안전점검 진척도와 변동형 KPI를 동시에 점검하세요.'

    return Insight(
        icon='📊',
        title=f'{half_label} 최종 평균 점수' if is_final else '전체 평균 점수',
        message=f'전체 {n_centers}개 센터 평균 **{avg:.1f}점**{delta_msg}',
        category=category, priority=1, action=action,
    )


def insight_achievers(df: pd.DataFrame, latest) -> Optional[Insight]:
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    achievers = df_latest[df_latest['총점'] >= TARGET_TOTAL].sort_values('총점', ascending=False)
    if achievers.empty:
        return None

    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))
    n_ach, n_total = len(achievers), len(df_latest)
    rate = n_ach / n_total * 100 if n_total else 0
    names = ', '.join(achievers['센터명'].head(5).tolist())
    extra = f' 외 {n_ach - 5}개' if n_ach > 5 else ''
    top_center, top_score = achievers.iloc[0]['센터명'], achievers.iloc[0]['총점']

    if is_final:
        title = f'🎉 {half_label} 911점 달성 {n_ach}개'
        message = (
            f'**{names}**{extra} 센터가 반기 목표(911점)를 달성했습니다. '
            f'최고: {top_center} {top_score:.1f}점 (달성률 {rate:.0f}%)'
        )
        action = (
            '우수 센터의 성공 요인을 분석해 하반기 시작 전 전사 공유하세요. '
            '이들 센터는 하반기 페이스만 유지해도 연간 pass 안정권입니다.'
            if half_label == '상반기' else
            '연간 우수 사례로 확산해 내년도 계획에 반영하세요.'
        )
    else:
        title = f'🎯 목표 달성 페이스 {n_ach}개'
        message = f'**{names}**{extra} 센터가 현재 911점 이상을 유지하고 있습니다. 선두: {top_center} {top_score:.1f}점'
        action = '현재 페이스를 반기 말까지 유지하도록 지원하세요.'

    return Insight('🏆', title, message, 'success', 2, action)


def insight_below_target(df: pd.DataFrame, latest) -> Optional[Insight]:
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    below = df_latest[df_latest['총점'] < TARGET_TOTAL].sort_values('총점')
    if below.empty:
        return None

    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))
    n_below = len(below)
    names = ', '.join(below['센터명'].head(3).tolist())
    extra = f' 외 {n_below - 3}개' if n_below > 3 else ''

    if is_final and half_label == '상반기':
        worst = below.iloc[0]
        worst_needed = _needed_for_annual_pass(worst['총점'])
        title = f'⚠️ 상반기 911점 미달 {n_below}개'
        message = (
            f'**{names}**{extra} 센터가 상반기 911점에 도달하지 못했습니다. '
            f'가장 낮은 {worst["센터명"]}({worst["총점"]:.1f}점)은 연간 pass 위해 '
            f'하반기 **{worst_needed:.0f}점** 필요.'
        )
        very_hard = below[below['총점'].apply(lambda s: _needed_for_annual_pass(s) > 950)]
        action = (
            f'{len(very_hard)}개 센터는 하반기 950점 이상 필요 — 구조적 개선 없이는 연간 pass 어려움. 우선순위 관리 대상.'
            if not very_hard.empty else
            '하반기에 상반기 대비 페이스 회복하면 연간 pass 가능한 수준. 변동형 KPI를 우선 점검하세요.'
        )
        category = 'warning'
    elif is_final:
        title, message = f'🚨 연간 911점 미달 {n_below}개', f'**{names}**{extra} 센터가 하반기에도 911점에 도달하지 못했습니다.'
        action, category = '연간 평가 최종 미달. 내년도 개선 계획 수립 시 근본 원인 분석 필요.', 'danger'
    else:
        title, message = f'911점 미달 {n_below}개 (진행 중)', f'**{names}**{extra} 센터가 현재 911점 미만입니다.'
        action, category = '반기 종료 전까지 페이스 회복 필요.', 'info'

    return Insight('📉' if not is_final else ('⚠️' if half_label == '상반기' else '🚨'),
                   title, message, category, 3, action)


def insight_danger_zone(df: pd.DataFrame, latest) -> Optional[Insight]:
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None
    danger = df_latest[df_latest['총점'] < DANGER_THRESHOLD].sort_values('총점')
    if danger.empty:
        return None

    names = ', '.join(danger['센터명'].head(3).tolist())
    extra = f' 외 {len(danger)-3}개' if len(danger) > 3 else ''
    is_final, half_label = _is_half_end(latest), _get_half(_to_month_int(latest))

    if is_final and half_label == '상반기':
        worst = danger.iloc[0]
        title = f'🚨 상반기 850점 미만 {len(danger)}개'
        action = (f'{worst["센터명"]}({worst["총점"]:.1f}점)은 하반기 '
                  f'{_needed_for_annual_pass(worst["총점"]):.0f}점 필요. 변동형 KPI + 안전점검 진척도 동시 집중 관리 시급.')
    elif is_final:
        title, action = f'🚨 연간 850점 미만 {len(danger)}개', '하반기에도 850점 미만. 근본 원인 분석 및 내년도 개선 계획 필요.'
    else:
        title, action = f'위험 센터 {len(danger)}개', '해당 센터의 변동형 KPI 회복과 안전점검 진척도를 우선 점검하세요.'

    return Insight('🚨', title, f'**{names}**{extra} 센터가 850점 미만입니다.', 'danger', 2, action)


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
    df: pd.DataFrame, center: str, current_month=None, df_last_year: Optional[pd.DataFrame] = None
) -> Optional[Dict]:
    df_c = df[df['센터명'] == center].copy()
    if df_c.empty:
        return None

    df_c['_month_dt'] = pd.to_datetime(df_c['평가월'], errors='coerce')
    df_c = df_c.dropna(subset=['_month_dt']).sort_values('_month_dt')
    if df_c.empty:
        return None

    if current_month is None:
        current_month = df_c['_month_dt'].max()
    current_month = pd.Timestamp(current_month)
    df_c = df_c[df_c['_month_dt'] <= current_month]
    if df_c.empty:
        return None

    cur_month_int = current_month.month
    half = _get_half(cur_month_int)
    half_months = range(1, 7) if half == '상반기' else range(7, 13)
    # 반기 리셋: 직전 반기(예: 6월)를 전망 추세에 포함하지 않는다.
    df_c = df_c[df_c['_month_dt'].dt.month.isin(half_months)].sort_values('_month_dt')
    if df_c.empty:
        return None

    half_last = _get_half_last_month(half)
    remaining = half_last - cur_month_int
    is_final = remaining == 0
    current_score = float(df_c['총점'].iloc[-1])

    current_penalty = 0
    if '주의경고' in df_c.columns:
        penalty = df_c['주의경고'].iloc[-1]
        current_penalty = float(0 if pd.isna(penalty) else penalty)

    if is_final:
        predicted_realistic = predicted_optimistic = current_score
    else:
        recent = df_c.tail(min(4, len(df_c)))
        diffs = recent['총점'].diff().dropna()
        avg_pace = diffs.mean() if not diffs.empty else 0
        predicted_realistic = current_score + avg_pace * remaining
        optimistic_pace = max(avg_pace, 80 / max(remaining, 1))
        predicted_optimistic = min(current_score + optimistic_pace * remaining, PERFECT_TOTAL)

    last_year_reference = None
    merged_flag = center in MERGED_CENTERS
    if df_last_year is not None and not merged_flag:
        df_ly = df_last_year[df_last_year['센터명'] == center].copy()
        if not df_ly.empty:
            df_ly['_month_dt'] = pd.to_datetime(df_ly['평가월'], errors='coerce')
            df_ly = df_ly.dropna(subset=['_month_dt'])
            # 현재와 같은 월(따라서 동일 반기)의 작년 실적을 참고값으로 사용
            df_ly = df_ly[df_ly['_month_dt'].dt.month == cur_month_int].sort_values('_month_dt')
            if not df_ly.empty:
                last_year_reference = float(df_ly['총점'].iloc[-1])

    h2_needed = _needed_for_annual_pass(current_score) if is_final and half == '상반기' else None
    if is_final:
        safety = '달성' if current_score >= TARGET_TOTAL else ('근접미달' if current_score >= 895 else '미달')
    else:
        safety = '안전' if predicted_realistic >= TARGET_TOTAL else ('주의' if predicted_realistic >= 895 else '위험')

    return {
        'center': center, 'half': half, 'is_final': is_final, 'current_score': current_score,
        'current_month': cur_month_int, 'remaining_months': remaining,
        'predicted_optimistic': predicted_optimistic, 'predicted_realistic': predicted_realistic,
        'last_year_reference': last_year_reference, 'merged_flag': merged_flag,
        'gap_to_target': TARGET_TOTAL - (current_score if is_final else predicted_realistic),
        'safety_level': safety, 'current_penalty': current_penalty, 'h2_needed_for_pass': h2_needed,
    }


def get_half_outlook(
    df: pd.DataFrame, current_month=None, df_last_year: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    if current_month is None:
        current_month = _safe_latest_month(df)
    if current_month is None:
        return pd.DataFrame()

    df_latest = _filter_by_month(df, current_month)
    if df_latest.empty:
        return pd.DataFrame()

    is_final, half = _is_half_end(current_month), _get_half(_to_month_int(current_month))
    rows = []
    for center in df_latest['센터명'].dropna().unique():
        result = predict_half_total(df, center, current_month, df_last_year)
        if result is None:
            continue
        row = {
            '센터명': result['center'], '현재점수': round(result['current_score'], 1),
            '목표차이': round(result['gap_to_target'], 1), '안전도': result['safety_level'],
            '통합여부': '🆕 통합' if result['merged_flag'] else '',
            '현재감점': result['current_penalty'],
            '작년참고': round(result['last_year_reference'], 1) if result['last_year_reference'] is not None else None,
        }
        if not is_final:
            row.update({'낙관전망': round(result['predicted_optimistic'], 1), '현실전망': round(result['predicted_realistic'], 1)})
        if is_final and half == '상반기' and result['h2_needed_for_pass'] is not None:
            row['하반기필요점수'] = round(result['h2_needed_for_pass'], 1)
        rows.append(row)

    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    return out.sort_values('현재점수' if is_final else '현실전망', ascending=False).reset_index(drop=True)


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
        insight_achievers(df, latest),
        insight_below_target(df, latest),
        insight_danger_zone(df, latest),
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
    df: pd.DataFrame, n: int = 5, df_last_year: Optional[pd.DataFrame] = None
) -> Dict:
    """
    1월/7월에는 작년 동월과 비교한다.
    기존 호출(get_change_ranking(df))도 유지되며, 작년 데이터가 전달되지 않은
    반기 시작월에는 빈 랭킹을 반환하여 6월/12월 오비교를 방지한다.
    """
    latest = _safe_latest_month(df)
    if latest is None:
        empty = pd.DataFrame()
        return {'up': empty, 'down': empty, 'rising': empty, 'falling': empty}

    months = pd.to_datetime(df['평가월'], errors='coerce').dropna().sort_values().unique()
    prev = None if _is_half_start(latest) else (pd.Timestamp(months[-2]) if len(months) >= 2 else None)
    df_l = _filter_by_month(df, latest)[['센터명', '총점']].copy()
    df_p, comparison_label = _comparison_data(df, latest, prev, df_last_year)
    if df_l.empty or df_p.empty or '총점' not in df_p.columns:
        empty = pd.DataFrame()
        return {'up': empty, 'down': empty, 'rising': empty, 'falling': empty}

    df_p = df_p[['센터명', '총점']].copy()
    merged = df_l.rename(columns={'총점': '총점_현재'}).merge(
        df_p.rename(columns={'총점': '총점_비교'}), on='센터명', how='inner'
    )
    if merged.empty:
        empty = pd.DataFrame()
        return {'up': empty, 'down': empty, 'rising': empty, 'falling': empty}

    merged['변화량'] = merged['총점_현재'] - merged['총점_비교']
    merged['총점'] = merged['총점_현재']
    merged['변화'] = merged['변화량']
    merged['점수변화'] = merged['변화량']
    merged['현재점수'] = merged['총점_현재']
    merged['전월점수'] = merged['총점_비교']  # 기존 화면 호환용 컬럼명
    merged['비교점수'] = merged['총점_비교']
    merged['비교기준'] = comparison_label

    rising = merged.sort_values('변화량', ascending=False).head(n).reset_index(drop=True)
    falling = merged.sort_values('변화량', ascending=True).head(n).reset_index(drop=True)
    return {'up': rising, 'down': falling, 'rising': rising, 'falling': falling}


def get_pace_lag_ranking(
    df: pd.DataFrame, n: int = 5, df_last_year: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    latest = _safe_latest_month(df)
    if latest is None or _is_half_end(latest):
        return pd.DataFrame()

    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return pd.DataFrame()

    rows = []
    for center in df_latest['센터명'].dropna().unique():
        result = predict_half_total(df, center, latest, df_last_year)
        if (
            result is None or result['current_score'] >= TARGET_TOTAL
            or result['predicted_realistic'] >= TARGET_TOTAL
        ):
            continue
        rows.append({
            '센터명': result['center'], '총점': round(result['current_score'], 1),
            '예상점수': round(result['predicted_realistic'], 1),
            '부족분': round(result['gap_to_target'], 1),
            '변화량': round(result['gap_to_target'], 1),
        })

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values('부족분', ascending=False).head(n).reset_index(drop=True)
    return result_df
