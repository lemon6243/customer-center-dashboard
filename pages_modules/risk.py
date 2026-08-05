"""
위험 관리 페이지
- 진행 중: 반기말 예측점수 기준 안전/주의/위험 분류
- 반기 마감: 실제 총점 기준 달성/근접미달/미달 분류
"""

import streamlit as st
import pandas as pd

from utils.styles import ScoreThresholds
from utils.half_year import (
    get_latest_month,
    filter_by_month,
    get_period_info,
)
from utils.prediction import add_predictions_to_df
from components.kpi_card import risk_card
from utils.simulator import (
    get_current_kpi_values,
    get_simulation_defaults,
    get_improvement_actions,
)



TARGET_SCORE = 911
CAUTION_SCORE = 895


def show(df: pd.DataFrame, device_type: str = "desktop"):
    """위험 관리 페이지 메인 함수"""
    try:
        latest_month = get_latest_month(df)

        if latest_month is None:
            st.warning("⚠️ 최신 평가월 데이터를 찾을 수 없습니다.")
            return

        df_latest = filter_by_month(df, latest_month)

        if df_latest.empty:
            st.warning("⚠️ 최신 월 데이터가 없습니다.")
            return

        period_info = get_period_info(latest_month)
        is_final_month = period_info["is_half_end"]
        half_label = period_info["half"]
        period_month = period_info["period_month"]

        # 진행월: 성과분석·홈과 동일한 예측점수 계산
        # 마감월: 예측점수는 실제 총점과 동일
        with st.spinner("🔮 반기 마감 전망 분석 중..."):
            df_latest = add_predictions_to_df(df_latest, period_month)

        if is_final_month:
            _render_final_result(df_latest, half_label, device_type)
        else:
            _render_pace_risk(df_latest, period_info, device_type)

    except Exception as e:
        st.error(f"❌ 위험 관리 분석 오류: {e}")

        with st.expander("🔍 상세 오류 정보"):
            import traceback
            st.code(traceback.format_exc())


def _render_pace_risk(
    df_latest: pd.DataFrame,
    period_info: dict,
    device_type: str,
):
    """진행 중 반기: 예측 반기말 점수 기준 위험 관리"""
    safe_df = df_latest[df_latest["예측점수"] >= TARGET_SCORE].copy()

    caution_df = df_latest[
        (df_latest["예측점수"] >= CAUTION_SCORE)
        & (df_latest["예측점수"] < TARGET_SCORE)
    ].copy()

    risk_df = df_latest[df_latest["예측점수"] < CAUTION_SCORE].copy()

    safe_df = safe_df.sort_values("예측점수", ascending=False)
    caution_df = caution_df.sort_values("예측점수")
    risk_df = risk_df.sort_values("예측점수")

    total = len(df_latest)

    st.markdown(
        f"### 📅 {period_info['period_text']} 반기 마감 전망"
    )
    st.caption(
        "※ 현재 누적점수가 아닌 반기말 예측점수로 판정합니다. "
        "예측 기준은 성과분석·홈 화면과 동일합니다."
    )

    cols = st.columns(3 if device_type != "mobile" else 1)

    summary = [
        ("✅ 안전", "911점 이상 예상", len(safe_df), "normal"),
        ("⚠️ 주의", "895~910점 예상", len(caution_df), "off"),
        ("🚨 위험", "895점 미만 예상", len(risk_df), "inverse"),
    ]

    for idx, (label, help_text, count, delta_color) in enumerate(summary):
        with cols[idx % len(cols)]:
            st.metric(
                label=label,
                value=f"{count}개 / {total}개",
                delta=help_text,
                delta_color=delta_color,
            )

    st.divider()

    # 위험 센터
    if not risk_df.empty:
        st.subheader(f"🚨 반기 마감 위험 센터 ({len(risk_df)}개)")
        st.caption("예측 반기말 점수가 895점 미만인 센터입니다.")

        for _, row in risk_df.iterrows():
            risk_card(
                center_name=row["센터명"],
                current_score=row["총점"],
                predicted_score=row["예측점수"],
                target=TARGET_SCORE,
            )
            _render_improvement_actions(
                df=df,
                center_name=row["센터명"],
                latest_row=row,
                period_month=period_info["period_month"],
            )

    else:
        st.success("🎉 예측 기준 895점 미만 위험 센터가 없습니다.")

    # 주의 센터
    if not caution_df.empty:
        st.divider()
        st.subheader(f"⚠️ 목표 근접 주의 센터 ({len(caution_df)}개)")
        st.caption("911점까지 소폭 보완이 필요한 센터입니다.")

        display_df = caution_df[
            ["센터명", "총점", "예측점수"]
        ].copy()

        display_df["목표차이"] = (
            display_df["예측점수"] - TARGET_SCORE
        )

        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "총점": st.column_config.NumberColumn(
                    "현재 누적점수",
                    format="%.1f점",
                ),
                "예측점수": st.column_config.NumberColumn(
                    "반기말 예상점수",
                    format="%.1f점",
                ),
                "목표차이": st.column_config.NumberColumn(
                    "911점 대비",
                    format="%+.1f점",
                ),
            },
        )

    # 안전 센터는 접어서 제공
    with st.expander(f"✅ 안전 페이스 센터 {len(safe_df)}개 보기", expanded=False):
        if safe_df.empty:
            st.info("안전 페이스 센터가 없습니다.")
        else:
            display_df = safe_df[
                ["센터명", "총점", "예측점수"]
            ].copy()

            display_df["목표여유"] = (
                display_df["예측점수"] - TARGET_SCORE
            )

            st.dataframe(
                display_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "총점": st.column_config.NumberColumn(
                        "현재 누적점수",
                        format="%.1f점",
                    ),
                    "예측점수": st.column_config.NumberColumn(
                        "반기말 예상점수",
                        format="%.1f점",
                    ),
                    "목표여유": st.column_config.NumberColumn(
                        "911점 대비",
                        format="%+.1f점",
                    ),
                },
            )


def _render_final_result(
    df_latest: pd.DataFrame,
    half_label: str,
    device_type: str,
):
    """6월·12월: 실제 최종점수 기준 결과"""
    achieved_df = df_latest[df_latest["총점"] >= TARGET_SCORE].copy()

    near_df = df_latest[
        (df_latest["총점"] >= CAUTION_SCORE)
        & (df_latest["총점"] < TARGET_SCORE)
    ].copy()

    fail_df = df_latest[df_latest["총점"] < CAUTION_SCORE].copy()

    achieved_df = achieved_df.sort_values("총점", ascending=False)
    near_df = near_df.sort_values("총점")
    fail_df = fail_df.sort_values("총점")

    total = len(df_latest)

    st.markdown(f"### 🏁 {half_label} 최종 위험 관리")
    st.caption("※ 반기 마감월이므로 예측이 아닌 실제 최종점수로 판정합니다.")

    cols = st.columns(3 if device_type != "mobile" else 1)

    summary = [
        ("✅ 달성", "911점 이상", len(achieved_df), "normal"),
        ("⚠️ 근접 미달", "895~910점", len(near_df), "off"),
        ("🚨 미달", "895점 미만", len(fail_df), "inverse"),
    ]

    for idx, (label, help_text, count, delta_color) in enumerate(summary):
        with cols[idx % len(cols)]:
            st.metric(
                label=label,
                value=f"{count}개 / {total}개",
                delta=help_text,
                delta_color=delta_color,
            )

    if fail_df.empty and near_df.empty:
        st.success("🎉 모든 센터가 반기 목표 911점을 달성했습니다.")
        return

    if not fail_df.empty:
        st.divider()
        st.subheader(f"🚨 {half_label} 미달 센터 ({len(fail_df)}개)")

        for _, row in fail_df.iterrows():
            risk_card(
                center_name=row["센터명"],
                current_score=row["총점"],
                predicted_score=row["총점"],
                target=TARGET_SCORE,
            )

    if not near_df.empty:
        st.divider()
        st.subheader(f"⚠️ {half_label} 근접 미달 센터 ({len(near_df)}개)")

        display_df = near_df[["센터명", "총점"]].copy()
        display_df["목표차이"] = display_df["총점"] - TARGET_SCORE

        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "총점": st.column_config.NumberColumn(
                    "최종점수",
                    format="%.1f점",
                ),
                "목표차이": st.column_config.NumberColumn(
                    "911점 대비",
                    format="%+.1f점",
                ),
            },
        )
def _render_improvement_actions(
    df: pd.DataFrame,
    center_name: str,
    latest_row: pd.Series,
    period_month: int,
):
    """위험센터의 KPI 개선 우선순위 표시"""

    current_kpis = get_current_kpi_values(df, center_name)

    if not current_kpis:
        return

    baseline_kpis = get_simulation_defaults(
        current_kpis,
        period_month,
    )

    adjustment = (
        float(latest_row.get("민원대응적정성", 0) or 0)
        + float(latest_row.get("주의경고", 0) or 0)
        + float(latest_row.get("가점", 0) or 0)
    )

    actions = get_improvement_actions(
        baseline_kpis=baseline_kpis,
        adjustment=adjustment,
        top_n=3,
    )

    if not actions:
        return

    with st.expander("🎯 911점 도달을 위한 우선 개선 항목", expanded=False):
        rows = []

        for idx, action in enumerate(actions, 1):
            rows.append({
                "우선순위": idx,
                "KPI": action["KPI"],
                "현재 페이스 전망": f'{action["현재전망"]:.1f}%',
                "권장 목표": f'{action["목표값"]:.1f}%',
                "필요 개선": f'+{action["필요상승"]:.1f}%p',
                "예상 점수 효과": f'+{action["예상기여점수"]:.1f}점',
            })

        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            "※ 현재 페이스 기준 반기말 전망에서 911점 도달에 필요한 "
            "최소 개선 조합을 제시합니다."
        )
