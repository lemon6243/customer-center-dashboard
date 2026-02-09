"""
1월 데이터를 기반으로 6개월 누적 테스트 데이터 생성
"""

import pandas as pd
import numpy as np
from datetime import datetime

def generate_6months_data():
    """1월 데이터를 기반으로 2~6월 누적 데이터 생성"""
    
    print("=" * 60)
    print("📊 6개월 누적 데이터 생성 시작")
    print("=" * 60)
    
    # 1. 기존 1월 데이터 로드
    try:
        df_jan = pd.read_excel("test.xlsx")
        print(f"\n✅ 1월 데이터 로드 완료: {len(df_jan)}행")
    except FileNotFoundError:
        print("❌ test.xlsx 파일을 찾을 수 없습니다.")
        print("📌 C:\\Users\\00595\\code\\dashboard_cumulative\\ 폴더에 test.xlsx가 있는지 확인하세요.")
        return
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return
    
    # 2. 센터 정보 확인
    centers = df_jan['센터명'].tolist()
    print(f"✅ 센터 수: {len(centers)}개")
    print(f"📌 센터 목록: {', '.join(centers[:5])}... 등")
    
    # 3. 2~6월 데이터 생성
    dfs = [df_jan]  # 1월 데이터 포함
    
    for month in range(2, 7):  # 2~6월
        print(f"\n🔄 {month}월 데이터 생성 중...")
        
        df_month = df_jan.copy()
        
        # 평가월 변경
        df_month['평가월'] = pd.to_datetime(f'2026-{month:02d}-01')
        
        # === 누적 점검율 시뮬레이션 ===
        # 1월 → 6월로 갈수록 누적 점검율 증가
        
        # 안전점검실점검율 (월별 누적)
        # 1월: 18% → 6월: 96% (목표)
        base_rate = df_jan['안전점검실점검율'].values
        target_rate = 0.96  # 6월 목표
        progress = (month - 1) / 5  # 0~1 진행률
        df_month['안전점검실점검율'] = np.clip(
            base_rate + (target_rate - base_rate) * progress + np.random.uniform(-0.02, 0.02, len(df_month)),
            0, 1
        )
        
        # 중점고객안전점검율 (월별 누적)
        base_rate = df_jan['중점고객안전점검율'].values
        target_rate = 0.94
        df_month['중점고객안전점검율'] = np.clip(
            base_rate + (target_rate - base_rate) * progress + np.random.uniform(-0.03, 0.03, len(df_month)),
            0, 1
        )
        
        # 사용계약율 (소폭 증가)
        df_month['사용계약율'] = np.clip(
            df_jan['사용계약율'].values + np.random.uniform(0, 0.05, len(df_month)),
            0, 1
        )
        
        # 상담응대율 (안정적 유지)
        df_month['상담응대율'] = np.clip(
            df_jan['상담응대율'].values + np.random.uniform(-0.01, 0.01, len(df_month)),
            0.95, 1
        )
        
        # 상담기여도 (안정적 유지)
        df_month['상담기여도'] = np.clip(
            df_jan['상담기여도'].values + np.random.uniform(-0.01, 0.01, len(df_month)),
            0.95, 1
        )
        
        # 고객서비스만족도 (소폭 변동)
        df_month['고객서비스만족도'] = np.clip(
            df_jan['고객서비스만족도'].values + np.random.randint(-2, 3, len(df_month)),
            80, 100
        )
        
        # 민원/주의경고/가점 (대부분 0 유지, 일부만 랜덤)
        df_month['민원대응적정성'] = np.where(
            np.random.random(len(df_month)) < 0.05,  # 5% 확률
            np.random.randint(-10, 0, len(df_month)),
            0
        )
        
        df_month['주의경고'] = np.where(
            np.random.random(len(df_month)) < 0.03,  # 3% 확률
            np.random.randint(-20, 0, len(df_month)),
            0
        )
        
        df_month['가점'] = np.where(
            np.random.random(len(df_month)) < 0.02,  # 2% 확률
            np.random.randint(5, 15, len(df_month)),
            0
        )
        
        dfs.append(df_month)
        print(f"   ✅ {month}월 데이터 생성 완료 (24행)")
    
    # 4. 전체 합치기
    df_all = pd.concat(dfs, ignore_index=True)
    
    # 5. 정렬 (센터명 → 평가월 순)
    df_all = df_all.sort_values(['센터명', '평가월']).reset_index(drop=True)
    
    print("\n" + "=" * 60)
    print("✅ 전체 데이터 생성 완료!")
    print("=" * 60)
    
    # 6. 요약 정보
    print(f"\n📊 데이터 요약:")
    print(f"   - 총 행수: {len(df_all):,}행")
    print(f"   - 센터 수: {df_all['센터명'].nunique()}개")
    print(f"   - 평가 기간: {df_all['평가월'].min().strftime('%Y-%m')} ~ {df_all['평가월'].max().strftime('%Y-%m')}")
    
    print(f"\n📅 월별 데이터 분포:")
    month_counts = df_all.groupby(df_all['평가월'].dt.to_period('M')).size()
    for month, count in month_counts.items():
        print(f"   - {month.strftime('%Y년 %m월')}: {count}행")
    
    # 7. 샘플 데이터 (자양센터)
    print(f"\n🔍 샘플 데이터 (자양센터):")
    sample = df_all[df_all['센터명'] == '자양'][['평가월', '안전점검실점검율', '중점고객안전점검율', '사용계약율']]
    print(sample.to_string(index=False))
    
    # 8. 저장
    output_file = "test_6months_full.xlsx"
    df_all.to_excel(output_file, index=False, engine='openpyxl')
    print(f"\n💾 저장 완료: {output_file}")
    
    # 9. data 폴더에도 복사 (latest_data.xlsx)
    try:
        import os
        if not os.path.exists('data'):
            os.makedirs('data')
        df_all.to_excel('data/latest_data.xlsx', index=False, engine='openpyxl')
        print(f"💾 저장 완료: data/latest_data.xlsx")
    except Exception as e:
        print(f"⚠️ data 폴더 저장 실패: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 완료! 이제 아래 명령어로 대시보드를 실행하세요:")
    print("   streamlit run app.py")
    print("=" * 60)

if __name__ == "__main__":
    generate_6months_data()
