"""
상반기 보고 페이지 (v1.1)
- 2026년 상반기 평가 결과 요약
- 전년(2025년) 하반기/연간 대비 비교 (달성률 기준)
- 통합센터(퇴계원/별내) 및 권역조정 센터(구리) 안내
"""

import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.styles import Colors, ScoreThresholds

# =========================================================
# 상수
# =========================================================

# 2026년 KPI 배점 (총 1000점)
KPI_MAX_THIS_YEAR = {
    '안전점검': 550,
    '중점고객': 100,
    '사용계약': 50,
    '상담응대': 100,
    '상담기여': 100,
    '만족도': 100,
}

# 2025년 KPI 배점 (총 1000점, 사용계약 없음)
KPI_MAX_LAST_YEAR = {
    '안전점검': 600,
    '중점고객': 100,
    '상담응대': 100,
    '상담기여': 100,
    '만족도': 100,
}

# KPI명 → 데이터프레임 점수 컬럼 매핑
KPI_SCORE_COLS = {
    '안전점검': '안전점검_점수',
    '중점고객': '중점고객_점수',
    '사용계약': '사용계약_점수',
    '상담응대': '상담응대_점수',
    '상담기여': '상담기여_점수',
    '만족도': '만족도_점수',
}

# 통합센터 (2026년 상·하반기 모두 유예, 단 결과는 참고로 표시)
INTEGRATED_CENTERS_THIS_YEAR = {'퇴계원/별내', '별내/퇴계원'}

# 전년(2025년) 통합센터 (2025년 유예 → YoY 비교에서 제외)
INTEGRATED_CENTERS_LAST_YEAR = {
    '금곡/경기동부', '경기동부/금곡',
    '덕소/양평', '양평/덕소',
}

# 권역조정 센터 (안전점검은 기존 관리세대 기준으로 평가)
ADJUSTED_CENTERS = {
    '구리': '2026년 4월 권역조정으로 행정동 흡수, 상·하반기 모두 안전점검은 기존 관리세대 기준으로 평가',
}

TARGET_SCORE = 911
PERFECT_SCORE = 1000
NEAR_MISS_MIN = 895


# =========================================================
# 메인
# =========================================================

def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """상반기 보고 페이지 메인"""

    st.markdown("## 📑 상반기 평가 결과 보고")
    st.caption("2026년 상반기(1~6월) 고객센터 평가 결과 요약 리포트")
    st.markdown("---")

    if df is None or df.empty:
        st.warning("데이터가 없습니다. 좌측 사이드바에서 데이터를 업로드해 주세요.")
        return

    # 상반기 최종월(6월) 데이터 확보
    h1_df, latest_month = _find_latest_h1_end(df)
    if h1_df is None or h1_df.empty:
        st.info("아직 상반기(6월) 마감 데이터가 반영되지 않았습니다.")
        return

    _render_status_banner(latest_month, h1_df)

    st.markdown("### 📊 상반기 요약")
    _render_summary_cards(h1_df)

    st.markdown("---")
    st.markdown("### 📈 전년 대비 비교 (달성률 기준)")
    _render_yoy_comparison(df, h1_df)

    st.markdown("---")
    st.markdown("### 🏢 센터별 상반기 결과")
    result_table = _build_result_table(df, h1_df)
    _render_result_table(result_table)

    st.markdown("---")
    st.markdown("### 📥 보고서 다운로드")
    _render_download_section(h1_df, result_table, latest_month)

    st.markdown("---")
    with st.expander("ℹ️ 평가 기준 안내", expanded=False):
        _render_evaluation_notes()


# =========================================================
# 데이터 헬퍼
# =========================================================

def _find_latest_h1_end(df: pd.DataFrame):
    """상반기(1~6월) 중 가장 최신 월의 데이터 반환"""
    if '평가월' not in df.columns:
        return None, None

    df = df.copy()
    df['평가월'] = pd.to_datetime(df['평가월'], errors='coerce')
    df = df.dropna(subset=['평가월'])

    # 올해 상반기
    this_year = datetime.now().year
    h1 = df[(df['평가월'].dt.year == this_year) & (df['평가월'].dt.month.between(1, 6))]
    if h1.empty:
        # 데이터 최신 연도 기준으로 재시도
        this_year = int(df['평가월'].dt.year.max())
        h1 = df[(df['평가월'].dt.year == this_year) & (df['평가월'].dt.month.between(1, 6))]
        if h1.empty:
            return None, None

    latest_month = h1['평가월'].max()
    latest_slice = h1[h1['평가월'] == latest_month].copy()
    return latest_slice, latest_month


def _is_integrated_this_year(center: str) -> bool:
    return center in INTEGRATED_CENTERS_THIS_YEAR


def _is_integrated_last_year(center: str) -> bool:
    return center in INTEGRATED_CENTERS_LAST_YEAR


def _get_score(row, col):
    v = row.get(col)
    try:
        return float(v) if pd.notna(v) else 0.0
    except (ValueError, TypeError):
        return 0.0


# =========================================================
# UI - 상단 배너
# =========================================================

def _render_status_banner(latest_month, h1_df):
    month_str = pd.to_datetime(latest_month).strftime("%Y년 %m월")
    total_centers = h1_df['센터명'].nunique() if '센터명' in h1_df.columns else len(h1_df)

    st.markdown(
        f"""
        <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
                    color: white; padding: 20px 24px; border-radius: 12px;
                    margin-bottom: 20px;">
            <div style="font-size: 14px; opacity: 0.9;">평가 마감</div>
            <div style="font-size: 24px; font-weight: 700; margin-top: 4px;">
                🏁 {month_str} 상반기 최종 결과
            </div>
            <div style="font-size: 14px; opacity: 0.9; margin-top: 8px;">
                총 {total_centers}개 센터 · 반기 만점 1,000점 · 목표 911점
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# UI - 요약 카드
# =========================================================

def _render_summary_cards(h1_df: pd.DataFrame):
    if '총점' not in h1_df.columns:
        st.warning("총점 컬럼이 없어 요약을 표시할 수 없습니다.")
        return

    scores = pd.to_numeric(h1_df['총점'], errors='coerce').dropna()
    if scores.empty:
        st.info("점수 데이터가 없습니다.")
        return

    total_n = len(scores)
    avg = scores.mean()
    achieved = int((scores >= TARGET_SCORE).sum())
    near_miss = int(((scores >= NEAR_MISS_MIN) & (scores < TARGET_SCORE)).sum())
    below = int((scores < NEAR_MISS_MIN).sum())

    c1, c2, c3, c4 = st.columns(4)
    _card(c1, "평균 점수", f"{avg:,.1f}점", f"목표 {TARGET_SCORE}점", Colors.PRIMARY)
    _card(c2, "911점 달성", f"{achieved}개", f"전체 {total_n}개 중", Colors.SUCCESS)
    _card(c3, "근접 미달 (895~910)", f"{near_miss}개", "하반기 회복 가능", Colors.WARNING)
    _card(c4, "미달 (<895)", f"{below}개", "집중 관리 필요", Colors.DANGER)


def _card(col, label, value, sub, color):
    col.markdown(
        f"""
        <div style="background: white; border-left: 4px solid {color};
                    padding: 16px 18px; border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.08); height: 110px;">
            <div style="font-size: 12px; color: #6b7280;">{label}</div>
            <div style="font-size: 22px; font-weight: 700; color: {color}; margin-top: 4px;">
                {value}
            </div>
            <div style="font-size: 11px; color: #9ca3af; margin-top: 6px;">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# UI - 전년 대비 비교 (달성률)
# =========================================================

def _render_yoy_comparison(df: pd.DataFrame, h1_df: pd.DataFrame):
    st.caption(
        "※ 2025년 대비 2026년은 배점 체계가 변경되어 (안전점검 600→550점, 사용계약 50점 신설) "
        "**KPI별 달성률(%)** 기준으로 비교합니다."
    )

    df_dt = df.copy()
    df_dt['평가월'] = pd.to_datetime(df_dt['평가월'], errors='coerce')
    df_dt = df_dt.dropna(subset=['평가월'])

    last_year = pd.to_datetime(h1_df['평가월'].iloc[0]).year - 1

    # 전년도 상반기 (2025년 6월 최종)
    ly = df_dt[
        (df_dt['평가월'].dt.year == last_year)
        & (df_dt['평가월'].dt.month == 6)
    ]

    if ly.empty:
        st.info(f"{last_year}년 상반기 데이터가 없어 전년 비교를 표시할 수 없습니다.")
        return

    # 통합센터 제외 (양쪽 모두)
    ty_valid = h1_df[~h1_df['센터명'].isin(
        INTEGRATED_CENTERS_THIS_YEAR | INTEGRATED_CENTERS_LAST_YEAR
    )]
    ly_valid = ly[~ly['센터명'].isin(
        INTEGRATED_CENTERS_THIS_YEAR | INTEGRATED_CENTERS_LAST_YEAR
    )]

    # 총점 달성률
    ty_avg_total = pd.to_numeric(ty_valid['총점'], errors='coerce').mean()
    ly_avg_total = pd.to_numeric(ly_valid['총점'], errors='coerce').mean()

    c1, c2, c3 = st.columns(3)
    c1.metric(f"{last_year}년 상반기 평균", f"{ly_avg_total:,.1f}점")
    c2.metric("2026년 상반기 평균", f"{ty_avg_total:,.1f}점",
              delta=f"{ty_avg_total - ly_avg_total:+.1f}점")
    c3.metric("달성률 변화",
              f"{ty_avg_total / 10:.1f}%",
              delta=f"{(ty_avg_total - ly_avg_total) / 10:+.1f}%p")

    # KPI별 달성률 비교
    kpi_rows = []
    common_kpis = ['안전점검', '중점고객', '상담응대', '상담기여', '만족도']

    for kpi in common_kpis:
        col = KPI_SCORE_COLS[kpi]
        ly_rate = _calc_kpi_achievement_rate(ly_valid, col, KPI_MAX_LAST_YEAR[kpi])
        ty_rate = _calc_kpi_achievement_rate(ty_valid, col, KPI_MAX_THIS_YEAR[kpi])
        kpi_rows.append({
            'KPI': kpi,
            f'{last_year}년 달성률(%)': round(ly_rate, 1),
            '2026년 달성률(%)': round(ty_rate, 1),
            '변화(%p)': round(ty_rate - ly_rate, 1),
        })

    # 사용계약 (올해 신설)
    ty_rate = _calc_kpi_achievement_rate(ty_valid, KPI_SCORE_COLS['사용계약'], KPI_MAX_THIS_YEAR['사용계약'])
    kpi_rows.append({
        'KPI': '사용계약 (신설)',
        f'{last_year}년 달성률(%)': None,
        '2026년 달성률(%)': round(ty_rate, 1),
        '변화(%p)': None,
    })

    kpi_df = pd.DataFrame(kpi_rows)
    st.dataframe(kpi_df, use_container_width=True, hide_index=True)

    # KPI 달성률 막대 차트
    plot_df = kpi_df[kpi_df[f'{last_year}년 달성률(%)'].notna()].copy()
    if not plot_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name=f'{last_year}년',
            x=plot_df['KPI'],
            y=plot_df[f'{last_year}년 달성률(%)'],
            marker_color=Colors.NEUTRAL if hasattr(Colors, 'NEUTRAL') else '#94a3b8',
        ))
        fig.add_trace(go.Bar(
            name='2026년',
            x=plot_df['KPI'],
            y=plot_df['2026년 달성률(%)'],
            marker_color=Colors.PRIMARY,
        ))
        fig.update_layout(
            barmode='group',
            height=380,
            yaxis_title='달성률(%)',
            yaxis_range=[0, 105],
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)


def _calc_kpi_achievement_rate(df: pd.DataFrame, score_col: str, max_score: float) -> float:
    if score_col not in df.columns or max_score <= 0:
        return 0.0
    s = pd.to_numeric(df[score_col], errors='coerce').dropna()
    if s.empty:
        return 0.0
    return float(s.mean() / max_score * 100)


# =========================================================
# UI - 센터별 결과 테이블
# =========================================================

def _build_result_table(df: pd.DataFrame, h1_df: pd.DataFrame) -> pd.DataFrame:
    df_dt = df.copy()
    df_dt['평가월'] = pd.to_datetime(df_dt['평가월'], errors='coerce')

    this_year = pd.to_datetime(h1_df['평가월'].iloc[0]).year
    last_year = this_year - 1

    ly_h1 = df_dt[(df_dt['평가월'].dt.year == last_year) & (df_dt['평가월'].dt.month == 6)]
    ly_map = dict(zip(ly_h1['센터명'], pd.to_numeric(ly_h1['총점'], errors='coerce')))

    rows = []
    for _, row in h1_df.iterrows():
        center = row['센터명']
        total = _get_score(row, '총점')

        # 상태
        if total >= TARGET_SCORE:
            status = "✅ 달성"
        elif total >= NEAR_MISS_MIN:
            status = "🟡 근접미달"
        else:
            status = "🔴 미달"

        # 특이사항
        notes = []
        if _is_integrated_this_year(center):
            notes.append("2026년 통합센터 (상·하반기 평가 유예 · 참고용)")
        if center in ADJUSTED_CENTERS:
            notes.append("권역조정 (안전점검은 기존 관리세대 기준)")

        # 전년 대비
        ly_score = ly_map.get(center)
        if _is_integrated_last_year(center):
            yoy = "전년 유예"
        elif ly_score is not None and pd.notna(ly_score):
            yoy = f"{total - ly_score:+.1f}점"
        else:
            yoy = "-"

        # 하반기 필요 점수 (연평균 911 = 총 1822 기준)
        if total >= TARGET_SCORE:
            need_h2 = "-"
        else:
            need = max(0, 1822 - total)
            need_h2 = f"{need:,.0f}점"

        rows.append({
            '센터명': center,
            '상반기 총점': round(total, 1),
            '상태': status,
            f'전년 상반기 대비': yoy,
            '하반기 필요점수': need_h2,
            '특이사항': " / ".join(notes) if notes else "",
        })

    result = pd.DataFrame(rows)
    # 총점 내림차순 정렬
    result = result.sort_values('상반기 총점', ascending=False).reset_index(drop=True)
    result.insert(0, '순위', result.index + 1)
    return result


def _render_result_table(result: pd.DataFrame):
    if result.empty:
        st.info("표시할 결과가 없습니다.")
        return

    st.caption(f"총 **{len(result)}개** 센터 · 상반기 총점 기준 내림차순")
    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True,
        height=min(600, 45 + 35 * len(result)),
    )


# =========================================================
# UI - 다운로드
# =========================================================

def _render_download_section(h1_df: pd.DataFrame, result_table: pd.DataFrame, latest_month):
    month_str = pd.to_datetime(latest_month).strftime("%Y%m")
    ts = datetime.now().strftime("%Y%m%d_%H%M")

    # 상반기 요약 보고서 (Excel)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        result_table.to_excel(writer, index=False, sheet_name='센터별 결과')

        summary = _build_summary_sheet(h1_df)
        summary.to_excel(writer, index=False, sheet_name='요약 통계')

    st.download_button(
        label="📄 상반기 요약 보고서 다운로드 (Excel)",
        data=buf.getvalue(),
        file_name=f"상반기_요약보고서_{month_str}_{ts}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )


def _build_summary_sheet(h1_df: pd.DataFrame) -> pd.DataFrame:
    scores = pd.to_numeric(h1_df['총점'], errors='coerce').dropna()
    total_n = len(scores)
    achieved = int((scores >= TARGET_SCORE).sum())
    near_miss = int(((scores >= NEAR_MISS_MIN) & (scores < TARGET_SCORE)).sum())
    below = int((scores < NEAR_MISS_MIN).sum())

    return pd.DataFrame([
        {'항목': '평가 기간', '값': '2026년 상반기 (1~6월)'},
        {'항목': '총 센터 수', '값': f'{total_n}개'},
        {'항목': '평균 점수', '값': f'{scores.mean():,.1f}점'},
        {'항목': '최고 점수', '값': f'{scores.max():,.1f}점'},
        {'항목': '최저 점수', '값': f'{scores.min():,.1f}점'},
        {'항목': '911점 달성', '값': f'{achieved}개'},
        {'항목': '근접 미달 (895~910)', '값': f'{near_miss}개'},
        {'항목': '미달 (<895)', '값': f'{below}개'},
        {'항목': '반기 목표', '값': '911점'},
        {'항목': '연간 패스 기준', '값': '상·하반기 평균 911점 (연 1,822점)'},
    ])


# =========================================================
# UI - 평가 기준 안내
# =========================================================

def _render_evaluation_notes():
    st.markdown(
        """
**■ 평가 체계**
- 반기 만점: **1,000점** / 반기 목표: **911점**
- 연간 패스 기준: 상·하반기 **평균 911점** (연 1,822점)
- 상반기 미달 시 하반기 회복으로 연평균 911점 달성 가능

**■ 2026년 KPI 배점**

| KPI | 배점 | 비고 |
|---|---:|---|
| 안전점검실점검율 | 550점 | 2025년 대비 -50점 |
| 중점고객 | 100점 | - |
| 사용계약율 | **50점** | **2026년 신설** |
| 상담응대율 | 100점 | - |
| 상담기여율 | 100점 | - |
| 만족도 | 100점 | - |
| **합계** | **1,000점** | - |

**■ 특이 센터 안내**
- **퇴계원/별내 (2026년 4월 통합)**: 2026년 상·하반기 모두 평가 유예. 상반기 결과는 참고용으로 표시.
- **금곡/경기동부, 덕소/양평 (2025년 4월 통합)**: 2025년 평가 유예. 전년 대비 비교에서 제외.
- **구리 (2026년 4월 권역조정)**: 흡수 행정동은 안전점검실점검율 평가에서 제외, 기존 관리세대수 기준으로만 상·하반기 모두 평가. 그 외 KPI는 정상 평가.
        """
    )
