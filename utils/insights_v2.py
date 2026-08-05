"""
자동 인사이트 생성 v2.6
- 평가 체계: 상/하반기 각 1000점, 2개 반기 평균 911점 = 연간 pass
- 상반기 미달 시 하반기 만회 가능 (반기 독립 평가 아님)
- 반기 마감 시: 달성 센터 축하 + 미달 센터의 하반기 만회 필요치 안내
- NaN 처리 버그 수정 (용산 -99% 오탐지 해결)
- 데이터 이상치(|변화폭| > 50%p) 필터링
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

# ==================== 상수 정의 ====================

TARGET_TOTAL = 911            # 반기 목표 (연간 평균 pass 기준)
PERFECT_TOTAL = 1000          # 반기 만점
ANNUAL_PASS_TOTAL = TARGET_TOTAL * 2  # 연간 pass 총점 (1822점)
DANGER_THRESHOLD = 851        # 850점 이하 위험 (반기 내)

MIN_CHANGE_PCT = {
    '상담응대': 3.0, '상담기여': 3.0, '만족도': 3.0, '사용계약': 5.0,
}

# 이 이상 변동은 데이터 오류로 간주
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
    m = _to_month_int(month_val)
    return m in HALF_END_MONTHS

def _normalize_pct(val) -> float:
    """0~1 / 0~100 혼재 대응 → 0~100. NaN은 그대로 NaN 반환."""
    if pd.isna(val):
        return np.nan
    v = float(val)
    return v * 100 if v <= 1.0 else v

def _safe_latest_month(df: pd.DataFrame):
    if '평가월' not in df.columns or df.empty:
        return None
    months = pd.to_datetime(df['평가월'], errors='coerce').dropna()
    if months.empty:
        return None
    return months.max()

def _filter_by_month(df: pd.DataFrame, month) -> pd.DataFrame:
    if month is None or df.empty:
        return df.iloc[0:0]
    return df[pd.to_datetime(df['평가월'], errors='coerce') == pd.Timestamp(month)]

def _needed_for_annual_pass(h1_score: float) -> float:
    """상반기 점수로 연간 pass 하려면 하반기에 필요한 최소 점수"""
    needed = ANNUAL_PASS_TOTAL - h1_score
    return max(needed, 0)


# ==================== 인사이트 함수 ====================

def insight_overall_score(df: pd.DataFrame, latest, prev) -> Optional[Insight]:
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None
    avg = df_latest['총점'].mean()
    n_centers = len(df_latest)

    delta_msg = ""
    if prev is not None:
        df_prev = _filter_by_month(df, prev)
        if not df_prev.empty:
            prev_avg = df_prev['총점'].mean()
            delta = avg - prev_avg
            arrow = '🔺' if delta > 0 else ('🔻' if delta < 0 else '➡️')
            delta_msg = f" (전월 대비 {arrow} {abs(delta):.1f}점)"

    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    if avg >= TARGET_TOTAL:
        category = 'success'
        if is_final:
            action = (
                f'{half_label} 평균 911점 이상 달성. '
                f'현재 페이스면 연간 pass 안정권입니다.'
            )
        else:
            action = '현재 페이스 유지하며 우수 센터의 성공 요인을 확산해 보세요.'
    elif avg >= 880:
        category = 'info'
        if is_final and half_label == '상반기':
            needed = _needed_for_annual_pass(avg)
            action = (
                f'{half_label} 평균 {avg:.1f}점. 연간 pass(평균 911점)를 위해 '
                f'**하반기 평균 {needed:.0f}점** 필요.'
            )
        elif is_final:
            action = f'{half_label} 최종 평균 {avg:.1f}점. 연간 종료. 개선 계획 필요.'
        else:
            action = f'전체 평균 911점까지 {TARGET_TOTAL - avg:.0f}점 부족.'
    else:
        category = 'warning'
        if is_final and half_label == '상반기':
            needed = _needed_for_annual_pass(avg)
            action = (
                f'{half_label} 평균 {avg:.1f}점(880점 미만). '
                f'연간 pass 위해 하반기 평균 **{needed:.0f}점** 필요 — 강력한 회복 전략 시급.'
            )
        elif is_final:
            action = f'{half_label} 최종 평균이 880점 미만입니다. 근본 원인 분석 필요.'
        else:
            action = '평균이 880점 미만입니다. 안전점검 진척도와 변동형 KPI를 동시에 점검하세요.'

    title = f'{half_label} 최종 평균 점수' if is_final else '전체 평균 점수'

    return Insight(
        icon='📊',
        title=title,
        message=f'전체 {n_centers}개 센터 평균 **{avg:.1f}점**{delta_msg}',
        category=category,
        priority=1,
        action=action,
    )


def insight_achievers(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    ⭐ v2.6 신규: 911점 달성 센터 축하 인사이트
    (반기 마감 시 특히 강조, 진행 중일 땐 페이스 좋은 곳)
    """
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    achievers = df_latest[df_latest['총점'] >= TARGET_TOTAL].sort_values('총점', ascending=False)
    if achievers.empty:
        return None

    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))
    n_ach = len(achievers)
    n_total = len(df_latest)
    rate = (n_ach / n_total * 100) if n_total > 0 else 0

    names = ', '.join(achievers['센터명'].head(5).tolist())
    extra = f' 외 {n_ach-5}개' if n_ach > 5 else ''
    top_center = achievers.iloc[0]['센터명']
    top_score = achievers.iloc[0]['총점']

    if is_final:
        title = f'🎉 {half_label} 911점 달성 {n_ach}개'
        message = (
            f'**{names}**{extra} 센터가 반기 목표(911점)를 달성했습니다. '
            f'최고: {top_center} {top_score:.1f}점 (달성률 {rate:.0f}%)'
        )
        if half_label == '상반기':
            action = (
                f'우수 센터의 성공 요인을 분석해 하반기 시작 전 전사 공유하세요. '
                f'이들 센터는 하반기 페이스만 유지해도 연간 pass 안정권입니다.'
            )
        else:
            action = '연간 우수 사례로 확산해 내년도 계획에 반영하세요.'
    else:
        title = f'🎯 목표 달성 페이스 {n_ach}개'
        message = (
            f'**{names}**{extra} 센터가 현재 911점 이상을 유지하고 있습니다. '
            f'선두: {top_center} {top_score:.1f}점'
        )
        action = '현재 페이스를 반기 말까지 유지하도록 지원하세요.'

    return Insight(
        icon='🏆',
        title=title,
        message=message,
        category='success',
        priority=2,  # 상단에 노출
        action=action,
    )


def insight_below_target(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    ⭐ v2.6 신규: 911점 미달 센터 (반기 마감 시 하반기 만회 필요치 안내)
    """
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
    extra = f' 외 {n_below-3}개' if n_below > 3 else ''

    if is_final and half_label == '상반기':
        # 하반기 만회 관점
        worst = below.iloc[0]
        worst_needed = _needed_for_annual_pass(worst['총점'])
        title = f'⚠️ 상반기 911점 미달 {n_below}개'
        message = (
            f'**{names}**{extra} 센터가 상반기 911점에 도달하지 못했습니다. '
            f'가장 낮은 {worst["센터명"]}({worst["총점"]:.1f}점)은 '
            f'연간 pass 위해 하반기 **{worst_needed:.0f}점** 필요.'
        )
        # 하반기 필요치가 950 초과면 사실상 어려움
        very_hard = below[below['총점'].apply(
            lambda s: _needed_for_annual_pass(s) > 950
        )]
        if not very_hard.empty:
            action = (
                f'{len(very_hard)}개 센터는 하반기 950점 이상 필요 — '
                f'구조적 개선(안전점검·변동형 KPI 동시 개선) 없이는 연간 pass 어려움. '
                f'우선순위 관리 대상.'
            )
        else:
            action = (
                f'하반기에 상반기 대비 페이스 회복하면 연간 pass 가능한 수준. '
                f'변동형 KPI(상담응대·기여·만족도) 우선 점검하세요.'
            )
        category = 'warning'
    elif is_final:  # 하반기 마감
        title = f'🚨 연간 911점 미달 {n_below}개'
        message = f'**{names}**{extra} 센터가 하반기에도 911점에 도달하지 못했습니다.'
        action = '연간 평가 최종 미달. 내년도 개선 계획 수립 시 근본 원인 분석 필요.'
        category = 'danger'
    else:
        # 진행 중: 그냥 정보성
        title = f'911점 미달 {n_below}개 (진행 중)'
        message = f'**{names}**{extra} 센터가 현재 911점 미만입니다.'
        action = '반기 종료 전까지 페이스 회복 필요.'
        category = 'info'

    return Insight(
        icon='📉' if not is_final else ('⚠️' if half_label == '상반기' else '🚨'),
        title=title,
        message=message,
        category=category,
        priority=3,
        action=action,
    )


def insight_danger_zone(df: pd.DataFrame, latest) -> Optional[Insight]:
    """850점 미만 위험 센터 (기존 유지, 문구만 조정)"""
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None
    danger = df_latest[df_latest['총점'] < DANGER_THRESHOLD].sort_values('총점')
    if danger.empty:
        return None

    names = ', '.join(danger['센터명'].head(3).tolist())
    extra = f' 외 {len(danger)-3}개' if len(danger) > 3 else ''
    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    if is_final and half_label == '상반기':
        worst = danger.iloc[0]
        worst_needed = _needed_for_annual_pass(worst['총점'])
        title = f'🚨 상반기 850점 미만 {len(danger)}개'
        action = (
            f'{worst["센터명"]}({worst["총점"]:.1f}점)은 하반기 {worst_needed:.0f}점 필요. '
            f'변동형 KPI + 안전점검 진척도 동시 집중 관리 시급.'
        )
    elif is_final:
        title = f'🚨 연간 850점 미만 {len(danger)}개'
        action = '하반기에도 850점 미만. 근본 원인 분석 및 내년도 개선 계획 필요.'
    else:
        title = f'위험 센터 {len(danger)}개'
        action = '해당 센터의 변동형 KPI 회복과 안전점검 진척도를 우선 점검하세요.'

    return Insight(
        icon='🚨',
        title=title,
        message=f'**{names}**{extra} 센터가 850점 미만입니다.',
        category='danger',
        priority=2,
        action=action,
    )


def insight_safety_progress(df: pd.DataFrame, latest) -> Optional[Insight]:
    """안전점검 진척도"""
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

    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    if is_final:
        behind = df_latest[df_latest['_progress'] < 90.0].sort_values('_progress')
        if behind.empty:
            return None
        names = ', '.join(behind['센터명'].head(3).tolist())
        extra = f' 외 {len(behind)-3}개' if len(behind) > 3 else ''
        return Insight(
            icon='🚨',
            title=f'안전점검 반기 목표 미달 {len(behind)}개',
            message=(
                f'**{names}**{extra} 센터의 반기 실점검율이 90% 미만으로 최종 확정되었습니다.'
            ),
            category='danger',
            priority=4,
            action=(
                f'{half_label} 안전점검 최종 미달. '
                f'다음 반기는 초기부터 월별 진척도 관리 필요.'
            ),
        )
    else:
        threshold = expected - PROGRESS_TOLERANCE
        behind = df_latest[df_latest['_progress'] < threshold].sort_values('_progress')
        if behind.empty:
            return None
        names = ', '.join(behind['센터명'].head(3).tolist())
        extra = f' 외 {len(behind)-3}개' if len(behind) > 3 else ''
        return Insight(
            icon='⚠️',
            title=f'안전점검 진척도 미달 {len(behind)}개',
            message=(
                f'**{names}**{extra} 센터의 안전점검 누적률이 '
                f'{month}월 정상치({expected}%) 대비 {PROGRESS_TOLERANCE:.0f}%p 이상 부족합니다.'
            ),
            category='warning',
            priority=4,
            action='반기 마지막 달까지 90% 도달을 위해 잔여 점검량을 재분배하세요.',
        )


def insight_volatile_kpi_drop(df: pd.DataFrame, latest, prev) -> Optional[Insight]:
    """변동형 KPI 하락 (NaN + 이상치 필터링)"""
    if prev is None:
        return None

    volatile_cols = {
        '상담응대': '상담응대율',
        '상담기여': '상담기여도',
        '만족도': '고객서비스만족도',
    }

    findings = []
    for kpi_name, col in volatile_cols.items():
        if col not in df.columns:
            continue

        pivot = df.pivot_table(index='센터명', columns='평가월', values=col, aggfunc='first')
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)
        if pivot.shape[1] < 2:
            continue

        latest_col = pivot.columns[-1]
        prev_col = pivot.columns[-2]

        threshold = MIN_CHANGE_PCT.get(kpi_name, 3.0)

        latest_vals = pivot[latest_col].apply(_normalize_pct)
        prev_vals = pivot[prev_col].apply(_normalize_pct)
        df_diff = (latest_vals - prev_vals).dropna()

        if df_diff.empty:
            continue

        df_diff = df_diff[df_diff.abs() <= MAX_REASONABLE_CHANGE_PCT]
        if df_diff.empty:
            continue

        meaningful_drops = df_diff[df_diff <= -threshold]
        if not meaningful_drops.empty:
            findings.append((
                kpi_name, len(meaningful_drops),
                meaningful_drops.idxmin(), meaningful_drops.min(),
            ))

    if not findings:
        return None

    msgs = []
    for kpi_name, cnt, worst_center, worst_val in findings:
        msgs.append(f'**{kpi_name}** {cnt}개 센터 (최대 하락: {worst_center} {worst_val:.1f}%p)')

    is_final = _is_half_end(latest)
    if is_final:
        priority = 8
        action = '반기 확정값입니다. 하락 원인은 다음 반기 시작 전 리뷰 자료로 활용하세요.'
    else:
        priority = 5
        action = '하락폭이 큰 센터의 원인을 파악하고 다음 달 회복 계획을 수립하세요.'

    return Insight(
        icon='📉',
        title='변동형 KPI 의미있는 하락',
        message=' / '.join(msgs),
        category='warning',
        priority=priority,
        action=action,
    )


def insight_volatile_kpi_rising(df: pd.DataFrame, latest, prev) -> Optional[Insight]:
    """변동형 KPI 상승"""
    if prev is None:
        return None

    volatile_cols = {
        '상담응대': '상담응대율',
        '상담기여': '상담기여도',
        '만족도': '고객서비스만족도',
    }

    rising_total = 0
    best_kpi = None
    best_center = None
    best_val = 0

    for kpi_name, col in volatile_cols.items():
        if col not in df.columns:
            continue
        pivot = df.pivot_table(index='센터명', columns='평가월', values=col, aggfunc='first')
        pivot = pivot.reindex(sorted(pivot.columns), axis=1)
        if pivot.shape[1] < 2:
            continue

        threshold = MIN_CHANGE_PCT.get(kpi_name, 3.0)
        latest_vals = pivot[pivot.columns[-1]].apply(_normalize_pct)
        prev_vals = pivot[pivot.columns[-2]].apply(_normalize_pct)
        df_diff = (latest_vals - prev_vals).dropna()

        if df_diff.empty:
            continue

        df_diff = df_diff[df_diff.abs() <= MAX_REASONABLE_CHANGE_PCT]
        if df_diff.empty:
            continue

        meaningful_rises = df_diff[df_diff >= threshold]
        rising_total += len(meaningful_rises)

        if not meaningful_rises.empty and meaningful_rises.max() > best_val:
            best_val = meaningful_rises.max()
            best_center = meaningful_rises.idxmax()
            best_kpi = kpi_name

    if rising_total == 0 or best_center is None:
        return None

    return Insight(
        icon='📈',
        title=f'변동형 KPI 상승 모멘텀 {rising_total}건',
        message=f'**{best_center}**의 {best_kpi}가 {best_val:.1f}%p 상승하는 등 회복세가 보입니다.',
        category='success',
        priority=6,
        action='상승 요인을 분석해 다른 센터에 확산할 만한 베스트 프랙티스를 도출하세요.',
    )


def insight_near_miss(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    911점 근접 (895~910점) — 진행 중엔 '도달 가능', 반기 마감엔 '근접 미달'
    """
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    near = df_latest[
        (df_latest['총점'] >= NEAR_TARGET_LOW) &
        (df_latest['총점'] < TARGET_TOTAL)
    ].sort_values('총점', ascending=False)

    if near.empty:
        return None

    names = ', '.join(near['센터명'].head(5).tolist())
    extra = f' 외 {len(near)-5}개' if len(near) > 5 else ''
    is_final = _is_half_end(latest)
    half_label = _get_half(_to_month_int(latest))

    if is_final:
        if half_label == '상반기':
            action = (
                f'하반기에 조금만 끌어올리면 연간 pass 가능한 센터들입니다. '
                f'변동형 KPI 1~2개 집중 관리 필요.'
            )
            category = 'warning'
        else:
            action = '연간 근접 미달. 아쉬운 결과. 미달 요인 정밀 분석 필요.'
            category = 'warning'
        return Insight(
            icon='😢',
            title=f'{half_label} 911점 근접 미달 {len(near)}개',
            message=f'**{names}**{extra} 센터가 911점까지 16점 이내로 근접했으나 미달 확정.',
            category=category,
            priority=5,
            action=action,
        )
    else:
        return Insight(
            icon='🎯',
            title=f'911점 도달 가능 {len(near)}개',
            message=f'**{names}**{extra} 센터가 911점까지 16점 이내로 근접해 있습니다.',
            category='info',
            priority=7,
            action='이들 센터에 변동형 KPI 1~2개를 집중 관리하면 목표 달성 가능합니다.',
        )


# ==================== 반기 전망 함수 ====================

def predict_half_total(
    df: pd.DataFrame,
    center: str,
    current_month=None,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Dict]:
    """
    개별 센터의 반기 최종 예상 총점 예측
    반기 마지막 달이면 확정값 반환 + 하반기 필요치도 포함
    """
    df_c = df[df['센터명'] == center].copy()
    if df_c.empty:
        return None

    df_c['_month_dt'] = pd.to_datetime(df_c['평가월'], errors='coerce')
    df_c = df_c.dropna(subset=['_month_dt']).sort_values('_month_dt')
    if df_c.empty:
        return None

    if current_month is None:
        current_month = df_c['_month_dt'].max()

    df_c = df_c[df_c['_month_dt'] <= pd.Timestamp(current_month)]
    if df_c.empty:
        return None

    cur_month_int = pd.Timestamp(current_month).month
    half = _get_half(cur_month_int)
    half_last = _get_half_last_month(half)
    remaining = half_last - cur_month_int
    is_final = (remaining == 0)

    current_score = float(df_c['총점'].iloc[-1])
    current_penalty = 0
    if '주의경고' in df_c.columns:
        current_penalty += float(df_c['주의경고'].iloc[-1] or 0)

    if is_final:
        predicted_realistic = current_score
        predicted_optimistic = current_score
        avg_pace = 0
    else:
        if len(df_c) >= 2:
            recent = df_c.tail(min(4, len(df_c)))
            diffs = recent['총점'].diff().dropna()
            avg_pace = diffs.mean() if not diffs.empty else 0
        else:
            avg_pace = 0
        predicted_realistic = current_score + (avg_pace * remaining)
        optimistic_pace = max(avg_pace, 80 / max(remaining, 1))
        predicted_optimistic = min(current_score + (optimistic_pace * remaining), PERFECT_TOTAL)

    # 작년 참고
    last_year_reference = None
    merged_flag = center in MERGED_CENTERS
    if df_last_year is not None and not merged_flag:
        df_ly = df_last_year[df_last_year['센터명'] == center].copy()
        if not df_ly.empty:
            df_ly['_month_dt'] = pd.to_datetime(df_ly['평가월'], errors='coerce')
            df_ly = df_ly.dropna(subset=['_month_dt']).sort_values('_month_dt')
            if not df_ly.empty:
                ly_same_half = df_ly[df_ly['_month_dt'].dt.month.isin(
                    range(1, 7) if half == '상반기' else range(7, 13)
                )]
                if not ly_same_half.empty:
                    last_year_reference = float(ly_same_half['총점'].iloc[-1])

    # ⭐ v2.6: 상반기 마감일 때 '하반기 필요 점수' 계산
    h2_needed = None
    if is_final and half == '상반기':
        h2_needed = _needed_for_annual_pass(current_score)

    # 안전도
    if is_final:
        if current_score >= TARGET_TOTAL:
            safety = '달성'
        elif current_score >= 895:
            safety = '근접미달'
        else:
            safety = '미달'
    else:
        if predicted_realistic >= TARGET_TOTAL:
            safety = '안전'
        elif predicted_realistic >= 895:
            safety = '주의'
        else:
            safety = '위험'

    return {
        'center': center,
        'half': half,
        'is_final': is_final,
        'current_score': current_score,
        'current_month': cur_month_int,
        'remaining_months': remaining,
        'predicted_optimistic': predicted_optimistic,
        'predicted_realistic': predicted_realistic,
        'last_year_reference': last_year_reference,
        'merged_flag': merged_flag,
        'gap_to_target': TARGET_TOTAL - current_score if is_final else TARGET_TOTAL - predicted_realistic,
        'safety_level': safety,
        'current_penalty': current_penalty,
        'h2_needed_for_pass': h2_needed,
    }


def get_half_outlook(
    df: pd.DataFrame,
    current_month=None,
    df_last_year: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """전 센터 반기 전망/최종결과 DataFrame"""
    if current_month is None:
        current_month = _safe_latest_month(df)
    if current_month is None:
        return pd.DataFrame()

    df_latest = _filter_by_month(df, current_month)
    if df_latest.empty:
        return pd.DataFrame()

    active_centers = df_latest['센터명'].dropna().unique()
    is_final = _is_half_end(current_month)
    half = _get_half(_to_month_int(current_month))

    rows = []
    for center in active_centers:
        result = predict_half_total(df, center, current_month, df_last_year)
        if result is None:
            continue
        row = {
            '센터명': result['center'],
            '현재점수': round(result['current_score'], 1),
            '목표차이': round(result['gap_to_target'], 1),
            '안전도': result['safety_level'],
            '통합여부': '🆕 통합' if result['merged_flag'] else '',
            '현재감점': result['current_penalty'],
            '작년참고': round(result['last_year_reference'], 1) if result['last_year_reference'] else None,
        }
        if not is_final:
            row['낙관전망'] = round(result['predicted_optimistic'], 1)
            row['현실전망'] = round(result['predicted_realistic'], 1)
        # ⭐ 상반기 마감 시 하반기 필요점수 추가
        if is_final and half == '상반기' and result.get('h2_needed_for_pass') is not None:
            row['하반기필요점수'] = round(result['h2_needed_for_pass'], 1)
        rows.append(row)

    if not rows:
        return pd.DataFrame()

    df_out = pd.DataFrame(rows)
    sort_col = '현재점수' if is_final else '현실전망'
    df_out = df_out.sort_values(sort_col, ascending=False).reset_index(drop=True)
    return df_out


def insight_half_strategy(
    df: pd.DataFrame,
    latest,
    df_last_year: Optional[pd.DataFrame] = None,
) -> Optional[Insight]:
    """진행 중 반기 전망 (반기 마감 시엔 None)"""
    if _is_half_end(latest):
        return None

    outlook = get_half_outlook(df, latest, df_last_year)
    if outlook.empty:
        return None

    safe = (outlook['안전도'] == '안전').sum()
    caution = (outlook['안전도'] == '주의').sum()
    danger = (outlook['안전도'] == '위험').sum()
    total = len(outlook)

    half = _get_half(_to_month_int(latest))
    half_last = _get_half_last_month(half)
    cur_m = _to_month_int(latest)
    remaining = half_last - cur_m

    if danger > 0:
        category = 'danger'
        priority = 3
        worst = outlook[outlook['안전도'] == '위험'].head(3)['센터명'].tolist()
        action = f'위험 센터 {danger}개({", ".join(worst)})의 잔여 {remaining}개월 집중 관리 필요'
    elif caution > 0:
        category = 'warning'
        priority = 5
        action = f'주의 센터 {caution}개의 변동형 KPI 회복으로 911점 달성 가능'
    else:
        category = 'success'
        priority = 7
        action = '현재 페이스 유지 시 전 센터 911점 달성 가능'

    return Insight(
        icon='📅',
        title=f'{half} 마감 전망 ({remaining}개월 남음)',
        message=(
            f'현실 전망 기준 **안전 {safe}개 / 주의 {caution}개 / 위험 {danger}개** '
            f'(전체 {total}개 센터)'
        ),
        category=category,
        priority=priority,
        action=action,
    )


# ==================== 메인 통합 함수 ====================

def get_all_insights(
    df: pd.DataFrame,
    max_count: int = 6,
    df_last_year: Optional[pd.DataFrame] = None,
) -> List[Insight]:
    """홈 화면 인사이트 목록"""
    if df is None or df.empty or '평가월' not in df.columns:
        return []

    months = pd.to_datetime(df['평가월'], errors='coerce').dropna().sort_values().unique()
    if len(months) == 0:
        return []

    latest_month_num = pd.Timestamp(latest).month
    if latest_month_num in (1, 7):
        prev = None
    else:
        prev = months[-2]
        
    candidates = [
        insight_overall_score(df, latest, prev),
        insight_achievers(df, latest),          # ⭐ 달성 센터 축하
        insight_below_target(df, latest),        # ⭐ 미달 센터 + 하반기 만회
        insight_danger_zone(df, latest),
        insight_safety_progress(df, latest),
        insight_volatile_kpi_drop(df, latest, prev),
        insight_volatile_kpi_rising(df, latest, prev),
        insight_near_miss(df, latest),
        insight_half_strategy(df, latest, df_last_year),
    ]

    valid = [ins for ins in candidates if ins is not None]
    valid.sort(key=lambda x: x.priority)
    return valid[:max_count]


# ==================== 랭킹 함수 ====================

def get_ranking_data(df_latest: pd.DataFrame, n: int = 5, mode: str = 'score') -> Dict:
    """
    Top/Bottom 랭킹
    ⭐ v2.6: Bottom은 '911점 미달 센터만' 반환 (등수 하위 아님)
             Top은 기존대로 점수 상위 N개
    """
    if df_latest.empty:
        return {'top': pd.DataFrame(), 'bottom': pd.DataFrame()}

    sorted_df = df_latest.sort_values('총점', ascending=False)

    # Top: 상위 N개
    top = sorted_df.head(n)[['센터명', '총점']].reset_index(drop=True)

    # ⭐ Bottom: 911점 미달 센터만 (점수 낮은 순, 최대 n개)
    below_target = df_latest[df_latest['총점'] < TARGET_TOTAL].sort_values('총점')
    bottom = below_target.head(n)[['센터명', '총점']].reset_index(drop=True)

    return {'top': top, 'bottom': bottom}


def get_change_ranking(df: pd.DataFrame, n: int = 5) -> Dict:
    months = pd.to_datetime(df['평가월'], errors='coerce').dropna().sort_values().unique()
    if len(months) < 2:
        empty = pd.DataFrame()
        return {'up': empty, 'down': empty, 'rising': empty, 'falling': empty}

    latest, prev = months[-1], months[-2]

    df_l = df[pd.to_datetime(df['평가월'], errors='coerce') == pd.Timestamp(latest)][['센터명', '총점']].copy()
    df_p = df[pd.to_datetime(df['평가월'], errors='coerce') == pd.Timestamp(prev)][['센터명', '총점']].copy()

    df_l = df_l.rename(columns={'총점': '총점_현재'})
    df_p = df_p.rename(columns={'총점': '총점_전월'})

    merged = df_l.merge(df_p, on='센터명', how='inner')
    if merged.empty:
        empty = pd.DataFrame()
        return {'up': empty, 'down': empty, 'rising': empty, 'falling': empty}

    merged['변화량'] = merged['총점_현재'] - merged['총점_전월']
    merged['총점'] = merged['총점_현재']
    merged['변화'] = merged['변화량']
    merged['점수변화'] = merged['변화량']
    merged['현재점수'] = merged['총점_현재']
    merged['전월점수'] = merged['총점_전월']

    rising = merged.sort_values('변화량', ascending=False).head(n).reset_index(drop=True)
    falling = merged.sort_values('변화량').head(n).reset_index(drop=True)

    return {'up': rising, 'down': falling, 'rising': rising, 'falling': falling}


def get_pace_lag_ranking(
    df: pd.DataFrame,
    n: int = 5,
    df_last_year: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """페이스 미달 Top N (반기 마감 시엔 빈 DF)"""
    if df is None or df.empty:
        return pd.DataFrame()

    latest = _safe_latest_month(df)
    if latest is None:
        return pd.DataFrame()

    if _is_half_end(latest):
        return pd.DataFrame()

    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return pd.DataFrame()
    active_centers = df_latest['센터명'].dropna().unique()

    rows = []
    for center in active_centers:
        result = predict_half_total(df, center, latest, df_last_year)
        if result is None:
            continue
        if result['current_score'] >= TARGET_TOTAL:
            continue
        if result['predicted_realistic'] >= TARGET_TOTAL:
            continue

        rows.append({
            '센터명': result['center'],
            '총점': round(result['current_score'], 1),
            '예상점수': round(result['predicted_realistic'], 1),
            '부족분': round(result['gap_to_target'], 1),
            '변화량': round(result['gap_to_target'], 1),
        })

    if not rows:
        return pd.DataFrame()

    result_df = pd.DataFrame(rows)
    result_df = result_df.sort_values('부족분', ascending=False).head(n).reset_index(drop=True)

    return result_df
