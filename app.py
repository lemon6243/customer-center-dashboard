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
    """GitHub에 저장된 최신 데이터 로드 (캐시 적용)"""
    data_path = "data/latest_data.xlsx"
    
    if os.path.exists(data_path):
        try:
            df = pd.read_excel(data_path)
            
            # 평가월을 datetime으로 변환
            if '평가월' in df.columns:
                df['평가월'] = pd.to_datetime(df['평가월'])
            
            return df
        except Exception as e:
            st.error(f"❌ 데이터 로드 실패: {e}")
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

def main():
    """메인 함수"""
    
    # 타이틀
    st.markdown('<div class="main-header">🏢 도시가스 고객센터 성과 대시보드</div>', 
                unsafe_allow_html=True)
    
    # 세션 상태 초기화
    if 'df' not in st.session_state:
        # GitHub에서 자동 로드
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
                    # 1. 데이터 로드
                    df_raw = load_cumulative_data(uploaded_file)
                    
                    # 2. 검증
                    is_valid, message = validate_cumulative_data(df_raw)
                    
                    if is_valid:
                        st.success(f"✅ {message}")
                        
                        # 3. 점수 계산
                        df_scored = calculate_scores(df_raw)
                        st.session_state['df'] = df_scored
                        
                        # 4. 요약 정보
                        st.info(f"""
                        📊 **처리 완료**
                        - 총 {len(df_scored):,}행
                        - {df_scored['센터명'].nunique()}개 센터
                        - {df_scored['평가월'].nunique()}개월 데이터
                        """)
                        
                        # 5. 다운로드 버튼 (GitHub 업로드용)
                        excel_data = convert_df_to_excel(df_scored)
                        
                        st.download_button(
                            label="💾 처리된 데이터 다운로드",
                            data=excel_data,
                            file_name=f"latest_data_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            help="이 파일을 data/latest_data.xlsx로 저장 후 GitHub에 업로드하세요"
                        )
                        
                        # 6. 안내 메시지
                        with st.expander("💡 팀 공유 방법 (클릭하여 펼치기)"):
                            st.markdown("""
                            ### 📋 단계별 가이드
                            
                            **1단계: 파일 다운로드**
                            - 위 "💾 처리된 데이터 다운로드" 버튼 클릭
                            - 파일이 다운로드 폴더에 저장됨
                            
                            **2단계: GitHub 업로드**
                            ```bash
                            # 다운로드한 파일을 프로젝트 폴더로 이동
                            move 다운로드폴더\\latest_data_*.xlsx C:\\Users\\00595\\code\\dashboard_cumulative\\data\\latest_data.xlsx
                            
                            # Git 커밋 및 푸시
                            cd C:\\Users\\00595\\code\\dashboard_cumulative
                            git add data/latest_data.xlsx
                            git commit -m "Update performance data"
                            git push origin main
                            ```
                            
                            **3단계: 자동 배포**
                            - Streamlit Cloud가 자동으로 감지 (1~2분)
                            - 팀원들이 새로고침하면 최신 데이터 조회
                            
                            **🎯 TIP**: 매월 말에 이 과정 반복
                            """)
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
            
            # 평가월 선택
            months = sorted(df['평가월'].dt.to_period('M').unique())
            selected_months = st.multiselect(
                "평가월 선택",
                options=months,
                default=months,
                format_func=lambda x: x.strftime('%Y년 %m월')
            )
            
            # 센터 선택
            centers = sorted(df['센터명'].unique())
            selected_centers = st.multiselect(
                "센터 선택",
                options=centers,
                default=centers
            )
            
            # 필터 적용
            if selected_months and selected_centers:
                df_filtered = df[
                    (df['평가월'].dt.to_period('M').isin(selected_months)) &
                    (df['센터명'].isin(selected_centers))
                ]
                st.session_state['df_filtered'] = df_filtered
                st.caption(f"필터 결과: {len(df_filtered):,}행")
            else:
                st.session_state['df_filtered'] = df
    
    # ==================== 메인 화면 ====================
    if st.session_state['df'] is None:
        # 데이터 없을 때
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
            
            # 샘플 이미지
            st.image("https://via.placeholder.com/600x300/003366/FFFFFF?text=Dashboard+Preview", 
                     use_container_width=True)
    else:
        # 데이터 있을 때
        df = st.session_state.get('df_filtered', st.session_state['df'])
        
        # 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 전체 현황",
            "📈 월별 누적 추이",
            "🎯 센터별 상세",
            "⚠️ 위험 관리"
        ])
        
        with tab1:
            show_overview(df)
        
        with tab2:
            show_trend_analysis(df)
        
        with tab3:
            show_center_detail(df)
        
        with tab4:
            show_risk_management(df)

def show_overview(df: pd.DataFrame):
    """전체 현황 탭"""
    st.header("📊 전체 현황")
    
    # 최신 월 데이터만 (반기 최종 점수)
    latest_month = df['평가월'].max()
    df_latest = df[df['평가월'] == latest_month].copy()
    
    # KPI 카드
    col1, col2, col3, col4 = st.columns(4)
    
    avg_score = df_latest['총점'].mean()
    target_achieved = (df_latest['총점'] >= 911).sum()
    total_centers = len(df_latest)
    risk_centers = (df_latest['총점'] < 911).sum()
    
    with col1:
        st.metric(
            label="📊 평균 점수",
            value=f"{avg_score:.1f}점",
            delta=f"{avg_score - 911:.1f}점",
            delta_color="normal"
        )
    
    with col2:
        achievement_rate = target_achieved / total_centers * 100
        st.metric(
            label="🎯 목표 달성",
            value=f"{target_achieved}/{total_centers}",
            delta=f"{achievement_rate:.1f}%"
        )
    
    with col3:
        st.metric(
            label="⚠️ 위험 센터",
            value=f"{risk_centers}개",
            delta=f"-{risk_centers}개" if risk_centers > 0 else "없음",
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="🏁 목표 점수",
            value="911점",
            delta="재계약 기준"
        )
    
    st.divider()
    
    # 센터별 순위 차트
    st.subheader(f"🏆 센터별 총점 순위 ({latest_month.strftime('%Y년 %m월')} 기준)")
    
    df_sorted = df_latest.sort_values('총점', ascending=True)
    
    # 색상: 911점 기준
    colors = ['#dc3545' if x < 911 else '#28a745' for x in df_sorted['총점']]
    
    fig = go.Figure(go.Bar(
        y=df_sorted['센터명'],
        x=df_sorted['총점'],
        orientation='h',
        marker=dict(color=colors),
        text=df_sorted['총점'].round(1),
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>총점: %{x:.1f}점<extra></extra>'
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
    
    fig.update_layout(
        xaxis_title="총점",
        yaxis_title="",
        height=600,
        showlegend=False,
        hovermode='closest'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 상세 테이블
    with st.expander("📋 상세 점수표 보기"):
        display_cols = [
            '센터명', '총점', '목표달성여부',
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수'
        ]
        
        # 스타일 적용
        styled_df = df_sorted[display_cols].style.background_gradient(
            subset=['총점'],
            cmap='RdYlGn',
            vmin=850,
            vmax=1000
        ).format({
            '총점': '{:.1f}',
            '안전점검_점수': '{:.1f}',
            '중점고객_점수': '{:.1f}',
            '사용계약_점수': '{:.1f}',
            '상담응대_점수': '{:.1f}',
            '상담기여_점수': '{:.1f}',
            '만족도_점수': '{:.1f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, height=400)

def show_trend_analysis(df: pd.DataFrame):
    """월별 누적 추이 탭"""
    st.header("📈 월별 누적 추이")
    
    # 월별 평균 점수
    monthly_avg = df.groupby('평가월').agg({
        '총점': 'mean',
        '센터명': 'count'
    }).reset_index()
    monthly_avg.columns = ['평가월', '평균점수', '센터수']
    
    # 라인 차트
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
        title="월별 전체 평균 점수 추이",
        xaxis_title="평가월",
        yaxis_title="평균 점수",
        hovermode='x unified',
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # 센터별 추이 (선택)
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
        show_all = st.checkbox("전체 센터 표시", value=False)
    
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
            title="선택 센터 총점 추이"
        )
        
        fig2.add_hline(y=911, line_dash="dash", line_color="orange", line_width=2)
        fig2.update_layout(height=400, hovermode='x unified')
        
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("센터를 선택하세요.")

def show_center_detail(df: pd.DataFrame):
    """센터별 상세 탭"""
    st.header("🎯 센터별 상세 분석")
    
    # 센터 선택
    col1, col2 = st.columns([2, 1])
    
    with col1:
        center_name = st.selectbox(
            "센터 선택",
            options=sorted(df['센터명'].unique())
        )
    
    df_center = df[df['센터명'] == center_name].sort_values('평가월')
    
    # 최신 데이터
    latest = df_center.iloc[-1]
    
    # KPI 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="총점",
            value=f"{latest['총점']:.1f}점",
            delta=f"{latest['총점'] - 911:.1f}점"
        )
    
    with col2:
        status_emoji = "✅" if latest['목표달성여부'] == '달성' else "❌"
        st.metric(
            label="목표 달성",
            value=latest['목표달성여부'],
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
        if len(df_center) > 1:
            prev_score = df_center.iloc[-2]['총점']
            diff = latest['총점'] - prev_score
            st.metric(
                label="전월 대비",
                value=f"{diff:+.1f}점",
                delta=f"{diff/prev_score*100:+.1f}%"
            )
        else:
            st.metric(label="전월 대비", value="-")
    
    st.divider()
    
    # 레이더 차트
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 7대 지표 분석")
        
        kpi_cols = [
            '안전점검_점수', '중점고객_점수', '사용계약_점수',
            '상담응대_점수', '상담기여_점수', '만족도_점수'
        ]
        
        kpi_names = ['안전점검', '중점고객', '사용계약', '상담응대', '상담기여', '만족도']
        kpi_max = [550, 100, 50, 100, 100, 100]
        
        values = [latest[col] for col in kpi_cols]
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
            score_data.append({
                '지표': name,
                '획득점수': f"{latest[col]:.1f}",
                '만점': max_val,
                '달성률': f"{latest[col]/max_val*100:.1f}%"
            })
        
        st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # 조정 점수
        st.caption("**조정 항목**")
        adj_data = {
            '민원대응': f"{latest.get('민원대응적정성', 0):.1f}점",
            '주의/경고': f"{latest.get('주의경고', 0):.1f}점",
            '가점': f"{latest.get('가점', 0):.1f}점"
        }
        st.json(adj_data)
    
    st.divider()
    
    # 월별 상세 테이블
    st.subheader("📅 월별 성과 이력")
    
    st.dataframe(
        df_center[['평가월', '총점', '목표달성여부'] + kpi_cols].sort_values('평가월', ascending=False),
        use_container_width=True,
        hide_index=True
    )

def show_risk_management(df: pd.DataFrame):
    """위험 관리 탭"""
    st.header("⚠️ 위험 관리")
    
    # 최신 월 데이터
    latest_month = df['평가월'].max()
    df_latest = df[df['평가월'] == latest_month].copy()
    
    # 위험 센터 (911점 미달)
    df_risk = df_latest[df_latest['총점'] < 911].copy()
    df_risk['부족점수'] = 911 - df_risk['총점']
    df_risk = df_risk.sort_values('총점')
    
    if len(df_risk) == 0:
        st.success("🎉 모든 센터가 목표(911점)를 달성했습니다!")
        st.balloons()
    else:
        st.warning(f"⚠️ **{len(df_risk)}개 센터**가 911점 미달 ({latest_month.strftime('%Y년 %m월')} 기준)")
        
        # 위험도별 분류
        critical = df_risk[df_risk['총점'] < 880]  # 30점 이상 부족
        warning = df_risk[(df_risk['총점'] >= 880) & (df_risk['총점'] < 900)]  # 11~30점 부족
        caution = df_risk[df_risk['총점'] >= 900]  # 11점 미만 부족
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🔴 심각", f"{len(critical)}개", "30점 이상 부족")
        with col2:
            st.metric("🟡 경고", f"{len(warning)}개", "11~30점 부족")
        with col3:
            st.metric("🟢 주의", f"{len(caution)}개", "11점 미만 부족")
        
        st.divider()
        
        # 위험 센터 목록
        st.subheader("📋 위험 센터 상세")
        
        for idx, row in df_risk.iterrows():
            # 위험도 판단
            if row['총점'] < 880:
                risk_level = "🔴 심각"
                color = "red"
            elif row['총점'] < 900:
                risk_level = "🟡 경고"
                color = "orange"
            else:
                risk_level = "🟢 주의"
                color = "green"
            
            with st.expander(f"{risk_level} | {row['센터명']} - {row['총점']:.1f}점 (부족: {row['부족점수']:.1f}점)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**현재 점수**")
                    score_list = [
                        f"- 안전점검: {row['안전점검_점수']:.1f} / 550",
                        f"- 중점고객: {row['중점고객_점수']:.1f} / 100",
                        f"- 사용계약: {row['사용계약_점수']:.1f} / 50",
                        f"- 상담응대: {row['상담응대_점수']:.1f} / 100",
                        f"- 상담기여: {row['상담기여_점수']:.1f} / 100",
                        f"- 만족도: {row['만족도_점수']:.1f} / 100"
                    ]
                    st.markdown("\n".join(score_list))
                
                with col2:
                    st.markdown("**개선 시나리오**")
                    
                    # 취약 지표 찾기
                    weak_kpis = []
                    if row['안전점검_점수'] / 550 < 0.85:
                        weak_kpis.append(("안전점검", row['안전점검_점수'], 550))
                    if row['중점고객_점수'] / 100 < 0.85:
                        weak_kpis.append(("중점고객", row['중점고객_점수'], 100))
                    if row['사용계약_점수'] / 50 < 0.9:
                        weak_kpis.append(("사용계약", row['사용계약_점수'], 50))
                    if row['상담응대_점수'] / 100 < 0.9:
                        weak_kpis.append(("상담응대", row['상담응대_점수'], 100))
                    
                    if weak_kpis:
                        st.error(f"🎯 **집중 개선 필요**: {', '.join([k[0] for k in weak_kpis])}")
                        
                        for name, score, max_val in weak_kpis:
                            gap = max_val * 0.95 - score
                            if gap > 0:
                                st.write(f"- **{name}**: {gap:.1f}점 향상 필요 (현재 {score/max_val*100:.1f}% → 목표 95%)")
                    else:
                        st.info("💡 전체적으로 소폭 상승 필요 (각 지표 +2~3%)")

if __name__ == "__main__":
    main()
