"""
🏠 홈 (Executive Dashboard)
- 핵심 KPI + 자동 인사이트 + Top/Bottom 랭킹 + 반기 전망 + 빠른 이동
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
    get_half_outlook,
    get_pace_lag_ranking,  # ⭐ 추가
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

    # 작년 데이터 (선택사항, session_state에 있으면 사용)
    df_last_year = st.session_state.get('df_last_year', None)

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
        max_s = 0
        min_s = 0

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

    insights = get_all_insights(df, max_count=6, df_last_year=df_last_year)
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

        # ----- 3-2) 전월 대비 동향 (상승 모멘텀 + 페이스 미달) -----
    st.markdown("")

    if df_prev is not None and not df_prev.empty:
        st.markdown(f"##### 📊 전월 대비 동향 (vs {prev_month})")

        change_rank = get_change_ranking(df, n=5)
        rising_df = change_rank.get("rising", change_rank.get("up", pd.DataFrame()))

        # 페이스 미달 Top 5 (911점 도달 위험)
        pace_lag_df = get_pace_lag_ranking(df, n=5, df_last_year=df_last_year)

        if device_type == "mobile":
            # 모바일: 세로 배치
            change_ranking_list(
                rising_df,
                title="📈 상승 모멘텀 Top 5",
                icon="📈",
                ascending=False,
            )
            st.markdown("")
            _render_pace_lag_list(pace_lag_df)
        else:
            # 데스크톱: 2열 배치
            col3, col4 = st.columns(2)
            with col3:
                change_ranking_list(
                    rising_df,
                    title="📈 상승 모멘텀 Top 5",
                    icon="📈",
                    ascending=False,
                )
            with col4:
                _render_pace_lag_list(pace_lag_df)
    else:
        st.info("📅 전월 데이터가 없어 변화 분석을 표시할 수 없습니다.")

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

    # ==================== 5. 반기 마감 전망 (신규) ====================
    st.markdown("### 📅 반기 마감 전망")
    _render_half_outlook(df, df_last_year, device_type)

    st.markdown("")

    # ==================== 6. 빠른 이동 ====================
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

        # ⭐ 최신월 데이터로만 센터 수 카운트 (통합 전 사라진 센터 제외)
        df_clean = df.dropna(subset=['평가월']).copy()
        if not df_clean.empty:
            latest_dt = sorted(df_clean['평가월'].unique())[-1]
            df_latest = df_clean[df_clean['평가월'] == latest_dt]
            n_centers = len(safe_unique_centers(df_latest))
        else:
            n_centers = 0

        html = (
            f'<div style="background:{Colors.PRIMARY_LIGHT};'
            f'border-left:4px solid {Colors.PRIMARY};'
            f'padding:12px 18px;border-radius:8px;margin-bottom:16px;'
            f'display:flex;justify-content:space-between;align-items:center;'
            f'flex-wrap:wrap;gap:12px;">'
            f'<div>'
            f'<span style="color:{Colors.TEXT_SUB};font-size:13px;">현재 평가월</span>'
            f'<span style="color:{Colors.PRIMARY};font-size:18px;font-weight:700;margin-left:8px;">{latest_month}</span>'
            f'<span style="color:{Colors.TEXT_SUB};font-size:13px;margin-left:12px;">'
            f'· {half} 진행률 <b style="color:{Colors.TEXT_MAIN};">{progress:.0f}%</b>'
            f'</span>'
            f'<span style="color:{Colors.TEXT_SUB};font-size:13px;margin-left:12px;">'
            f'· 대상 센터 <b style="color:{Colors.TEXT_MAIN};">{n_centers}개</b>'
            f'</span>'
            f'</div>'
            f'<div style="color:{Colors.TEXT_SUB};font-size:12px;">'
            f'🎯 목표: {ScoreThresholds.TARGET}점 ({target_text})'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    except Exception:
        st.caption(f"📅 현재 평가월: {latest_month}")



def _render_insights(insights, device_type: str):
    """인사이트 박스 렌더링 (카테고리별 색상 + 액션 가이드)"""
    category_colors = {
        "success": Colors.SUCCESS,
        "warning": Colors.WARNING,
        "danger": Colors.DANGER,
        "info": Colors.PRIMARY,
    }

    # hex → rgba 변환 (배경 반투명용)
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

        # 액션 가이드 영역 (action 필드가 있을 때만)
        action_html = ""
        action = getattr(ins, 'action', None)
        if action:
            action_bg = _to_rgba(color, 0.08)
            action_html = (
                f'<div style="background:{action_bg};'
                f'border-radius:6px;padding:8px 12px;margin-top:10px;'
                f'border-left:3px solid {color};">'
                f'<div style="color:{color};font-size:12px;font-weight:700;'
                f'margin-bottom:3px;">💡 권장 액션</div>'
                f'<div style="color:{Colors.TEXT_MAIN};font-size:13px;'
                f'line-height:1.5;">{action}</div>'
                f'</div>'
            )

        with col:
            # ⚠️ HTML을 한 줄로 압축 (마크다운 코드블록 회피)
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
                f'{ins.message}'
                f'</div>'
                f'{action_html}'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)

def _render_pace_lag_list(pace_lag_df: pd.DataFrame):
    """페이스 미달 Top 5 (911점 도달 위험 센터) 렌더링"""
    title = "⚠️ 페이스 미달 Top 5"
    
    if pace_lag_df is None or pace_lag_df.empty:
        # 위험 센터가 없으면 긍정 메시지
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

        # 순위 배지 (1~3위는 메달, 나머지는 숫자)
        if i == 1:
            badge = "🥇"
        elif i == 2:
            badge = "🥈"
        elif i == 3:
            badge = "🥉"
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


# home.py 내 _render_half_outlook 함수 전체 교체

def _render_half_outlook(df: pd.DataFrame, df_last_year, device_type: str):
    """반기 마감 전망 / 반기 최종 결과 섹션"""
    from utils.insights_v2 import _safe_latest_month, _is_half_end, _get_half, _to_month_int
    
    latest_month = _safe_latest_month(df)
    is_final = _is_half_end(latest_month) if latest_month is not None else False
    half_label = _get_half(_to_month_int(latest_month)) if latest_month is not None else ""
    
    try:
        outlook = get_half_outlook(df, df_last_year=df_last_year)
    except Exception as e:
        st.warning(f"반기 전망 계산 중 오류: {e}")
        return

    if outlook is None or outlook.empty:
        st.info("반기 데이터를 계산할 수 없습니다.")
        return

    # ⭐ 반기 마지막 달: 최종 결과 카드 (달성/근접미달/미달)
    if is_final:
        achieved_cnt = int((outlook['안전도'] == '달성').sum())
        near_cnt = int((outlook['안전도'] == '근접미달').sum())
        fail_cnt = int((outlook['안전도'] == '미달').sum())
        total_cnt = len(outlook)

        n_cols = 1 if device_type == "mobile" else 3
        cols = st.columns(n_cols)

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
                    f'{card["label"]}</div>'
                    f'<div style="color:{Colors.TEXT_SUB};font-size:11px;margin-bottom:6px;">'
                    f'{card["sublabel"]}</div>'
                    f'<div style="font-size:32px;font-weight:700;color:{card["color"]};line-height:1.1;">'
                    f'{card["count"]}<span style="font-size:16px;font-weight:500;'
                    f'color:{Colors.TEXT_SUB};margin-left:4px;">/ {total_cnt}개</span>'
                    f'</div>'
                    f'</div>'
                )
                st.markdown(html, unsafe_allow_html=True)

        st.markdown("")

        # 최종 결과 상세 표
        with st.expander(f"📋 센터별 {half_label} 최종 결과 상세 보기", expanded=False):
            display_cols = ['센터명', '현재점수', '목표차이', '안전도', '통합여부']
            if '작년참고' in outlook.columns and outlook['작년참고'].notna().any():
                display_cols.insert(3, '작년참고')
            if '현재감점' in outlook.columns and (outlook['현재감점'].fillna(0) != 0).any():
                display_cols.append('현재감점')

            safety_order = {'미달': 0, '근접미달': 1, '달성': 2}
            outlook_sorted = outlook.copy()
            outlook_sorted['_sort'] = outlook_sorted['안전도'].map(safety_order).fillna(99)
            outlook_sorted = outlook_sorted.sort_values(['_sort', '현재점수'], ascending=[True, True])

            column_config = {
                '현재점수': st.column_config.NumberColumn(
                    f"{half_label} 최종점수", format="%.1f점"
                ),
                '목표차이': st.column_config.NumberColumn(
                    format="%+.1f점", help="911점 - 최종점수"
                ),
            }
            if '작년참고' in display_cols:
                column_config['작년참고'] = st.column_config.NumberColumn(
                    format="%.1f점",
                    help="작년 동기 점수 (구조 변경으로 참고용)"
                )

            st.dataframe(
                outlook_sorted[display_cols],
                use_container_width=True,
                hide_index=True,
                column_config=column_config,
            )

            st.caption(
                f"💡 **{half_label} 최종 결과 확정** — "
                f"다음 반기는 0점부터 새로 시작됩니다. "
                f"작년참고는 구조 변경(안전점검 600→550점, 사용계약 신설)으로 직접 비교 부적합."
            )
        return

    # ⭐ 진행 중: 기존 예측 전망 로직 유지
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
                f'{card["label"]}</div>'
                f'<div style="color:{Colors.TEXT_SUB};font-size:11px;margin-bottom:6px;">'
                f'{card["sublabel"]}</div>'
                f'<div style="font-size:32px;font-weight:700;color:{card["color"]};line-height:1.1;">'
                f'{card["count"]}<span style="font-size:16px;font-weight:500;'
                f'color:{Colors.TEXT_SUB};margin-left:4px;">/ {total_cnt}개</span>'
                f'</div>'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)

    st.markdown("")

    with st.expander("📋 센터별 반기 전망 상세 보기", expanded=False):
        display_cols = ['센터명', '현재점수', '낙관전망', '현실전망', '목표차이', '안전도', '통합여부']
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
                help="최근 3개월 평균 페이스 유지 시 예상 반기 최종 점수"
            ),
            '목표차이': st.column_config.NumberColumn(
                format="%+.1f점", help="911점 - 현실전망"
            ),
        }
        if '작년참고' in display_cols:
            column_config['작년참고'] = st.column_config.NumberColumn(
                format="%.1f점",
                help="작년 동기 점수 (구조 변경 참고용)"
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
            "💡 **현실 전망**: 최근 3개월 평균 증가 페이스 유지 시 예상 점수 / "
            "**낙관 전망**: 911점 목표 페이스 달성 시 예상 점수 / "
            "**작년참고**: 참고용 / "
            "**통합**: 4월 통합된 센터는 작년 직접 비교 제외"
        )
