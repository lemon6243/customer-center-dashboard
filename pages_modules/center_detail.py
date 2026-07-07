"""
센터별 상세 페이지
- 센터 선택
- 핵심 지표 카드
- 항목별 레이더 차트
- 911점 달성 시뮬레이션 (KPI별 what-if 분석)
"""

import streamlit as st
import pandas as pd
from utils.styles import ScoreThresholds, Colors
from utils.helpers import safe_unique_centers, get_period_info
from utils.prediction import calculate_predicted_score
from components.score_chart import create_kpi_radar_chart
from utils.simulator import (
    get_current_kpi_values,
    calculate_simulated_score,
    find_minimum_combo,
    CUMULATIVE_KPIS,
    VARIABLE_KPIS,
    TARGET_TOTAL,
)


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """센터별 상세 페이지 메인 함수"""

    try:
        all_centers = safe_unique_centers(df)

        if not all_centers:
            st.warning("⚠️ 분석 가능한 센터 데이터가 없습니다.")
            return

        # 센터 선택
        if device_type == 'mobile':
            center_name = st.selectbox("센터 선택", options=all_centers)
        else:
            col1, _ = st.columns([2, 1])
            with col1:
                center_name = st.selectbox("센터 선택", options=all_centers)

        # 해당 센터 데이터 필터링
        df_center = df[df['센터명'] == center_name].sort_values('평가월')

        if df_center.empty:
            st.warning("⚠️ 선택한 센터의 데이터가 없습니다.")
            return

        latest = df_center.iloc[-1]
        period_info = get_period_info(latest['평가월'])
        period_month = period_info['period_month']

        # 예측 점수
        prediction = calculate_predicted_score(latest, period_month)
        predicted_score = prediction['예측총점']

        # ====== 핵심 지표 카드 ======
        _show_center_metrics(
            latest, predicted_score, period_info,
            df, all_centers, device_type
        )

        st.divider()

        # ====== 레이더 차트 ======
        st.subheader("📊 항목별 점수 (레이더 차트)")

        scores = {
            '안전점검': latest.get('안전점검_점수', 0),
            '중점고객': latest.get('중점고객_점수', 0),
            '사용계약': latest.get('사용계약_점수', 0),
            '상담응대': latest.get('상담응대_점수', 0),
            '상담기여': latest.get('상담기여_점수', 0),
            '만족도': latest.get('만족도_점수', 0),
        }

        fig = create_kpi_radar_chart(scores, center_name=center_name)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        # ====== 시뮬레이션 섹션 ======
        _render_simulation_section(df, center_name, latest, period_month, device_type)

    except Exception as e:
        st.error(f"❌ 센터별 상세 분석 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


def _show_center_metrics(latest, predicted_score, period_info,
                          df, all_centers, device_type):
    """센터의 핵심 4개 지표 표시"""

    col_count = 2 if device_type == 'mobile' else 4
    cols = st.columns(col_count)

    target = ScoreThresholds.TARGET
    period_month = period_info['period_month']
    is_half_end = period_month in (6, 12)

    # 1) 현재 총점 (반기 마감 시엔 '최종 점수')
    with cols[0]:
        st.metric(
            label="반기 최종 점수" if is_half_end else "현재 총점",
            value=f"{latest['총점']:.1f}점",
            delta=f"{latest['총점'] - target:.1f}점 vs 911"
        )

    # 2) 예측 또는 목표 달성 여부
    with cols[1]:
        if not is_half_end:
            st.metric(
                label="반기 예측",
                value=f"{predicted_score:.1f}점",
                delta=f"{predicted_score - target:.1f}점",
                help="진행률 기반 예측 (반기 마감 시 사라짐)"
            )
        else:
            achieved = latest['총점'] >= target
            st.metric(
                label="911점 달성",
                value="달성" if achieved else "미달",
                delta="✅" if achieved else "❌"
            )

    if col_count >= 3:
        # 3) 전체 순위
        with cols[2]:
            latest_month_df = df[df['평가월'] == df['평가월'].max()]
            rank = int((latest_month_df['총점'] >= latest['총점']).sum())
            st.metric(
                label="전체 순위",
                value=f"{rank}위",
                delta=f"/ {len(all_centers)}개"
            )

        # 4) 진행 상황
        with cols[3]:
            st.metric(
                label="진행 상황",
                value=period_info['period_text'],
                delta=f"{period_info['progress_rate']*100:.1f}%"
            )


# ============================================================
# 시뮬레이션 섹션
# ============================================================

def _render_simulation_section(
    df: pd.DataFrame,
    center_name: str,
    latest: pd.Series,
    period_month: int,
    device_type: str = 'desktop',
):
    """
    911점 달성 시뮬레이션 섹션
    - 현재 KPI 값 표시
    - KPI 조정 슬라이더 (변동형은 목표값, 누적형은 반기 최종 도달치)
    - 시뮬레이션 결과 및 최소 조합 제안
    """
    is_half_end = period_month in (6, 12)

    if is_half_end:
        st.subheader("🎯 반기 결과 (확정)")
        current_score = float(latest['총점'])
        if current_score >= TARGET_TOTAL:
            st.success(
                f"✅ **{center_name}** 센터는 이번 반기 **{current_score:.1f}점**으로 "
                f"911점을 달성했습니다. 시뮬레이션은 다음 반기(다음 달) 시작 후 활성화됩니다."
            )
        else:
            gap = TARGET_TOTAL - current_score
            annual_needed = 2 * TARGET_TOTAL - current_score
            st.warning(
                f"⚠️ **{center_name}** 센터는 이번 반기 **{current_score:.1f}점**으로 "
                f"911점에 **{gap:.1f}점** 미달했습니다.\n\n"
                f"연간 pass(평균 911점) 위해 다음 반기에 **{annual_needed:.0f}점** 필요합니다. "
                f"시뮬레이션은 다음 반기 시작 후 활성화됩니다."
            )
        return

    st.subheader("🎯 911점 달성 시뮬레이션")
    st.caption(
        "KPI 값을 조정해서 예상 총점을 확인해보세요. "
        "누적형은 '반기 최종 도달치', 변동형은 '월 평균 목표값' 기준입니다."
    )

    # 현재 KPI 값
    current_kpis = get_current_kpi_values(df, center_name)
    if not current_kpis:
        st.info("KPI 데이터를 조회할 수 없습니다.")
        return

    current_score = float(latest['총점'])

    # ===== 상단: 현재 상태 요약 =====
    gap = TARGET_TOTAL - current_score
    if gap <= 0:
        st.success(
            f"✅ 현재 **{current_score:.1f}점**으로 이미 911점을 달성했습니다! "
            f"아래에서 추가 상승 시나리오를 시뮬레이션할 수 있습니다."
        )
    else:
        st.info(
            f"📌 현재 **{current_score:.1f}점** → 911점까지 **{gap:.1f}점** 필요"
        )

    # ===== 최소 조합 제안 =====
    with st.expander("💡 911점 달성 최소 조합 제안 보기", expanded=False):
        min_combo = find_minimum_combo(current_kpis, current_score, TARGET_TOTAL)
        if min_combo is None:
            st.error("❌ 모든 KPI를 100%로 올려도 911점 달성이 불가능합니다.")
        elif gap <= 0:
            st.success("현재 이미 911점을 달성했습니다. 조정 불필요.")
        else:
            st.caption("배점이 큰 KPI부터 효율적으로 끌어올리는 최소 조합입니다.")
            rows = []
            for kpi in list(CUMULATIVE_KPIS.keys()) + list(VARIABLE_KPIS.keys()):
                cur = current_kpis.get(kpi, 0.0)
                tgt = min_combo.get(kpi, cur)
                diff = tgt - cur
                if abs(diff) > 0.05:
                    rows.append({
                        'KPI': kpi,
                        '현재값(%)': round(cur, 1),
                        '목표값(%)': round(tgt, 1),
                        '필요 상승(%p)': round(diff, 1),
                    })
            if rows:
                st.dataframe(
                    pd.DataFrame(rows),
                    hide_index=True,
                    use_container_width=True,
                )
            else:
                st.info("조정이 필요하지 않습니다.")

    st.markdown("")

    # ===== KPI 조정 슬라이더 =====
    st.markdown("##### 🎚️ KPI 값 조정")

    n_cols = 1 if device_type == 'mobile' else 2
    simulated_kpis = {}

    # 누적형 KPI
    st.markdown(f"**📈 누적형 KPI** (반기 최종 도달치 기준)")
    cumul_cols = st.columns(n_cols)
    for idx, (kpi, score_max) in enumerate(CUMULATIVE_KPIS.items()):
        cur = current_kpis.get(kpi, 0.0)
        with cumul_cols[idx % n_cols]:
            simulated_kpis[kpi] = st.slider(
                f"{kpi} (배점 {score_max}점)",
                min_value=0.0,
                max_value=100.0,
                value=float(cur),
                step=0.5,
                key=f"sim_cumul_{center_name}_{kpi}",
                help=f"현재 {cur:.1f}% / 반기 최종 목표 90% 이상 권장",
            )

    st.markdown("")
    st.markdown(f"**⚡ 변동형 KPI** (월 평균 목표값 기준)")
    var_cols = st.columns(n_cols)
    for idx, (kpi, score_max) in enumerate(VARIABLE_KPIS.items()):
        cur = current_kpis.get(kpi, 0.0)
        with var_cols[idx % n_cols]:
            simulated_kpis[kpi] = st.slider(
                f"{kpi} (배점 {score_max}점)",
                min_value=0.0,
                max_value=100.0,
                value=float(cur),
                step=0.5,
                key=f"sim_var_{center_name}_{kpi}",
                help=f"현재 {cur:.1f}%",
            )

    st.markdown("")

    # ===== 시뮬레이션 계산 =====
    penalty = float(latest.get('주의경고', 0) or 0)
    bonus = float(latest.get('가점', 0) or 0)

    result = calculate_simulated_score(
        current_kpis=current_kpis,
        simulated_kpis=simulated_kpis,
        current_score=current_score,
        penalty=penalty,
        bonus=bonus,
    )

    # ===== 결과 카드 =====
    st.markdown("##### 📊 시뮬레이션 결과")

    r_cols = st.columns(3)
    with r_cols[0]:
        st.metric(
            label="시뮬레이션 예상 점수",
            value=f"{result.predicted_score:.1f}점",
            delta=f"{result.delta:+.1f}점 vs 현재",
        )
    with r_cols[1]:
        st.metric(
            label="911점 대비",
            value=f"{result.target_gap:+.1f}점",
            delta="달성 ✅" if result.achieved else "미달 ❌",
            delta_color="normal" if result.achieved else "inverse",
        )
    with r_cols[2]:
        change_count = sum(
            1 for kpi in simulated_kpis
            if abs(simulated_kpis[kpi] - current_kpis.get(kpi, 0.0)) > 0.05
        )
        st.metric(
            label="조정된 KPI 개수",
            value=f"{change_count}개",
            delta=f"/ {len(simulated_kpis)}개",
            delta_color="off",
        )

    # ===== 기여도 세부 =====
    if any(abs(v) > 0.05 for v in result.breakdown.values()):
        with st.expander("📋 KPI별 점수 기여 변화 보기", expanded=False):
            rows = []
            for kpi in list(CUMULATIVE_KPIS.keys()) + list(VARIABLE_KPIS.keys()):
                cur = current_kpis.get(kpi, 0.0)
                sim = simulated_kpis.get(kpi, cur)
                contrib = result.breakdown.get(kpi, 0.0)
                if abs(sim - cur) > 0.05 or abs(contrib) > 0.05:
                    rows.append({
                        'KPI': kpi,
                        '현재값(%)': round(cur, 1),
                        '시뮬값(%)': round(sim, 1),
                        '변화(%p)': round(sim - cur, 1),
                        '점수 기여 변화': round(contrib, 1),
                    })
            if rows:
                st.dataframe(
                    pd.DataFrame(rows),
                    hide_index=True,
                    use_container_width=True,
                )

    # ===== 안내 문구 =====
    if result.achieved:
        st.success(
            f"🎉 시뮬레이션한 KPI 값을 달성하면 **{result.predicted_score:.1f}점**으로 "
            f"911점 목표를 달성합니다."
        )
    else:
        st.warning(
            f"⚠️ 이 조합으로는 **{-result.target_gap:.1f}점** 부족합니다. "
            f"위 '최소 조합 제안'을 참고하거나 배점이 큰 KPI(안전점검·중점고객·상담응대·기여·만족도)를 "
            f"추가로 조정해보세요."
        )
