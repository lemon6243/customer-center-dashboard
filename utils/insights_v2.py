"""
자동 인사이트 생성 v2 - 911점 절대평가 기준 반영
- 안전점검/중점고객/사용계약은 누적형 (하락 불가)
- 상담응대/상담기여/만족도는 변동형 (2개월 연속 하락 경고)
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

# 변동형 KPI 연속 하락 경고 기준
DROP_STREAK_THRESHOLD = 2


# ==================== 데이터 클래스 ====================

@dataclass
class Insight:
    icon: str
    title: str
    message: str
    category: str = "info"   # success / warning / danger / info
    priority: int = 5         # 낮을수록 우선
    action: Optional[str] = None  # 액션 가이드 (선택)


# ==================== 헬퍼 함수 ====================

def _get_half_progress(month: int) -> tuple:
    """
    월 → (반기, 진행 개월수, 진척도 %)
    예: 5월 → ('상반기', 5, 83.3%)
    """
    if 1 <= month <= 6:
        return '상반기', month, month / 6 * 100
    else:
        return '하반기', month - 6, (month - 6) / 6 * 100


def _expected_rate(target_rate: float, month: int) -> float:
    """
    해당 월의 정상 누적 진척도 계산
    예: 안전점검 목표 90%, 5월 → 90% × 5/6 = 75%
    """
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
    안전점검·중점고객 진척도 미달 센터 경고
    (누적형 KPI - 하락은 없지만 진척도가 늦으면 마감 도달 어려움)
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
        # 미달 기준: 정상 진척도 - 5%p 이상 부족
        threshold = expected - 5

        df_behind = df_latest[df_latest[rate_col] < threshold].copy()

        if df_behind.empty:
            continue

        # 진척도 가장 낮은 센터 Top 3
        df_behind = df_behind.sort_values(rate_col).head(3)

        names = []
        for _, row in df_behind.iterrows():
            actual = row[rate_col]
            # 데이터가 0~1 비율이면 100배
            if actual <= 1:
                actual = actual * 100
            shortfall = expected - actual
            names.append(f"{row['센터명']}({actual:.0f}%, -{shortfall:.0f}%p)")

        n_total = len(df_latest[df_latest[rate_col].notna()])
        n_behind = len(df_latest[df_latest[rate_col] < threshold])

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
            remaining_months = 6 - half_month
            need_per_month = (cfg['rate'] - expected) / max(remaining_months, 1)
            action = f"잔여 {remaining_months}개월간 월평균 +{need_per_month:.1f}%p 점검 필요"

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
    변동형 KPI (상담응대/상담기여/만족도/사용계약) 2개월 연속 하락 센터
    """
    insights = []
    if prev is None:
        return insights

    # 최근 3개월 확보 (2개월 연속 하락 = 3개 시점 필요)
    months = sorted(df.dropna(subset=['평가월'])['평가월'].unique())
    if len(months) < 3:
        return insights

    m1, m2, m3 = months[-3], months[-2], months[-1]  # 3개월 전, 전월, 최신

    for kpi_name, cfg in KPI_TARGETS.items():
        # 변동형 + 사용계약 포함 (사용계약도 하락 가능)
        if cfg['type'] != '변동' and kpi_name != '사용계약':
            continue

        rate_col = _find_col(df, [cfg['rate_col'], f"{kpi_name}_달성률"])
        if rate_col is None:
            continue

        # 센터별 3개월 추이
        df3 = df[df['평가월'].isin([m1, m2, m3])].copy()
        if df3.empty:
            continue

        pivot = df3.pivot_table(
            index='센터명', columns='평가월', values=rate_col, aggfunc='mean'
        )

        if m1 not in pivot.columns or m2 not in pivot.columns or m3 not in pivot.columns:
            continue

        # 2개월 연속 하락 = m1 > m2 > m3
        falling = pivot[
            (pivot[m1] > pivot[m2]) & (pivot[m2] > pivot[m3])
        ].copy()

        if falling.empty:
            continue

        falling['총하락폭'] = pivot[m1] - pivot[m3]
        falling = falling.sort_values('총하락폭', ascending=False).head(3)

        names = []
        for center, row in falling.iterrows():
            v1, v2, v3 = row[m1], row[m2], row[m3]
            if v1 <= 1:
                v1, v2, v3 = v1 * 100, v2 * 100, v3 * 100
            drop = v1 - v3
            names.append(f"{center} ({v1:.0f}%→{v2:.0f}%→{v3:.0f}%, -{drop:.0f}%p)")

        message = (
            f"<b>{kpi_name}</b> 2개월 연속 하락 센터 "
            f"<b>{len(pivot[(pivot[m1] > pivot[m2]) & (pivot[m2] > pivot[m3])])}개</b><br>"
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
    """변동형 KPI 2개월 연속 상승 센터 (긍정 인사이트)"""
    insights = []
    if prev is None:
        return insights

    months = sorted(df.dropna(subset=['평가월'])['평가월'].unique())
    if len(months) < 3:
        return insights

    m1, m2, m3 = months[-3], months[-2], months[-1]

    rising_centers_all = []

    for kpi_name, cfg in KPI_TARGETS.items():
        if cfg['type'] != '변동' and kpi_name != '사용계약':
            continue

        rate_col = _find_col(df, [cfg['rate_col'], f"{kpi_name}_달성률"])
        if rate_col is None:
            continue

        df3 = df[df['평가월'].isin([m1, m2, m3])].copy()
        pivot = df3.pivot_table(index='센터명', columns='평가월', values=rate_col, aggfunc='mean')

        if m1 not in pivot.columns or m2 not in pivot.columns or m3 not in pivot.columns:
            continue

        rising = pivot[(pivot[m1] < pivot[m2]) & (pivot[m2] < pivot[m3])]
        for center in rising.index:
            v1, v3 = rising.loc[center, m1], rising.loc[center, m3]
            if v1 <= 1:
                v1, v3 = v1 * 100, v3 * 100
            rising_centers_all.append((center, kpi_name, cfg['icon'], v3 - v1))

    if not rising_centers_all:
        return insights

    # 상승폭 큰 순으로 Top 3
    rising_centers_all.sort(key=lambda x: -x[3])
    top3 = rising_centers_all[:3]

    items = [f"{icon} {center} <b>{kpi}</b> +{gain:.0f}%p" for center, kpi, icon, gain in top3]

    insights.append(Insight(
        icon="📈",
        title="상승 모멘텀",
        message=f"2개월 연속 상승 사례 발견<br>{'<br>'.join(items)}",
        category="success",
        priority=4,
    ))

    return insights


def insight_target_scenario(df: pd.DataFrame, latest) -> List[Insight]:
    """
    911점 도달 가능 센터 (현재 875~910점)
    어떤 KPI를 얼마나 올리면 911점이 되는지 시뮬레이션
    """
    insights = []
    if '총점' not in df.columns:
        return insights

    df_latest = df[df['평가월'] == latest].copy()
    month = pd.Timestamp(latest).month

    # 875~910점 센터 (조금만 더 끌어올리면 가능)
    df_near = df_latest[
        (df_latest['총점'] >= TARGET_TOTAL - 36) &
        (df_latest['총점'] < TARGET_TOTAL)
    ].sort_values('총점', ascending=False).head(3)

    if df_near.empty:
        return insights

    scenarios = []
    for _, row in df_near.iterrows():
        center = row['센터명']
        score = row['총점']
        gap = TARGET_TOTAL - score

        # 가장 임팩트 큰 KPI 찾기 (현재 점수와 만점의 차이가 큰 것)
        candidates = []
        for kpi_name, cfg in KPI_TARGETS.items():
            score_col = cfg['score_col']
            if score_col not in row.index:
                continue
            current = row.get(score_col, 0)
            if pd.isna(current):
                continue

            # 누적형 KPI는 반기 마감 기준 만점, 변동형은 즉시 만점 가능
            if cfg['type'] == '누적':
                # 반기 마감 시 도달 가능한 최대 점수
                max_possible = cfg['score']  # 911 기준 점수 (90% 등)
            else:
                max_possible = cfg['max']

            potential = max_possible - current
            if potential > 0:
                candidates.append((kpi_name, cfg['icon'], current, potential, cfg['type']))

        if not candidates:
            continue

        # 잠재 점수 큰 순
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
            priority=4,
            action="해당 센터에 우선 지원 집중 권장",
        ))

    return insights


def insight_danger_zone(df: pd.DataFrame, latest) -> Optional[Insight]:
    """
    위험 센터 (현재 점수가 매우 낮은 센터)
    + 진척도 정상 기준 대비 얼마나 부족한지
    """
    if '총점' not in df.columns:
        return None

    df_latest = df[df['평가월'] == latest].copy()
    month = pd.Timestamp(latest).month

    # 위험 기준: 911 - 60 = 851점 미만
    df_danger = df_latest[df_latest['총점'] < 851].sort_values('총점').head(5)

    if df_danger.empty:
        return None

    half_name, half_month, progress = _get_half_progress(month)
    expected_total = TARGET_TOTAL * progress / 100  # 5월 기준 911 × 83% = 759점

    items = []
    for _, row in df_danger.iterrows():
        center = row['센터명']
        score = row['총점']
        items.append(f"{center} <b>{score:.0f}점</b>")

    return Insight(
        icon="🚨",
        title=f"위험 센터 ({len(df_danger)}개)",
        message=f"851점 미만 센터<br>{', '.join(items)}",
        category="danger",
        priority=1,
        action=f"{half_name} 마감({6 if month <= 6 else 12}월)까지 911점 도달 위한 집중 관리 필요",
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

    # 1. 전체 평균
    ins = insight_overall_score(df, latest, prev)
    if ins:
        all_insights.append(ins)

    # 2. 위험 센터
    ins = insight_danger_zone(df, latest)
    if ins:
        all_insights.append(ins)

    # 3. 안전점검·중점고객 진척도 미달
    all_insights.extend(insight_safety_progress(df, latest))

    # 4. 변동형 KPI 연속 하락
    all_insights.extend(insight_volatile_kpi_drop(df, latest, prev))

    # 5. 911점 도달 가능 센터
    all_insights.extend(insight_target_scenario(df, latest))

    # 6. 상승 모멘텀
    all_insights.extend(insight_volatile_kpi_rising(df, latest, prev))

    # 7. 목표 달성 센터
    ins = insight_top_performers(df, latest)
    if ins:
        all_insights.append(ins)

    # 우선순위 정렬 후 상위 N개
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
