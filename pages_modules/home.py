"""
🏠 홈 (Executive Dashboard)
- 핵심 KPI + 자동 인사이트 + Top/Bottom 랭킹 + 빠른 이동
- 모든 사용자(센터장/본사/평가)에게 동일한 화면 제공
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.styles import Colors, ScoreThresholds, get_score_color, PLOTLY_LAYOUT
from utils.helpers import safe_unique_centers
from utils.insights_v2 import (
    get_all_insights,
    get_ranking_data,
    get_change_ranking,
)
from components.big_metric_card import score_big_card, count_big_card, big_metric_card
from components.ranking_list import ranking_list, change_ranking_list
from components.quick_nav import quick_nav_buttons


# ==================== 빠른 이동 메뉴 (전체 공통) ====================

QUICK_NAV_ITEMS = [
    {"icon": "📊", "label": "성과 분석",  "page_key": "📊 성과 분석",  "desc": "전체 현황 + 추이"},
    {"icon": "🎯", "label": "센터 진단",  "page_key": "🎯 센터 진단",  "desc": "센터별 상세 진단"},
    {"icon": "⚠️", "label": "위험 관리",  "page_key": "⚠️ 위험 관리",  "desc": "주의/위험 센터"},
    {"icon": "🌡️", "label": "KPI 히트맵", "page_key": "🌡️ KPI 히트맵", "desc": "센터×KPI 매트릭스"},
    {"icon": "🔬", "label": "심화 분석",  "page_key": "🔬 심화 분석",  "desc": "분석 + 원본"},
]



# ==================== 메인 함수 ====================

def show(df: pd.DataFrame, device_type: str = "desktop"):
    """홈 페이지 메인 함수"""

    # 헤더는 app.py에서 공통 출력하므로 생략

    if df is None or df.empty:
        st.warning("⚠️ 표시할 데이터가 없습니다. 사이드바에서 데이터를 확인해주세요.")
        return

    # ----- 최신 월/전월 데이터 추출 -----
    df_latest, df_prev, latest_month, prev_month = _get_latest_and_prev(df)


    if df_latest is None or df_latest.empty:
        st.warning("⚠️ 최신 월 데이터를 추출할 수 없습니다.")
        return

    # 평가월/진행률 헤더
    _render_period_header(df, latest_month)

    # ==================== 1. 핵심 KPI 카드 ====================
    st.markdown("### 📊 핵심 지표")

    n_cols = 2 if device_type == "mobile" else 4
    cols = st.columns(n_cols)

    # 1) 전체 평균 점수
    avg_score = df_latest['총점'].mean() if '총점' in df_latest.columns else 0
    prev_avg = df_prev['총점'].mean() if df_prev is not None and '총점' in df_prev.columns else None
    delta_avg = None
    if prev_avg is not None and pd.notna(prev_avg):
        diff = avg_score - prev_avg
        delta_avg = f"{'+' if diff >= 0 else ''}{diff:,.1f} vs 전월"

    with cols[0]:
        score_big_card(
            label="전체 평균 점수",
            score=avg_score,
            target=ScoreThresholds.TARGET,
            icon="🎯",
            delta=delta_avg,
        )

    # 2) 목표 달성 센터 수
    n_total = len(df_latest)
    if '목표달성여부' in df_latest.columns:
        n_achieved = int(df_latest['목표달성여부'].sum())
    else:
        n_achieved = int((df_latest['총점'] >= ScoreThresholds.TARGET).sum()) if '총점' in df_latest.columns else 0

    with cols[1 % n_cols]:
        count_big_card(
            label="목표 달성 센터",
            count=n_achieved,
            total=n_total,
            icon="✅",
            color=Colors.SUCCESS,
            suffix="개",
        )

    # 3) 위험 센터 수 (850점 미만)
    if '총점' in df_latest.columns:
        n_danger = int((df_latest['총점'] < ScoreThresholds.ALERT_MIN).sum())
    else:
        n_danger = 0

    with cols[2 % n_cols]:
        count_big_card(
            label="위험 센터 (850점 미만)",
            count=n_danger,
            total=n_total,
            icon="🚨",
            color=Colors.DANGER if n_danger > 0 else Colors.SUCCESS,
            suffix="개",
        )

    # 4) 최고 - 최저 점수 차이
    if '총점' in df_latest.columns and len(df_latest) > 0:
        max_s = df_latest['총점'].max()
        min_s = df_latest['총점'].min()
        gap = max_s - min_s
    else:
        gap = 0

    with cols[3 % n_cols]:
        big_metric_card(
            label="최고-최저 격차",
            value=f"{gap:,.1f}점",
            delta=f"최고 {max_s:,.1f} / 최저 {min_s:,.1f}" if '총점' in df_latest.columns else None,
            delta_color="off",
            icon="📏",
        )

    st.markdown("")

    # ==================== 2. 자동 인사이트 박스 ====================
    st.markdown("### 💡 이번 달 주요 인사이트")

    insights = get_all_insights(df, max_count=5)
    if insights:
        _render_insights(insights, device_type)
    else:
        st.info("표시할 인사이트가 없습니다.")

    st.markdown("")

       # ==================== 3. 센터 랭킹 ====================
    st.markdown("### 🏆 센터 랭킹")

    # ----- 3-1) 점수 순위 (Top 5 / Bottom 5) -----
    ranking = get_ranking_data(df_latest, n=5, mode="score")

    if device_type == "mobile":
        ranking_list(
            ranking.get("top", pd.DataFrame()),
            title="🥇 Top 5 우수 센터",
            value_col="총점",
            icon="🥇",
            use_score_color=True,
        )
        st.markdown("")
        ranking_list(
            ranking.get("bottom", pd.DataFrame()),
            title="🔻 Bottom 5 관리 필요 센터",
            value_col="총점",
            ascending=True,
            icon="🔻",
            use_score_color=True,
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            ranking_list(
                ranking.get("top", pd.DataFrame()),
                title="Top 5 우수 센터",
                value_col="총점",
                icon="🥇",
                use_score_color=True,
            )
        with col2:
            ranking_list(
                ranking.get("bottom", pd.DataFrame()),
                title="Bottom 5 관리 필요 센터",
                value_col="총점",
                ascending=True,
                icon="🔻",
                use_score_color=True,
            )

    # ----- 3-2) 전월 대비 변화 (상승 / 하락) -----
    st.markdown("")

    if df_prev is not None and not df_prev.empty:
        st.markdown(f"##### 📊 전월 대비 변화 (vs {prev_month})")

        change_rank = get_change_ranking(df, n=5)

        if device_type == "mobile":
            change_ranking_list(
                change_rank.get("rising", pd.DataFrame()),
                title="📈 상승 Top 5",
                icon="📈",
                ascending=False,
            )
            st.markdown("")
            change_ranking_list(
                change_rank.get("falling", pd.DataFrame()),
                title="📉 하락 Top 5",
                icon="📉",
                ascending=True,
            )
        else:
            col3, col4 = st.columns(2)
            with col3:
                change_ranking_list(
                    change_rank.get("rising", pd.DataFrame()),
                    title="📈 상승 Top 5",
                    icon="📈",
                    ascending=False,
                )
            with col4:
                change_ranking_list(
                    change_rank.get("falling", pd.DataFrame()),
                    title="📉 하락 Top 5",
                    icon="📉",
                    ascending=True,
                )
    else:
        st.info("📅 전월 데이터가 없어 변화 랭킹을 표시할 수 없습니다.")

    st.markdown("")


    # ==================== 4. 분포 + 추이 차트 ====================
    st.markdown("### 📈 분포 및 추이")

    if device_type == "mobile":
        _render_distribution_chart(df_latest)
        st.markdown("")
        _render_trend_chart(df)
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            _render_distribution_chart(df_latest)
        with col_b:
            _render_trend_chart(df)

    st.markdown("")

    # ==================== 5. 빠른 이동 ====================
        # ==================== 5. 빠른 이동 ====================
    st.markdown("### 🚀 빠른 이동")
    st.caption("자주 사용하는 메뉴로 바로 이동하세요.")

    n_cols_nav = 2 if device_type == "mobile" else 4
    quick_nav_buttons(QUICK_NAV_ITEMS, columns=n_cols_nav)



# ==================== 헬퍼 함수들 ====================

def _get_latest_and_prev(df: pd.DataFrame):
    """최신 월과 전월 데이터프레임, 월 라벨 반환"""
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


def _render_period_header(df: pd.DataFrame, latest_month: str):
    """현재 평가월/반기 진행률 헤더"""
    try:
        # latest_month가 "2026년 05월" 형식
        month_num = int(latest_month.split("년")[1].replace("월", "").strip())
        if month_num <= 6:
            half = "상반기"
            progress = month_num / 6 * 100
            target_text = "6월 누적"
        else:
            half = "하반기"
            progress = (month_num - 6) / 6 * 100
            target_text = "12월 누적"

        n_centers = len(safe_unique_centers(df))

        html = f"""
        <div style="
            background: {Colors.PRIMARY_LIGHT};
            border-left: 4px solid {Colors.PRIMARY};
            padding: 12px 18px;
            border-radius: 8px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        ">
            <div>
                <span style="color:{Colors.TEXT_SUB}; font-size:13px;">현재 평가월</span>
                <span style="color:{Colors.PRIMARY}; font-size:18px; font-weight:700; margin-left:8px;">
                    {latest_month}
                </span>
                <span style="color:{Colors.TEXT_SUB}; font-size:13px; margin-left:12px;">
                    · {half} 진행률 <b style="color:{Colors.TEXT_MAIN};">{progress:.0f}%</b>
                </span>
                <span style="color:{Colors.TEXT_SUB}; font-size:13px; margin-left:12px;">
                    · 대상 센터 <b style="color:{Colors.TEXT_MAIN};">{n_centers}개</b>
                </span>
            </div>
            <div style="color:{Colors.TEXT_SUB}; font-size:12px;">
                🎯 목표: {ScoreThresholds.TARGET}점 ({target_text})
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        st.caption(f"📅 현재 평가월: {latest_month}")


def _render_insights(insights, device_type: str):
    """인사이트 박스 렌더링 (카테고리별 색상)"""
    category_colors = {
        "success": Colors.SUCCESS,
        "warning": Colors.WARNING,
        "danger": Colors.DANGER,
        "info": Colors.PRIMARY,
    }

    n_cols = 1 if device_type == "mobile" else 2
    cols = st.columns(n_cols)

    for idx, ins in enumerate(insights):
        color = category_colors.get(ins.category, Colors.PRIMARY)
        col = cols[idx % n_cols]
        with col:
            html = f"""
            <div style="
                background: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-left: 4px solid {color};
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 10px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            ">
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                    <span style="font-size:18px;">{ins.icon}</span>
                    <span style="color:{color}; font-size:14px; font-weight:700;">{ins.title}</span>
                </div>
                <div style="color:{Colors.TEXT_MAIN}; font-size:14px; line-height:1.5;">
                    {ins.message}
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)


def _render_distribution_chart(df_latest: pd.DataFrame):
    """점수 구간별 분포 (등급별 도넛)"""
    if df_latest is None or df_latest.empty or '총점' not in df_latest.columns:
        st.info("분포 데이터가 없습니다.")
        return

    scores = df_latest['총점'].dropna()
    if scores.empty:
        st.info("점수 데이터가 없습니다.")
        return

    grades = {
        "🟢 달성 (911+)": int((scores >= ScoreThresholds.SUCCESS_MIN).sum()),
        "🟡 주의 (881~910)": int(((scores >= ScoreThresholds.WARNING_MIN) & (scores < ScoreThresholds.SUCCESS_MIN)).sum()),
        "🟠 경고 (851~880)": int(((scores >= ScoreThresholds.ALERT_MIN) & (scores < ScoreThresholds.WARNING_MIN)).sum()),
        "🔴 위험 (~850)": int((scores < ScoreThresholds.ALERT_MIN).sum()),
    }

    colors = [Colors.SUCCESS, Colors.WARNING, Colors.ALERT, Colors.DANGER]

    fig = go.Figure(data=[go.Pie(
        labels=list(grades.keys()),
        values=list(grades.values()),
        hole=0.55,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textinfo="value",
        textfont=dict(size=14, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value}개 (%{percent})<extra></extra>",
    )])

    total = sum(grades.values())
    fig.update_layout(
        title=dict(text=f"<b>점수 구간 분포</b> (총 {total}개)", font=dict(size=15)),
        height=320,
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=12)),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_trend_chart(df: pd.DataFrame):
    """월별 전체 평균 추이"""
    if df is None or df.empty or '평가월' not in df.columns or '총점' not in df.columns:
        st.info("추이 데이터가 없습니다.")
        return

    df_clean = df.dropna(subset=['평가월', '총점']).copy()
    if df_clean.empty:
        st.info("추이 데이터가 없습니다.")
        return

    monthly_avg = df_clean.groupby('평가월')['총점'].mean().reset_index().sort_values('평가월')
    monthly_avg['월라벨'] = pd.to_datetime(monthly_avg['평가월']).dt.strftime("%Y-%m")

    fig = go.Figure()

    # 평균 점수 라인
    fig.add_trace(go.Scatter(
        x=monthly_avg['월라벨'],
        y=monthly_avg['총점'],
        mode='lines+markers+text',
        name='전체 평균',
        line=dict(color=Colors.PRIMARY, width=3),
        marker=dict(size=10, color=Colors.PRIMARY),
        text=[f"{v:.1f}" for v in monthly_avg['총점']],
        textposition="top center",
        textfont=dict(size=11, color=Colors.TEXT_MAIN),
        hovertemplate="<b>%{x}</b><br>평균 %{y:.1f}점<extra></extra>",
    ))

    # 목표선
    fig.add_hline(
        y=ScoreThresholds.TARGET,
        line_dash="dash",
        line_color=Colors.WARNING,
        annotation_text=f"목표 {ScoreThresholds.TARGET}",
        annotation_position="right",
    )

    fig.update_layout(
        title=dict(text="<b>전체 평균 점수 추이</b>", font=dict(size=15)),
        height=320,
        margin=dict(t=50, b=40, l=40, r=40),
        showlegend=False,
        xaxis=dict(title="", gridcolor=Colors.BORDER),
        yaxis=dict(title="평균 점수", gridcolor=Colors.BORDER),
        **PLOTLY_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)
