"""
============================================================
🌡️ KPI 히트맵 모듈
파일명: kpi_heatmap.py

3가지 히트맵 뷰를 제공합니다:
  Tab 1 - 센터 × KPI 달성률  (최신월 기준)
  Tab 2 - 센터 × 월별 총점   (전체 월 추이)
  Tab 3 - 월별 KPI 평균       (전체 센터 평균)

🎨 v2.0 - 디자인 시스템 통합 (utils/styles.py 기준)
============================================================
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from utils.styles import (
    Colors,
    ScoreThresholds,
    PLOTLY_LAYOUT,
    HEATMAP_COLORSCALE as STYLES_HEATMAP_COLORSCALE,
)


# ──────────────────────────────────────────────
# 상수 정의
# ──────────────────────────────────────────────

KPI_CONFIG = {
    '안전점검': {
        'score_col':  '안전점검_점수',
        'rate_col':   '안전점검_달성률',
        'max_score':  550,
        'weight_pct': 55.0,
        'icon':       '🔵',
    },
    '중점고객': {
        'score_col':  '중점고객_점수',
        'rate_col':   '중점고객_달성률',
        'max_score':  100,
        'weight_pct': 10.0,
        'icon':       '🟢',
    },
    '사용계약': {
        'score_col':  '사용계약_점수',
        'rate_col':   '사용계약_달성률',
        'max_score':  50,
        'weight_pct': 5.0,
        'icon':       '🟡',
    },
    '상담응대': {
        'score_col':  '상담응대_점수',
        'rate_col':   '상담응대_달성률',
        'max_score':  100,
        'weight_pct': 10.0,
        'icon':       '🟠',
    },
    '상담기여': {
        'score_col':  '상담기여_점수',
        'rate_col':   '상담기여_달성률',
        'max_score':  100,
        'weight_pct': 10.0,
        'icon':       '🔴',
    },
    '만족도': {
        'score_col':  '만족도_점수',
        'rate_col':   '만족도_달성률',
        'max_score':  100,
        'weight_pct': 10.0,
        'icon':       '🟣',
    },
}

# 목표 점수 (styles.py 기준)
TARGET_SCORE = ScoreThresholds.TARGET

# 달성률 색상 기준 (%)
GRADE_THRESHOLDS = {
    'S': 95,
    'A': 90,
    'B': 85,
    'C': 75,
    'D': 0,
}

# 🎨 디자인 시스템 색상 사용
HEATMAP_COLORSCALE = STYLES_HEATMAP_COLORSCALE

# 등급별 색상 (Colors 상수 활용)
GRADE_COLOR_MAP = {
    'S': Colors.SUCCESS,    # 진초록
    'A': "#84cc16",         # 연두 (styles.py의 중간색)
    'B': Colors.WARNING,    # 노랑
    'C': Colors.ALERT,      # 주황
    'D': Colors.DANGER,     # 빨강
}


# ──────────────────────────────────────────────
# 헬퍼 함수
# ──────────────────────────────────────────────

def _ensure_rate_cols(df: pd.DataFrame) -> pd.DataFrame:
    """달성률 컬럼이 없으면 자동 계산"""
    df = df.copy()
    for kpi, cfg in KPI_CONFIG.items():
        if cfg['rate_col'] not in df.columns and cfg['score_col'] in df.columns:
            df[cfg['rate_col']] = (df[cfg['score_col']] / cfg['max_score'] * 100).round(1)
    return df


def _get_grade(rate: float) -> str:
    """달성률 → 등급 문자 반환"""
    if rate >= GRADE_THRESHOLDS['S']:
        return 'S'
    elif rate >= GRADE_THRESHOLDS['A']:
        return 'A'
    elif rate >= GRADE_THRESHOLDS['B']:
        return 'B'
    elif rate >= GRADE_THRESHOLDS['C']:
        return 'C'
    else:
        return 'D'


def _grade_color(grade: str) -> str:
    """등급 → 색상 (디자인 시스템 기준)"""
    return GRADE_COLOR_MAP.get(grade, Colors.REFERENCE)


def _grade_badge(grade: str) -> str:
    badges = {
        'S': '🏆 S등급',
        'A': '🥇 A등급',
        'B': '🥈 B등급',
        'C': '🥉 C등급',
        'D': '⛔ D등급',
    }
    return badges.get(grade, grade)


def _hex_to_rgba(hex_color: str, alpha: float = 0.2) -> str:
    """hex 색상 → rgba 변환 (Plotly·CSS 안전)"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ──────────────────────────────────────────────
# Tab 1 : 센터 × KPI 달성률 히트맵
# ──────────────────────────────────────────────

def _show_center_kpi_heatmap(df: pd.DataFrame, selected_month=None):
    """센터(행) × KPI(열) 달성률 히트맵"""

    df = _ensure_rate_cols(df)

    all_months = sorted(df['평가월'].unique())
    month_labels = [m.strftime('%Y년 %m월') for m in all_months]

    if selected_month is None:
        selected_month = all_months[-1]

    selected_label = selected_month.strftime('%Y년 %m월')

    col_filter, col_info = st.columns([2, 1])
    with col_filter:
        chosen_label = st.selectbox(
            "📅 분석 기준 월",
            options=month_labels,
            index=month_labels.index(selected_label),
            key="heatmap_tab1_month"
        )
    chosen_month = all_months[month_labels.index(chosen_label)]

    with col_info:
        sort_by = st.selectbox(
            "🔽 센터 정렬 기준",
            options=['총점 높은 순', '총점 낮은 순', '센터명 순'],
            key="heatmap_tab1_sort"
        )

    df_month = df[df['평가월'] == chosen_month].copy()

    if df_month.empty:
        st.warning("해당 월의 데이터가 없습니다.")
        return

    if sort_by == '총점 높은 순':
        df_month = df_month.sort_values('총점', ascending=False)
    elif sort_by == '총점 낮은 순':
        df_month = df_month.sort_values('총점', ascending=True)
    else:
        df_month = df_month.sort_values('센터명')

    centers = df_month['센터명'].tolist()
    kpi_names = list(KPI_CONFIG.keys())

    z_vals, text_vals = [], []
    for _, row in df_month.iterrows():
        z_row, t_row = [], []
        for kpi in kpi_names:
            cfg = KPI_CONFIG[kpi]
            rate = row.get(cfg['rate_col'], 0)
            if pd.isna(rate):
                rate = 0.0
            grade = _get_grade(rate)
            z_row.append(round(rate, 1))
            t_row.append(f"{rate:.1f}%<br>{grade}등급")
        z_vals.append(z_row)
        text_vals.append(t_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=[f"{cfg['icon']} {k}<br>({cfg['max_score']}점)" for k, cfg in KPI_CONFIG.items()],
        y=centers,
        text=text_vals,
        texttemplate="%{text}",
        textfont={"size": 11, "color": Colors.TEXT_MAIN},
        colorscale=HEATMAP_COLORSCALE,
        zmin=0,
        zmax=100,
        colorbar=dict(
            title="달성률(%)",
            tickvals=[0, 25, 50, 75, 85, 95, 100],
            ticktext=["0%", "25%", "50%", "75%<br>C기준", "85%<br>B기준", "95%<br>S기준", "100%"],
            len=0.8,
        ),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "지표: %{x}<br>"
            "달성률: %{z:.1f}%<extra></extra>"
        ),
    ))

    n_centers = len(centers)
    chart_height = max(500, n_centers * 38 + 120)

    fig.update_layout(
        title=dict(
            text=f"📊 센터 × KPI 달성률 히트맵 ({chosen_label})",
            font=dict(size=18, color=Colors.TEXT_MAIN),
            x=0.5,
        ),
        xaxis=dict(side='top', tickfont=dict(size=12)),
        yaxis=dict(autorange='reversed', tickfont=dict(size=11)),
        height=chart_height,
        margin=dict(l=120, r=80, t=100, b=40),
        **PLOTLY_LAYOUT,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── 요약 지표 카드 ──
    st.markdown("#### 📌 KPI별 전체 센터 평균 달성률")
    cols = st.columns(len(KPI_CONFIG))
    for i, (kpi, cfg) in enumerate(KPI_CONFIG.items()):
        avg_rate = df_month[cfg['rate_col']].mean()
        grade = _get_grade(avg_rate)
        with cols[i]:
            st.metric(
                label=f"{cfg['icon']} {kpi}",
                value=f"{avg_rate:.1f}%",
                delta=f"{_grade_badge(grade)}",
            )

    st.divider()

    # ── 취약 KPI 센터 요약 ──
    st.markdown("#### ⚠️ KPI별 취약 센터 (달성률 80% 미만)")
    weak_rows = []
    for kpi, cfg in KPI_CONFIG.items():
        weak = df_month[df_month[cfg['rate_col']] < 80][['센터명', cfg['rate_col'], '총점']].copy()
        for _, row in weak.iterrows():
            weak_rows.append({
                '센터명': row['센터명'],
                '취약 KPI': f"{cfg['icon']} {kpi}",
                '달성률': f"{row[cfg['rate_col']]:.1f}%",
                '총점': f"{row['총점']:.1f}점",
            })

    if weak_rows:
        df_weak = pd.DataFrame(weak_rows).sort_values('센터명')
        st.dataframe(
            df_weak,
            use_container_width=True,
            hide_index=True,
            height=min(400, len(df_weak) * 38 + 40)
        )
    else:
        st.success("✅ 모든 센터·KPI가 80% 이상 달성 중입니다!")


# ──────────────────────────────────────────────
# Tab 2 : 센터 × 월별 총점 히트맵
# ──────────────────────────────────────────────

def _show_monthly_score_heatmap(df: pd.DataFrame):
    """센터(행) × 월(열) 총점 히트맵"""

    all_months_raw = sorted(df['평가월'].unique())
    month_labels = [m.strftime('%m월') for m in all_months_raw]

    col_a, col_b = st.columns([2, 1])
    with col_a:
        view_mode = st.radio(
            "표시 방식",
            options=["점수 (절대값)", "달성률 (%)"],
            horizontal=True,
            key="heatmap_tab2_mode"
        )
    with col_b:
        sort_by2 = st.selectbox(
            "센터 정렬",
            options=['최신월 총점 높은 순', '최신월 총점 낮은 순', '센터명 순'],
            key="heatmap_tab2_sort"
        )

    pivot = df.pivot_table(
        index='센터명',
        columns='평가월',
        values='총점',
        aggfunc='mean'
    )
    pivot.columns = [c.strftime('%m월') for c in pivot.columns]

    latest_col = month_labels[-1]
    if sort_by2 == '최신월 총점 높은 순' and latest_col in pivot.columns:
        pivot = pivot.sort_values(latest_col, ascending=False)
    elif sort_by2 == '최신월 총점 낮은 순' and latest_col in pivot.columns:
        pivot = pivot.sort_values(latest_col, ascending=True)
    else:
        pivot = pivot.sort_index()

    centers = pivot.index.tolist()
    months_display = pivot.columns.tolist()

    if view_mode == "달성률 (%)":
        z_data = (pivot.values / TARGET_SCORE * 100).round(1)
        zmin, zmax = 80, 110
        colorbar_title = "달성률(%)"
        fmt = ".1f"
        unit = "%"
    else:
        z_data = pivot.values.round(1)
        zmin, zmax = 800, 1000
        colorbar_title = "총점(점)"
        fmt = ".0f"
        unit = "점"

    text_data = []
    for row_vals in z_data:
        text_row = []
        for v in row_vals:
            if np.isnan(v):
                text_row.append("-")
            else:
                text_row.append(f"{v:{fmt}}{unit}")
        text_data.append(text_row)

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=months_display,
        y=centers,
        text=text_data,
        texttemplate="%{text}",
        textfont={"size": 11, "color": Colors.TEXT_MAIN},
        colorscale=HEATMAP_COLORSCALE,
        zmin=zmin,
        zmax=zmax,
        colorbar=dict(title=colorbar_title, len=0.8),
        hovertemplate=(
            "<b>%{y}</b> | %{x}<br>"
            f"{colorbar_title}: %{{z:{fmt}}}{unit}<extra></extra>"
        ),
    ))

    n_centers = len(centers)
    chart_height = max(500, n_centers * 35 + 140)

    fig.update_layout(
        title=dict(
            text=f"📈 센터별 월별 총점 히트맵 (목표: {TARGET_SCORE}점)",
            font=dict(size=18, color=Colors.TEXT_MAIN),
            x=0.5,
        ),
        xaxis=dict(side='top', tickfont=dict(size=12)),
        yaxis=dict(autorange='reversed', tickfont=dict(size=11)),
        height=chart_height,
        margin=dict(l=120, r=80, t=100, b=40),
        annotations=[
            dict(
                text=f"🎯 목표: {TARGET_SCORE}점 기준 색상 구분 | 🟢 초록=우수 / 🟡 노랑=주의 / 🔴 빨강=위험",
                xref="paper", yref="paper",
                x=0.5, y=-0.04,
                showarrow=False,
                font=dict(size=11, color=Colors.TEXT_SUB),
                align='center',
            )
        ],
        **PLOTLY_LAYOUT,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── 월별 통계 요약 ──
    st.markdown("#### 📊 월별 전체 센터 통계")
    monthly_stats = df.groupby('평가월')['총점'].agg(
        평균='mean', 최고='max', 최저='min',
        목표달성수=lambda x: (x >= TARGET_SCORE).sum()
    ).reset_index()
    monthly_stats['평가월'] = monthly_stats['평가월'].dt.strftime('%Y년 %m월')
    monthly_stats['달성률(%)'] = (monthly_stats['목표달성수'] / df['센터명'].nunique() * 100).round(1)
    monthly_stats[['평균', '최고', '최저']] = monthly_stats[['평균', '최고', '최저']].round(1)

    st.dataframe(
        monthly_stats.rename(columns={
            '평가월': '월',
            '평균': '평균점수',
            '최고': '최고점수',
            '최저': '최저점수',
        }),
        use_container_width=True,
        hide_index=True,
    )


# ──────────────────────────────────────────────
# Tab 3 : 월별 × KPI 평균 히트맵
# ──────────────────────────────────────────────

def _show_monthly_kpi_avg_heatmap(df: pd.DataFrame):
    """월(행) × KPI(열) 전체 센터 평균 달성률 히트맵"""

    df = _ensure_rate_cols(df)

    kpi_names = list(KPI_CONFIG.keys())
    rate_cols = [KPI_CONFIG[k]['rate_col'] for k in kpi_names]
    available_rate_cols = [c for c in rate_cols if c in df.columns]
    available_kpi_names = [kpi_names[rate_cols.index(c)] for c in available_rate_cols]

    monthly_avg = df.groupby('평가월')[available_rate_cols].mean().round(1)
    monthly_avg.index = monthly_avg.index.strftime('%m월')
    monthly_avg.columns = available_kpi_names

    months_order = monthly_avg.index.tolist()
    kpi_order = monthly_avg.columns.tolist()

    z_vals = monthly_avg.values.tolist()
    text_vals = [
        [f"{v:.1f}%<br>{_get_grade(v)}등급" for v in row]
        for row in monthly_avg.values
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_vals,
        x=[f"{KPI_CONFIG[k]['icon']} {k}" for k in kpi_order],
        y=months_order,
        text=text_vals,
        texttemplate="%{text}",
        textfont={"size": 12, "color": Colors.TEXT_MAIN},
        colorscale=HEATMAP_COLORSCALE,
        zmin=0,
        zmax=100,
        colorbar=dict(
            title="평균 달성률(%)",
            tickvals=[0, 50, 75, 85, 95, 100],
            ticktext=["0%", "50%", "75%", "85%", "95%", "100%"],
            len=0.8,
        ),
        hovertemplate=(
            "<b>%{y}</b> | %{x}<br>"
            "평균 달성률: %{z:.1f}%<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=dict(
            text="📅 월별 KPI 평균 달성률 히트맵 (전체 센터 평균)",
            font=dict(size=18, color=Colors.TEXT_MAIN),
            x=0.5,
        ),
        xaxis=dict(side='top', tickfont=dict(size=13)),
        yaxis=dict(autorange='reversed', tickfont=dict(size=12)),
        height=max(350, len(months_order) * 60 + 160),
        margin=dict(l=80, r=80, t=100, b=80),
        **PLOTLY_LAYOUT,
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── KPI별 월간 추이 선 그래프 ──
    st.markdown("#### 📈 KPI별 월간 달성률 추이 (전체 센터 평균)")

    col_sel, _ = st.columns([2, 3])
    with col_sel:
        selected_kpis = st.multiselect(
            "표시할 KPI 선택",
            options=kpi_order,
            default=kpi_order,
            key="heatmap_tab3_kpi_select"
        )

    if selected_kpis:
        fig2 = go.Figure()
        # 디자인 시스템의 colorway 사용
        line_colors = PLOTLY_LAYOUT.get('colorway', [Colors.PRIMARY])

        for i, kpi in enumerate(selected_kpis):
            cfg = KPI_CONFIG[kpi]
            if cfg['rate_col'] in df.columns:
                trend = df.groupby('평가월')[cfg['rate_col']].mean().reset_index()
                trend['평가월_label'] = trend['평가월'].dt.strftime('%m월')
                fig2.add_trace(go.Scatter(
                    x=trend['평가월_label'],
                    y=trend[cfg['rate_col']].round(1),
                    mode='lines+markers',
                    name=f"{cfg['icon']} {kpi}",
                    line=dict(color=line_colors[i % len(line_colors)], width=2.5),
                    marker=dict(size=8),
                    hovertemplate=f"<b>{kpi}</b><br>%{{x}} | 평균 %{{y:.1f}}%<extra></extra>"
                ))

        # 등급 기준선 (디자인 시스템 색상)
        fig2.add_hline(
            y=85, line_dash="dash", line_color=Colors.WARNING, line_width=1.5,
            annotation_text="B등급 기준 (85%)", annotation_position="right"
        )
        fig2.add_hline(
            y=95, line_dash="dot", line_color=Colors.SUCCESS, line_width=1.5,
            annotation_text="S등급 기준 (95%)", annotation_position="right"
        )

        fig2.update_layout(
            height=400,
            yaxis=dict(title="달성률 (%)", range=[40, 105], gridcolor=Colors.BORDER),
            xaxis=dict(title="평가월", gridcolor=Colors.BORDER),
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
            **PLOTLY_LAYOUT,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── KPI별 등급 분포 표 ──
    st.markdown("#### 🏅 KPI별 등급 분포 요약")
    grade_rows = []
    latest_month = df['평가월'].max()
    df_latest = df[df['평가월'] == latest_month].copy()
    df_latest = _ensure_rate_cols(df_latest)

    for kpi, cfg in KPI_CONFIG.items():
        if cfg['rate_col'] not in df_latest.columns:
            continue
        rates = df_latest[cfg['rate_col']].dropna()
        grade_counts = {'KPI': f"{cfg['icon']} {kpi}"}
        for grade in ['S', 'A', 'B', 'C', 'D']:
            lo = GRADE_THRESHOLDS.get(grade, 0)
            if grade == 'S':
                cnt = (rates >= lo).sum()
            elif grade == 'D':
                hi = GRADE_THRESHOLDS['C']
                cnt = (rates < hi).sum()
            else:
                grades_order = ['S', 'A', 'B', 'C', 'D']
                idx = grades_order.index(grade)
                hi = GRADE_THRESHOLDS[grades_order[idx - 1]]
                cnt = ((rates >= lo) & (rates < hi)).sum()
            grade_counts[f'{grade}등급'] = int(cnt)
        grade_counts['평균'] = f"{rates.mean():.1f}%"
        grade_rows.append(grade_counts)

    if grade_rows:
        st.dataframe(
            pd.DataFrame(grade_rows),
            use_container_width=True,
            hide_index=True
        )


# ──────────────────────────────────────────────
# 메인 진입점
# ──────────────────────────────────────────────

def show_kpi_heatmap(df: pd.DataFrame):
    """
    🌡️ KPI 히트맵 메인 함수
    app.py의 메인 라우터에서 호출합니다.
    """
    try:
        # ── 헤더 (디자인 시스템 파랑 톤) ──
        header_html = (
            f'<div style="background:{Colors.GRADIENT_PRIMARY};'
            f'padding:1.2rem 1.5rem;border-radius:12px;color:white;'
            f'margin-bottom:1.5rem;box-shadow:0 4px 12px rgba(37,99,235,0.15);">'
            f'<h2 style="margin:0;font-size:1.6rem;">🌡️ KPI 성과 히트맵</h2>'
            f'<p style="margin:0.3rem 0 0;opacity:0.88;font-size:0.95rem;">'
            f'센터별·KPI별 달성률을 색상으로 한눈에 파악합니다</p>'
            f'</div>'
        )
        st.markdown(header_html, unsafe_allow_html=True)

        # ── 필수 컬럼 검증 ──
        required = ['센터명', '평가월', '총점']
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"❌ 필수 컬럼 누락: {missing}")
            return

        df = _ensure_rate_cols(df)

        # ── 범례 카드 (디자인 시스템 색상) ──
        with st.expander("🎨 색상 범례 보기", expanded=False):
            legend_cols = st.columns(5)
            legends = [
                ("🏆 S등급", "95%~100%", GRADE_COLOR_MAP['S']),
                ("🥇 A등급", "90%~95%",  GRADE_COLOR_MAP['A']),
                ("🥈 B등급", "85%~90%",  GRADE_COLOR_MAP['B']),
                ("🥉 C등급", "75%~85%",  GRADE_COLOR_MAP['C']),
                ("⛔ D등급", "0%~75%",   GRADE_COLOR_MAP['D']),
            ]
            for col, (title, rng, color) in zip(legend_cols, legends):
                bg = _hex_to_rgba(color, 0.15)
                legend_html = (
                    f'<div style="background:{bg};border-left:4px solid {color};'
                    f'padding:8px 10px;border-radius:6px;font-size:0.85rem;'
                    f'color:{Colors.TEXT_MAIN};">'
                    f'<b>{title}</b><br>{rng}</div>'
                )
                col.markdown(legend_html, unsafe_allow_html=True)

        st.markdown("")

        # ── 탭 레이아웃 ──
        tab1, tab2, tab3 = st.tabs([
            "📊 센터 × KPI 달성률",
            "📈 센터 × 월별 총점",
            "📅 월별 KPI 평균",
        ])

        with tab1:
            st.caption("각 센터(행)의 KPI별(열) 달성률을 색상으로 표시합니다. 특정 센터의 강점·약점 KPI를 즉시 파악하세요.")
            _show_center_kpi_heatmap(df)

        with tab2:
            st.caption("각 센터(행)의 월별(열) 총점 변화를 추적합니다. 성과가 오르거나 떨어지는 시점을 색상으로 확인하세요.")
            _show_monthly_score_heatmap(df)

        with tab3:
            st.caption("전체 센터 평균 기준으로 월별 KPI 달성률 흐름을 보여줍니다. 시스템 전체의 약한 지표를 발견할 수 있습니다.")
            _show_monthly_kpi_avg_heatmap(df)

    except Exception as e:
        st.error(f"❌ KPI 히트맵 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
