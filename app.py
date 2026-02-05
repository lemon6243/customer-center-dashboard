"""
도시가스 고객센터 성과 대시보드 (GitHub 데이터 저장 방식)
완전 무료 - 카드 등록 불필요
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

# 페이지 설정
st.set_page_config(
    page_title="고객센터 성과 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 전역 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #003366;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_latest_data_from_github():
    """
    GitHub에 저장된 최신 데이터 로드 (캐시 적용) + 점수 자동 계산
    
    핵심: raw 데이터에서 세부 점수 컬럼이 없으면 자동 계산
    """
    data_path = "data/latest_data.xlsx"
    
    if os.path.exists(data_path):
        try:
            df = pd.read_excel(data_path)
            
            # 평가월을 datetime으로 변환
            if '평가월' in df.columns:
                df['평가월'] = pd.to_datetime(df['평가월'])
            
            # ⭐ 핵심: 점수 계산 (세부 점수 컬럼 생성)
            required_score_cols = [
                '안전점검_점수', '중점고객_점수', '사용계약_점수',
                '상담응대_점수', '상담기여_점수', '만족도_점수', '목표달성여부'
            ]
            
            missing_cols = [col for col in required_score_cols if col not in df.columns]
            
            if missing_cols:
                df = calculate_scores(df)
            
            return df
            
        except Exception as e:
            st.error(f"❌ 데이터 로드 실패: {e}")
            import traceback
            st.code(traceback.format_exc())
            return None
    else:
        return None

def convert_df_to_excel(df):
    """DataFrame을 Excel 바이트로 변환 (다운로드용)"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='성과데이터')
    output.seek(0)
    return output.getvalue()

def calculate_predicted_score_v2(row, current_month):
    """
    개선된 예측 점수 계산 (항목별 특성 반영)
    
    Args:
        row: DataFrame의 한 행 (센터 데이터)
        current_month: 현재 월 (1~6)
    
    Returns:
        예측 총점 (딕셔너리: 항목별 예측 점수 포함)
    """
    if current_month >= 6:
        # 6월이면 현재 점수가 최종 점수
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
    
    # 진행률 계산
    progress_rate = current_month / 6
    
    # 1️⃣ 누적형 지표: 진행률 기반 예측
    안전점검_현재 = row.get('안전점검_점수', 0)
    중점고객_현재 = row.get('중점고객_점수', 0)
    사용계약_현재 = row.get('사용계약_점수', 0)
    
    안전점검_예측 = min(안전점검_현재 / progress_rate, 550)  # 최대 550점
    중점고객_예측 = min(중점고객_현재 / progress_rate, 100)  # 최대 100점
    
    # 사용계약은 등급제이므로 현재 등급 유지 또는 상승 가능성 고려
    # 보수적 예측: 현재 점수의 1.1배까지만 상승 가능 (최대 50점)
    사용계약_예측 = min(사용계약_현재 * 1.1, 50)
    
    # 2️⃣ 비누적형 지표: 현재 점수 기반 소폭 조정
    # 상담응대율, 상담기여도: 누적 콜 대비 처리 건수이므로 큰 변화 없음
    # 만족도: 누적 평균이므로 변화 적음
    상담응대_현재 = row.get('상담응대_점수', 0)
    상담기여_현재 = row.get('상담기여_점수', 0)
    만족도_현재 = row.get('만족도_점수', 0)
    
    # 보수적 예측: 현재 점수에서 ±5% 범위 내 변동 가능
    # 여기서는 현재 점수 그대로 유지 (가장 보수적)
    상담응대_예측 = 상담응대_현재
    상담기여_예측 = 상담기여_현재
    만족도_예측 = 만족도_현재
    
    # 3️⃣ 조정 항목 (민원, 주의경고, 가점)
    # 향후 발생 가능성이 있으므로 현재값 유지
    조정항목 = row.get('민원대응적정성', 0) + row.get('주의경고', 0) + row.get('가점', 0)
    
    # 4️⃣ 예측 총점 계산
    예측총점 = (
        안전점검_예측 + 
        중점고객_예측 + 
        사용계약_예측 + 
        상담응대_예측 + 
        상담기여_예측 + 
        만족도_예측 + 
        조정항목
    )
    
    # 안전장치: 1000점 초과 방지
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

def get_risk_level(predicted_score, current_month):
    """
    예측 점수 기반 위험도 판정
    
    Args:
        predicted_score: 6월 예측 점수
        current_month: 현재 월
    
    Returns:
        (위험레벨, 색상, 아이콘)
    """
    gap = predicted_score - 911
    
    # 6월인 경우 (최종 점수)
    if current_month >= 6:
        if gap >= 0:
            return "안전", "#28a745", "🟢"
        elif gap >= -30:
            return "주의", "#ffc107", "🟡"
        elif gap >= -60:
            return "경고", "#fd7e14", "🟠"
        else:
            return "심각", "#dc3545", "🔴"
    
    # 1~5월인 경우 (예측 기반)
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

def main():
    """메인 함수"""
    
    # 타이틀
    st.markdown('<div class="main-header">🏢 도시가스 고객센터 성과 대시보드</div>', 
                unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'df' not in st.session_state:
        df_github = load_latest_data_from_github()
        if df_github is not None:
            st.session_state['df'] = df_github
        else:
            st.session_state['df'] = None
    
    # ==================== 사이드바: 데이터 관리 ====================
    with st.sidebar:
        st.header("📂 데이터 관리")
        
        # 현재 데이터 정보
        if st.session_state['df'] is not None:
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
                        st.success(f"✅ {message}")
                        df_scored = calculate_scores(df_raw)
                        st.session_state['df'] = df_scored
                        
                        st.info(f"""
                        📊 **처리 완료**
                        - 총 {len(df_scored):,}행
                        - {df_scored['센터명'].nunique()}개 센터
                        - {df_scored['평가월'].nunique()}개월 데이터
                        """)
                        
                        excel_data = convert_df_to_excel(df_scored)
                        
                        st.download_button(
                            label="💾 처리된 데이터 다운로드",
                            data=excel_data,
                            file_name=f"latest_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="이 파일을 data/latest_data.xlsx로 저장 후 GitHub에 업로드하세요"
                        )
                    else:
                        st.error(f"❌ {message}")
                        
                except Exception as e:
                    st.error(f"❌ 오류 발생: {e}")
                    import traceback
                    with st.expander("🔍 상세 오류 (개발자용)"):
                        st.code(traceback.format_exc())
        
        st.divider()
        
        # 필터 옵션
        if st.session_state['df'] is not None:
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
        
        with st.expander("📖 배점 규칙 및 예측 방식"):
            st.markdown("""
            **총점: 1000점**
            
            ### 📊 점수 구성
            
            **1️⃣ 누적형 지표** (진행률 기반 예측)
            - **안전점검**: 최대 550점
            - **중점고객**: 최대 100점
            - **사용계약**: 최대 50점 (등급제)
              - A등급 (90% 이상): 50점
              - B등급 (80~90% 미만): 45점
              - C등급 (70~80% 미만): 40점
              - D등급 (70% 미만): 35점
            
            **2️⃣ 비누적형 지표** (현재 점수 유지)
            - **상담응대**: 최대 100점 (누적 인입콜 대비 처리건수)
            - **상담기여**: 최대 100점 (누적 인입콜 대비 처리건수)
            - **만족도**: 최대 100점 (누적 평균 점수)
            
            **3️⃣ 조정 항목**
            - 민원대응적정성 (감점)
            - 주의/경고 (감점)
            - 가점
            
            ---
            
            ### 🔮 예측 로직
            
            **누적형 지표**: 



            $$\\text{예측 점수} = \\frac{\\text{현재 점수}}{\\text{진행률}} \\text{ (최대값 제한)}$$
            
            **비누적형 지표**: 



            $$\\text{예측 점수} = \\text{현재 점수} \\text{ (변화 없음)}$$
            
            **최종 예측 총점**:
            - 누적형 지표 예측값 + 비누적형 지표 현재값 + 조정항목
            - **1000점 초과 방지** (안전장치)
            
            ---
            
            **목표: 911점 이상**
            
            ⚠️ **누적 평가 방식**
            - 1~6월: 상반기 누적
            - 6월 점수가 상반기 최종 점수
            """)
    
    # ==================== 메인 화면 ====================
    if st.session_state['df'] is None:
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
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 전체 현황",
            "📈 월별 누적 추이",
            "🎯 센터별 상세",
            "⚠️ 위험 관리",
            "📋 원본 데이터 확인"
        ])
        
        with tab1:
            show_overview(df)
        
        with tab2:
            show_trend_analysis(df)
        
        with tab3:
            show_center_detail(df)
        
        with tab4:
            show_risk_management(df)
        
        with tab5:
            show_raw_data_verification(df)

def show_overview(df: pd.DataFrame):
    """전체 현황 탭 - 개선된 예측 로직 적용 + 순위 추가"""
    st.header("📊 전체 현황")
    
    # 안전장치: 필수 컬럼 확인
    required_cols = ['총점', '목표달성여부']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        st.error(f"❌ 필수 컬럼 누락: {missing}")
        return
    
    latest_month = df['평가월'].max()
    df_latest = df[df['평가월'] == latest_month].copy()
    
    # 현재 월 계산 (1~12)
    current_month = latest_month.month
    is_first_half = current_month <= 6
    period_month = current_month if is_first_half else current_month - 6
    
    # 개선된 예측 점수 계산
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
    
    # KPI 카드
    col1, col2, col3, col4 = st.columns(4)
    
    avg_score = df_latest['총점'].mean()
    avg_predicted = df_latest['예측점수'].mean()
    target_achieved = (df_latest['예측점수'] >= 911).sum()
    total_centers = len(df_latest)
    
    with col1:
        st.metric(
            label="📊 현재 평균 점수",
            value=f"{avg_score:.1f}점",
            delta=f"예측: {avg_predicted:.1f}점",
            help="현재 누적 점수 및 6월 예측 점수"
        )
    
    with col2:
        achievement_rate = target_achieved / total_centers * 100
        st.metric(
            label="🎯 목표 달성 예상",
            value=f"{target_achieved}/{total_centers}",
            delta=f"{achievement_rate:.1f}%",
            help="예측 점수 911점 이상 센터 수"
        )
    
    with col3:
        period_text = f"상반기 {period_month}월" if is_first_half else f"하반기 {period_month}월"
        st.metric(
            label="📅 현재 진행",
            value=period_text,
            delta=f"{period_month}/6개월"
        )
    
    with col4:
        st.metric(
            label="🏁 목표 점수",
            value="911점",
            delta="반기 최종 기준"
        )
    
    st.divider()
    
    # 안내 메시지
    if period_month < 6:
        st.info(f"""
        💡 **개선된 예측 로직 안내**
        - 현재: {period_text} (진행률 {period_month/6*100:.1f}%)
        - **누적형 지표** (안전점검, 중점고객, 사용계약): 진행률 기반 예측
        - **비누적형 지표** (상담응대, 상담기여, 만족도): 현재 점수 유지
        - 예측 총점은 **1000점을 초과하지 않도록** 제한됩니다
        - 최종 평가는 6월 데이터로 진행됩니다
        """)
    
    # 센터별 순위 차트
    st.subheader(f"🏆 센터별 현재 점수 및 예측 ({latest_month.strftime('%Y년 %m월')} 기준)")
    
    # ⭐ 수정: 총점 기준 내림차순 정렬 후 순위 부여
    df_sorted = df_latest.sort_values('총점', ascending=False).reset_index(drop=True)
    df_sorted['순위'] = range(1, len(df_sorted) + 1)
    
    # 차트용: 오름차순 정렬 (하단부터 표시)
    df_chart = df_sorted.sort_values('총점', ascending=True)
    
    # 예측 점수 기준으로 색상 결정
    colors = ['#28a745' if x >= 911 else '#ffc107' if x >= 870 else '#dc3545' 
              for x in df_chart['예측점수']]
    
    fig = go.Figure()
    
    # 현재 점수
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
    
    # 예측 점수 (마커)
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
    
    # 911점 기준선
    fig.add_vline(
        x=911,
        line_dash="dash",
        line_color="orange",
        line_width=2,
        annotation_text="목표: 911점",
        annotation_position="top right"
    )
    
    # 1000점 기준선 (최대값)
    fig.add_vline(
        x=1000,
        line_dash="dot",
        line_color="red",
        line_width=1,
        annotation_text="만점: 1000점",
        annotation_position="bottom right"
    )
    
    fig.update_layout(
        xaxis_title="점수",
        yaxis_title="",
        height=600,
        showlegend=True,
        hovermode='closest',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(range=[0, 1050])  # x축 범위 설정
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ⭐ 수정: 상세 테이블 (순위 포함, 1위부터 24위까지)
    with st.expander("📋 상세 점수표 보기 (예측 점수 포함)"):
        # 순위 컬럼을 맨 앞에 배치
        display_cols = ['순위', '센터명', '총점']
        
        if period_month < 6:
            display_cols.extend(['예측점수', '안전점검_예측', '중점고객_예측', '사용계약_예측'])
        
        display_cols.append('목표달성여부')
        
        optional_cols = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수'
        ]
        
        for col in optional_cols:
            if col in df_sorted.columns:
                display_cols.append(col)
        
        # 컬럼 존재 여부 확인
        display_cols = [col for col in display_cols if col in df_sorted.columns]
        
        # ⭐ 스타일링: 총점 그라디언트
        styled_df = df_sorted[display_cols].style.background_gradient(
            subset=['총점'],
            cmap='RdYlGn',
            vmin=400,
            vmax=1000
        ).format({
            '순위': '{}위',
            '총점': '{:.1f}',
            '예측점수': '{:.1f}',
            '안전점검_점수': '{:.1f}',
            '안전점검_예측': '{:.1f}',
            '중점고객_점수': '{:.1f}',
            '중점고객_예측': '{:.1f}',
            '사용계약_점수': '{:.1f}',
            '사용계약_예측': '{:.1f}',
            '상담응대_점수': '{:.1f}',
            '상담기여_점수': '{:.1f}',
            '만족도_점수': '{:.1f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=600)
        
        st.caption("""
        💡 **예측 점수 설명**
        - **순위**: 현재 총점 기준 순위 (1위가 최고점)
        - **누적형** (안전점검, 중점고객, 사용계약): 진행률 기반으로 6월까지 증가 예상
        - **비누적형** (상담응대, 상담기여, 만족도): 현재 점수 유지 예상
        - 예측 총점은 1000점을 초과하지 않습니다
        """)

def show_trend_analysis(df: pd.DataFrame):
    """월별 누적 추이 탭"""
    st.header("📈 월별 누적 추이")
    
    monthly_avg = df.groupby('평가월').agg({
        '총점': 'mean',
        '센터명': 'count'
    }).reset_index()
    monthly_avg.columns = ['평가월', '평균점수', '센터수']
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_avg['평가월'],
        y=monthly_avg['평균점수'],
        mode='lines+markers',
        name='전체 평균',
        line=dict(color='#003366', width=3),
        marker=dict(size=10, color='#003366'),
        hovertemplate='<b>%{x|%Y년 %m월}</b><br>평균: %{y:.1f}점<extra></extra>'
    ))
    
    # 목표선
    fig.add_hline(
        y=911,
        line_dash="dash",
        line_color="orange",
        line_width=2,
        annotation_text="목표: 911점",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="월별 전체 평균 점수 추이 (누적)",
        xaxis_title="평가월",
        yaxis_title="평균 점수",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("""
    💡 **누적 추이 안내**
    - 점수는 1월부터 누적되어 증가합니다
    - 6월 또는 12월 데이터가 해당 반기 최종 점수입니다
    """)
    
    st.divider()
    
    st.subheader("🎯 센터별 추이 비교")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        centers = st.multiselect(
            "비교할 센터 선택 (최대 5개)",
            options=sorted(df['센터명'].unique()),
            default=sorted(df['센터명'].unique())[:3],
            max_selections=5
        )
    
    with col2:
        show_all = st.checkbox("전체 센터 표시", value=True)  # ⬅️ 수정: value=True로 변경
    
    if show_all:
        df_filtered = df
    elif centers:
        df_filtered = df[df['센터명'].isin(centers)]
    else:
        df_filtered = pd.DataFrame()
    
    if len(df_filtered) > 0:
        fig2 = px.line(
            df_filtered,
            x='평가월',
            y='총점',
            color='센터명',
            markers=True,
            title="선택 센터 총점 추이 (누적)"
        )
        
        fig2.add_hline(y=911, line_dash="dash", line_color="orange", line_width=2)
        fig2.update_layout(height=400, hovermode='x unified')
        
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("센터를 선택하세요.")

def show_center_detail(df: pd.DataFrame):
    """센터별 상세 탭 - 개선된 예측 로직 적용"""
    st.header("🎯 센터별 상세 분석")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        center_name = st.selectbox(
            "센터 선택",
            options=sorted(df['센터명'].unique())
        )
    
    df_center = df[df['센터명'] == center_name].sort_values('평가월')
    
    latest = df_center.iloc[-1]
    
    # 현재 월 계산
    current_month = latest['평가월'].month
    is_first_half = current_month <= 6
    period_month = current_month if is_first_half else current_month - 6
    
    # 개선된 예측 점수
    prediction = calculate_predicted_score_v2(latest, period_month)
    predicted_score = prediction['예측총점']
    
    # KPI 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="현재 총점",
            value=f"{latest['총점']:.1f}점",
            delta=f"{latest['총점'] - 911:.1f}점"
        )
    
    with col2:
        if period_month < 6:
            st.metric(
                label="6월 예측 점수",
                value=f"{predicted_score:.1f}점",
                delta=f"{predicted_score - 911:.1f}점",
                help="개선된 예측 로직 적용 (1000점 이하)"
            )
        else:
            status_emoji = "✅" if latest.get('목표달성여부', False) else "❌"
            status_text = "달성" if latest.get('목표달성여부', False) else "미달성"
            st.metric(
                label="목표 달성",
                value=status_text,
                delta=status_emoji
            )
    
    with col3:
        latest_month_df = df[df['평가월'] == df['평가월'].max()]
        rank = (latest_month_df['총점'] >= latest['총점']).sum()
        st.metric(
            label="전체 순위",
            value=f"{rank}위",
            delta=f"/ {df['센터명'].nunique()}개"
        )
    
    with col4:
        period_text = f"상반기 {period_month}월" if is_first_half else f"하반기 {period_month}월"
        st.metric(
            label="진행 상황",
            value=period_text,
            delta=f"{period_month/6*100:.1f}%"
        )
    
    st.divider()
    
    # 예측 상세 분석 (기간 중일 때만)
    if period_month < 6:
        st.subheader("🔮 항목별 예측 분석")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 누적형 지표 (증가 예상)")
            
            pred_data_cumulative = pd.DataFrame({
                '지표': ['안전점검', '중점고객', '사용계약'],
                '현재': [
                    latest.get('안전점검_점수', 0),
                    latest.get('중점고객_점수', 0),
                    latest.get('사용계약_점수', 0)
                ],
                '예측': [
                    prediction['안전점검_예측'],
                    prediction['중점고객_예측'],
                    prediction['사용계약_예측']
                ],
                '증가폭': [
                    prediction['안전점검_예측'] - latest.get('안전점검_점수', 0),
                    prediction['중점고객_예측'] - latest.get('중점고객_점수', 0),
                    prediction['사용계약_예측'] - latest.get('사용계약_점수', 0)
                ]
            })
            
            st.dataframe(
                pred_data_cumulative.style.format({
                    '현재': '{:.1f}',
                    '예측': '{:.1f}',
                    '증가폭': '{:+.1f}'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        with col2:
            st.markdown("### 📊 비누적형 지표 (유지 예상)")
            
            pred_data_static = pd.DataFrame({
                '지표': ['상담응대', '상담기여', '만족도'],
                '현재': [
                    latest.get('상담응대_점수', 0),
                    latest.get('상담기여_점수', 0),
                    latest.get('만족도_점수', 0)
                ],
                '예측': [
                    prediction['상담응대_예측'],
                    prediction['상담기여_예측'],
                    prediction['만족도_예측']
                ],
                '변화': [
                    prediction['상담응대_예측'] - latest.get('상담응대_점수', 0),
                    prediction['상담기여_예측'] - latest.get('상담기여_점수', 0),
                    prediction['만족도_예측'] - latest.get('만족도_점수', 0)
                ]
            })
            
            st.dataframe(
                pred_data_static.style.format({
                    '현재': '{:.1f}',
                    '예측': '{:.1f}',
                    '변화': '{:+.1f}'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        st.divider()
    
    # 레이더 차트와 월별 추이
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 KPI 달성률")
        
        kpi_cols = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수'
        ]
        
        kpi_names = ['안전점검', '중점고객', '사용계약', '상담응대', '상담기여', '만족도']
        kpi_max = [550, 100, 50, 100, 100, 100]
        
        values = [latest.get(col, 0) for col in kpi_cols]
        percentages = [v/m*100 for v, m in zip(values, kpi_max)]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=percentages,
            theta=kpi_names,
            fill='toself',
            name=center_name,
            line_color='#003366',
            fillcolor='rgba(0, 51, 102, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    ticksuffix='%'
                )
            ),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📋 세부 점수")
        
        score_data = []
        for name, col, max_val in zip(kpi_names, kpi_cols, kpi_max):
            score = latest.get(col, 0)
            score_data.append({
                '지표': name,
                '획득점수': f"{score:.1f}",
                '만점': max_val,
                '달성률': f"{score/max_val*100:.1f}%"
            })
        
        st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.caption("**조정 항목**")
        adj_data = {
            '민원대응': f"{latest.get('민원대응적정성', 0):.1f}점",
            '주의/경고': f"{latest.get('주의경고', 0):.1f}점",
            '가점': f"{latest.get('가점', 0):.1f}점"
        }
        st.json(adj_data)
    
    st.divider()
    
    st.subheader("📅 월별 성과 이력 (누적)")
    
    display_cols = ['평가월', '총점']
    if '목표달성여부' in df_center.columns:
        display_cols.append('목표달성여부')
    
    for col in kpi_cols:
        if col in df_center.columns:
            display_cols.append(col)
    
    st.dataframe(
        df_center[display_cols].sort_values('평가월', ascending=False),
        use_container_width=True,
        hide_index=True
    )

def show_risk_management(df: pd.DataFrame):
    """위험 관리 탭 - 개선된 예측 로직 적용"""
    st.header("⚠️ 위험 관리")
    
    latest_month = df['평가월'].max()
    df_latest = df[df['평가월'] == latest_month].copy()
    
    # 현재 월 계산
    current_month = latest_month.month
    is_first_half = current_month <= 6
    period_month = current_month if is_first_half else current_month - 6
    
    # 개선된 예측 점수 계산
    prediction_results = df_latest.apply(
        lambda row: calculate_predicted_score_v2(row, period_month),
        axis=1
    )
    
    df_latest['예측점수'] = prediction_results.apply(lambda x: x['예측총점'])
    
    # 위험도 분류 (예측 점수 기준)
    df_latest['위험레벨'], df_latest['위험색상'], df_latest['위험아이콘'] = zip(
        *df_latest.apply(
            lambda row: get_risk_level(row['예측점수'], period_month),
            axis=1
        )
    )
    
    df_latest['부족점수'] = 911 - df_latest['예측점수']
    
    # 위험도별 집계
    risk_summary = df_latest['위험레벨'].value_counts()
    
    st.info(f"""
    💡 **개선된 위험도 판정 기준** ({latest_month.strftime('%Y년 %m월')} 기준)
    - 현재: {period_month}월차 진행 중 (진행률 {period_month/6*100:.1f}%)
    - **누적형 지표**: 진행률 기반 예측 (안전점검, 중점고객, 사용계약)
    - **비누적형 지표**: 현재 점수 유지 (상담응대, 상담기여, 만족도)
    - 예측 총점은 **1000점을 초과하지 않습니다**
    - 위험도는 6월 예측 점수를 기준으로 판정합니다
    """)
    
    # 위험도별 카운트
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        safe_count = risk_summary.get('안전', 0) + risk_summary.get('양호', 0)
        st.metric("🟢 안전/양호", f"{safe_count}개")
    
    with col2:
        caution_count = risk_summary.get('주의', 0)
        st.metric("🟡 주의", f"{caution_count}개")
    
    with col3:
        warning_count = risk_summary.get('경고', 0)
        st.metric("🟠 경고", f"{warning_count}개")
    
    with col4:
        danger_count = risk_summary.get('위험', 0) + risk_summary.get('심각', 0)
        st.metric("🔴 위험/심각", f"{danger_count}개")
    
    st.divider()
    
    # 위험 센터 목록 (예측 점수 < 911)
    df_risk = df_latest[df_latest['예측점수'] < 911].copy()
    df_risk = df_risk.sort_values('예측점수')
    
    if len(df_risk) == 0:
        st.success("🎉 모든 센터가 목표 달성 예상입니다!")
        st.balloons()
    else:
        st.warning(f"⚠️ **{len(df_risk)}개 센터**가 목표 점수 미달 예상 (개선된 예측 기준)")
        
        st.subheader("📋 개선 필요 센터 상세")
        
        for idx, row in df_risk.iterrows():
            risk_icon = row['위험아이콘']
            risk_level = row['위험레벨']
            
            with st.expander(
                f"{risk_icon} {risk_level} | {row['센터명']} - 현재 {row['총점']:.1f}점 / 예측 {row['예측점수']:.1f}점 (1000점 이하)"
            ):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**현재 점수**")
                    score_list = []
                    if '안전점검_점수' in row:
                        score_list.append(f"- 안전점검: {row['안전점검_점수']:.1f} / 550")
                    if '중점고객_점수' in row:
                        score_list.append(f"- 중점고객: {row['중점고객_점수']:.1f} / 100")
                    if '사용계약_점수' in row:
                        score_list.append(f"- 사용계약: {row['사용계약_점수']:.1f} / 50")
                    if '상담응대_점수' in row:
                        score_list.append(f"- 상담응대: {row['상담응대_점수']:.1f} / 100")
                    if '상담기여_점수' in row:
                        score_list.append(f"- 상담기여: {row['상담기여_점수']:.1f} / 100")
                    if '만족도_점수' in row:
                        score_list.append(f"- 만족도: {row['만족도_점수']:.1f} / 100")
                    
                    st.markdown("\n".join(score_list))
                
                with col2:
                    st.markdown("**개선 시나리오**")
                    
                    gap_to_target = 911 - row['예측점수']
                    
                    if gap_to_target < 0:
                        st.success(f"✅ 예측 점수가 목표를 {abs(gap_to_target):.1f}점 초과합니다!")
                    else:
                        st.error(f"⚠️ 6월까지 약 {gap_to_target:.1f}점 추가 필요")
                        
                        # 취약 지표 찾기 (누적형 지표 중심)
                        weak_kpis = []
                        if row.get('안전점검_점수', 0) / 550 < 0.7:
                            weak_kpis.append("안전점검 (누적)")
                        if row.get('중점고객_점수', 0) / 100 < 0.7:
                            weak_kpis.append("중점고객 (누적)")
                        if row.get('사용계약_점수', 0) / 50 < 0.8:
                            weak_kpis.append("사용계약 (등급)")
                        
                        if weak_kpis:
                            st.warning(f"🎯 **집중 개선 필요**: {', '.join(weak_kpis)}")
                            st.caption("💡 누적형 지표는 6월까지 지속적으로 상승합니다")
                        else:
                            st.info("💡 비누적형 지표(상담/만족도) 개선 필요")

def show_raw_data_verification(df: pd.DataFrame):
    """원본 데이터 확인 탭"""
    st.header("📋 원본 데이터 확인")
    
    st.info("""
    💡 **사용 안내**
    - 담당자가 제출한 원본(Raw) 데이터를 확인할 수 있습니다
    - 센터와 월을 선택하여 입력값과 계산된 점수를 비교하세요
    """)
    
    st.divider()
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        centers = ['전체'] + sorted(df['센터명'].unique().tolist())
        selected_center = st.selectbox("🏢 센터 선택", options=centers, index=0)
    
    with col2:
        months = sorted(df['평가월'].dt.to_period('M').unique())
        month_options = ['전체'] + [m.strftime('%Y년 %m월') for m in months]
        selected_month_str = st.selectbox("📅 평가월 선택", options=month_options, index=0)
    
    df_filtered = df.copy()
    
    if selected_center != '전체':
        df_filtered = df_filtered[df_filtered['센터명'] == selected_center]
    
    if selected_month_str != '전체':
        selected_month = pd.Period(selected_month_str.replace('년 ', '-').replace('월', ''), freq='M')
        df_filtered = df_filtered[df_filtered['평가월'].dt.to_period('M') == selected_month]
    
    if len(df_filtered) == 0:
        st.warning("⚠️ 선택한 조건에 해당하는 데이터가 없습니다.")
        return
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 조회 행수", f"{len(df_filtered):,}행")
    
    with col2:
        st.metric("🏢 센터 수", f"{df_filtered['센터명'].nunique()}개")
    
    with col3:
        st.metric("📅 기간", f"{df_filtered['평가월'].nunique()}개월")
    
    with col4:
        avg_score = df_filtered['총점'].mean()
        st.metric("📈 평균 점수", f"{avg_score:.1f}점")
    
    st.divider()
    
    subtab1, subtab2, subtab3 = st.tabs([
        "📊 항목별 비교",
        "📋 원본 데이터 테이블",
        "📥 데이터 다운로드"
    ])
    
    with subtab1:
        st.subheader("📊 입력값 vs 계산 점수 비교")
        
        for idx, row in df_filtered.iterrows():
            with st.expander(f"🏢 {row['센터명']} | 📅 {row['평가월'].strftime('%Y년 %m월')}", 
                           expanded=(len(df_filtered) == 1)):
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### 🔵 핵심 지표")
                    
                    st.markdown(f"""
                    **1️⃣ 안전점검실점검율**
                    - 입력값: `{row['안전점검실점검율']:.4f}` ({row['안전점검실점검율']*100:.2f}%)
                    - 계산 점수: **{row.get('안전점검_점수', 0):.1f}점** / 550점
                    """)
                    
                    st.markdown("---")
                    
                    st.markdown(f"""
                    **2️⃣ 중점고객안전점검율**
                    - 입력값: `{row['중점고객안전점검율']:.4f}` ({row['중점고객안전점검율']*100:.2f}%)
                    - 계산 점수: **{row.get('중점고객_점수', 0):.1f}점** / 100점
                    """)
                    
                    st.markdown("---")
                    
                    contract_rate = row['사용계약율']
                    if contract_rate >= 0.9:
                        contract_grade = "A등급 (90% 이상)"
                    elif contract_rate >= 0.8:
                        contract_grade = "B등급 (80~90% 미만)"
                    elif contract_rate >= 0.7:
                        contract_grade = "C등급 (70~80% 미만)"
                    else:
                        contract_grade = "D등급 (70% 미만)"
                    
                    st.markdown(f"""
                    **3️⃣ 사용계약율 (등급제)**
                    - 입력값: `{contract_rate:.4f}` ({contract_rate*100:.2f}%)
                    - 등급: {contract_grade}
                    - 계산 점수: **{row.get('사용계약_점수', 0):.1f}점** / 50점
                    """)
                
                with col2:
                    st.markdown("### 🟢 상담 지표")
                    
                    st.markdown(f"""
                    **4️⃣ 상담응대율**
                    - 입력값: `{row['상담응대율']:.4f}` ({row['상담응대율']*100:.2f}%)
                    - 계산 점수: **{row.get('상담응대_점수', 0):.1f}점** / 100점
                    """)
                    
                    st.markdown("---")
                    
                    st.markdown(f"""
                    **5️⃣ 상담기여도**
                    - 입력값: `{row['상담기여도']:.4f}` ({row['상담기여도']*100:.2f}%)
                    - 계산 점수: **{row.get('상담기여_점수', 0):.1f}점** / 100점
                    """)
                    
                    st.markdown("---")
                    
                    st.markdown(f"""
                    **6️⃣ 고객서비스만족도**
                    - 입력값: `{row['고객서비스만족도']:.0f}점`
                    - 계산 점수: **{row.get('만족도_점수', 0):.1f}점** / 100점
                    """)
                
                with col3:
                    st.markdown("### 🟡 조정 항목")
                    
                    status = "✅ 없음" if row['민원대응적정성'] == 0 else f"⚠️ {row['민원대응적정성']:.0f}점"
                    st.markdown(f"""
                    **7️⃣ 민원대응적정성 (감점)**
                    - 상태: {status}
                    """)
                    
                    st.markdown("---")
                    
                    status = "✅ 없음" if row['주의경고'] == 0 else f"⚠️ {row['주의경고']:.0f}점"
                    st.markdown(f"""
                    **8️⃣ 주의/경고 (감점)**
                    - 상태: {status}
                    """)
                    
                    st.markdown("---")
                    
                    status = "➖ 없음" if row['가점'] == 0 else f"✨ +{row['가점']:.0f}점"
                    st.markdown(f"""
                    **9️⃣ 가점**
                    - 상태: {status}
                    """)
                
                st.divider()
                
                col_total1, col_total2, col_total3 = st.columns(3)
                
                with col_total1:
                    st.metric("📊 총점", f"{row['총점']:.1f}점", f"{row['총점']-911:.1f}점")
                
                with col_total2:
                    status_emoji = "✅" if row.get('목표달성여부', False) else "❌"
                    status_text = "달성" if row.get('목표달성여부', False) else "미달성"
                    st.metric("🎯 목표 달성", status_text, status_emoji)
                
                with col_total3:
                    achievement = row['총점'] / 911 * 100
                    st.metric("📈 달성률", f"{achievement:.1f}%")
    
    with subtab2:
        st.subheader("📋 원본 데이터 전체 테이블")
        
        display_mode = st.radio(
            "표시 모드 선택",
            options=["입력값만 보기", "입력값 + 점수", "전체 데이터"],
            horizontal=True
        )
        
        if display_mode == "입력값만 보기":
            display_cols = [
                '센터명', '평가월',
                '안전점검실점검율', '중점고객안전점검율', '사용계약율',
                '상담응대율', '상담기여도', '고객서비스만족도',
                '민원대응적정성', '주의경고', '가점'
            ]
        elif display_mode == "입력값 + 점수":
            display_cols = [
                '센터명', '평가월', '총점',
                '안전점검실점검율', '안전점검_점수',
                '중점고객안전점검율', '중점고객_점수',
                '사용계약율', '사용계약_점수',
                '상담응대율', '상담응대_점수',
                '상담기여도', '상담기여_점수',
                '고객서비스만족도', '만족도_점수'
            ]
        else:
            display_cols = df_filtered.columns.tolist()
        
        display_cols = [col for col in display_cols if col in df_filtered.columns]
        
        st.dataframe(
            df_filtered[display_cols],
            use_container_width=True,
            height=500
        )
    
    with subtab3:
        st.subheader("📥 데이터 다운로드")
        
        st.info("💡 현재 필터링된 데이터를 엑셀 파일로 다운로드할 수 있습니다")
        
        col1, col2 = st.columns(2)
        
        with col1:
            download_option = st.radio(
                "다운로드 형식 선택",
                options=["입력값만", "입력값 + 점수", "전체 데이터"],
                index=1
            )
        
        with col2:
            file_format = st.radio(
                "파일 형식",
                options=["Excel (.xlsx)", "CSV (.csv)"],
                index=0
            )
        
        if download_option == "입력값만":
            download_cols = [
                '센터명', '평가월',
                '안전점검실점검율', '중점고객안전점검율', '사용계약율',
                '상담응대율', '상담기여도', '고객서비스만족도',
                '민원대응적정성', '주의경고', '가점'
            ]
        elif download_option == "입력값 + 점수":
            download_cols = [
                '센터명', '평가월', '총점',
                '안전점검실점검율', '안전점검_점수',
                '중점고객안전점검율', '중점고객_점수',
                '사용계약율', '사용계약_점수',
                '상담응대율', '상담응대_점수',
                '상담기여도', '상담기여_점수',
                '고객서비스만족도', '만족도_점수',
                '민원대응적정성', '주의경고', '가점'
            ]
        else:
            download_cols = df_filtered.columns.tolist()
        
        download_cols = [col for col in download_cols if col in df_filtered.columns]
        df_download = df_filtered[download_cols].copy()
        
        df_download['평가월'] = df_download['평가월'].dt.strftime('%Y-%m-%d')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        
        if selected_center == '전체' and selected_month_str == '전체':
            filename_prefix = "전체_원본데이터"
        elif selected_center == '전체':
            filename_prefix = f"{selected_month_str.replace('년 ', '').replace('월', '')}_원본데이터"
        elif selected_month_str == '전체':
            filename_prefix = f"{selected_center}_원본데이터"
        else:
            filename_prefix = f"{selected_center}_{selected_month_str.replace('년 ', '').replace('월', '')}"
        
        if file_format == "Excel (.xlsx)":
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_download.to_excel(writer, index=False, sheet_name='원본데이터')
            output.seek(0)
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 Excel 파일 다운로드",
                data=excel_data,
                file_name=f"{filename_prefix}_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            csv_data = df_download.to_csv(index=False, encoding='utf-8-sig')
            
            st.download_button(
                label="📥 CSV 파일 다운로드",
                data=csv_data,
                file_name=f"{filename_prefix}_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        st.divider()
        st.markdown("**📋 다운로드 미리보기 (상위 10행)**")
        st.dataframe(df_download.head(10), use_container_width=True)
        
        st.caption(f"총 {len(df_download):,}행 × {len(df_download.columns)}열")

if __name__ == "__main__":
    main()
