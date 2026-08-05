"""
반기말 예측 기반 KPI 시뮬레이터

- 성과분석 / 홈 / 위험관리의 prediction.py 예측 기준과 동일
- 누적형 KPI: 현재 진행률을 반기말 기준으로 환산
- 변동형 KPI: 현재 수준을 반기말 예상값으로 사용
- 민원대응·주의경고·가점: 조정항목으로 고정
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


TARGET_TOTAL = 911
PERFECT_TOTAL = 1000

# score_calculator.py 배점 기준
CUMULATIVE_KPIS = {
    "안전점검실점검율": 550,
    "중점고객안전점검율": 100,
    "사용계약율": 50,
}

VARIABLE_KPIS = {
    "상담응대율": 100,
    "상담기여도": 100,
    "고객서비스만족도": 100,
}


@dataclass
class SimulationResult:
    current_score: float
    predicted_score: float
    delta: float
    target_gap: float
    achieved: bool
    breakdown: Dict[str, float]


def _to_pct(value) -> float:
    """0~1 또는 0~100 값을 0~100으로 통일"""
    if value is None or pd.isna(value):
        return 0.0

    value = float(value)

    if 0 <= value <= 1.5:
        value *= 100

    return max(0.0, min(100.0, value))


def _contract_score(rate_pct: float) -> float:
    """사용계약율 등급제 점수"""
    if rate_pct >= 90:
        return 50.0
    if rate_pct >= 80:
        return 45.0
    if rate_pct >= 70:
        return 40.0
    return 35.0


def _predicted_contract_score(rate_pct: float) -> float:
    """사용계약율 반기말 예측 점수"""
    return min(_contract_score(rate_pct) * 1.1, 50.0)


def get_center_latest(df: pd.DataFrame, center: str) -> Optional[pd.Series]:
    """특정 센터의 최신월 행 반환"""
    if df is None or df.empty:
        return None

    result = df[df["센터명"] == center].copy()

    if result.empty:
        return None

    result["_month_dt"] = pd.to_datetime(result["평가월"], errors="coerce")
    result = result.dropna(subset=["_month_dt"]).sort_values("_month_dt")

    return None if result.empty else result.iloc[-1]


def get_current_kpi_values(df: pd.DataFrame, center: str) -> Dict[str, float]:
    """센터 최신 KPI 실측값을 % 기준으로 반환"""
    row = get_center_latest(df, center)

    if row is None:
        return {}

    result = {}

    for kpi in list(CUMULATIVE_KPIS) + list(VARIABLE_KPIS):
        result[kpi] = _to_pct(row.get(kpi, 0))

    return result


def get_simulation_defaults(
    current_kpis: Dict[str, float],
    period_month: int,
) -> Dict[str, float]:
    """
    현재 페이스 기준 반기말 예상 KPI를 슬라이더 기본값으로 반환.

    예:
    - 하반기 1개월차 안전점검 15% → 반기말 전망 90%
    - 하반기 2개월차 안전점검 30% → 반기말 전망 90%
    """
    progress_rate = min(max(period_month / 6, 0.01), 1.0)

    result = {}

    # 누적형 KPI: 반기 진행률로 반기말 수준 환산
    for kpi in ["안전점검실점검율", "중점고객안전점검율"]:
        current = current_kpis.get(kpi, 0.0)
        result[kpi] = min(current / progress_rate, 100.0)

    # 사용계약율: 현재 수준 기반
    result["사용계약율"] = current_kpis.get("사용계약율", 0.0)

    # 변동형 KPI: 현재 월 수준 유지
    for kpi in VARIABLE_KPIS:
        result[kpi] = current_kpis.get(kpi, 0.0)

    return result


def _calculate_components(kpis: Dict[str, float]) -> Dict[str, float]:
    """반기말 KPI 목표값을 점수 구성요소로 변환"""
    return {
        "안전점검실점검율": min(
            kpis.get("안전점검실점검율", 0.0) / 100 * 550,
            550,
        ),
        "중점고객안전점검율": min(
            kpis.get("중점고객안전점검율", 0.0) / 100 * 100,
            100,
        ),
        "사용계약율": _predicted_contract_score(
            kpis.get("사용계약율", 0.0)
        ),
        "상담응대율": min(
            kpis.get("상담응대율", 0.0) / 100 * 100,
            100,
        ),
        "상담기여도": min(
            kpis.get("상담기여도", 0.0) / 100 * 100,
            100,
        ),
        "고객서비스만족도": min(
            kpis.get("고객서비스만족도", 0.0) / 100 * 100,
            100,
        ),
    }


def calculate_simulated_score(
    baseline_kpis: Dict[str, float],
    simulated_kpis: Dict[str, float],
    adjustment: float = 0.0,
) -> SimulationResult:
    """
    반기말 예측 기준 점수 시뮬레이션.

    baseline_kpis: 현재 페이스 기준 반기말 예상 KPI
    simulated_kpis: 사용자가 조정한 반기말 목표 KPI
    """
    baseline_components = _calculate_components(baseline_kpis)
    simulated_components = _calculate_components(simulated_kpis)

    baseline_score = min(
        sum(baseline_components.values()) + adjustment,
        PERFECT_TOTAL,
    )

    predicted_score = min(
        sum(simulated_components.values()) + adjustment,
        PERFECT_TOTAL,
    )

    breakdown = {
        kpi: simulated_components[kpi] - baseline_components[kpi]
        for kpi in simulated_components
    }

    return SimulationResult(
        current_score=baseline_score,
        predicted_score=predicted_score,
        delta=predicted_score - baseline_score,
        target_gap=predicted_score - TARGET_TOTAL,
        achieved=predicted_score >= TARGET_TOTAL,
        breakdown=breakdown,
    )


def find_minimum_combo(
    baseline_kpis: Dict[str, float],
    adjustment: float = 0.0,
    target: float = TARGET_TOTAL,
) -> Optional[Dict[str, float]]:
    """
    목표점수 도달을 위한 KPI 최소 개선 조합.

    점수 기여도가 큰 KPI부터 0.5%p 단위로 개선합니다.
    """
    current = baseline_kpis.copy()

    initial = calculate_simulated_score(
        baseline_kpis=baseline_kpis,
        simulated_kpis=current,
        adjustment=adjustment,
    )

    if initial.predicted_score >= target:
        return current

    all_kpis = list(CUMULATIVE_KPIS) + list(VARIABLE_KPIS)

    for _ in range(1200):
        current_result = calculate_simulated_score(
            baseline_kpis=baseline_kpis,
            simulated_kpis=current,
            adjustment=adjustment,
        )

        if current_result.predicted_score >= target:
            return current

        best_kpi = None
        best_gain = 0.0

        for kpi in all_kpis:
            if current.get(kpi, 0.0) >= 100:
                continue

            candidate = current.copy()
            candidate[kpi] = min(candidate[kpi] + 0.5, 100.0)

            candidate_result = calculate_simulated_score(
                baseline_kpis=baseline_kpis,
                simulated_kpis=candidate,
                adjustment=adjustment,
            )

            gain = (
                candidate_result.predicted_score
                - current_result.predicted_score
            )

            if gain > best_gain:
                best_gain = gain
                best_kpi = kpi

        if best_kpi is None or best_gain <= 0:
            break

        current[best_kpi] = min(current[best_kpi] + 0.5, 100.0)

    final_result = calculate_simulated_score(
        baseline_kpis=baseline_kpis,
        simulated_kpis=current,
        adjustment=adjustment,
    )

    return current if final_result.predicted_score >= target else None


def get_improvement_actions(
    baseline_kpis: Dict[str, float],
    adjustment: float = 0.0,
    target: float = TARGET_TOTAL,
    top_n: int = 3,
) -> list[Dict[str, float]]:
    """
    목표점수 도달을 위한 우선 개선 KPI 목록 반환.

    반환 항목:
    - KPI
    - 현재전망
    - 목표값
    - 필요상승
    - 예상기여점수
    """
    baseline_result = calculate_simulated_score(
        baseline_kpis=baseline_kpis,
        simulated_kpis=baseline_kpis,
        adjustment=adjustment,
    )

    if baseline_result.predicted_score >= target:
        return []

    min_combo = find_minimum_combo(
        baseline_kpis=baseline_kpis,
        adjustment=adjustment,
        target=target,
    )

    if min_combo is None:
        return []

    actions = []

    for kpi in list(CUMULATIVE_KPIS) + list(VARIABLE_KPIS):
        current = baseline_kpis.get(kpi, 0.0)
        goal = min_combo.get(kpi, current)
        increase = goal - current

        if increase <= 0.05:
            continue

        candidate_kpis = baseline_kpis.copy()
        candidate_kpis[kpi] = goal

        candidate_result = calculate_simulated_score(
            baseline_kpis=baseline_kpis,
            simulated_kpis=candidate_kpis,
            adjustment=adjustment,
        )

        contribution = (
            candidate_result.predicted_score
            - baseline_result.predicted_score
        )

        actions.append({
            "KPI": kpi,
            "현재전망": round(current, 1),
            "목표값": round(goal, 1),
            "필요상승": round(increase, 1),
            "예상기여점수": round(contribution, 1),
        })


    return sorted(
        actions,
        key=lambda item: item["예상기여점수"],
        reverse=True,
    )[:top_n]
