"""
🏠 홈 (Executive Dashboard)
- v2.6: 반기별 독립평가가 아닌 '연간 평균 911점' pass 체계 반영
- 반기 마감 시: 달성 센터 축하, 미달 센터엔 하반기 필요치 표시
- Bottom 랭킹: 등수 하위가 아닌 '911점 미달 센터만' 표시
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

from utils.styles import Colors, ScoreThresholds, get_score_color, PLOTLY_LAYOUT
from utils.helpers import safe_unique_centers
from utils.insights_v2 import (
    get_all_insights,
    get_ranking_data,
    get_change_ranking,
    get_half_outlook,
    get_pace_lag_ranking,
    TARGET_TOTAL,
    ANNUAL_PASS_TOTAL,
)
from components.big_metric_card import score_big_card, count_big_card, big_metric_card
from components.ranking_list import ranking_list, change_ranking_list
from components.quick_nav import quick_nav_buttons
from utils.half_year import (
    get_latest_month as _safe_latest_month,
    is_half_start as _is_half_start,
    is_half_end as _is_half_end,
    get_half as _get_half,
    to_month_int as _to_month_int,
    filter_by_month,
    get_comparison_data,
    month_label,
)



QUICK_NAV_ITEMS = [
    {"icon": "📊", "label": "성과 분석",  "page_key": "📊 성과 분석",  "desc": "전체 현황 + 추이"},
    {"icon": "🎯", "label": "센터 진단",  "page_key": "🎯 센터 진단",  "desc": "센터별 상세 진단"},
    {"icon": "⚠️", "label": "위험 관리",  "page_key": "⚠️ 위험 관리",  "desc": "주의/위험 센터"},
    {"icon": "🌡️", "label": "KPI 히트맵", "page_key": "🌡️ KPI 히트맵", "desc": "센터×KPI 매트릭스"},
    {"icon": "🔬", "label": "심화 분석",  "page_key": "🔬 심화 분석",  "desc": "분석 + 원본"},
]



def show(df: pd.DataFrame, device_type: str = "desktop"):
    if df is None or df.empty:
        st.warning("⚠️ 표시할 데이터가 없습니다. 사이드바에서 데이터를 확인해주세요.")
        return

    df_last_year = st.session_state.get("df_last_year", None)

    # 최신월·비교월을 공통 반기 정책으로 계산
    latest_month_dt = _safe_latest_month(df)
    
    if latest_month_dt is None:
        st.warning("⚠️ 최신 월 데이터를 추출할 수 없습니다.")
        return
    
    df_latest = filter_by_month(df, latest_month_dt)
    
    if df_latest.empty:
        st.warning("⚠️ 최신 월 데이터를 추출할 수 없습니다.")
        return
    
    df_prev, compare_label, compare_month_dt = get_comparison_data(
        df=df,
        latest_month=latest_month_dt,
        df_last_year=df_last_year,
    )
    
    latest_month = month_label(latest_month_dt)
    prev_month = month_label(compare_month_dt)
    
    is_half_start_month = _is_half_start(latest_month_dt)
    is_final_month = _is_half_end(latest_month_dt)
    half_label = _get_half(latest_month_dt)


    _render_period_header(df, latest_month, is_final_month, half_label)

    if is_half_start_month and df_prev is not None and not df_prev.empty:
        st.caption(
            "※ 전년 동월 총점 비교는 평가항목·배점 체계 변경 가능성으로 참고용입니다. "
            "반기말 전망과 KPI별 지표를 함께 확인하세요."
    )



     # ==================== 1. 핵심 KPI 카드 ====================
    st.markdown("### 📊 핵심 지표")

    n_cols = 2 if device_type == "mobile" else 4
    cols = st.columns(n_cols)

    avg_score = df_latest["총점"].mean() if "총점" in df_latest.columns else 0
    prev_avg = df_prev["총점"].mean() if df_prev is not None and not df_prev.empty else None

    if prev_avg is not None and pd.notna(prev_avg):
        diff = avg_score - prev_avg
        compare_word = compare_label or ("전년 동월" if is_half_start_month else "전월")
        delta_avg = f"{'+' if diff >= 0 else ''}{diff:,.1f} vs {compare_word}"
    else:
        delta_avg = None

    # 진행 중에는 전체 평균도 전망 점수로 안전도를 판정
    outlook = get_half_outlook(df, df_last_year=df_last_year)
    avg_forecast = outlook["현실전망"].mean() if (not is_final_month and not outlook.empty) else None

    if is_final_month:
        pace_color = Colors.SUCCESS if avg_score >= TARGET_TOTAL else (
            Colors.WARNING if avg_score >= 895 else Colors.DANGER
        )
        score_label = f"{half_label} 최종 평균"
        score_status = "반기 최종 확정"
        show_target = True
    else:
        pace_color = Colors.SUCCESS if avg_forecast is not None and avg_forecast >= TARGET_TOTAL else (
            Colors.WARNING if avg_forecast is not None and avg_forecast >= 895 else Colors.DANGER
        )
        elapsed = latest_month_dt.month if latest_month_dt.month <= 6 else latest_month_dt.month - 6
        score_label = f"{half_label} {elapsed}개월차 평균"
        score_status = (
            f"반기 전망 {avg_forecast:.1f}점 · "
            f"{'안전 페이스' if avg_forecast >= TARGET_TOTAL else ('주의 페이스' if avg_forecast >= 895 else '위험 페이스')}"
            if avg_forecast is not None else "반기 전망 산출 중"
        )
        # 진행 중 532점/911점 같은 오해를 막기 위해 현재점수의 목표 대비 퍼센트는 숨김
        show_target = False

    with cols[0]:
        score_big_card(
            label=score_label,
            score=avg_score,
            target=TARGET_TOTAL,
            icon="🏁" if is_final_month else "🎯",
            delta=delta_avg,
            color=pace_color,
            status_text=score_status,
            show_target=show_target,
        )

    n_total = len(df_latest)
    if is_final_month:
        n_achieved = int((df_latest["총점"] >= TARGET_TOTAL).sum())
        n_below = n_total - n_achieved
        second_label, second_count, second_color = f"{half_label} 911점 달성", n_achieved, Colors.SUCCESS
        third_label, third_count, third_color = f"{half_label} 911점 미달", n_below, (Colors.WARNING if n_below else Colors.SUCCESS)
    else:
        n_safe = int((outlook["안전도"] == "안전").sum()) if not outlook.empty else 0
        n_caution = int((outlook["안전도"] == "주의").sum()) if not outlook.empty else 0
        n_risk = int((outlook["안전도"] == "위험").sum()) if not outlook.empty else 0
        second_label, second_count, second_color = "911점 달성 안전 페이스", n_safe, Colors.SUCCESS
        third_label = "페이스 주의·위험 센터"
        third_count = n_caution + n_risk
        
        if n_risk > 0:
            third_color = Colors.DANGER
        elif n_caution > 0:
            third_color = Colors.WARNING
        else:
            third_color = Colors.SUCCESS


    with cols[1 % n_cols]:
        count_big_card(label=second_label, count=second_count, total=n_total, icon="🏆", color=second_color, suffix="개")

    with cols[2 % n_cols]:
        count_big_card(label=third_label, count=third_count, total=n_total, icon="⚠️", color=third_color, suffix="개")

    max_s = df_latest["총점"].max() if "총점" in df_latest.columns else 0
    min_s = df_latest["총점"].min() if "총점" in df_latest.columns else 0
    with cols[3 % n_cols]:
        big_metric_card(
            label="최고-최저 격차",
            value=f"{max_s - min_s:,.1f}점",
            delta=f"최고 {max_s:,.1f} / 최저 {min_s:,.1f}",
            delta_color="off",
            icon="📏",
        )
    st.markdown("")


    # ==================== 2. 인사이트 ====================
    if is_final_month:
        st.markdown(f"### 💡 {half_label} 최종 인사이트")
    else:
        st.markdown("### 💡 이번 달 주요 인사이트")

    insights = get_all_insights(df, max_count=6, df_last_year=df_last_year)
    if insights:
        _render_insights(insights, device_type)
    else:
        st.info("표시할 인사이트가 없습니다.")

    st.markdown("")

    # ==================== 3. 센터 랭킹 ====================
    st.markdown(f"### 🏆 {half_label} 최종 랭킹" if is_final_month else "### 🏆 센터 랭킹")

    ranking = get_ranking_data(df_latest, n=5, mode="score")
    top_df = ranking.get("top", pd.DataFrame())
    bottom_df = ranking.get("bottom", pd.DataFrame())

    
    # 진행 중인 반기에는 실제 누적점수 미달이 아닌
    # '반기 마감 예상점수' 기준의 페이스 위험 센터를 사용
    pace_lag_df = pd.DataFrame()
    
    if not is_final_month:
        pace_lag_df = get_pace_lag_ranking(
            df,
            n=5,
            df_last_year=df_last_year,
        )
    
    top_title = "🏆 911점 달성 Top 5" if is_final_month else "🥇 Top 5 우수 센터"
    
    if device_type == "mobile":
        ranking_list(
            top_df,
            title=top_title,
            value_col="총점",
            icon="🏆" if is_final_month else "🥇",
    
            # 진행 중인 반기에는 500점대가 빨갛게 표시되지 않게 함
            use_score_color=is_final_month,
        )
    
        st.markdown("")
    
        if is_final_month:
            _render_below_target_list(bottom_df, is_final_month, half_label)
        else:
            pace_lag_df = get_pace_lag_ranking(
                df,
                n=5,
                df_last_year=df_last_year,
            )
            _render_pace_lag_list(pace_lag_df)

    
    else:
        col1, col2 = st.columns(2)
    
        with col1:
            ranking_list(
                top_df,
                title=top_title.replace("🏆 ", "").replace("🥇 ", ""),
                value_col="총점",
                icon="🏆" if is_final_month else "🥇",
    
                # 진행 중인 반기에는 절대점수 색상 판정 비활성화
                use_score_color=is_final_month,
            )
    
        with col2:
            if is_final_month:
                _render_below_target_list(bottom_df, is_final_month, half_label)
            else:
                pace_lag_df = get_pace_lag_ranking(
                    df,
                    n=5,
                    df_last_year=df_last_year,
                )
                _render_pace_lag_list(pace_lag_df)

    st.markdown("")

    if df_prev is not None and not df_prev.empty:
        if is_half_start_month:
            st.markdown(f"##### 📊 전년 동월 대비 동향 (vs {prev_month})")
            st.caption(
                "※ 총점 변화는 참고용이며, KPI별 달성률·반기말 예측점수 중심으로 해석하세요."
            )

        elif is_final_month:
            st.markdown(f"##### 📊 최종 월 대비 동향 (vs {prev_month})")
        else:
            st.markdown(f"##### 📊 전월 대비 동향 (vs {prev_month})")


        change_rank = get_change_ranking(
            df,
            n=5,
            df_last_year=df_last_year,
        )

        rising_df = change_rank.get("rising", pd.DataFrame())
        falling_df = change_rank.get("falling", pd.DataFrame())

        if is_final_month:
            if device_type == "mobile":
                change_ranking_list(rising_df, title="📈 상승 모멘텀 Top 5", icon="📈", ascending=False)
                st.markdown("")
                change_ranking_list(falling_df, title="📉 하락 Top 5 (최종월)", icon="📉", ascending=True)
            else:
                col3, col4 = st.columns(2)
                with col3:
                    change_ranking_list(rising_df, title="📈 상승 모멘텀 Top 5", icon="📈", ascending=False)
                with col4:
                    change_ranking_list(falling_df, title="📉 하락 Top 5 (최종월)", icon="📉", ascending=True)
        else:
            pace_lag_df = get_pace_lag_ranking(df, n=5, df_last_year=df_last_year)
            if device_type == "mobile":
                change_ranking_list(rising_df, title="📈 상승 모멘텀 Top 5", icon="📈", ascending=False)
                st.markdown("")
                _render_pace_lag_list(pace_lag_df)
            else:
                col3, col4 = st.columns(2)
                with col3:
                    change_ranking_list(rising_df, title="📈 상승 모멘텀 Top 5", icon="📈", ascending=False)
                with col4:
                    _render_pace_lag_list(pace_lag_df)
    else:
        st.info("📅 전월 데이터가 없어 변화 분석을 표시할 수 없습니다.")

    st.markdown("")

    # ==================== 4. 분포 + 추이 ====================
    st.markdown("### 📈 분포 및 추이")

    if device_type == "mobile":
        _render_distribution_chart(df_latest, is_final_month, half_label, df, df_last_year)
        st.markdown("")
        _render_trend_chart(df)
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            _render_distribution_chart(
                df_latest,
                is_final_month,
                half_label,
                df,
                df_last_year,
            )

        with col_b:
            _render_trend_chart(df)

    st.markdown("")

    # ==================== 5. 반기 마감 / 반기 전망 ====================
    if is_final_month and half_label == '상반기':
        section_title = "### 🏁 상반기 최종 결과 & 하반기 만회 필요치"
    elif is_final_month:
        section_title = f"### 🏁 {half_label} 최종 결과 (연간 확정)"
    else:
        section_title = "### 📅 반기 마감 전망"
    st.markdown(section_title)
    _render_half_outlook(df, df_last_year, device_type, is_final_month, half_label)

    st.markdown("")

    # ==================== 6. 빠른 이동 ====================
    st.markdown("### 🚀 빠른 이동")
    st.caption("자주 사용하는 메뉴로 바로 이동하세요.")

    n_cols_nav = 2 if device_type == "mobile" else 4
    quick_nav_buttons(QUICK_NAV_ITEMS, columns=n_cols_nav)


# ==================== 헬퍼 함수들 ====================

def _get_latest_and_prev(df: pd.DataFrame):
    if df is None or df.empty or '평가월' not in df.columns:
        return None, None, None, None

    df_sorted = df.dropna(subset=['평가월']).copy()
    if df_sorted.empty:
        return None, None, None, None

    months = sorted(df_sorted['평가월'].unique())
    latest_month_dt = months[-1]
    prev_month_dt = months[-2] if len(months) >= 2 else None

    df_latest = df_sorted[df_sorted['평가월'] == latest_month_dt].copy()
    df_prev = df_sorted[df_sorted['평가월'] == prev_month_dt].copy() if prev_month_dt is not None else None

    latest_label = pd.Timestamp(latest_month_dt).strftime("%Y년 %m월")
    prev_label = pd.Timestamp(prev_month_dt).strftime("%Y년 %m월") if prev_month_dt is not None else None

    return df_latest, df_prev, latest_label, prev_label


def _render_period_header(df: pd.DataFrame, latest_month: str, is_final_month: bool, half_label: str):
    """평가월/반기 진행률 헤더"""
    try:
        month_num = int(latest_month.split("년")[1].replace("월", "").strip())
        if month_num <= 6:
            half = "상반기"
            progress = month_num / 6 * 100
        else:
            half = "하반기"
            progress = (month_num - 6) / 6 * 100

        df_clean = df.dropna(subset=['평가월']).copy()
        if not df_clean.empty:
            latest_dt = sorted(df_clean['평가월'].unique())[-1]
            df_latest = df_clean[df_clean['평가월'] == latest_dt]
            n_centers = len(safe_unique_centers(df_latest))
        else:
            n_centers = 0

        if is_final_month:
            status_badge = (
                f'<span style="background:{Colors.SUCCESS};color:white;'
                f'font-size:11px;font-weight:700;padding:3px 8px;border-radius:10px;'
                f'margin-left:10px;">🏁 {half_label} 마감</span>'
            )
            progress_text = (
                f'<span style="color:{Colors.SUCCESS};font-size:13px;font-weight:600;'
                f'margin-left:12px;">✅ {half} 확정 (100%)</span>'
            )
            if half == '상반기':
                right_text = f'🎯 연간 pass 기준: 상+하반기 평균 911점 (하반기 7월부터 재시작)'
            else:
                right_text = f'🏁 연간 최종 확정 (2000점 만점, 평균 911점 기준)'
        else:
            status_badge = ""
            progress_text = (
                f'<span style="color:{Colors.TEXT_SUB};font-size:13px;margin-left:12px;">'
                f'· {half} 진행률 <b style="color:{Colors.TEXT_MAIN};">{progress:.0f}%</b>'
                f'</span>'
            )
            right_text = f'🎯 목표: 반기 {ScoreThresholds.TARGET}점 (연간 평균 pass)'

        html = (
            f'<div style="background:{Colors.PRIMARY_LIGHT};'
            f'border-left:4px solid {Colors.SUCCESS if is_final_month else Colors.PRIMARY};'
            f'padding:12px 18px;border-radius:8px;margin-bottom:16px;'
            f'display:flex;justify-content:space-between;align-items:center;'
            f'flex-wrap:wrap;gap:12px;">'
            f'<div>'
            f'<span style="color:{Colors.TEXT_SUB};font-size:13px;">현재 평가월</span>'
            f'<span style="color:{Colors.PRIMARY};font-size:18px;font-weight:700;margin-left:8px;">{latest_month}</span>'
            f'{status_badge}'
            f'{progress_text}'
            f'<span style="color:{Colors.TEXT_SUB};font-size:13px;margin-left:12px;">'
            f'· 대상 센터 <b style="color:{Colors.TEXT_MAIN};">{n_centers}개</b>'
            f'</span>'
            f'</div>'
            f'<div style="color:{Colors.TEXT_SUB};font-size:12px;">'
            f'{right_text}'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        st.caption(f"📅 현재 평가월: {latest_month}")


def _render_insights(insights, device_type: str):
    category_colors = {
        "success": Colors.SUCCESS, "warning": Colors.WARNING,
        "danger": Colors.DANGER, "info": Colors.PRIMARY,
    }

    def _to_rgba(hex_color: str, alpha: float = 0.08) -> str:
        h = hex_color.lstrip('#')
        if len(h) == 3:
            h = ''.join(c * 2 for c in h)
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    n_cols = 1 if device_type == "mobile" else 2
    cols = st.columns(n_cols)

    for idx, ins in enumerate(insights):
        color = category_colors.get(ins.category, Colors.PRIMARY)
        col = cols[idx % n_cols]
    
        # 인사이트 문자열의 **굵게** 표기를 HTML <b> 태그로 변환
        message_html = re.sub(
            r"\*\*(.*?)\*\*",
            r"<b>\1</b>",
            str(ins.message or ""),
        )
    
        action = getattr(ins, "action", None)
        action_html = ""
    
        if action:
            action_text_html = re.sub(
                r"\*\*(.*?)\*\*",
                r"<b>\1</b>",
                str(action),
            )
    
            action_bg = _to_rgba(color, 0.08)
    
            action_html = (
                f'<div style="background:{action_bg};'
                f'border-radius:6px;padding:8px 12px;margin-top:10px;'
                f'border-left:3px solid {color};">'
                f'<div style="color:{color};font-size:12px;font-weight:700;'
                f'margin-bottom:3px;">💡 권장 액션</div>'
                f'<div style="color:{Colors.TEXT_MAIN};font-size:13px;'
                f'line-height:1.5;">{action_text_html}</div>'
                f'</div>'
            )


        with col:
            html = (
                f'<div style="background:{Colors.BG_CARD};'
                f'border:1px solid {Colors.BORDER};'
                f'border-left:4px solid {color};'
                f'border-radius:10px;padding:14px 18px;margin-bottom:10px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">'
                f'<span style="font-size:18px;">{ins.icon}</span>'
                f'<span style="color:{color};font-size:14px;font-weight:700;">{ins.title}</span>'
                f'</div>'
                f'<div style="color:{Colors.TEXT_MAIN};font-size:14px;line-height:1.5;">'
                f'{message_html}'
                f'</div>'
                f'{action_html}'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)


def _render_below_target_list(below_df: pd.DataFrame, is_final_month: bool, half_label: str):
    """
    ⭐ v2.6: 911점 미달 센터 리스트
    - 미달 센터가 없으면 축하 메시지
    - 있으면 최대 5개까지 표시
    """
    title = f"⚠️ {half_label} 911점 미달 센터" if is_final_month else "⚠️ 911점 미달 센터"

    if below_df is None or below_df.empty:
        # 미달 센터 없음 → 축하
        html = (
            f'<div style="background:{Colors.BG_CARD};border:1px solid {Colors.BORDER};'
            f'border-left:4px solid {Colors.SUCCESS};'
            f'border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
            f'<div style="padding:0 0 10px 0;display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:20px;">🎉</span>'
            f'<span style="color:{Colors.TEXT_MAIN};font-size:15px;font-weight:700;">'
            f'전 센터 911점 달성!</span>'
            f'</div>'
            f'<div style="color:{Colors.TEXT_SUB};font-size:13px;line-height:1.6;padding:4px 0;">'
            f'모든 센터가 반기 목표를 달성했습니다. 우수 사례를 공유하며 다음 반기에도 페이스를 이어가세요.'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
        return

    rows_html = ""
    for i, (_, row) in enumerate(below_df.iterrows(), 1):
        name = str(row['센터명'])
        score = row['총점']
        gap = TARGET_TOTAL - score

        # 상반기 마감이면 하반기 필요점수 계산
        h2_needed_text = ""
        if is_final_month and half_label == '상반기':
            h2_needed = ANNUAL_PASS_TOTAL - score
            if h2_needed > 950:
                h2_color = Colors.DANGER
                h2_label = "매우 어려움"
            elif h2_needed > 920:
                h2_color = Colors.WARNING
                h2_label = "쉽지 않음"
            else:
                h2_color = Colors.PRIMARY
                h2_label = "가능"
            h2_needed_text = (
                f'<div style="margin-left:40px;margin-top:4px;color:{Colors.TEXT_SUB};font-size:12px;">'
                f'하반기 필요 <b style="color:{h2_color};">{h2_needed:.0f}점</b> '
                f'<span style="color:{h2_color};font-weight:600;">({h2_label})</span>'
                f'</div>'
            )

        # 배지
        if score < 850:
            score_color = Colors.DANGER
        elif score < 895:
            score_color = Colors.ALERT
        else:
            score_color = Colors.WARNING

        rows_html += (
            f'<div style="padding:10px 12px;border-bottom:1px solid {Colors.BG_GRAY};">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<span style="width:24px;text-align:center;display:inline-block;'
            f'color:{Colors.TEXT_SUB};font-size:12px;font-weight:600;">{i}</span>'
            f'<span style="color:{Colors.TEXT_MAIN};font-size:14px;font-weight:600;">{name}</span>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<span style="color:{score_color};font-size:15px;font-weight:700;">{score:.1f}점</span>'
            f'<span style="color:{Colors.TEXT_SUB};font-size:12px;margin-left:6px;">'
            f'(-{gap:.1f})</span>'
            f'</div>'
            f'</div>'
            f'{h2_needed_text}'
            f'</div>'
        )

    subtitle = ""
    if is_final_month and half_label == '상반기':
        subtitle = (
            f'<span style="color:{Colors.TEXT_SUB};font-size:11px;margin-left:auto;">'
            f'하반기 만회 필요</span>'
        )
    elif is_final_month:
        subtitle = (
            f'<span style="color:{Colors.DANGER};font-size:11px;margin-left:auto;">'
            f'연간 미달 확정</span>'
        )

    html = (
        f'<div style="background:{Colors.BG_CARD};border:1px solid {Colors.BORDER};'
        f'border-radius:12px;padding:16px 8px 8px 8px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<div style="padding:0 12px 12px 12px;border-bottom:2px solid {Colors.WARNING};'
        f'margin-bottom:4px;display:flex;align-items:center;gap:8px;">'
        f'<span style="font-size:18px;">⚠️</span>'
        f'<span style="color:{Colors.TEXT_MAIN};font-size:15px;font-weight:700;">{title}</span>'
        f'{subtitle}'
        f'</div>'
        f'{rows_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def _render_pace_lag_list(pace_lag_df: pd.DataFrame):
    """페이스 미달 Top 5 (진행 중일 때만)"""
    title = "⚠️ 페이스 미달 Top 5"

    if pace_lag_df is None or pace_lag_df.empty:
        html = (
            f'<div style="background:{Colors.BG_CARD};border:1px solid {Colors.BORDER};'
            f'border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
            f'<div style="padding:0 0 12px 0;border-bottom:2px solid {Colors.SUCCESS};'
            f'margin-bottom:12px;display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:18px;">✅</span>'
            f'<span style="color:{Colors.TEXT_MAIN};font-size:15px;font-weight:700;">'
            f'페이스 미달 센터 없음</span>'
            f'</div>'
            f'<div style="color:{Colors.TEXT_SUB};font-size:13px;line-height:1.6;padding:8px 4px;">'
            f'🎉 현재 페이스를 유지하면 모든 센터가 911점에 도달할 것으로 예상됩니다.'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
        return

    rows_html = ""
    for i, (_, row) in enumerate(pace_lag_df.iterrows(), 1):
        name = str(row['센터명'])
        current = row['총점']
        predicted = row['예상점수']
        gap = row['부족분']

        if i == 1: badge = "🥇"
        elif i == 2: badge = "🥈"
        elif i == 3: badge = "🥉"
        else:
            badge = (
                f'<span style="display:inline-block;width:22px;height:22px;'
                f'border-radius:50%;background:{Colors.BG_CARD};'
                f'border:1px solid {Colors.BORDER};text-align:center;'
                f'font-size:12px;font-weight:600;color:{Colors.TEXT_SUB};">{i}</span>'
            )

        rows_html += (
            f'<div style="padding:10px 12px;border-bottom:1px solid {Colors.BG_GRAY};">'
            f'<div style="display:flex;align-items:center;justify-content:space-between;">'
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'<span style="width:30px;text-align:center;display:inline-block;">{badge}</span>'
            f'<span style="color:{Colors.TEXT_MAIN};font-size:14px;font-weight:600;">{name}</span>'
            f'</div>'
            f'<span style="color:{Colors.DANGER};font-size:15px;font-weight:700;">'
            f'-{gap:.1f}점</span>'
            f'</div>'
            f'<div style="margin-left:40px;margin-top:4px;color:{Colors.TEXT_SUB};font-size:12px;">'
            f'현재 <b style="color:{Colors.TEXT_MAIN};">{current:.1f}</b> → '
            f'예상 <b style="color:{Colors.WARNING};">{predicted:.1f}</b> '
            f'<span style="color:{Colors.TEXT_SUB};">(목표 911점 대비)</span>'
            f'</div>'
            f'</div>'
        )

    html = (
        f'<div style="background:{Colors.BG_CARD};border:1px solid {Colors.BORDER};'
        f'border-radius:12px;padding:16px 8px 8px 8px;box-shadow:0 1px 3px rgba(0,0,0,0.05);">'
        f'<div style="padding:0 12px 12px 12px;border-bottom:2px solid {Colors.DANGER};'
        f'margin-bottom:4px;display:flex;align-items:center;gap:8px;">'
        f'<span style="font-size:18px;">⚠️</span>'
        f'<span style="color:{Colors.TEXT_MAIN};font-size:15px;font-weight:700;">{title}</span>'
        f'<span style="color:{Colors.TEXT_SUB};font-size:12px;margin-left:auto;">'
        f'911점 도달 위험</span>'
        f'</div>'
        f'{rows_html}'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def _render_distribution_chart(
    df_latest: pd.DataFrame,
    is_final_month: bool = False,
    half_label: str = "",
    df_all: pd.DataFrame = None,
    df_last_year: pd.DataFrame = None,
):
    if df_latest is None or df_latest.empty or "총점" not in df_latest.columns:
        st.info("분포 데이터가 없습니다.")
        return

    # 진행 중: 현재 누적점수 구간 대신 반기 최종 전망 안전도를 분포로 사용
    if not is_final_month and df_all is not None:
        outlook = get_half_outlook(df_all, df_last_year=df_last_year)
        if not outlook.empty:
            grades = {
                "🟢 안전 (911점 이상 전망)": int((outlook["안전도"] == "안전").sum()),
                "🟡 주의 (895~910점 전망)": int((outlook["안전도"] == "주의").sum()),
                "🔴 위험 (895점 미만 전망)": int((outlook["안전도"] == "위험").sum()),
            }
            colors = [Colors.SUCCESS, Colors.WARNING, Colors.DANGER]
            chart_title = f"<b>{half_label} 마감 페이스 분포</b> (총 {len(outlook)}개)"
        else:
            grades, colors, chart_title = {}, [], "페이스 데이터 없음"
    else:
        scores = df_latest["총점"].dropna()
        grades = {
            "🟢 달성 (911+)": int((scores >= ScoreThresholds.SUCCESS_MIN).sum()),
            "🟡 주의 (881~910)": int(((scores >= ScoreThresholds.WARNING_MIN) & (scores < ScoreThresholds.SUCCESS_MIN)).sum()),
            "🟠 경고 (851~880)": int(((scores >= ScoreThresholds.ALERT_MIN) & (scores < ScoreThresholds.WARNING_MIN)).sum()),
            "🔴 위험 (~850)": int((scores < ScoreThresholds.ALERT_MIN).sum()),
        }
        colors = [Colors.SUCCESS, Colors.WARNING, Colors.ALERT, Colors.DANGER]
        chart_title = f"<b>{half_label} 최종 점수 구간 분포</b> (총 {sum(grades.values())}개)"

    fig = go.Figure(data=[go.Pie(
        labels=list(grades.keys()),
        values=list(grades.values()),
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="value",
        textfont=dict(size=14, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value}개 (%{percent})<extra></extra>",
    )])
    fig.update_layout(
        title=dict(text=chart_title, font=dict(size=15)),
        height=320,
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=12)),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)



def _render_trend_chart(df: pd.DataFrame):
    """현재 반기 데이터만 그린다. 6월→7월 리셋을 하나의 하락선으로 연결하지 않는다."""
    if df is None or df.empty or "평가월" not in df.columns or "총점" not in df.columns:
        st.info("추이 데이터가 없습니다.")
        return

    df_clean = df.dropna(subset=["평가월", "총점"]).copy()
    df_clean["_month_dt"] = pd.to_datetime(df_clean["평가월"], errors="coerce")
    df_clean = df_clean.dropna(subset=["_month_dt"])
    if df_clean.empty:
        st.info("추이 데이터가 없습니다.")
        return

    latest = df_clean["_month_dt"].max()
    half_label = _get_half(latest.month)
    valid_months = range(1, 7) if half_label == "상반기" else range(7, 13)

    # 현재 연도·현재 반기만 표시
    df_half = df_clean[
        (df_clean["_month_dt"].dt.year == latest.year)
        & (df_clean["_month_dt"].dt.month.isin(valid_months))
    ].copy()

    monthly_avg = (
        df_half.groupby("_month_dt")["총점"]
        .mean()
        .reset_index()
        .sort_values("_month_dt")
    )
    monthly_avg["월라벨"] = monthly_avg["_month_dt"].dt.strftime("%b")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly_avg["월라벨"],
        y=monthly_avg["총점"],
        mode="lines+markers+text",
        name="전체 평균",
        line=dict(color=Colors.PRIMARY, width=3),
        marker=dict(size=10, color=Colors.PRIMARY),
        text=[f"{v:.1f}" for v in monthly_avg["총점"]],
        textposition="top center",
        textfont=dict(size=11, color=Colors.TEXT_MAIN),
        hovertemplate="<b>%{x}</b><br>평균 %{y:.1f}점<extra></extra>",
    ))

    # 911점은 반기 최종 목표이므로, 진행 중에는 목표선 대신 참고 문구만 표시
    if _is_half_end(latest):
        fig.add_hline(
            y=ScoreThresholds.TARGET,
            line_dash="dash",
            line_color=Colors.WARNING,
            annotation_text=f"반기 목표 {ScoreThresholds.TARGET}",
            annotation_position="right",
        )

    fig.update_layout(
        title=dict(text=f"<b>{latest.year}년 {half_label} 평균 점수 추이</b>", font=dict(size=15)),
        height=320,
        margin=dict(t=50, b=40, l=40, r=40),
        showlegend=False,
        xaxis=dict(title="", gridcolor=Colors.BORDER),
        yaxis=dict(title="평균 점수", gridcolor=Colors.BORDER),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)

    if not _is_half_end(latest):
        st.caption("※ 반기 누적점수는 1월·7월에 0점부터 다시 시작합니다. 진행 중에는 911점 목표선을 현재 점수와 직접 비교하지 않습니다.")


def _render_half_outlook(
    df: pd.DataFrame,
    df_last_year,
    device_type: str,
    is_final_month: bool = False,
    half_label: str = "",
):
    """반기 마감 결과 / 진행 중 전망"""
    try:
        outlook = get_half_outlook(df, df_last_year=df_last_year)
    except Exception as e:
        st.warning(f"반기 전망 계산 중 오류: {e}")
        return

    if outlook is None or outlook.empty:
        st.info("반기 데이터를 계산할 수 없습니다.")
        return

    # ==================== 반기 마감 ====================
    if is_final_month:
        achieved_cnt = int((outlook['안전도'] == '달성').sum())
        near_cnt = int((outlook['안전도'] == '근접미달').sum())
        fail_cnt = int((outlook['안전도'] == '미달').sum())
        total_cnt = len(outlook)

        n_cols = 1 if device_type == "mobile" else 3
        cols = st.columns(n_cols)

        if half_label == '상반기':
            summary_cards = [
                {"label": "✅ 911점 달성", "sublabel": "연간 pass 안정권",
                 "count": achieved_cnt, "color": Colors.SUCCESS},
                {"label": "⚠️ 근접 미달", "sublabel": "895~910점 / 하반기 소폭 회복 필요",
                 "count": near_cnt, "color": Colors.WARNING},
                {"label": "🚨 미달", "sublabel": "895점 미만 / 하반기 강력 회복 필요",
                 "count": fail_cnt, "color": Colors.DANGER},
            ]
        else:
            summary_cards = [
                {"label": "✅ 달성", "sublabel": "911점 이상",
                 "count": achieved_cnt, "color": Colors.SUCCESS},
                {"label": "⚠️ 근접 미달", "sublabel": "895~910점",
                 "count": near_cnt, "color": Colors.WARNING},
                {"label": "🚨 미달", "sublabel": "895점 미만",
                 "count": fail_cnt, "color": Colors.DANGER},
            ]

        for idx, card in enumerate(summary_cards):
            with cols[idx % n_cols]:
                html = (
                    f'<div style="background:{Colors.BG_CARD};'
                    f'border:1px solid {Colors.BORDER};'
                    f'border-left:4px solid {card["color"]};'
                    f'border-radius:10px;padding:16px 18px;margin-bottom:10px;'
                    f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                    f'<div style="color:{Colors.TEXT_SUB};font-size:13px;font-weight:600;">'
                    f'{card["label"]}'
                    f'</div>'
                    f'<div style="color:{Colors.TEXT_SUB};font-size:11px;margin-bottom:6px;">'
                    f'{card["sublabel"]}'
                    f'</div>'
                    f'<div style="font-size:32px;font-weight:700;color:{card["color"]};line-height:1.1;">'
                    f'{card["count"]}<span style="font-size:16px;font-weight:500;'
                    f'color:{Colors.TEXT_SUB};margin-left:4px;">/ {total_cnt}개</span>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(html, unsafe_allow_html=True)

        st.markdown("")

        with st.expander(f"📋 센터별 {half_label} 최종 결과 상세 보기", expanded=False):
            # ⭐ 상반기 마감이면 '하반기필요점수' 컬럼 표시
            if half_label == '상반기' and '하반기필요점수' in outlook.columns:
                display_cols = ["센터명", "현재점수", "현실전망", "낙관전망", "목표차이", "안전도", "전망근거", "통합여부"]
            else:
                display_cols = ['센터명', '현재점수', '목표차이', '안전도', '통합여부']

            if '작년참고' in outlook.columns and outlook['작년참고'].notna().any():
                # 안전도 앞에 삽입
                idx = display_cols.index('안전도')
                display_cols.insert(idx, '작년참고')

            if '현재감점' in outlook.columns and (outlook['현재감점'].fillna(0) != 0).any():
                display_cols.append('현재감점')

            safety_order = {'미달': 0, '근접미달': 1, '달성': 2}
            outlook_sorted = outlook.copy()
            outlook_sorted['_sort'] = outlook_sorted['안전도'].map(safety_order).fillna(99)
            outlook_sorted = outlook_sorted.sort_values(
                ['_sort', '현재점수'], ascending=[True, True]
            )

            column_config = {
                '현재점수': st.column_config.NumberColumn(
                    f"{half_label} 최종점수", format="%.1f점"
                ),
                '목표차이': st.column_config.NumberColumn(
                    format="%+.1f점", help="911점 - 최종점수"
                ),
            }

            if '하반기필요점수' in display_cols:
                column_config['하반기필요점수'] = st.column_config.NumberColumn(
                    format="%.0f점",
                    help="연간 pass(평균 911점) 위해 하반기에 필요한 최소 점수. 950점 초과 시 매우 어려움."
                )

            if '작년참고' in display_cols:
                column_config['작년참고'] = st.column_config.NumberColumn(
                    format="%.1f점",
                    help="작년 동기 점수 (구조 변경으로 참고용)"
                )

            if '현재감점' in display_cols:
                column_config['현재감점'] = st.column_config.NumberColumn(
                    format="%.0f점", help="반기 누적 감점"
                )

            st.dataframe(
                outlook_sorted[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
            )

            if half_label == '상반기':
                st.caption(
                    f"💡 **상반기 최종 확정** — 하반기는 7월부터 0점 재시작 / "
                    f"**연간 pass = 상+하반기 평균 911점 이상** (총 1822점) / "
                    f"**하반기필요점수**: 연간 pass 위해 하반기에 획득해야 할 최소 점수 "
                    f"(950점 초과 시 매우 어려움, 920점 이하면 회복 가능) / "
                    f"**작년참고**: 구조 변경으로 참고용."
                )
            else:
                st.caption(
                    f"💡 **{half_label} 최종 확정 = 연간 결과 확정** — "
                    f"연간 pass 기준: 상+하반기 평균 911점 이상. "
                    f"**작년참고**: 구조 변경으로 참고용."
                )
        return

    # ==================== 진행 중 ====================
    safe_cnt = int((outlook['안전도'] == '안전').sum())
    caution_cnt = int((outlook['안전도'] == '주의').sum())
    danger_cnt = int((outlook['안전도'] == '위험').sum())
    total_cnt = len(outlook)

    n_cols = 1 if device_type == "mobile" else 3
    cols = st.columns(n_cols)

    summary_cards = [
        {"label": "✅ 안전", "sublabel": "911점 달성 예상",
         "count": safe_cnt, "color": Colors.SUCCESS},
        {"label": "⚠️ 주의", "sublabel": "895~910점 예상",
         "count": caution_cnt, "color": Colors.WARNING},
        {"label": "🚨 위험", "sublabel": "895점 미만 예상",
         "count": danger_cnt, "color": Colors.DANGER},
    ]

    for idx, card in enumerate(summary_cards):
        with cols[idx % n_cols]:
            html = (
                f'<div style="background:{Colors.BG_CARD};'
                f'border:1px solid {Colors.BORDER};'
                f'border-left:4px solid {card["color"]};'
                f'border-radius:10px;padding:16px 18px;margin-bottom:10px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                f'<div style="color:{Colors.TEXT_SUB};font-size:13px;font-weight:600;">'
                f'{card["label"]}'
                f'</div>'
                f'<div style="color:{Colors.TEXT_SUB};font-size:11px;margin-bottom:6px;">'
                f'{card["sublabel"]}'
                f'</div>'
                f'<div style="font-size:32px;font-weight:700;color:{card["color"]};line-height:1.1;">'
                f'{card["count"]}<span style="font-size:16px;font-weight:500;'
                f'color:{Colors.TEXT_SUB};margin-left:4px;">/ {total_cnt}개</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("")

    with st.expander("📋 센터별 반기 전망 상세 보기", expanded=False):
        display_cols = [
            '센터명',
            '현재점수',
            '현실전망',
            '목표차이',
            '안전도',
            '전망근거',
            '통합여부',
        ]

        if '작년참고' in outlook.columns and outlook['작년참고'].notna().any():
            display_cols.insert(4, '작년참고')
        if '현재감점' in outlook.columns and (outlook['현재감점'].fillna(0) != 0).any():
            display_cols.append('현재감점')

        safety_order = {'위험': 0, '주의': 1, '안전': 2}
        outlook_sorted = outlook.copy()
        outlook_sorted['_sort'] = outlook_sorted['안전도'].map(safety_order).fillna(99)
        outlook_sorted = outlook_sorted.sort_values(['_sort', '현실전망'], ascending=[True, True])

        column_config = {
            '현재점수': st.column_config.NumberColumn(format="%.1f점"),
            '낙관전망': st.column_config.NumberColumn(
                format="%.1f점",
                help="911점 목표 페이스 달성 시 예상 반기 최종 점수"
            ),
            '현실전망': st.column_config.NumberColumn(
                format="%.1f점",
                help="작년 동일 반기 누적 진행률을 우선 적용한 예상 반기 최종 점수 (작년 데이터 없으면 반기 경과개월 환산)"
            ),
            '목표차이': st.column_config.NumberColumn(
                format="%+.1f점", help="911점 - 현실전망"
            ),
        }

        if '작년참고' in display_cols:
            column_config['작년참고'] = st.column_config.NumberColumn(
                format="%.1f점",
                help="작년 동기 점수 (구조 변경으로 직접 비교 부적합, 참고용)"
            )

        if '현재감점' in display_cols:
            column_config['현재감점'] = st.column_config.NumberColumn(
                format="%.0f점", help="현재 누적 감점"
            )

        st.dataframe(
            outlook_sorted[display_cols],
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
        )

        st.caption(
            "💡 **반기 전망**: 성과분석과 동일한 예측 로직을 적용합니다. "
            "누적형 KPI는 반기 진행률로 환산하고, 비누적형 KPI는 현재 점수를 유지합니다. / "
            "**낙관 전망**: 911점 목표 페이스 달성 시 예상 점수 / "
            "**연간 pass**: 상+하반기 평균 911점 (반기 미달해도 다음 반기로 만회 가능) / "
            "**통합**: 4월 통합된 센터는 작년 직접 비교 제외"
        )
