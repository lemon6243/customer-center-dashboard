"""
데이터 분석 페이지
- 상관관계 분석
- 이상치 탐지 (IQR)
- 점수 분포 분석
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.styles import Colors, ScoreThresholds, PLOTLY_LAYOUT


# ==================== 점수 컬럼 정의 ====================
KPI_SCORE_COLS = [
    '안전점검_점수', '중점고객_점수', '사용계약_점수',
    '상담응대_점수', '상담기여_점수', '만족도_점수'
]


def show(df: pd.DataFrame, device_type: str = 'desktop'):
    """데이터 분석 페이지 메인 함수"""
    
    try:
        if device_type == 'mobile':
            # 모바일: 셀렉트박스로 전환
            analysis_type = st.selectbox(
                "분석 유형 선택",
                options=["상관관계 분석", "이상치 탐지", "점수 분포 분석"]
            )
            
            if analysis_type == "상관관계 분석":
                _show_correlation(df)
            elif analysis_type == "이상치 탐지":
                _show_outliers(df)
            else:
                _show_distribution(df)
        else:
            # 데스크톱: 탭으로 전환
            tab1, tab2, tab3 = st.tabs([
                "📊 상관관계 분석",
                "🔍 이상치 탐지",
                "📈 점수 분포"
            ])
            
            with tab1:
                _show_correlation(df)
            with tab2:
                _show_outliers(df)
            with tab3:
                _show_distribution(df)
                
    except Exception as e:
        st.error(f"❌ 데이터 분석 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


# ==================== 상관관계 분석 ====================

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def _calculate_correlation(df: pd.DataFrame):
    """상관관계 매트릭스 계산 (캐시)"""
    available_cols = [c for c in KPI_SCORE_COLS if c in df.columns]
    if len(available_cols) < 2:
        return None
    return df[available_cols].corr()


def _show_correlation(df: pd.DataFrame):
    """상관관계 분석 표시"""
    st.subheader("📊 지표 간 상관관계 분석")
    
    with st.spinner("🔍 상관관계 분석 중..."):
        corr_matrix = _calculate_correlation(df)
    
    if corr_matrix is None:
        st.warning("⚠️ 상관관계 분석을 위한 데이터가 부족합니다.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig = px.imshow(
            corr_matrix,
            text_auto='.2f',
            color_continuous_scale='RdBu_r',
            title="지표 간 상관계수",
            labels=dict(color="상관계수"),
        )
        fig.update_layout(height=500, **PLOTLY_LAYOUT)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        _show_strong_correlations(corr_matrix)


def _show_strong_correlations(corr_matrix):
    """강한 상관관계 표시"""
    st.markdown("### 🔍 강한 상관관계")
    
    strong_corr = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            value = corr_matrix.iloc[i, j]
            if abs(value) > 0.7:
                strong_corr.append({
                    '지표1': corr_matrix.columns[i].replace('_점수', ''),
                    '지표2': corr_matrix.columns[j].replace('_점수', ''),
                    '상관계수': f"{value:.3f}",
                    '관계': '양의 상관' if value > 0 else '음의 상관'
                })
    
    if strong_corr:
        st.dataframe(
            pd.DataFrame(strong_corr),
            use_container_width=True,
            hide_index=True
        )
        st.caption("""
        💡 **해석**
        - r > 0.7: 강한 양의 상관 (함께 증가)
        - r < -0.7: 강한 음의 상관 (반대로 변화)
        """)
    else:
        st.info("💡 강한 상관관계(|r| > 0.7)가 발견되지 않았습니다.")


# ==================== 이상치 탐지 ====================

def _show_outliers(df: pd.DataFrame):
    """IQR 기반 이상치 탐지"""
    st.subheader("🔍 이상치 탐지")
    
    target_cols = ['총점', '안전점검_점수', '중점고객_점수', '사용계약_점수']
    available_cols = [c for c in target_cols if c in df.columns]
    
    if not available_cols:
        st.warning("⚠️ 분석 가능한 데이터가 없습니다.")
        return
    
    outliers_detected = []
    
    for col in available_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        
        if len(outliers) > 0:
            outliers_detected.append({
                '지표': col.replace('_점수', ''),
                '이상치 건수': len(outliers),
                '정상 범위': f"{lower:.1f} ~ {upper:.1f}",
                '센터 수': outliers['센터명'].nunique()
            })
    
    if outliers_detected:
        st.warning(f"⚠️ {len(outliers_detected)}개 지표에서 이상치 발견")
        st.dataframe(
            pd.DataFrame(outliers_detected),
            use_container_width=True,
            hide_index=True
        )
        _show_outlier_details(df, available_cols)
    else:
        st.success("✅ 이상치가 발견되지 않았습니다.")
    
    st.caption("""
    💡 **IQR(Interquartile Range) 방식**
    - 정상 범위: Q1 - 1.5×IQR ~ Q3 + 1.5×IQR
    - 이상치: 정상 범위를 벗어난 값
    """)


def _show_outlier_details(df: pd.DataFrame, cols: list):
    """이상치 상세 정보"""
    for col in cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outliers = df[(df[col] < lower) | (df[col] > upper)]
        
        if len(outliers) > 0:
            st.markdown(f"**{col.replace('_점수', '')} 이상치 센터:**")
            items = []
            for _, row in outliers.iterrows():
                items.append(f"- {row['센터명']}: {row[col]:.1f}점")
            st.markdown("\n".join(items[:5]))
            if len(outliers) > 5:
                st.caption(f"... 외 {len(outliers)-5}개")


# ==================== 점수 분포 ====================

def _show_distribution(df: pd.DataFrame):
    """점수 분포 분석"""
    st.subheader("📊 점수 분포 분석")
    
    latest_month = df['평가월'].max()
    df_latest = df[df['평가월'] == latest_month]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        _show_distribution_chart(df_latest, '총점')
    
    with col2:
        _show_distribution_stats(df_latest)


def _show_distribution_chart(df: pd.DataFrame, col: str):
    """분포 히스토그램"""
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=df[col],
        nbinsx=20,
        marker_color=Colors.PRIMARY,
        opacity=0.7,
        name='분포'
    ))
    
    # 목표선
    fig.add_vline(
        x=ScoreThresholds.TARGET,
        line_dash="dash",
        line_color=Colors.WARNING,
        line_width=2,
        annotation_text=f"목표: {ScoreThresholds.TARGET}점"
    )
    
    # 평균선
    mean_val = df[col].mean()
    fig.add_vline(
        x=mean_val,
        line_dash="dot",
        line_color=Colors.DANGER,
        line_width=2,
        annotation_text=f"평균: {mean_val:.1f}"
    )
    
    fig.update_layout(
        title=f"{col.replace('_점수', '')} 분포",
        xaxis_title="점수",
        yaxis_title="센터 수",
        height=400,
        showlegend=False,
        **PLOTLY_LAYOUT,
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _show_distribution_stats(df: pd.DataFrame):
    """통계 요약"""
    st.markdown("### 📈 통계 요약")
    
    stats = {
        '평균': df['총점'].mean(),
        '중앙값': df['총점'].median(),
        '표준편차': df['총점'].std(),
        '최솟값': df['총점'].min(),
        '최댓값': df['총점'].max(),
        '범위': df['총점'].max() - df['총점'].min()
    }
    
    for key, value in stats.items():
        st.metric(key, f"{value:.1f}점")
    
    st.divider()
    
    Q1 = df['총점'].quantile(0.25)
    Q2 = df['총점'].quantile(0.50)
    Q3 = df['총점'].quantile(0.75)
    
    st.markdown("**📊 사분위수**")
    st.markdown(f"- Q1 (25%): {Q1:.1f}점")
    st.markdown(f"- Q2 (50%): {Q2:.1f}점")
    st.markdown(f"- Q3 (75%): {Q3:.1f}점")
