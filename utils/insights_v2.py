# utils/insights_v2.py
"""
자동 인사이트 생성 v2.5
- 911점 절대평가 기준 (반기별 총점, 상/하반기 평균 911점 합격)
- 변동형 KPI 잔변동 무시 (MIN_CHANGE_PCT)
- 안전점검 누적 진척도 검증
- 911점 도달 가능 센터 시나리오
- 반기 전망 (낙관/현실 두 시나리오)
- 작년 동기 비교 (달성률 기준)
- 페이스 미달 랭킹 (911점 도달 위험 센터)
- 통합센터 작년 비교 자동 제외
- ⭐ v2.5: 반기 마지막 달(6/12월) 감지 → 예측/전망/페이스 인사이트 비활성화
- ⭐ v2.5: NaN 처리 버그 수정 (용산 -99% 오탐지 해결)
- ⭐ v2.5: 데이터 이상치(|변화폭| > 50%p) 필터링
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

# ==================== 상수 정의 ====================

TARGET_TOTAL = 911
PERFECT_TOTAL = 1000
DANGER_THRESHOLD = 851

MIN_CHANGE_PCT = {
    '상담응대': 3.0,
    '상담기여': 3.0,
    '만족도': 3.0,
    '사용계약': 5.0,
}

# ⭐ 신규: 이 이상 변동은 데이터 오류로 간주하고 인사이트에서 제외
MAX_REASONABLE_CHANGE_PCT = 50.0

PROGRESS_TOLERANCE = 8.0
NEAR_TARGET_LOW = 895
NEAR_TARGET_HIGH = 910
DROP_STREAK_THRESHOLD = 2

MERGED_CENTERS = {
    '퇴계원/별내', '별내/퇴계원',
    '금곡/경기동부', '경기동부/금곡',
    '덕소/양평', '양평/덕소',
}

LAST_YEAR_KPI_MAX = {
    '안전점검': 600, '중점고객': 100, '상담응대': 100,
    '상담기여': 100, '만족도': 100,
}
THIS_YEAR_KPI_MAX = {
    '안전점검': 550, '중점고객': 100, '사용계약': 50,
    '상담응대': 100, '상담기여': 100, '만족도': 100,
}

SAFETY_MONTHLY_TARGET = {
    1: 15, 2: 30, 3: 45, 4: 60, 5: 75, 6: 90,
    7: 15, 8: 30, 9: 45, 10: 60, 11: 75, 12: 90,
}

# ⭐ 반기 마지막 달 (평가 확정월)
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
    """⭐ 신규: 반기 마지막 달(6월/12월)인지 판정"""
    m = _to_month_int(month_val)
    return m in HALF_END_MONTHS

def _normalize_pct(val) -> float:
    """
    0~1 / 0~100 혼재 대응 → 0~100
    ⭐ v2.5: NaN은 NaN 그대로 반환 (기존엔 0.0 반환 → 오탐지 원인)
    """
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


# ==================== 기존 인사이트 함수 ====================

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
            action = f'{half_label} 평균 목표(911점) 달성 완료. 다음 반기 시작 전 성공 요인 공유 필요.'
        else:
            action = '현재 페이스 유지하며 우수 센터의 성공 요인을 확산해 보세요.'
    elif avg >= 880:
        category = 'info'
        if is_final:
            action = f'{half_label} 최종 평균 911점 미달({TARGET_TOTAL - avg:.0f}점 부족). 하반기 개선 계획 필요.'
        else:
            action = f'전체 평균 911점까지 {TARGET_TOTAL - avg:.0f}점 부족. 변동형 KPI 개선 여력 점검 필요.'
    else:
        category = 'warning'
        if is_final:
            action = f'{half_label} 최종 평균이 880점 미만입니다. 반기 리뷰 및 근본 원인 분석이 필요합니다.'
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


def insight_danger_zone(df: pd.DataFrame, latest) -> Optional[Insight]:
    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None
    danger = df_latest[df_latest['총점'] < DANGER_THRESHOLD].sort_values('총점')
    if danger.empty:
        return None

    names = ', '.join(danger['센터명'].head(3).tolist())
    extra = f' 외 {len(danger)-3}개' if len(danger) > 3 else ''
    is_final = _is_half_end(latest)

    if is_final:
        title = f'반기 최종 850점 미만 {len(danger)}개'
        action = '반기 최종 결과로 확정되었습니다. 하반기 시작 전 원인 분석 및 개선 액션 수립 필요.'
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
    """
    ⭐ v2.5: 반기 마지막 달엔 '진척도' 대신 '최종 달성률'로 판정
    """
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

    if is_final:
        # 6월/12월: 90% 미달 = 최종 미달
        behind = df_latest[df_latest['_progress'] < 90.0].sort_values('_progress')
        if behind.empty:
            return None
        names = ', '.join(behind['센터명'].head(3).tolist())
        extra = f' 외 {len(behind)-3}개' if len(behind) > 3 else ''
        return Insight(
            icon='🚨',
            title=f'안전점검 반기 목표 미달 {len(behind)}개',
            message=f'**{names}**{extra} 센터의 반기 실점검율이 90% 미만으로 최종 확정되었습니다.',
            category='danger',
            priority=3,
            action='반기 최종 결과입니다. 다음 반기 계획 수립 시 미달 원인 반영이 필요합니다.',
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
            priority=3,
            action=f'반기 마지막 달까지 90% 도달을 위해 잔여 점검량을 재분배하세요.',
        )


def insight_volatile_kpi_drop(df: pd.DataFrame, latest, prev) -> Optional[Insight]:
    """
    변동형 KPI 의미있는 하락
    ⭐ v2.5: NaN 완전 제거 + 이상치(-50%p 초과) 필터링
    """
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

        # ⭐ NaN → np.nan 유지, 이후 dropna로 완전 제거
        latest_vals = pivot[latest_col].apply(_normalize_pct)
        prev_vals = pivot[prev_col].apply(_normalize_pct)
        df_diff = (latest_vals - prev_vals).dropna()

        if df_diff.empty:
            continue

        # ⭐ 이상치 필터: |변화폭| > 50%p 는 데이터 오류로 간주
        df_diff = df_diff[df_diff.abs() <= MAX_REASONABLE_CHANGE_PCT]
        if df_diff.empty:
            continue

        meaningful_drops = df_diff[df_diff <= -threshold]
        if not meaningful_drops.empty:
            findings.append((
                kpi_name,
                len(meaningful_drops),
                meaningful_drops.idxmin(),
                meaningful_drops.min(),
            ))

    if not findings:
        return None

    msgs = []
    for kpi_name, cnt, worst_center, worst_val in findings:
        msgs.append(f'**{kpi_name}** {cnt}개 센터 (최대 하락: {worst_center} {worst_val:.1f}%p)')

    is_final = _is_half_end(latest)
    if is_final:
        # 반기 마지막 달엔 "월간 하락"보다는 "반기 최종 미달" 관점이 맞지만,
        # 마지막 달 자체의 흐름 참고용으로만 남기고 우선순위 낮춤
        priority = 8
        action = '반기 확정값입니다. 하락 원인은 하반기 시작 전 리뷰 자료로 활용하세요.'
    else:
        priority = 4
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
    """⭐ v2.5: NaN/이상치 필터링 동일 적용"""
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

        # 이상치 제거
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
        priority=5,
        action='상승 요인을 분석해 다른 센터에 확산할 만한 베스트 프랙티스를 도출하세요.',
    )


def insight_target_scenario(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    911점 도달 가능 센터
    ⭐ v2.5: 반기 마지막 달엔 '아쉬운 근접 미달'로 문구 변경
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

    if is_final:
        return Insight(
            icon='😢',
            title=f'911점 근접 미달 {len(near)}개',
            message=f'**{names}**{extra} 센터가 911점까지 16점 이내로 근접했으나 최종 미달로 확정되었습니다.',
            category='warning',
            priority=6,
            action='근접 미달 요인을 정밀 분석하여 하반기에는 목표 달성 계획을 수립하세요.',
        )
    else:
        return Insight(
            icon='🎯',
            title=f'911점 도달 가능 {len(near)}개',
            message=f'**{names}**{extra} 센터가 911점까지 16점 이내로 근접해 있습니다.',
            category='info',
            priority=6,
            action='이들 센터에 변동형 KPI 1~2개를 집중 관리하면 목표 달성 가능합니다.',
        )


def insight_half_final(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    ⭐ v2.5 신규: 반기 마지막 달 전용 - 최종 결과 요약 인사이트
    (예측/전망 대신 표시)
    """
    if not _is_half_end(latest):
        return None

    df_latest = _filter_by_month(df, latest)
    if df_latest.empty:
        return None

    total = len(df_latest)
    achieved = int((df_latest['총점'] >= TARGET_TOTAL).sum())
    caution = int(((df_latest['총점'] >= 895) & (df_latest['총점'] < TARGET_TOTAL)).sum())
    fail = int((df_latest['총점'] < 895).sum())

    rate = (achieved / total * 100) if total > 0 else 0
    half_label = _get_half(_to_month_int(latest))

    if rate >= 80:
        category = 'success'
        action = f'{half_label} 목표 달성률 {rate:.0f}%. 우수 성과. 다음 반기 시작 전 성공 사례 공유 필요.'
    elif rate >= 50:
        category = 'info'
        action = f'{half_label} 목표 달성률 {rate:.0f}%. 근접 미달 센터의 정밀 리뷰 필요.'
    else:
        category = 'warning'
        action = f'{half_label} 목표 달성률 {rate:.0f}%. 전사 차원의 개선 계획 수립 필요.'

    return Insight(
        icon='🏁',
        title=f'{half_label} 최종 결과 확정',
        message=(
            f'**911점 달성 {achieved}개** / 근접 미달 {caution}개 / 미달 {fail}개 '
            f'(전체 {total}개, 달성률 {rate:.0f}%)'
        ),
        category=category,
        priority=2,
        action=action,
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
    ⭐ v2.5: 반기 마지막 달이면 현재점수 = 최종점수 (예측 없음)
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
        # ⭐ 반기 마지막 달: 예측 = 현재점수 (확정값)
        predicted_realistic = current_score
        predicted_optimistic = current_score
        avg_pace = 0
    else:
        # 현실 예측: 최근 3개월 평균 증가 페이스
        if len(df_c) >= 2:
            recent = df_c.tail(min(4, len(df_c)))
            diffs = recent['총점'].diff().dropna()
            avg_pace = diffs.mean() if not diffs.empty else 0
        else:
            avg_pace = 0
        predicted_realistic = current_score + (avg_pace * remaining)

        # 낙관 예측
        optimistic_pace = max(avg_pace, 80 / max(remaining, 1))
        predicted_optimistic = min(current_score + (optimistic_pace * remaining), PERFECT_TOTAL)

    # 작년 동기 참고값
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

    # ⭐ 안전도: 반기 마지막이면 확정 결과 기준
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
    }


def get_half_outlook(
    df: pd.DataFrame,
    current_month=None,
    df_last_year: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    전 센터 반기 전망 DataFrame
    ⭐ v2.5: 반기 마지막 달이면 '반기 최종 결과' DataFrame 반환
    """
    if current_month is None:
        current_month = _safe_latest_month(df)
    if current_month is None:
        return pd.DataFrame()

    df_latest = _filter_by_month(df, current_month)
    if df_latest.empty:
        return pd.DataFrame()

    active_centers = df_latest['센터명'].dropna().unique()
    is_final = _is_half_end(current_month)

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
    """
    반기 전망 인사이트
    ⭐ v2.5: 반기 마지막 달이면 None 반환 (insight_half_final이 대신 표시)
    """
    if _is_half_end(latest):
        return None  # 반기 마지막 달엔 예측 없이 최종 결과만

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
        priority = 2
        worst = outlook[outlook['안전도'] == '위험'].head(3)['센터명'].tolist()
        action = f'위험 센터 {danger}개({", ".join(worst)})의 잔여 {remaining}개월 집중 관리 필요'
    elif caution > 0:
        category = 'warning'
        priority = 4
        action = f'주의 센터 {caution}개의 변동형 KPI 회복으로 911점 달성 가능'
    else:
        category = 'success'
        priority = 6
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
    """
    홈 화면에 표시할 인사이트 목록
    ⭐ v2.5: 반기 마지막 달이면 예측/전망 대신 최종 결과 인사이트 표시
    """
    if df is None or df.empty or '평가월' not in df.columns:
        return []

    months = pd.to_datetime(df['평가월'], errors='coerce').dropna().sort_values().unique()
    if len(months) == 0:
        return []

    latest = months[-1]
    prev = months[-2] if len(months) >= 2 else None

    candidates = [
        insight_overall_score(df, latest, prev),
        insight_danger_zone(df, latest),
        insight_safety_progress(df, latest),
        insight_volatile_kpi_drop(df, latest, prev),
        insight_volatile_kpi_rising(df, latest, prev),
        insight_target_scenario(df, latest),
        insight_half_strategy(df, latest, df_last_year),  # 반기 마지막이면 None
        insight_half_final(df, latest),                    # ⭐ 반기 마지막에만 나옴
    ]

    valid = [ins for ins in candidates if ins is not None]
    valid.sort(key=lambda x: x.priority)
    return valid[:max_count]


# ==================== 랭킹 함수 ====================

def get_ranking_data(df_latest: pd.DataFrame, n: int = 5, mode: str = 'score') -> Dict:
    if df_latest.empty:
        return {'top': pd.DataFrame(), 'bottom': pd.DataFrame()}

    sorted_df = df_latest.sort_values('총점', ascending=False)
    return {
        'top': sorted_df.head(n)[['센터명', '총점']].reset_index(drop=True),
        'bottom': sorted_df.tail(n).sort_values('총점')[['센터명', '총점']].reset_index(drop=True),
    }


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

    return {
        'up': rising, 'down': falling,
        'rising': rising, 'falling': falling,
    }


def get_pace_lag_ranking(
    df: pd.DataFrame,
    n: int = 5,
    df_last_year: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    페이스 미달 Top N 센터
    ⭐ v2.5: 반기 마지막 달이면 빈 DataFrame (예측 불필요)
    """
    if df is None or df.empty:
        return pd.DataFrame()

    latest = _safe_latest_month(df)
    if latest is None:
        return pd.DataFrame()

    # ⭐ 반기 마지막 달이면 페이스 예측 불필요
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
