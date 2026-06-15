"""
자동 인사이트 생성 v2.1 - 911점 절대평가 기준 반영 + 미세 조정
- 안전점검/중점고객/사용계약은 누적형 (하락 불가)
- 상담응대/상담기여/만족도는 변동형 (2개월 연속 + 의미있는 하락폭 경고)
- 반기 진척도 기반 정상 여부 판단
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass


# ==================== 평가 기준 ====================

# 911점 기준 (KPI별 달성률·점수)
TARGET_TOTAL = 911

KPI_TARGETS = {
    '안전점검':  {'rate': 90, 'score': 495, 'max': 550, 'type': '누적', 'icon': '🔵',
                'rate_col': '안전점검실점검율', 'score_col': '안전점검_점수'},
    '중점고객':  {'rate': 93, 'score': 93,  'max': 100, 'type': '누적', 'icon': '🟢',
                'rate_col': '중점고객안전점검율', 'score_col': '중점고객_점수'},
    '사용계약':  {'rate': 90, 'score': 45,  'max': 50,  'type': '누적', 'icon': '🟡',
                'rate_col': '사용계약율', 'score_col': '사용계약_점수'},
    '상담응대':  {'rate': 93, 'score': 93,  'max': 100, 'type': '변동', 'icon': '🟠',
                'rate_col': '상담응대율', 'score_col': '상담응대_점수'},
    '상담기여':  {'rate': 93, 'score': 93,  'max': 100, 'type': '변동', 'icon': '🔴',
                'rate_col': '상담기여도', 'score_col': '상담기여_점수'},
    '만족도':    {'rate': 92, 'score': 92,  'max': 100, 'type': '변동', 'icon': '🟣',
                'rate_col': '고객서비스만족도', 'score_col': '만족도_점수'},
}

# 변동형 KPI 연속 하락/상승 경고 - 최소 변동폭 (잔변동 무시용)
MIN_CHANGE_PCT = {
    '상담응대': 3.0,   # 3%p 이상 변동만
    '상담기여': 3.0,
    '만족도':   3.0,
    '사용계약': 5.0,   # 5%p 이상
}

# 안전점검 진척도 미달 허용 오차 (정상 진척도 대비 -8%p까지는 정상으로 간주)
PROGRESS_TOLERANCE = 8.0

# 911점 도달 가능 범위 (목표 -16점 ~ -1점)
NEAR_TARGET_GAP = 16


# ==================== 데이터 클래스 ====================

@dataclass
class Insight:
    icon: str
    title: str
    message: str
    category: str = "info"   # success / warning / danger / info
    priority: int = 5         # 낮을수록 우선
    action: Optional[str] = None


# ==================== 헬퍼 함수 ====================

def _get_half_progress(month: int) -> tuple:
    """월 → (반기, 진행 개월수, 진척도 %)"""
    if 1 <= month <= 6:
        return '상반기', month, month / 6 * 100
    else:
        return '하반기', month - 6, (month - 6) / 6 * 100


def _expected_rate(target_rate: float, month: int) -> float:
    """해당 월의 정상 누적 진척도 계산 (월별 산술 비례)"""
    _, _, progress = _get_half_progress(month)
    return target_rate * progress / 100


def _get_latest_two_months(df: pd.DataFrame):
    """최신 월과 전월 추출"""
    if '평가월' not in df.columns or df.empty:
        return None, None
    months = sorted(df.dropna(subset=['평가월'])['평가월'].unique())
    if len(months) < 1:
        return None, None
    latest = months[-1]
    prev = months[-2] if len(months) >= 2 else None
    return latest, prev


def _find_col(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """후보 컬럼명 중 데이터에 있는 첫 번째 컬럼 반환"""
    for c in candidates:
        if c in df.columns:
            return c
    return None


def _normalize_rate(value) -> float:
    """비율 값을 0~100 스케일로 정규화 (0~1 또는 0~100 자동 감지)"""
    if pd.isna(value):
        return 0.0
    v = float(value)
    if v <= 1.5:  # 0~1 비율로 저장된 경우
        return v * 100
    return v


# ==================== 인사이트 생성 함수 ====================

def insight_overall_score(df: pd.DataFrame, latest, prev) -> Optional[Insight]:
    """전체 평균 점수 및 변화"""
    if '총점' not in df.columns:
        return None

    df_latest = df[df['평가월'] == latest]
    avg = df_latest['총점'].mean()

    if pd.isna(avg):
        return None

    if prev is not None:
        df_prev = df[df['평가월'] == prev]
        prev_avg = df_prev['총점'].mean()
        if pd.notna(prev_avg):
            diff = avg - prev_avg
            sign = "+" if diff >= 0 else ""
            change_text = f" (전월 대비 {sign}{diff:.1f}점)"
        else:
            change_text = ""
    else:
        change_text = ""

    # 911점 대비
    gap = avg - TARGET_TOTAL
    if gap >= 0:
        category = "success"
        status = f"목표 +{gap:.1f}점 달성 중"
        priority = 5
    elif gap >= -30:
        category = "warning"
        status = f"목표까지 {-gap:.1f}점 부족"
        priority = 3
    else:
        category = "danger"
        status = f"목표까지 {-gap:.1f}점 부족 (긴급)"
        priority = 2

    return Insight(
        icon="📊",
        title="전체 평균",
        message=f"이번 달 평균 <b>{avg:.1f}점</b>{change_text} — {status}",
        category=category,
        priority=priority,
    )


def insight_safety_progress(df: pd.DataFrame, latest) -> List[Insight]:
    """
    안전점검·중점고객·사용계약 진척도 미달 센터 경고
    - 정상 진척도 - 허용 오차(8%p) 미달 시 경고
    - 반기 마감(6월/12월) 임박 시 긴급
    """
    insights = []
    month = pd.Timestamp(latest).month
    half_name, half_month, _ = _get_half_progress(month)

    df_latest = df[df['평가월'] == latest].copy()

    for kpi_name in ['안전점검', '중점고객']:
        cfg = KPI_TARGETS[kpi_name]
        rate_col = _find_col(df_latest, [cfg['rate_col'], f"{kpi_name}_달성률"])

        if rate_col is None:
            continue

        expected = _expected_rate(cfg['rate'], month)
        threshold = expected - PROGRESS_TOLERANCE  # 허용 오차 완화

        # 비율 정규화 컬럼 (분석용)
        df_work = df_latest[['센터명', rate_col]].copy()
        df_work['_norm_rate'] = df_work[rate_col].apply(_normalize_rate)

        df_behind = df_work[df_work['_norm_rate'] < threshold].copy()

        if df_behind.empty:
            continue

        df_behind = df_behind.sort_values('_norm_rate').head(3)

        names = []
        for _, row in df_behind.iterrows():
            actual = row['_norm_rate']
            shortfall = expected - actual
            names.append(f"{row['센터명']}({actual:.1f}%, -{shortfall:.1f}%p)")

        n_behind = len(df_work[df_work['_norm_rate'] < threshold])

        message = (
            f"{half_name} {half_month}개월차 정상 진척도 "
            f"<b>{expected:.0f}%</b> 미달 센터 <b>{n_behind}개</b><br>"
            f"하위: {', '.join(names)}"
        )

        # 6월/12월 (반기 마감) 임박 시 긴급도 ↑
        is_endmonth = (month in [6, 12])
        if is_endmonth:
            category = "danger"
            priority = 1
            action = f"⚡ 반기 마감 임박! 6월 내 {cfg['rate']}% 도달 필수"
        else:
            category = "warning"
            priority = 3
            remaining_months = 6 - half_month if month <= 6 else 12 - month
            if remaining_months > 0:
                need_per_month = (cfg['rate'] - expected) / remaining_months
                action = f"잔여 {remaining_months}개월간 월평균 +{need_per_month:.1f}%p 점검 필요"
            else:
                action = f"이번 달 내 {cfg['rate']}% 도달 점검 시급"

        insights.append(Insight(
            icon=cfg['icon'],
            title=f"{kpi_name} 진척도 미달",
            message=message,
            category=category,
            priority=priority,
            action=action,
        ))

    return insights


def insight_volatile_kpi_drop(df: pd.DataFrame, latest, prev) -> List[Insight]:
    """
    변동형 KPI 2개월 연속 하락 (의미있는 하락폭만)
    - 3개월 데이터 필요 (m1 > m2 > m3)
    - 누적 하락폭이 MIN_CHANGE_PCT 이상인 케이스만
    """
    insights = []
    if prev is None:
        return insights

    months = sorted(df.dropna(subset=['평가월'])['평가월'].unique())
    if len(months) < 3:
        return insights

    m1, m2, m3 = months[-3], months[-2], months[-1]

    for kpi_name, cfg in KPI_TARGETS.items():
        # 변동형만 + 사용계약 (사용계약도 하락 가능)
        if cfg['type'] != '변동' and kpi_name != '사용계약':
            continue

        rate_col = _find_col(df, [cfg['rate_col'], f"{kpi_name}_달성률"])
        if rate_col is None:
            continue

        df3 = df[df['평가월'].isin([m1, m2, m3])].copy()
        if df3.empty:
            continue

        # 비율 정규화
        df3['_norm_rate'] = df3[rate_col].apply(_normalize_rate)

        pivot = df3.pivot_table(
            index='센터명', columns='평가월', values='_norm_rate', aggfunc='mean'
        )

        if m1 not in pivot.columns or m2 not in pivot.columns or m3 not in pivot.columns:
            continue

        # 최소 하락폭 기준
        min_drop = MIN_CHANGE_PCT.get(kpi_name, 3.0)

        # 2개월 연속 하락 + 누적 하락폭 기준 충족
        falling = pivot[
            (pivot[m1] > pivot[m2]) &
            (pivot[m2] > pivot[m3]) &
            ((pivot[m1] - pivot[m3]) >= min_drop)
        ].copy()

        if falling.empty:
            continue

        falling['_drop'] = pivot[m1] - pivot[m3]
        falling = falling.sort_values('_drop', ascending=False).head(3)

        names = []
        for center, row in falling.iterrows():
            v1, v2, v3 = row[m1], row[m2], row[m3]
            drop = v1 - v3
            names.append(f"{center} ({v1:.1f}%→{v2:.1f}%→{v3:.1f}%, -{drop:.1f}%p)")

        total_count = len(falling) if len(falling) >= 3 else len(falling)
        # 정확한 전체 카운트
        full_count = (
            (pivot[m1] > pivot[m2]) &
            (pivot[m2] > pivot[m3]) &
            ((pivot[m1] - pivot[m3]) >= min_drop)
        ).sum()

        message = (
            f"<b>{kpi_name}</b> 2개월 연속 하락 "
            f"(누적 -{min_drop:.0f}%p 이상) <b>{full_count}개</b><br>"
            f"{'<br>'.join(names)}"
        )

        insights.append(Insight(
            icon=cfg['icon'],
            title=f"{kpi_name} 연속 하락 경고",
            message=message,
            category="danger",
            priority=2,
            action=f"{kpi_name} 하락 원인 점검 및 6월 회복 계획 수립 필요",
        ))

    return insights


def insight_volatile_kpi_rising(df: pd.DataFrame, latest, prev) -> List[Insight]:
    """변동형 KPI 2개월 연속 상승 (의미있는 상승폭만)"""
    insights = []
    if prev is None:
        return insights

    months = sorted(df.dropna(subset=['평가월'])['평가월'].unique())
    if len(months) < 3:
        return insights

    m1, m2, m3 = months[-3], months[-2], months[-1]
    rising_all = []

    for kpi_name, cfg in KPI_TARGETS.items():
        if cfg['type'] != '변동' and kpi_name != '사용계약':
            continue

        rate_col = _find_col(df, [cfg['rate_col'], f"{kpi_name}_달성률"])
        if rate_col is None:
            continue

        df3 = df[df['평가월'].isin([m1, m2, m3])].copy()
        df3['_norm_rate'] = df3[rate_col].apply(_normalize_rate)

        pivot = df3.pivot_table(index='센터명', columns='평가월', values='_norm_rate', aggfunc='mean')

        if m1 not in pivot.columns or m2 not in pivot.columns or m3 not in pivot.columns:
            continue

        min_rise = MIN_CHANGE_PCT.get(kpi_name, 3.0)

        rising = pivot[
            (pivot[m1] < pivot[m2]) &
            (pivot[m2] < pivot[m3]) &
            ((pivot[m3] - pivot[m1]) >= min_rise)
        ]

        for center in rising.index:
            v1, v3 = rising.loc[center, m1], rising.loc[center, m3]
            rising_all.append((center, kpi_name, cfg['icon'], v3 - v1))

    if not rising_all:
        return insights

    rising_all.sort(key=lambda x: -x[3])
    top3 = rising_all[:3]

    items = [
        f"{icon} {center} <b>{kpi}</b> +{gain:.1f}%p"
        for center, kpi, icon, gain in top3
    ]

    insights.append(Insight(
        icon="📈",
        title="상승 모멘텀",
        message=f"2개월 연속 의미있는 상승 사례<br>{'<br>'.join(items)}",
        category="success",
        priority=4,
    ))

    return insights


def insight_target_scenario(df: pd.DataFrame, latest) -> List[Insight]:
    """
    911점 도달 가능 센터 (현재 895~910점, 16점 이내)
    어떤 KPI를 얼마나 올리면 911점이 되는지 시뮬레이션
    """
    insights = []
    if '총점' not in df.columns:
        return insights

    df_latest = df[df['평가월'] == latest].copy()

    # 911점에서 NEAR_TARGET_GAP(16점) 이내 센터
    df_near = df_latest[
        (df_latest['총점'] >= TARGET_TOTAL - NEAR_TARGET_GAP) &
        (df_latest['총점'] < TARGET_TOTAL)
    ].sort_values('총점', ascending=False).head(5)

    if df_near.empty:
        return insights

    scenarios = []
    for _, row in df_near.iterrows():
        center = row['센터명']
        score = row['총점']
        gap = TARGET_TOTAL - score

        # 가장 임팩트 큰 KPI 찾기
        candidates = []
        for kpi_name, cfg in KPI_TARGETS.items():
            score_col = cfg['score_col']
            if score_col not in row.index:
                continue
            current = row.get(score_col, 0)
            if pd.isna(current):
                continue

            if cfg['type'] == '누적':
                max_possible = cfg['score']  # 911 기준 점수
            else:
                max_possible = cfg['max']

            potential = max_possible - current
            if potential > 0:
                candidates.append((kpi_name, cfg['icon'], current, potential, cfg['type']))

        if not candidates:
            continue

        candidates.sort(key=lambda x: -x[3])
        top_kpi = candidates[0]

        scenarios.append(
            f"<b>{center}</b> {score:.0f}점 (목표 -{gap:.0f}점)<br>"
            f"&nbsp;&nbsp;→ {top_kpi[1]} {top_kpi[0]} +{min(top_kpi[3], gap):.0f}점이면 911점 도달"
        )

    if scenarios:
        insights.append(Insight(
            icon="🎯",
            title="911점 도달 가능 센터",
            message="<br><br>".join(scenarios),
            category="info",
            priority=3,
            action="해당 센터에 우선 지원 집중 권장",
        ))

    return insights


def insight_danger_zone(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    위험 센터 (851점 미만)
    - 0개면 표시 안 함
    """
    if '총점' not in df.columns:
        return None

    df_latest = df[df['평가월'] == latest].copy()
    month = pd.Timestamp(latest).month
    half_name, _, _ = _get_half_progress(month)

    df_danger = df_latest[df_latest['총점'] < 851].sort_values('총점').head(5)

    if df_danger.empty:
        return None

    items = []
    for _, row in df_danger.iterrows():
        center = row['센터명']
        score = row['총점']
        items.append(f"{center} <b>{score:.0f}점</b>")

    endmonth = 6 if month <= 6 else 12

    return Insight(
        icon="🚨",
        title=f"위험 센터 ({len(df_danger)}개)",
        message=f"851점 미만<br>{', '.join(items)}",
        category="danger",
        priority=1,
        action=f"{half_name} 마감({endmonth}월)까지 911점 도달 위한 집중 관리 필요",
    )


def insight_top_performers(df: pd.DataFrame, latest) -> Optional[Insight]:
    """상위 우수 센터 (911점 이상)"""
    if '총점' not in df.columns:
        return None

    df_latest = df[df['평가월'] == latest].copy()
    df_top = df_latest[df_latest['총점'] >= TARGET_TOTAL].sort_values('총점', ascending=False)

    if df_top.empty:
        return None

    n = len(df_top)
    top3 = df_top.head(3)
    names = [f"{r['센터명']} <b>{r['총점']:.0f}점</b>" for _, r in top3.iterrows()]

    return Insight(
        icon="🏆",
        title=f"목표 달성 센터 {n}개",
        message=f"911점 이상 달성<br>Top 3: {', '.join(names)}",
        category="success",
        priority=4,
    )


# ==================== 통합 함수 ====================

def get_all_insights(df: pd.DataFrame, max_count: int = 6) -> List[Insight]:
    """
    모든 인사이트 생성 → 우선순위로 정렬 후 상위 N개 반환
    """
    if df is None or df.empty:
        return []

    latest, prev = _get_latest_two_months(df)
    if latest is None:
        return []

    all_insights = []

    ins = insight_overall_score(df, latest, prev)
    if ins:
        all_insights.append(ins)

    ins = insight_danger_zone(df, latest)
    if ins:
        all_insights.append(ins)

    all_insights.extend(insight_safety_progress(df, latest))
    all_insights.extend(insight_volatile_kpi_drop(df, latest, prev))
    all_insights.extend(insight_target_scenario(df, latest))
    all_insights.extend(insight_volatile_kpi_rising(df, latest, prev))

    ins = insight_top_performers(df, latest)
    if ins:
        all_insights.append(ins)

    all_insights.sort(key=lambda x: x.priority)
    return all_insights[:max_count]


# ==================== 랭킹 데이터 (기존 호환) ====================

def get_ranking_data(df_latest: pd.DataFrame, n: int = 5, mode: str = "score") -> Dict[str, pd.DataFrame]:
    """Top N / Bottom N 랭킹 데이터"""
    if df_latest is None or df_latest.empty or '총점' not in df_latest.columns:
        return {"top": pd.DataFrame(), "bottom": pd.DataFrame()}

    df_clean = df_latest.dropna(subset=['총점', '센터명']).copy()
    top = df_clean.sort_values('총점', ascending=False).head(n)
    bottom = df_clean.sort_values('총점', ascending=True).head(n)

    return {"top": top, "bottom": bottom}


def get_change_ranking(df: pd.DataFrame, n: int = 5) -> Dict[str, pd.DataFrame]:
    """전월 대비 상승/하락 랭킹"""
    if df is None or df.empty or '총점' not in df.columns:
        return {"rising": pd.DataFrame(), "falling": pd.DataFrame()}

    latest, prev = _get_latest_two_months(df)
    if prev is None:
        return {"rising": pd.DataFrame(), "falling": pd.DataFrame()}

    df_latest = df[df['평가월'] == latest][['센터명', '총점']].copy()
    df_prev = df[df['평가월'] == prev][['센터명', '총점']].rename(columns={'총점': '전월총점'})

    merged = df_latest.merge(df_prev, on='센터명', how='left')
    merged['변화량'] = merged['총점'] - merged['전월총점']
    merged = merged.dropna(subset=['변화량'])

    return {
        "rising": merged.sort_values('변화량', ascending=False).head(n),
        "falling": merged.sort_values('변화량', ascending=True).head(n),
    }
