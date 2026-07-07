"""
📑 상반기 보고 페이지
- 상반기 최종 결과 요약 (KMAC 및 내부 보고용)
- 작년 상/하반기와 올해 상반기 비교 (달성률 기준, 구조 변경 반영)
- 통합 유예 센터 자동 처리
- 센터별 최종 점수표 다운로드 (CSV / Excel)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime

from utils.styles import Colors, ScoreThresholds, PLOTLY_LAYOUT
from utils.helpers import safe_unique_centers
from utils.insights_v2 import (
    _safe_latest_month,
    _is_half_end,
    _get_half,
    _to_month_int,
    _filter_by_month,
    TARGET_TOTAL,
    ANNUAL_PASS_TOTAL,
)


# ==================== KPI 배점 정의 ====================

# 올해(2026) 배점 - 총 1000점
KPI_MAX_THIS_YEAR = {
    '안전점검': 550,
    '중점고객': 100,
    '사용계약': 50,
    '상담응대': 100,
    '상담기여': 100,
    '만족도': 100,
}

# 작년(2025) 배점 - 총 1000점 (사용계약 없음, 안전점검 600점)
KPI_MAX_LAST_YEAR = {
    '안전점검': 600,
    '중점고객': 100,
    '상담응대': 100,
    '상담기여': 100,
    '만족도': 100,
}

# 데이터프레임 컬럼명 매핑
KPI_SCORE_COLS = {
    '안전점검': '안전점검_점수',
    '중점고객': '중점고객_점수',
    '사용계약': '사용계약_점수',
    '상담응대': '상담응대_점수',
    '상담기여': '상담기여_점수',
    '만족도': '만족도_점수',
}

# ==================== 평가 유예 센터 정의 ====================

# 올해(2026) 유예: 2026-04월 통합 → 올해 상반기 평가 유예
DEFERRED_THIS_YEAR = {
    '퇴계원/별내', '별내/퇴계원',
}

# 작년(2025) 유예: 2025-04월 통합 → 작년 평가 유예 (작년 데이터 없음/불완전)
DEFERRED_LAST_YEAR = {
    '금곡/경기동부', '경기동부/금곡',
    '덕소/양평', '양평/덕소',
}

# 권역조정 센터 (평가는 진행되나 주석 필요)
ADJUSTED_CENTERS = {
    '구리': '4월 권역조정으로 행정동 흡수 (안전점검은 기존 관리세대 기준 평가)',
}


# ==================== 메인 함수 ====================

def show(df: pd.DataFrame, device_type: str = "desktop"):
    """상반기 보고 페이지"""

    if df is None or df.empty:
        st.warning("⚠️ 데이터가 없습니다.")
        return

    latest_month = _safe_latest_month(df)
    if latest_month is None:
        st.warning("⚠️ 평가월 데이터가 없습니다.")
        return

    latest_month_int = _to_month_int(latest_month)
    latest_half = _get_half(latest_month_int)
    latest_year = pd.Timestamp(latest_month).year

    # ==================== 헤더 ====================
    st.markdown("### 📑 상반기 평가 결과 보고")

    if latest_half == '상반기' and latest_month_int == 6:
        st.success(
            f"✅ **{latest_year}년 상반기 최종 결과 확정** "
            f"(6월 데이터 반영 완료)"
        )
        report_month = latest_month
    elif latest_half == '상반기':
        st.info(
            f"📌 현재 **{latest_year}년 상반기 진행 중** ({latest_month_int}월까지 반영). "
            f"6월 데이터 반영 후 최종 확정됩니다."
        )
        report_month = latest_month
    else:
        st.info(
            f"📌 현재 최신 데이터는 {latest_year}년 {latest_month_int}월(하반기)입니다. "
            f"직전 상반기 결과를 표시합니다."
        )
        report_month = _find_latest_h1_end(df)
        if report_month is None:
            st.warning("⚠️ 상반기 최종(6월) 데이터를 찾을 수 없습니다.")
            return
        latest_year = pd.Timestamp(report_month).year

    st.markdown("---")

    # ==================== 상반기 데이터 추출 ====================
    df_h1_latest = _filter_by_month(df, report_month).copy()
    if df_h1_latest.empty:
        st.warning("⚠️ 상반기 최종 데이터가 비어있습니다.")
        return

    # ⭐ 올해 유예 센터 분리 (참고용으로 별도 저장)
    df_h1_deferred = df_h1_latest[df_h1_latest['센터명'].isin(DEFERRED_THIS_YEAR)].copy()
    df_h1_active = df_h1_latest[~df_h1_latest['센터명'].isin(DEFERRED_THIS_YEAR)].copy()

    df_last_year = st.session_state.get('df_last_year', None)

    # ==================== 유예 센터 안내 ====================
    if not df_h1_deferred.empty:
        deferred_names = ', '.join(df_h1_deferred['센터명'].unique().tolist())
        st.warning(
            f"⚠️ **{latest_year}년 상반기 평가 유예 센터: {deferred_names}** "
            f"(4월 통합으로 인해 평가에서 제외됩니다. 아래 통계는 유예 센터를 제외한 값입니다.)"
        )

    # ==================== 1. 총평 요약 카드 ====================
    st.markdown(f"#### 🎯 {latest_year}년 상반기 총평")

    _render_summary_cards(df_h1_active, device_type)

    st.markdown("")

    # ==================== 2. 전년 대비 비교 ====================
    st.markdown("#### 📊 전년 대비 비교 (KPI 달성률 기준)")
    st.caption(
        "💡 배점 구조가 변경되어 **달성률(%)** 기준으로 비교합니다. "
        f"{latest_year-1}년: 안전점검 600점·사용계약 없음 → "
        f"{latest_year}년: 안전점검 550점·사용계약 50점 신설"
    )

    _render_yoy_comparison(df_h1_active, df_last_year, latest_year, device_type)

    st.markdown("")

    # ==================== 3. 센터별 최종 결과표 ====================
    st.markdown("#### 📋 센터별 상반기 최종 결과")

    result_table = _build_center_result_table(
        df_h1_latest, df_last_year, latest_year
    )
    _render_result_table(result_table)

    st.markdown("")

    # ==================== 4. 다운로드 ====================
    st.markdown("#### 📥 보고서 다운로드 (KMAC 송부용)")

    _render_downloads(df, df_h1_latest, result_table, latest_year, report_month)

    st.markdown("")

    # ==================== 5. 하단 주석 ====================
    with st.expander("📖 평가 체계 및 특이사항 안내", expanded=False):
        st.markdown(f"""
**평가 체계**
- 반기별 총점 1000점 (상반기·하반기 각각)
- 반기 목표: **911점**
- **연간 pass 기준: 상+하반기 평균 911점** (총 1822점)
- 상반기 미달 시 하반기 만회 가능

**{latest_year}년 배점 구조** (총 1000점)
- 안전점검 550점 / 중점고객 100점 / 사용계약 50점 (🆕 신설)
- 상담응대 100점 / 상담기여 100점 / 만족도 100점

**{latest_year - 1}년 배점 구조** (총 1000점, 참고용)
- 안전점검 600점 / 중점고객 100점
- 상담응대 100점 / 상담기여 100점 / 만족도 100점
- (사용계약 항목 없음)

**{latest_year}년 통합 및 평가 유예**
- **{latest_year}년 4월 통합**: 퇴계원/별내 → **올해 상반기 평가 유예**
- **{latest_year - 1}년 4월 통합**: 금곡/경기동부, 덕소/양평 → **작년 평가 유예** (작년 비교 데이터 없음)

**권역조정 센터 (평가 진행)**
- **구리**: 4월 권역조정으로 여러 행정동을 흡수. 
  - 안전점검실점검율: **기존 관리세대수 기준으로만 평가** (흡수한 행정동은 안전점검 산정 제외)
  - 그 외 항목: 정상 평가 (평가 이견 없음)
        """)


# ==================== 헬퍼 함수 ====================

def _find_latest_h1_end(df: pd.DataFrame):
    """DataFrame에서 가장 최근 상반기 마지막 달(6월) 반환"""
    months = pd.to_datetime(df['평가월'], errors='coerce').dropna().unique()
    h1_ends = [m for m in months if pd.Timestamp(m).month == 6]
    if not h1_ends:
        return None
    return max(h1_ends)


def _render_summary_cards(df_h1: pd.DataFrame, device_type: str):
    """상반기 총평 요약 카드 4개 (유예 센터 제외)"""
    n_total = len(df_h1)
    if n_total == 0:
        st.info("표시할 데이터가 없습니다.")
        return

    avg = df_h1['총점'].mean() if '총점' in df_h1.columns else 0
    n_achieved = int((df_h1['총점'] >= TARGET_TOTAL).sum())
    n_near = int(((df_h1['총점'] >= 895) & (df_h1['총점'] < TARGET_TOTAL)).sum())
    n_fail = int((df_h1['총점'] < 895).sum())
    achieve_rate = (n_achieved / n_total * 100) if n_total > 0 else 0

    n_cols = 2 if device_type == 'mobile' else 4
    cols = st.columns(n_cols)

    cards = [
        {
            "label": "상반기 평균",
            "value": f"{avg:.1f}점",
            "sub": f"목표 911점 대비 {avg - TARGET_TOTAL:+.1f}점",
            "color": Colors.SUCCESS if avg >= TARGET_TOTAL else Colors.WARNING,
            "icon": "📊",
        },
        {
            "label": "911점 달성",
            "value": f"{n_achieved} / {n_total}개",
            "sub": f"달성률 {achieve_rate:.1f}%",
            "color": Colors.SUCCESS,
            "icon": "🏆",
        },
        {
            "label": "근접 미달 (895~910)",
            "value": f"{n_near}개",
            "sub": "하반기 소폭 회복 필요",
            "color": Colors.WARNING,
            "icon": "⚠️",
        },
        {
            "label": "미달 (895 미만)",
            "value": f"{n_fail}개",
            "sub": "하반기 강력 회복 필요",
            "color": Colors.DANGER if n_fail > 0 else Colors.SUCCESS,
            "icon": "🚨",
        },
    ]

    for idx, card in enumerate(cards):
        with cols[idx % n_cols]:
            html = (
                f'<div style="background:{Colors.BG_CARD};'
                f'border:1px solid {Colors.BORDER};'
                f'border-left:4px solid {card["color"]};'
                f'border-radius:10px;padding:16px 18px;margin-bottom:10px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.04);">'
                f'<div style="display:flex;align-items:center;gap:6px;'
                f'color:{Colors.TEXT_SUB};font-size:13px;font-weight:600;margin-bottom:4px;">'
                f'<span>{card["icon"]}</span><span>{card["label"]}</span>'
                f'</div>'
                f'<div style="font-size:26px;font-weight:700;color:{card["color"]};'
                f'line-height:1.2;margin-bottom:4px;">{card["value"]}</div>'
                f'<div style="color:{Colors.TEXT_SUB};font-size:12px;">{card["sub"]}</div>'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)


def _calc_kpi_achievement_rate(
    df: pd.DataFrame,
    kpi_name: str,
    kpi_max_dict: dict,
) -> float:
    """
    KPI별 달성률(%) 계산 = 실제 획득 점수 평균 / 배점 × 100
    """
    if kpi_name not in kpi_max_dict:
        return np.nan
    score_col = KPI_SCORE_COLS.get(kpi_name)
    if score_col is None or score_col not in df.columns:
        return np.nan
    max_score = kpi_max_dict[kpi_name]
    if max_score == 0:
        return np.nan
    avg_score = df[score_col].mean()
    if pd.isna(avg_score):
        return np.nan
    return (avg_score / max_score) * 100


def _render_yoy_comparison(
    df_h1_this: pd.DataFrame,
    df_last_year: pd.DataFrame,
    this_year: int,
    device_type: str,
):
    """전년 대비 비교 (작년 상/하반기 vs 올해 상반기, 달성률 기준)"""

    if df_last_year is None or df_last_year.empty:
        st.info("작년 데이터가 없어 비교할 수 없습니다.")
        return

    # 작년 데이터에서도 작년 유예 센터 제외
    df_ly = df_last_year.copy()
    df_ly = df_ly[~df_ly['센터명'].isin(DEFERRED_LAST_YEAR)]

    df_ly['_month_dt'] = pd.to_datetime(df_ly['평가월'], errors='coerce')
    df_ly = df_ly.dropna(subset=['_month_dt'])

    df_ly_h1 = df_ly[df_ly['_month_dt'].dt.month == 6]
    df_ly_h2 = df_ly[df_ly['_month_dt'].dt.month == 12]

    ly_year = this_year - 1

    # ===== 총점 평균 비교 카드 =====
    this_avg = df_h1_this['총점'].mean() if not df_h1_this.empty else np.nan
    ly_h1_avg = df_ly_h1['총점'].mean() if not df_ly_h1.empty else np.nan
    ly_h2_avg = df_ly_h2['총점'].mean() if not df_ly_h2.empty else np.nan

    st.markdown("##### 📈 총점 평균 추이 (전 센터, 유예 제외)")

    tot_cols = st.columns(3)
    tot_cards = [
        {
            "label": f"{ly_year}년 상반기",
            "value": f"{ly_h1_avg:.1f}점" if pd.notna(ly_h1_avg) else "데이터 없음",
            "color": Colors.REFERENCE,
        },
        {
            "label": f"{ly_year}년 하반기",
            "value": f"{ly_h2_avg:.1f}점" if pd.notna(ly_h2_avg) else "데이터 없음",
            "color": Colors.REFERENCE,
        },
        {
            "label": f"{this_year}년 상반기",
            "value": f"{this_avg:.1f}점" if pd.notna(this_avg) else "데이터 없음",
            "color": Colors.PRIMARY,
        },
    ]

    for idx, card in enumerate(tot_cards):
        with tot_cols[idx]:
            html = (
                f'<div style="background:{Colors.BG_CARD};'
                f'border:1px solid {Colors.BORDER};'
                f'border-top:3px solid {card["color"]};'
                f'border-radius:8px;padding:14px;text-align:center;">'
                f'<div style="color:{Colors.TEXT_SUB};font-size:13px;'
                f'font-weight:600;margin-bottom:6px;">{card["label"]}</div>'
                f'<div style="color:{card["color"]};font-size:24px;'
                f'font-weight:700;">{card["value"]}</div>'
                f'</div>'
            )
            st.markdown(html, unsafe_allow_html=True)

    # 전년 대비 증감 안내
    if pd.notna(this_avg) and pd.notna(ly_h1_avg):
        diff = this_avg - ly_h1_avg
        icon = "🔺" if diff > 0 else ("🔻" if diff < 0 else "➡️")
        color = Colors.SUCCESS if diff > 0 else (Colors.DANGER if diff < 0 else Colors.TEXT_SUB)
        st.markdown(
            f'<div style="text-align:center;margin-top:8px;color:{color};font-size:14px;">'
            f'{icon} 전년 상반기 대비 <b>{diff:+.1f}점</b> '
            f'(전년 하반기 대비 {this_avg - ly_h2_avg:+.1f}점)'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ===== KPI별 달성률 비교표 =====
    st.markdown("##### 📊 KPI 항목별 달성률 비교 (%)")

    all_kpis = ['안전점검', '중점고객', '사용계약', '상담응대', '상담기여', '만족도']
    rows = []
    for kpi in all_kpis:
        this_rate = _calc_kpi_achievement_rate(df_h1_this, kpi, KPI_MAX_THIS_YEAR)
        ly_h1_rate = _calc_kpi_achievement_rate(df_ly_h1, kpi, KPI_MAX_LAST_YEAR) \
            if not df_ly_h1.empty else np.nan
        ly_h2_rate = _calc_kpi_achievement_rate(df_ly_h2, kpi, KPI_MAX_LAST_YEAR) \
            if not df_ly_h2.empty else np.nan

        note = ""
        if kpi == '사용계약':
            note = "🆕 올해 신설"
        elif kpi == '안전점검':
            note = "배점 600→550 조정"

        rows.append({
            'KPI': kpi,
            f'{ly_year}년 상반기 달성률': ly_h1_rate,
            f'{ly_year}년 하반기 달성률': ly_h2_rate,
            f'{this_year}년 상반기 달성률': this_rate,
            '전년 동기 대비': (this_rate - ly_h1_rate)
                if pd.notna(ly_h1_rate) and pd.notna(this_rate) else np.nan,
            '비고': note,
        })

    df_compare = pd.DataFrame(rows)

    column_config = {
        f'{ly_year}년 상반기 달성률': st.column_config.NumberColumn(format="%.1f%%"),
        f'{ly_year}년 하반기 달성률': st.column_config.NumberColumn(format="%.1f%%"),
        f'{this_year}년 상반기 달성률': st.column_config.NumberColumn(format="%.1f%%"),
        '전년 동기 대비': st.column_config.NumberColumn(
            format="%+.1f%p",
            help="올해 상반기 - 작년 상반기 (음수면 하락)"
        ),
    }

    st.dataframe(
        df_compare,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    # ===== KPI 달성률 시각화 =====
    _render_yoy_bar_chart(df_compare, ly_year, this_year)


def _render_yoy_bar_chart(df_compare: pd.DataFrame, ly_year: int, this_year: int):
    """전년 대비 KPI 달성률 막대 차트"""
    fig = go.Figure()

    kpis = df_compare['KPI'].tolist()

    fig.add_trace(go.Bar(
        name=f'{ly_year}년 상반기',
        x=kpis,
        y=df_compare[f'{ly_year}년 상반기 달성률'],
        marker_color=Colors.REFERENCE,
        text=[f"{v:.1f}%" if pd.notna(v) else "N/A"
              for v in df_compare[f'{ly_year}년 상반기 달성률']],
        textposition='outside',
    ))
    fig.add_trace(go.Bar(
        name=f'{ly_year}년 하반기',
        x=kpis,
        y=df_compare[f'{ly_year}년 하반기 달성률'],
        marker_color="#94a3b8",
        text=[f"{v:.1f}%" if pd.notna(v) else "N/A"
              for v in df_compare[f'{ly_year}년 하반기 달성률']],
        textposition='outside',
    ))
    fig.add_trace(go.Bar(
        name=f'{this_year}년 상반기',
        x=kpis,
        y=df_compare[f'{this_year}년 상반기 달성률'],
        marker_color=Colors.PRIMARY,
        text=[f"{v:.1f}%" if pd.notna(v) else "N/A"
              for v in df_compare[f'{this_year}년 상반기 달성률']],
        textposition='outside',
    ))

    fig.update_layout(
        title=dict(text="<b>KPI별 달성률 비교</b>", font=dict(size=14)),
        barmode='group',
        height=380,
        yaxis=dict(title="달성률(%)", range=[0, 110], gridcolor=Colors.BORDER),
        xaxis=dict(title="", gridcolor=Colors.BORDER),
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(t=50, b=60, l=40, r=20),
        **PLOTLY_LAYOUT,
    )

    st.plotly_chart(fig, use_container_width=True)


def _build_center_result_table(
    df_h1: pd.DataFrame,
    df_last_year: pd.DataFrame,
    this_year: int,
) -> pd.DataFrame:
    """센터별 최종 결과표 생성"""

    ly_year = this_year - 1

    # 작년 6월 데이터
    ly_h1_scores = {}
    if df_last_year is not None and not df_last_year.empty:
        df_ly = df_last_year.copy()
        df_ly['_month_dt'] = pd.to_datetime(df_ly['평가월'], errors='coerce')
        df_ly_h1 = df_ly[df_ly['_month_dt'].dt.month == 6]
        if not df_ly_h1.empty:
            ly_h1_scores = dict(zip(df_ly_h1['센터명'], df_ly_h1['총점']))

    rows = []
    for _, row in df_h1.iterrows():
        center = row['센터명']
        total = row.get('총점', np.nan)

        # 유예 여부
        is_deferred_this = center in DEFERRED_THIS_YEAR
        is_deferred_last = center in DEFERRED_LAST_YEAR

        # 평가 상태
        if is_deferred_this:
            status = '⏸️ 평가 유예'
        elif pd.isna(total):
            status = '❓ 데이터 없음'
        elif total >= TARGET_TOTAL:
            status = '✅ 달성'
        elif total >= 895:
            status = '⚠️ 근접 미달'
        else:
            status = '🚨 미달'

        # 작년 상반기 점수
        ly_score = ly_h1_scores.get(center, np.nan)

        # 작년 비교 가능 여부
        if is_deferred_this:
            note_parts = [f'{this_year}년 4월 통합 유예']
            ly_score_display = None  # 유예 센터는 비교 불필요
        elif is_deferred_last:
            note_parts = [f'{ly_year}년 4월 통합 (작년 비교 불가)']
            ly_score_display = None
        else:
            note_parts = []
            ly_score_display = ly_score

        # 권역조정 안내
        if center in ADJUSTED_CENTERS:
            note_parts.append(ADJUSTED_CENTERS[center])

        # 하반기 필요점수 (연간 pass 관점)
        if is_deferred_this or pd.isna(total):
            h2_needed = None
        else:
            h2_needed = max(0, ANNUAL_PASS_TOTAL - total)

        # 전년 대비 증감
        if pd.notna(total) and pd.notna(ly_score_display):
            yoy_diff = total - ly_score_display
        else:
            yoy_diff = None

        rows.append({
            '센터명': center,
            f'{this_year}년 상반기 총점': total if not is_deferred_this else None,
            f'{ly_year}년 상반기 총점': ly_score_display,
            '전년 대비': yoy_diff,
            '평가 상태': status,
            '연간 pass 위한 하반기 필요점수': h2_needed,
            '비고': ' / '.join(note_parts) if note_parts else '',
        })

    df_result = pd.DataFrame(rows)

    # 정렬: 유예 → 미달 → 근접미달 → 달성 → 나머지
    status_order = {
        '⏸️ 평가 유예': 4,
        '🚨 미달': 0,
        '⚠️ 근접 미달': 1,
        '✅ 달성': 2,
        '❓ 데이터 없음': 3,
    }
    df_result['_sort'] = df_result['평가 상태'].map(status_order).fillna(5)
    # 유예는 맨 아래, 그 위는 점수 낮은 순
    df_result = df_result.sort_values(
        ['_sort', f'{this_year}년 상반기 총점'],
        ascending=[True, True],
        na_position='last',
    )
    df_result = df_result.drop(columns=['_sort']).reset_index(drop=True)
    return df_result


def _render_result_table(df_result: pd.DataFrame):
    """센터별 결과표 렌더링"""
    if df_result is None or df_result.empty:
        st.info("표시할 결과가 없습니다.")
        return

    # 컬럼명 자동 감지
    this_year_col = next(
        (c for c in df_result.columns if '년 상반기 총점' in c and str(c).startswith('20')
         and c != next((k for k in df_result.columns if k != c and '년 상반기 총점' in k), '')),
        None
    )

    # 컬럼별 포맷
    column_config = {}
    for col in df_result.columns:
        if '상반기 총점' in col:
            column_config[col] = st.column_config.NumberColumn(
                col, format="%.1f점"
            )
        elif col == '전년 대비':
            column_config[col] = st.column_config.NumberColumn(
                format="%+.1f점",
                help="올해 상반기 - 작년 상반기 (양수면 상승)"
            )
        elif col == '연간 pass 위한 하반기 필요점수':
            column_config[col] = st.column_config.NumberColumn(
                format="%.0f점",
                help="연간 평균 911점(총 1822점) 달성 위해 하반기에 필요한 최소 점수. "
                     "950점 초과 시 매우 어려움."
            )

    st.dataframe(
        df_result,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

    st.caption(
        "💡 **하반기 필요점수**가 950점을 초과하면 연간 pass가 매우 어려움 / "
        "**평가 유예 센터**는 상반기 평가에서 제외 / "
        "**작년 통합 센터**는 전년 비교 데이터 없음"
    )


def _render_downloads(
    df_full: pd.DataFrame,
    df_h1: pd.DataFrame,
    result_table: pd.DataFrame,
    this_year: int,
    report_month,
):
    """다운로드 버튼 (RAW 데이터 + 요약 보고서)"""

    timestamp = datetime.now().strftime('%Y%m%d')
    report_month_str = pd.Timestamp(report_month).strftime('%Y%m')

    cols = st.columns(2)

    # ===== 1) 상반기 요약 보고서 (엑셀, 다중 시트) =====
    with cols[0]:
        summary_excel = _build_summary_excel(
            df_h1, result_table, this_year, report_month
        )
        st.download_button(
            label="📊 상반기 요약 보고서 (Excel)",
            data=summary_excel,
            file_name=f"상반기_요약보고_{this_year}년_{report_month_str}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="센터별 최종 결과 + 전년 대비 요약 (KMAC 송부용)",
            use_container_width=True,
        )

    # ===== 2) RAW 데이터 전체 (엑셀) =====
    with cols[1]:
        raw_excel = _build_raw_excel(df_full, this_year)
        st.download_button(
            label="📁 RAW 데이터 전체 (Excel)",
            data=raw_excel,
            file_name=f"RAW데이터_{this_year}년상반기_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="1~6월 원본 평가 데이터 전체 (KMAC 검토용)",
            use_container_width=True,
        )


def _build_summary_excel(
    df_h1: pd.DataFrame,
    result_table: pd.DataFrame,
    this_year: int,
    report_month,
) -> bytes:
    """요약 보고서 엑셀 (다중 시트)"""
    output = BytesIO()

    ly_year = this_year - 1
    report_str = pd.Timestamp(report_month).strftime('%Y-%m')

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # 시트 1: 요약
        summary_data = _make_summary_sheet(df_h1, this_year, report_str)
        summary_data.to_excel(writer, sheet_name='1_상반기요약', index=False)

        # 시트 2: 센터별 결과
        result_table.to_excel(writer, sheet_name='2_센터별결과', index=False)

        # 시트 3: 특이사항
        notes_data = _make_notes_sheet(this_year)
        notes_data.to_excel(writer, sheet_name='3_특이사항', index=False)

    output.seek(0)
    return output.getvalue()


def _make_summary_sheet(df_h1: pd.DataFrame, this_year: int, report_str: str) -> pd.DataFrame:
    """요약 시트 데이터"""
    df_active = df_h1[~df_h1['센터명'].isin(DEFERRED_THIS_YEAR)]
    n_total = len(df_active)
    n_deferred = len(df_h1[df_h1['센터명'].isin(DEFERRED_THIS_YEAR)])

    if n_total > 0:
        avg = df_active['총점'].mean()
        n_achieved = int((df_active['총점'] >= TARGET_TOTAL).sum())
        n_near = int(((df_active['총점'] >= 895) & (df_active['총점'] < TARGET_TOTAL)).sum())
        n_fail = int((df_active['총점'] < 895).sum())
    else:
        avg = n_achieved = n_near = n_fail = 0

    rows = [
        ['보고 기준월', report_str],
        ['평가 대상 센터 수', f'{n_total}개'],
        ['평가 유예 센터 수', f'{n_deferred}개 ({this_year}년 4월 통합)'],
        ['상반기 평균 점수', f'{avg:.1f}점'],
        ['목표(911점) 대비', f'{avg - TARGET_TOTAL:+.1f}점'],
        ['911점 달성 센터', f'{n_achieved}개 ({n_achieved/n_total*100:.1f}%)' if n_total > 0 else '0개'],
        ['근접 미달 (895~910)', f'{n_near}개'],
        ['미달 (895 미만)', f'{n_fail}개'],
        ['최고 점수', f'{df_active["총점"].max():.1f}점 ({df_active.loc[df_active["총점"].idxmax(), "센터명"]})' if n_total > 0 else '-'],
        ['최저 점수', f'{df_active["총점"].min():.1f}점 ({df_active.loc[df_active["총점"].idxmin(), "센터명"]})' if n_total > 0 else '-'],
    ]

    return pd.DataFrame(rows, columns=['항목', '값'])


def _make_notes_sheet(this_year: int) -> pd.DataFrame:
    """특이사항 시트"""
    ly_year = this_year - 1
    rows = [
        ['평가 체계', f'반기 총점 1000점 / 목표 911점 / 연간 pass = 상+하반기 평균 911점'],
        ['', ''],
        [f'{this_year}년 배점', '안전점검 550 / 중점고객 100 / 사용계약 50(신설) / 상담응대 100 / 상담기여 100 / 만족도 100'],
        [f'{ly_year}년 배점(참고)', '안전점검 600 / 중점고객 100 / 상담응대 100 / 상담기여 100 / 만족도 100'],
        ['', ''],
        [f'{this_year}년 평가 유예', '퇴계원/별내 (4월 통합)'],
        [f'{ly_year}년 평가 유예', '금곡/경기동부, 덕소/양평 (4월 통합) — 작년 비교 데이터 없음'],
        ['', ''],
        ['권역조정 (평가 진행)', '구리: 4월 행정동 흡수. 안전점검은 기존 관리세대 기준 평가, 그 외 정상 평가'],
    ]
    return pd.DataFrame(rows, columns=['구분', '내용'])


def _build_raw_excel(df_full: pd.DataFrame, this_year: int) -> bytes:
    """RAW 데이터 엑셀 (상반기 1~6월 전체)"""
    output = BytesIO()

    df_out = df_full.copy()
    df_out['_month_dt'] = pd.to_datetime(df_out['평가월'], errors='coerce')

    # 상반기 데이터만
    df_h1_all = df_out[
        (df_out['_month_dt'].dt.year == this_year) &
        (df_out['_month_dt'].dt.month.between(1, 6))
    ].drop(columns=['_month_dt'])

    df_h1_all = df_h1_all.sort_values(['평가월', '센터명']).reset_index(drop=True)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_h1_all.to_excel(writer, sheet_name=f'{this_year}년_상반기_RAW', index=False)

    output.seek(0)
    return output.getvalue()
