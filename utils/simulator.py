"""
시뮬레이션 로직 v1.0
- 변동형 KPI 조정 시 예상 총점 계산
- 누적형 KPI 잔여월 진척도 시뮬레이션
- 911점 달성 최소 조합 탐색
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

# ============================================================
# 배점 상수 (총 1000점)
# ============================================================
# 누적형 KPI (반기 누적, 하락 불가)
SCORE_SAFETY_INSPECTION = 550      # 안전점검실점검율
SCORE_KEY_CUSTOMER = 100           # 중점고객안전점검율
SCORE_CONTRACT_USAGE = 50          # 사용계약율

# 변동형 KPI (월별 변동, 총 300점)
SCORE_CONSULT_RESPONSE = 75        # 상담응대율
SCORE_CONSULT_CONTRIB = 75         # 상담기여도
SCORE_SATISFACTION = 75            # 고객서비스만족도
SCORE_COMPLAINT = 75               # 민원대응적정성

TARGET_TOTAL = 911                 # 반기 합격 기준

# KPI 컬럼명 매핑
CUMULATIVE_KPIS = {
    '안전점검실점검율': SCORE_SAFETY_INSPECTION,
    '중점고객안전점검율': SCORE_KEY_CUSTOMER,
    '사용계약율': SCORE_CONTRACT_USAGE,
}

VARIABLE_KPIS = {
    '상담응대율': SCORE_CONSULT_RESPONSE,
    '상담기여도': SCORE_CONSULT_CONTRIB,
    '고객서비스만족도': SCORE_SATISFACTION,
    '민원대응적정성': SCORE_COMPLAINT,
}


# ============================================================
# 데이터 클래스
# ============================================================
@dataclass
class SimulationResult:
    """시뮬레이션 결과"""
    current_score: float        # 현재 점수
    predicted_score: float      # 시뮬레이션 예상 점수
    delta: float                # 변화량
    target_gap: float           # 911 대비 (양수=초과달성, 음수=부족)
    achieved: bool              # 911 달성 여부
    breakdown: Dict[str, float] # KPI별 기여 점수


# ============================================================
# 헬퍼 함수
# ============================================================
def _to_pct(value) -> float:
    """% 값을 0~100 스케일로 정규화"""
    if value is None or pd.isna(value):
        return 0.0
    v = float(value)
    if 0 <= v <= 1.5:  # 0.85 같은 비율
        v = v * 100
    return max(0.0, min(100.0, v))


def get_center_latest(df: pd.DataFrame, center: str) -> Optional[pd.Series]:
    """센터의 최신월 데이터 조회"""
    if df is None or df.empty:
        return None
    df_c = df[df['센터명'] == center].dropna(subset=['평가월'])
    if df_c.empty:
        return None
    df_c = df_c.sort_values('평가월')
    return df_c.iloc[-1]


def get_current_kpi_values(df: pd.DataFrame, center: str) -> Dict[str, float]:
    """센터의 현재 KPI 값 조회 (%)"""
    row = get_center_latest(df, center)
    if row is None:
        return {}
    result = {}
    for col in list(CUMULATIVE_KPIS.keys()) + list(VARIABLE_KPIS.keys()):
        if col in row.index:
            result[col] = _to_pct(row[col])
        else:
            result[col] = 0.0
    return result


# ============================================================
# 점수 계산 (비례 추정 방식)
# ============================================================
def calculate_simulated_score(
    current_kpis: Dict[str, float],
    simulated_kpis: Dict[str, float],
    current_score: float,
    penalty: float = 0.0,
    bonus: float = 0.0,
) -> SimulationResult:
    """
    시뮬레이션 점수 계산 (비례 추정 방식)
    
    누적형 KPI: 잔여 진척도 × 배점 (현재 점수에 가산)
    변동형 KPI: (목표값 / 100) × 배점
    
    Parameters
    ----------
    current_kpis : Dict
        현재 KPI 값 (%) - {'안전점검실점검율': 82.5, ...}
    simulated_kpis : Dict
        시뮬레이션 KPI 값 (%) - 누적형은 "목표 도달치", 변동형은 "월 평균 목표값"
    current_score : float
        현재 총점
    penalty, bonus : float
        주의경고, 가점
    """
    breakdown = {}
    
    # 누적형 KPI 기여도 변화 계산
    # (목표값 - 현재값) / 100 × 배점 = 추가로 얻는 점수
    cumul_delta = 0.0
    for kpi, score_max in CUMULATIVE_KPIS.items():
        cur = current_kpis.get(kpi, 0.0)
        sim = simulated_kpis.get(kpi, cur)
        delta_pct = max(0.0, sim - cur)  # 누적형은 하락 불가
        added = (delta_pct / 100.0) * score_max
        cumul_delta += added
        breakdown[kpi] = added
    
    # 변동형 KPI는 "월 평균 목표값" 기준으로 재계산
    # 현재 변동형 기여도를 빼고, 시뮬값 기여도를 더함
    var_current_total = 0.0
    var_simulated_total = 0.0
    for kpi, score_max in VARIABLE_KPIS.items():
        cur = current_kpis.get(kpi, 0.0)
        sim = simulated_kpis.get(kpi, cur)
        cur_contrib = (cur / 100.0) * score_max
        sim_contrib = (sim / 100.0) * score_max
        var_current_total += cur_contrib
        var_simulated_total += sim_contrib
        breakdown[kpi] = sim_contrib - cur_contrib
    
    var_delta = var_simulated_total - var_current_total
    
    predicted = current_score + cumul_delta + var_delta
    delta = predicted - current_score
    target_gap = predicted - TARGET_TOTAL
    
    return SimulationResult(
        current_score=current_score,
        predicted_score=predicted,
        delta=delta,
        target_gap=target_gap,
        achieved=(predicted >= TARGET_TOTAL),
        breakdown=breakdown,
    )


# ============================================================
# 최소 조합 탐색
# ============================================================
def find_minimum_combo(
    current_kpis: Dict[str, float],
    current_score: float,
    target: float = TARGET_TOTAL,
) -> Optional[Dict[str, float]]:
    """
    911점 달성 최소 조합 탐색
    전략: 효율(점수/노력) 높은 순으로 KPI를 끌어올림
    - 노력 = 끌어올려야 할 %p
    - 효율 = 배점 / 100 (즉, 1%p당 얻는 점수)
    
    Returns
    -------
    Dict | None : 목표 KPI 값들, 달성 불가능 시 None
    """
    gap = target - current_score
    if gap <= 0:
        return current_kpis.copy()  # 이미 달성
    
    # 효율 = 배점 / 1%p (모든 KPI 1%p당 배점/100점)
    # 따라서 배점이 큰 KPI(=안전점검 550점)부터 끌어올리는 게 효율적
    kpi_list = []
    for kpi, score_max in CUMULATIVE_KPIS.items():
        cur = current_kpis.get(kpi, 0.0)
        headroom = 100.0 - cur  # 끌어올릴 수 있는 여유
        if headroom > 0.1:
            kpi_list.append((kpi, score_max, cur, headroom, 'cumul'))
    for kpi, score_max in VARIABLE_KPIS.items():
        cur = current_kpis.get(kpi, 0.0)
        headroom = 100.0 - cur
        if headroom > 0.1:
            kpi_list.append((kpi, score_max, cur, headroom, 'var'))
    
    # 배점 큰 순으로 정렬 (= 효율 높은 순)
    kpi_list.sort(key=lambda x: x[1], reverse=True)
    
    target_kpis = current_kpis.copy()
    remaining_gap = gap
    
    for kpi, score_max, cur, headroom, kind in kpi_list:
        if remaining_gap <= 0:
            break
        # 1%p당 얻는 점수
        score_per_pct = score_max / 100.0
        # 필요한 %p 증가량
        needed_pct = remaining_gap / score_per_pct
        # 실제 가능한 증가량
        actual_pct = min(needed_pct, headroom)
        target_kpis[kpi] = cur + actual_pct
        remaining_gap -= actual_pct * score_per_pct
    
    if remaining_gap > 0.5:
        return None  # 모든 KPI 100%로도 달성 불가
    
    return target_kpis
