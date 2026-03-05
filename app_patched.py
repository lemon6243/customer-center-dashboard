"""
도시가스 고객센터 성과 대시보드 (개선된 UI)
완전 무료 - 카드 등록 불필요
버전 2.0 - 안정성 개선
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from io import BytesIO

# 로컬 모듈
from data_loader import load_cumulative_data, validate_cumulative_data
from score_calculator import calculate_scores
from kpi_heatmap import show_kpi_heatmap  # ✅ KPI 히트맵 모듈

# 페이지 설정
st.set_page_config(
    page_title="고객센터 성과 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 전역 CSS (개선된 디자인) ====================
st.markdown("""
<style>
    /* 메인 헤더 */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    }
    
    /* 사이드바 네비게이션 스타일 */
    div.row-widget.stRadio > div {
        flex-direction: column;
        gap: 12px;
    }
    
    div.row-widget.stRadio > div > label {
        background-color: white;
        padding: 18px 20px;
        border-radius: 12px;
        border: 2px solid #e9ecef;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: 600;
        font-size: 17px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    div.row-widget.stRadio > div > label:hover {
        border-color: #667eea;
        background-color: #f8f9fa;
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    
    div.row-widget.stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        border-color: #667eea;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
        transform: translateX(5px);
    }
    
    /* 알림 메시지 */
    .stAlert {
        margin-top: 1rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
    }
    
    /* 메트릭 카드 */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* 사이드바 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        color: #667eea;
        font-weight: 700;
        font-size: 1.4rem;
        margin-top: 1rem;
    }
    
    /* 버튼 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 8px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
    }
    
    /* 다운로드 버튼 */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 8px rgba(40, 167, 69, 0.2);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
    }
    
    /* 모바일 반응형 */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem;
            padding: 1rem;
        }
        
        div.row-widget.stRadio > div > label {
            padding: 15px 16px;
            font-size: 15px;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.6rem;
        }
    }
    
    @media (max-width: 480px) {
        .main-header {
            font-size: 1.5rem;
            padding: 0.8rem;
        }
        
        div.row-widget.stRadio > div > label {
            padding: 12px 14px;
            font-size: 14px;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.3rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==================== 유틸리티 함수 ====================

def get_device_type():
    """디바이스 타입 감지"""
    if 'device_type' not in st.session_state:
        st.session_state['device_type'] = 'desktop'
    return st.session_state['device_type']

def get_responsive_columns(desktop_cols=4, tablet_cols=2, mobile_cols=1):
    """반응형 컬럼 수 반환"""
    device = get_device_type()
    
    if device == 'mobile':
        return mobile_cols
    elif device == 'tablet':
        return tablet_cols
    else:
        return desktop_cols

@st.cache_data(ttl=3600, show_spinner=False)  # 1시간 캐시, 스피너 비활성화
def load_latest_data_from_github():
    """GitHub에 저장된 최신 데이터 로드 (개선된 버전)"""
    data_path = "data/latest_data.xlsx"
    
    # 파일 존재 여부 확인
    if not os.path.exists(data_path):
        return None
    
    try:
        # 파일 크기 확인
        file_size = os.path.getsize(data_path)
        if file_size == 0:
            st.error("❌ 데이터 파일이 비어있습니다.")
            return None
        
        # 파일 읽기 시도
        df = pd.read_excel(data_path, engine='openpyxl')
        
        # 데이터 유효성 검증
        if df.empty:
            st.error("❌ 데이터가 비어있습니다.")
            return None
        
        # 필수 컬럼 확인
        required_cols = ['센터명', '평가월']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"❌ 필수 컬럼 누락: {missing_cols}")
            return None
        
        # 날짜 변환
        if '평가월' in df.columns:
            df['평가월'] = pd.to_datetime(df['평가월'], errors='coerce')
            
            # 날짜 변환 실패 확인
            if df['평가월'].isna().all():
                st.error("❌ 평가월 데이터를 날짜로 변환할 수 없습니다.")
                return None
        
        # 점수 컬럼 확인 및 계산
        required_score_cols = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수', '목표달성여부'
        ]
        
        missing_score_cols = [col for col in required_score_cols if col not in df.columns]
        
        if missing_score_cols:
            try:
                df = calculate_scores(df)
            except Exception as e:
                st.error(f"❌ 점수 계산 실패: {e}")
                return None
        
        return df
        
    except PermissionError:
        st.error("❌ 파일 접근 권한이 없습니다.")
        return None
    except pd.errors.EmptyDataError:
        st.error("❌ 엑셀 파일이 손상되었거나 비어있습니다.")
        return None
    except ValueError as e:
        st.error(f"❌ 데이터 형식 오류: {e}")
        return None
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())
        return None

def convert_df_to_excel(df):
    """DataFrame을 Excel 바이트로 변환"""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='성과데이터')
        output.seek(0)
        return output.getvalue()
    except Exception as e:
        st.error(f"❌ Excel 변환 실패: {e}")
        return None

def calculate_predicted_score_v2(row, current_month):
    """개선된 예측 점수 계산"""
    try:
        if current_month >= 6:
            return {
                '예측총점': row['총점'],
                '안전점검_예측': row.get('안전점검_점수', 0),
                '중점고객_예측': row.get('중점고객_점수', 0),
                '사용계약_예측': row.get('사용계약_점수', 0),
                '상담응대_예측': row.get('상담응대_점수', 0),
                '상담기여_예측': row.get('상담기여_점수', 0),
                '만족도_예측': row.get('만족도_점수', 0),
                '조정항목': row.get('민원대응적정성', 0) + row.get('주의경고', 0) + row.get('가점', 0)
            }
        
        progress_rate = current_month / 6
        
        안전점검_현재 = row.get('안전점검_점수', 0)
        중점고객_현재 = row.get('중점고객_점수', 0)
        사용계약_현재 = row.get('사용계약_점수', 0)
        
        안전점검_예측 = min(안전점검_현재 / progress_rate, 550)
        중점고객_예측 = min(중점고객_현재 / progress_rate, 100)
        사용계약_예측 = min(사용계약_현재 * 1.1, 50)
        
        상담응대_현재 = row.get('상담응대_점수', 0)
        상담기여_현재 = row.get('상담기여_점수', 0)
        만족도_현재 = row.get('만족도_점수', 0)
        
        상담응대_예측 = 상담응대_현재
        상담기여_예측 = 상담기여_현재
        만족도_예측 = 만족도_현재
        
        조정항목 = row.get('민원대응적정성', 0) + row.get('주의경고', 0) + row.get('가점', 0)
        
        예측총점 = (
            안전점검_예측 + 
            중점고객_예측 + 
            사용계약_예측 + 
            상담응대_예측 + 
            상담기여_예측 + 
            만족도_예측 + 
            조정항목
        )
        
        예측총점 = min(예측총점, 1000)
        
        return {
            '예측총점': 예측총점,
            '안전점검_예측': 안전점검_예측,
            '중점고객_예측': 중점고객_예측,
            '사용계약_예측': 사용계약_예측,
            '상담응대_예측': 상담응대_예측,
            '상담기여_예측': 상담기여_예측,
            '만족도_예측': 만족도_예측,
            '조정항목': 조정항목
        }
    except Exception as e:
        st.error(f"❌ 예측 점수 계산 오류: {e}")
        return {
            '예측총점': 0,
            '안전점검_예측': 0,
            '중점고객_예측': 0,
            '사용계약_예측': 0,
            '상담응대_예측': 0,
            '상담기여_예측': 0,
            '만족도_예측': 0,
            '조정항목': 0
        }

def get_risk_level(predicted_score, current_month):
    """예측 점수 기반 위험도 판정"""
    gap = predicted_score - 911
    
    if current_month >= 6:
        if gap >= 0:
            return "안전", "#28a745", "🟢"
        elif gap >= -30:
            return "주의", "#ffc107", "🟡"
        elif gap >= -60:
            return "경고", "#fd7e14", "🟠"
        else:
            return "심각", "#dc3545", "🔴"
    else:
        if gap >= 50:
            return "안전", "#28a745", "🟢"
        elif gap >= 0:
            return "양호", "#20c997", "🟢"
        elif gap >= -30:
            return "주의", "#ffc107", "🟡"
        elif gap >= -60:
            return "경고", "#fd7e14", "🟠"
        else:
            return "위험", "#dc3545", "🔴"

# ==================== 사이드바 네비게이션 ====================

def sidebar_navigation():
    """사이드바 네비게이션 메뉴"""
    with st.sidebar:
        st.markdown("## 📍 빠른 메뉴")
        
        if 'current_page' not in st.session_state:
            st.session_state['current_page'] = '📊 전체 현황'
        
        menu_options = [
            "📊 전체 현황",
            "📈 월별 추이", 
            "🎯 센터별 상세",
            "⚠️ 위험 관리",
            "🌡️ KPI 히트맵",     # ✅ 신규 추가
            "📊 데이터 분석",
            "📋 원본 데이터"
        ]
        
        selected_page = st.radio(
            "페이지 이동",
            menu_options,
            index=menu_options.index(st.session_state['current_page']) 
                  if st.session_state['current_page'] in menu_options 
                  else 0,
            label_visibility="collapsed"
        )
        
        st.session_state['current_page'] = selected_page
        
        st.markdown("---")
        
    return selected_page

# ==================== 데이터 분석 함수들 ====================

@st.cache_data(ttl=3600, max_entries=10, show_spinner=False)
def calculate_correlation_matrix(df: pd.DataFrame):
    """지표 간 상관관계 매트릭스 계산"""
    try:
        numeric_cols = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수'
        ]
        
        available_cols = [col for col in numeric_cols if col in df.columns]
        
        if len(available_cols) >= 2:
            return df[available_cols].corr()
        return None
    except Exception as e:
        st.error(f"❌ 상관관계 계산 오류: {e}")
        return None

def show_correlation_analysis(df: pd.DataFrame):
    """📊 지표 간 상관관계 분석"""
    st.subheader("📊 지표 간 상관관계 분석")
    
    with st.spinner("🔍 상관관계 분석 중..."):
        corr_matrix = calculate_correlation_matrix(df)
    
    if corr_matrix is None:
        st.warning("⚠️ 상관관계 분석을 위한 데이터가 부족합니다.")
        return
    
    device = get_device_type()
    
    try:
        if device == 'mobile':
            fig = px.imshow(
                corr_matrix,
                text_auto='.2f',
                color_continuous_scale='RdBu_r',
                title="지표 간 상관계수",
                labels=dict(color="상관계수"),
                aspect='auto'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            show_strong_correlations(corr_matrix)
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = px.imshow(
                    corr_matrix,
                    text_auto='.2f',
                    color_continuous_scale='RdBu_r',
                    title="지표 간 상관계수",
                    labels=dict(color="상관계수")
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                show_strong_correlations(corr_matrix)
    except Exception as e:
        st.error(f"❌ 차트 생성 오류: {e}")

def show_strong_correlations(corr_matrix):
    """강한 상관관계 표시"""
    st.markdown("### 🔍 강한 상관관계")
    
    try:
        strong_corr = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:
                    strong_corr.append({
                        '지표1': corr_matrix.columns[i].replace('_점수', ''),
                        '지표2': corr_matrix.columns[j].replace('_점수', ''),
                        '상관계수': f"{corr_value:.3f}",
                        '관계': '양의 상관' if corr_value > 0 else '음의 상관'
                    })
        
        if strong_corr:
            st.dataframe(
                pd.DataFrame(strong_corr),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption("""
            💡 **해석**
            - 상관계수 > 0.7: 강한 양의 상관관계 (함께 증가)
            - 상관계수 < -0.7: 강한 음의 상관관계 (반대로 변화)
            """)
        else:
            st.info("💡 강한 상관관계(|r| > 0.7)가 발견되지 않았습니다.")
    except Exception as e:
        st.error(f"❌ 상관관계 분석 오류: {e}")

def detect_outliers(df: pd.DataFrame):
    """🔍 IQR 기반 이상치 탐지"""
    st.subheader("🔍 이상치 탐지")
    
    try:
        with st.spinner("🔍 이상치 분석 중..."):
            numeric_cols = ['총점', '안전점검_점수', '중점고객_점수', '사용계약_점수']
            available_cols = [col for col in numeric_cols if col in df.columns]
            
            if not available_cols:
                st.warning("⚠️ 분석 가능한 데이터가 없습니다.")
                return
            
            outliers_detected = []
            
            for col in available_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
                
                if len(outliers) > 0:
                    outliers_detected.append({
                        '지표': col.replace('_점수', ''),
                        '이상치 건수': len(outliers),
                        '정상 범위': f"{lower_bound:.1f} ~ {upper_bound:.1f}",
                        '센터 수': outliers['센터명'].nunique()
                    })
        
        if outliers_detected:
            st.warning(f"⚠️ {len(outliers_detected)}개 지표에서 이상치 발견")
            
            df_outliers = pd.DataFrame(outliers_detected)
            st.dataframe(df_outliers, use_container_width=True, hide_index=True)
            
            device = get_device_type()
            
            if device == 'mobile':
                with st.expander("📊 이상치 상세 보기"):
                    show_outlier_details(df, available_cols)
            else:
                show_outlier_details(df, available_cols)
        else:
            st.success("✅ 이상치가 발견되지 않았습니다.")
        
        st.caption("""
        💡 **IQR(Interquartile Range) 방식**
        - 정상 범위: Q1 - 1.5×IQR ~ Q3 + 1.5×IQR
        - 이상치: 정상 범위를 벗어난 값
        """)
    except Exception as e:
        st.error(f"❌ 이상치 탐지 오류: {e}")

def show_outlier_details(df: pd.DataFrame, cols: list):
    """이상치 상세 정보 표시"""
    try:
        for col in cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            
            if len(outliers) > 0:
                st.markdown(f"**{col.replace('_점수', '')} 이상치 센터:**")
                outlier_list = []
                for _, row in outliers.iterrows():
                    outlier_list.append(
                        f"- {row['센터명']}: {row[col]:.1f}점"
                    )
                st.markdown("\n".join(outlier_list[:5]))
                
                if len(outliers) > 5:
                    st.caption(f"... 외 {len(outliers)-5}개")
    except Exception as e:
        st.error(f"❌ 이상치 상세 정보 표시 오류: {e}")

def analyze_score_distribution(df: pd.DataFrame):
    """📊 점수 분포 분석"""
    st.subheader("📊 점수 분포 분석")
    
    try:
        with st.spinner("📊 분포 분석 중..."):
            latest_month = df['평가월'].max()
            df_latest = df[df['평가월'] == latest_month]
            
            device = get_device_type()
            
            if device == 'mobile':
                show_distribution_chart(df_latest, '총점')
                show_distribution_stats(df_latest)
            else:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    show_distribution_chart(df_latest, '총점')
                
                with col2:
                    show_distribution_stats(df_latest)
    except Exception as e:
        st.error(f"❌ 점수 분포 분석 오류: {e}")

def show_distribution_chart(df: pd.DataFrame, col: str):
    """분포 히스토그램"""
    try:
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df[col],
            nbinsx=20,
            marker_color='#003366',
            opacity=0.7,
            name='분포'
        ))
        
        fig.add_vline(
            x=911,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text="목표: 911점"
        )
        
        mean_val = df[col].mean()
        fig.add_vline(
            x=mean_val,
            line_dash="dot",
            line_color="red",
            line_width=2,
            annotation_text=f"평균: {mean_val:.1f}"
        )
        
        fig.update_layout(
            title=f"{col.replace('_점수', '')} 분포",
            xaxis_title="점수",
            yaxis_title="센터 수",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ 분포 차트 생성 오류: {e}")

def show_distribution_stats(df: pd.DataFrame):
    """분포 통계"""
    try:
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
    except Exception as e:
        st.error(f"❌ 통계 요약 생성 오류: {e}")

# ==================== 페이지 함수들 ====================

def show_overview(df: pd.DataFrame):
    """전체 현황 탭"""
    try:
        required_cols = ['총점', '목표달성여부']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"❌ 필수 컬럼 누락: {missing}")
            return
        
        latest_month = df['평가월'].max()
        df_latest = df[df['평가월'] == latest_month].copy()
        
        current_month = latest_month.month
        is_first_half = current_month <= 6
        period_month = current_month if is_first_half else current_month - 6
        
        with st.spinner("🔮 예측 점수 계산 중..."):
            prediction_results = df_latest.apply(
                lambda row: calculate_predicted_score_v2(row, period_month),
                axis=1
            )
        
        df_latest['예측점수'] = prediction_results.apply(lambda x: x['예측총점'])
        df_latest['안전점검_예측'] = prediction_results.apply(lambda x: x['안전점검_예측'])
        df_latest['중점고객_예측'] = prediction_results.apply(lambda x: x['중점고객_예측'])
        df_latest['사용계약_예측'] = prediction_results.apply(lambda x: x['사용계약_예측'])
        df_latest['상담응대_예측'] = prediction_results.apply(lambda x: x['상담응대_예측'])
        df_latest['상담기여_예측'] = prediction_results.apply(lambda x: x['상담기여_예측'])
        df_latest['만족도_예측'] = prediction_results.apply(lambda x: x['만족도_예측'])
        
        device = get_device_type()
        col_count = get_responsive_columns(desktop_cols=4, tablet_cols=2, mobile_cols=2)
        
        cols = st.columns(col_count)
        
        avg_score = df_latest['총점'].mean()
        avg_predicted = df_latest['예측점수'].mean()
        target_achieved = (df_latest['예측점수'] >= 911).sum()
        total_centers = len(df_latest)
        
        with cols[0]:
            st.metric(
                label="📊 평균 점수",
                value=f"{avg_score:.1f}",
                delta=f"예측: {avg_predicted:.1f}",
                help="현재 누적 점수 및 6월 예측 점수"
            )
        
        with cols[1]:
            achievement_rate = target_achieved / total_centers * 100
            st.metric(
                label="🎯 목표 달성",
                value=f"{target_achieved}/{total_centers}",
                delta=f"{achievement_rate:.1f}%",
                help="예측 점수 911점 이상 센터 수"
            )
        
        if col_count >= 3:
            with cols[2]:
                period_text = f"상반기 {period_month}월" if is_first_half else f"하반기 {period_month}월"
                st.metric(
                    label="📅 현재 진행",
                    value=period_text,
                    delta=f"{period_month}/6개월"
                )
        
        if col_count >= 4:
            with cols[3]:
                st.metric(
                    label="🏁 목표 점수",
                    value="911점",
                    delta="반기 최종"
                )
        
        st.divider()
        
        if period_month < 6:
            st.info(f"""
            💡 **개선된 예측 로직 안내**
            - 현재: {period_text} (진행률 {period_month/6*100:.1f}%)
            - **누적형 지표** (안전점검, 중점고객, 사용계약): 진행률 기반 예측
            - **비누적형 지표** (상담응대, 상담기여, 만족도): 현재 점수 유지
            - 예측 총점은 **1000점을 초과하지 않도록** 제한됩니다
            - 최종 평가는 6월 데이터로 진행됩니다
            """)
        
        st.subheader(f"🏆 센터별 현재 점수 및 예측 ({latest_month.strftime('%Y년 %m월')} 기준)")
        
        df_sorted = df_latest.sort_values('총점', ascending=False).reset_index(drop=True)
        df_sorted['순위'] = range(1, len(df_sorted) + 1)
        
        df_chart = df_sorted.sort_values('총점', ascending=True)
        
        colors = ['#28a745' if x >= 911 else '#ffc107' if x >= 870 else '#dc3545' 
                  for x in df_chart['예측점수']]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            y=df_chart['센터명'],
            x=df_chart['총점'],
            orientation='h',
            marker=dict(color=colors, opacity=0.6),
            name='현재 점수',
            text=df_chart['총점'].round(1),
            textposition='inside',
            hovertemplate='<b>%{y}</b><br>현재: %{x:.1f}점<extra></extra>'
        ))
        
        if period_month < 6:
            fig.add_trace(go.Scatter(
                y=df_chart['센터명'],
                x=df_chart['예측점수'],
                mode='markers',
                marker=dict(
                    size=12,
                    color=colors,
                    symbol='diamond',
                    line=dict(width=2, color='white')
                ),
                name='6월 예측',
                hovertemplate='<b>%{y}</b><br>예측: %{x:.1f}점<extra></extra>'
            ))
        
        fig.add_vline(
            x=911,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text="목표: 911점",
            annotation_position="top right"
        )
        
        fig.add_vline(
            x=1000,
            line_dash="dot",
            line_color="red",
            line_width=1,
            annotation_text="만점: 1000점",
            annotation_position="bottom right"
        )
        
        chart_height = 400 if device == 'mobile' else 600
        
        fig.update_layout(
            xaxis_title="점수",
            yaxis_title="",
            height=chart_height,
            showlegend=True,
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(range=[0, 1050])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("📋 상세 점수표 보기 (예측 점수 포함)"):
            display_cols = ['순위', '센터명', '총점', '예측점수', '목표대비', 
                           '안전점검_점수', '중점고객_점수', '사용계약_점수',
                           '상담응대_점수', '상담기여_점수', '만족도_점수']
            
            df_display = df_sorted[display_cols].copy()
            df_display['목표대비'] = (df_display['예측점수'] - 911).round(1)
            
            st.dataframe(
                df_display.style.format({
                    '총점': '{:.1f}',
                    '예측점수': '{:.1f}',
                    '목표대비': '{:+.1f}',
                    '안전점검_점수': '{:.1f}',
                    '중점고객_점수': '{:.1f}',
                    '사용계약_점수': '{:.1f}',
                    '상담응대_점수': '{:.1f}',
                    '상담기여_점수': '{:.1f}',
                    '만족도_점수': '{:.1f}'
                }).background_gradient(subset=['예측점수'], cmap='RdYlGn', vmin=850, vmax=950),
                use_container_width=True,
                hide_index=True,
                height=600
            )
    except Exception as e:
        st.error(f"❌ 전체 현황 표시 오류: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())

def show_trend_analysis(df: pd.DataFrame):
    """월별 추이 분석"""
    try:
        st.subheader("🎯 센터별 추이 비교")
        
        # 전체 센터를 기본값으로 설정
        centers = st.multiselect(
            "비교할 센터 선택",
            options=sorted(df['센터명'].unique()),
            default=sorted(df['센터명'].unique()),
            help="비교하고 싶은 센터를 선택하세요. 기본값은 전체 센터입니다."
        )
        
        if not centers:
            st.warning("⚠️ 센터를 선택하세요.")
            return
        
        df_filtered = df[df['센터명'].isin(centers)]
        
        fig = px.line(
            df_filtered,
            x='평가월',
            y='총점',
            color='센터명',
            markers=True,
            title='센터별 월별 총점 추이',
            labels={'총점': '총점 (점)', '평가월': '평가월'}
        )
        
        fig.add_hline(
            y=911,
            line_dash="dash",
            line_color="orange",
            line_width=2,
            annotation_text="목표: 911점",
            annotation_position="right"
        )
        
        fig.update_layout(
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=1.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.subheader("📊 항목별 추이")
        
        kpi_options = {
            '안전점검': '안전점검_점수',
            '중점고객': '중점고객_점수',
            '사용계약': '사용계약_점수',
            '상담응대': '상담응대_점수',
            '상담기여': '상담기여_점수',
            '만족도': '만족도_점수'
        }
        
        selected_kpi = st.selectbox(
            "분석할 항목 선택",
            options=list(kpi_options.keys())
        )
        
        kpi_col = kpi_options[selected_kpi]
        
        if kpi_col in df_filtered.columns:
            fig2 = px.line(
                df_filtered,
                x='평가월',
                y=kpi_col,
                color='센터명',
                markers=True,
                title=f'{selected_kpi} 월별 추이',
                labels={kpi_col: f'{selected_kpi} 점수', '평가월': '평가월'}
            )
            
            fig2.update_layout(
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(f"❌ 추이 분석 오류: {e}")

def show_center_detail(df: pd.DataFrame):
    """센터별 상세 분석"""
    try:
        device = get_device_type()
        
        if device == 'mobile':
            center_name = st.selectbox(
                "센터 선택",
                options=sorted(df['센터명'].unique())
            )
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                center_name = st.selectbox(
                    "센터 선택",
                    options=sorted(df['센터명'].unique())
                )
        
        df_center = df[df['센터명'] == center_name].sort_values('평가월')
        
        latest = df_center.iloc[-1]
        
        current_month = latest['평가월'].month
        is_first_half = current_month <= 6
        period_month = current_month if is_first_half else current_month - 6
        
        prediction = calculate_predicted_score_v2(latest, period_month)
        predicted_score = prediction['예측총점']
        
        col_count = get_responsive_columns(desktop_cols=4, tablet_cols=2, mobile_cols=2)
        cols = st.columns(col_count)
        
        with cols[0]:
            st.metric(
                label="현재 총점",
                value=f"{latest['총점']:.1f}점",
                delta=f"{latest['총점'] - 911:.1f}점"
            )
        
        with cols[1]:
            if period_month < 6:
                st.metric(
                    label="6월 예측",
                    value=f"{predicted_score:.1f}점",
                    delta=f"{predicted_score - 911:.1f}점",
                    help="개선된 예측 로직 적용"
                )
            else:
                status_emoji = "✅" if latest.get('목표달성여부', False) else "❌"
                status_text = "달성" if latest.get('목표달성여부', False) else "미달성"
                st.metric(
                    label="목표 달성",
                    value=status_text,
                    delta=status_emoji
                )
        
        if col_count >= 3:
            with cols[2]:
                latest_month_df = df[df['평가월'] == df['평가월'].max()]
                rank = (latest_month_df['총점'] >= latest['총점']).sum()
                st.metric(
                    label="전체 순위",
                    value=f"{rank}위",
                    delta=f"/ {df['센터명'].nunique()}개"
                )
        
        if col_count >= 4:
            with cols[3]:
                period_text = f"상반기 {period_month}월" if is_first_half else f"하반기 {period_month}월"
                st.metric(
                    label="진행 상황",
                    value=period_text,
                    delta=f"{period_month/6*100:.1f}%"
                )
        
        st.divider()
        
        st.subheader("📊 항목별 점수 (레이더 차트)")
        
        categories = ['안전점검', '중점고객', '사용계약', '상담응대', '상담기여', '만족도']
        
        scores = [
            latest.get('안전점검_점수', 0),
            latest.get('중점고객_점수', 0),
            latest.get('사용계약_점수', 0),
            latest.get('상담응대_점수', 0),
            latest.get('상담기여_점수', 0),
            latest.get('만족도_점수', 0)
        ]
        
        max_scores = [550, 100, 50, 100, 100, 100]
        
        normalized_scores = [s/m*100 for s, m in zip(scores, max_scores)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=normalized_scores,
            theta=categories,
            fill='toself',
            name=center_name,
            line_color='#667eea'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=500,
            title=f"{center_name} 항목별 달성률 (%)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ 센터별 상세 분석 오류: {e}")

def show_risk_management(df: pd.DataFrame):
    """위험 관리"""
    try:
        latest_month = df['평가월'].max()
        df_latest = df[df['평가월'] == latest_month].copy()
        
        current_month = latest_month.month
        is_first_half = current_month <= 6
        period_month = current_month if is_first_half else current_month - 6
        
        with st.spinner("🔮 위험도 분석 중..."):
            prediction_results = df_latest.apply(
                lambda row: calculate_predicted_score_v2(row, period_month),
                axis=1
            )
            
            df_latest['예측점수'] = prediction_results.apply(lambda x: x['예측총점'])
        
        risk_centers = df_latest[df_latest['예측점수'] < 911].copy()
        
        if len(risk_centers) == 0:
            st.success("🎉 모든 센터가 목표 달성 예상입니다!")
            return
        
        st.warning(f"⚠️ **{len(risk_centers)}개 센터**가 목표 점수 미달 예상")
        
        for _, row in risk_centers.iterrows():
            risk_level, color, icon = get_risk_level(row['예측점수'], period_month)
            
            with st.container():
                st.markdown(f"""
                <div style="
                    background-color: {color}22;
                    border-left: 5px solid {color};
                    padding: 1rem;
                    border-radius: 5px;
                    margin-bottom: 1rem;
                ">
                    <h3 style="color: {color}; margin: 0;">
                        {icon} {row['센터명']} - {risk_level}
                    </h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("현재 점수", f"{row['총점']:.1f}")
                
                with col2:
                    st.metric("예측 점수", f"{row['예측점수']:.1f}")
                
                with col3:
                    gap = row['예측점수'] - 911
                    st.metric("목표 대비", f"{gap:+.1f}", delta_color="inverse")
                
                st.markdown("---")
    except Exception as e:
        st.error(f"❌ 위험 관리 분석 오류: {e}")

def show_data_analysis(df: pd.DataFrame):
    """데이터 분석"""
    try:
        device = get_device_type()
        
        if device == 'mobile':
            analysis_type = st.selectbox(
                "분석 유형 선택",
                options=["상관관계 분석", "이상치 탐지", "점수 분포 분석"]
            )
            
            if analysis_type == "상관관계 분석":
                show_correlation_analysis(df)
            elif analysis_type == "이상치 탐지":
                detect_outliers(df)
            else:
                analyze_score_distribution(df)
        else:
            subtab1, subtab2, subtab3 = st.tabs([
                "📊 상관관계 분석",
                "🔍 이상치 탐지",
                "📈 점수 분포"
            ])
            
            with subtab1:
                show_correlation_analysis(df)
            
            with subtab2:
                detect_outliers(df)
            
            with subtab3:
                analyze_score_distribution(df)
    except Exception as e:
        st.error(f"❌ 데이터 분석 오류: {e}")

def show_raw_data_verification(df: pd.DataFrame):
    """원본 데이터 확인"""
    try:
        st.dataframe(
            df,
            use_container_width=True,
            height=600
        )
        
        excel_data = convert_df_to_excel(df)
        
        if excel_data:
            st.download_button(
                label="💾 데이터 다운로드 (Excel)",
                data=excel_data,
                file_name=f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"❌ 데이터 표시 오류: {e}")

# ==================== 메인 함수 ====================

def main():
    """메인 함수"""
    
    try:
        # 타이틀
        st.markdown('<div class="main-header">🏢 도시가스 고객센터 성과 대시보드</div>', 
                    unsafe_allow_html=True)
        
        # 세션 상태 초기화 - 개선된 버전
        if 'df' not in st.session_state or st.session_state.get('df') is None:
            with st.spinner("📊 데이터 로드 중..."):
                try:
                    df_github = load_latest_data_from_github()
                    st.session_state['df'] = df_github
                    
                    if df_github is not None:
                        st.success("✅ 데이터 로드 완료!", icon="✅")
                    else:
                        st.info("💡 저장된 데이터가 없습니다. 사이드바에서 새 데이터를 업로드해주세요.")
                        
                except Exception as e:
                    st.error(f"❌ 데이터 로드 중 오류: {e}")
                    st.session_state['df'] = None
        
        # ⭐ 사이드바 네비게이션 (최상단 배치)
        selected_page = sidebar_navigation()
        
        # 사이드바: 데이터 관리
        with st.sidebar:
            st.header("📂 데이터 관리")
            
            # 현재 데이터 정보
            if st.session_state.get('df') is not None:
                df = st.session_state['df']
                
                st.success("✅ 데이터 로드됨")
                
                st.info(f"""
                📌 **현재 데이터**
                - 총 행수: {len(df):,}
                - 센터 수: {df['센터명'].nunique()}개
                - 평가 기간: {df['평가월'].min().strftime('%Y-%m')} ~ {df['평가월'].max().strftime('%Y-%m')}
                - 최종 업데이트: GitHub 최신 버전
                """)
            else:
                st.warning("⚠️ 데이터가 없습니다.")
            
            st.divider()
            
            # 새 데이터 업로드
            st.subheader("📤 새 데이터 업로드")
            
            uploaded_file = st.file_uploader(
                "엑셀 파일 선택 (xlsx)",
                type=['xlsx'],
                help="월별 평가 데이터가 포함된 엑셀 파일을 업로드하세요"
            )
            
            if uploaded_file:
                with st.spinner("📊 데이터 처리 중..."):
                    try:
                        df_raw = load_cumulative_data(uploaded_file)
                        is_valid, message = validate_cumulative_data(df_raw)
                        
                        if is_valid:
                            st.success("✅ 데이터 검증 완료")
                            df_scored = calculate_scores(df_raw)
                            st.session_state['df'] = df_scored
                            
                            st.info(f"""
                            📊 **처리 완료**
                            - 총 {len(df_scored):,}행
                            - {df_scored['센터명'].nunique()}개 센터
                            - {df_scored['평가월'].nunique()}개월 데이터
                            """)
                            
                            excel_data = convert_df_to_excel(df_scored)
                            
                            if excel_data:
                                st.download_button(
                                    label="💾 처리된 데이터 다운로드",
                                    data=excel_data,
                                    file_name=f"latest_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    help="이 파일을 data/latest_data.xlsx로 저장 후 GitHub에 업로드하세요"
                                )
                                
                                st.warning("""
                                ⚠️ **다음 단계:**
                                1. 위 버튼으로 파일 다운로드
                                2. `data/latest_data.xlsx`로 저장
                                3. GitHub에 커밋 & 푸시
                                """)
                        else:
                            st.error("❌ 데이터 검증 실패")
                            for msg in message:
                                st.error(msg)
                            
                    except Exception as e:
                        st.error(f"❌ 오류 발생: {e}")
                        import traceback
                        with st.expander("🔍 상세 오류 (개발자용)"):
                            st.code(traceback.format_exc())
            
            st.divider()
            
            # 필터 옵션
            if st.session_state.get('df') is not None:
                df = st.session_state['df']
                
                st.subheader("🔍 필터")
                
                months = sorted(df['평가월'].dt.to_period('M').unique())
                selected_months = st.multiselect(
                    "평가월 선택",
                    options=months,
                    default=months,
                    format_func=lambda x: x.strftime('%Y년 %m월')
                )
                
                centers = sorted(df['센터명'].unique())
                selected_centers = st.multiselect(
                    "센터 선택",
                    options=centers,
                    default=centers
                )
                
                if selected_months and selected_centers:
                    df_filtered = df[
                        (df['평가월'].dt.to_period('M').isin(selected_months)) &
                        (df['센터명'].isin(selected_centers))
                    ]
                    st.session_state['df_filtered'] = df_filtered
                    st.caption(f"필터 결과: {len(df_filtered):,}행")
                else:
                    st.session_state['df_filtered'] = df
            
            st.divider()
            
            with st.expander("📖 배점 규칙"):
                st.markdown("""
                **총점: 1000점**
                
                - 안전점검: 550점
                - 중점고객: 100점
                - 사용계약: 50점
                - 상담응대: 100점
                - 상담기여: 100점
                - 만족도: 100점
                
                **목표: 911점 이상**
                """)
            
            # 디바이스 타입 선택 (개발/테스트용)
            with st.expander("⚙️ 화면 설정"):
                device = st.radio(
                    "디바이스 모드",
                    options=['desktop', 'tablet', 'mobile'],
                    index=0,
                    format_func=lambda x: {'desktop': '🖥️ 데스크톱', 'tablet': '📱 태블릿', 'mobile': '📱 모바일'}[x]
                )
                st.session_state['device_type'] = device
                st.caption("실제 배포 시에는 자동 감지됩니다")
            
            # 캐시 초기화 버튼
            st.divider()
            if st.button("🔄 캐시 초기화", help="데이터 로딩 문제가 있을 때 사용하세요"):
                st.cache_data.clear()
                st.session_state.clear()
                st.success("✅ 캐시가 초기화되었습니다. 페이지를 새로고침하세요.")
                st.rerun()
        
        # 메인 화면
        if st.session_state.get('df') is None:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.info("""
                ### 👋 환영합니다!
                
                **시작하기:**
                1. 왼쪽 사이드바에서 엑셀 파일 업로드
                2. 처리된 데이터 다운로드
                3. GitHub에 업로드하여 팀 공유
                
                **또는**
                
                `data/latest_data.xlsx` 파일이 있다면 자동으로 로드됩니다.
                """)
        else:
            df = st.session_state.get('df_filtered', st.session_state['df'])
            
            # ⭐⭐⭐ 사이드바 네비게이션으로 직접 페이지 전환 ⭐⭐⭐
            if selected_page == "📊 전체 현황":
                show_overview(df)
            elif selected_page == "📈 월별 추이":
                show_trend_analysis(df)
            elif selected_page == "🎯 센터별 상세":
                show_center_detail(df)
            elif selected_page == "⚠️ 위험 관리":
                show_risk_management(df)
            elif selected_page == "🌡️ KPI 히트맵":   # ✅ 신규 추가
                show_kpi_heatmap(df)
            elif selected_page == "📊 데이터 분석":
                show_data_analysis(df)
            elif selected_page == "📋 원본 데이터":
                show_raw_data_verification(df)
    
    except Exception as e:
        st.error(f"❌ 앱 실행 중 오류 발생: {e}")
        import traceback
        with st.expander("🔍 상세 오류 정보"):
            st.code(traceback.format_exc())


if __name__ == "__main__":
    main()