# generate_6months_test.py

import pandas as pd
import numpy as np
from datetime import datetime

def generate_test_data():
    """1월 데이터를 기반으로 2~6월 테스트 데이터 생성"""
    
    # 1. 기존 1월 데이터 로드
    df_jan = pd.read_excel("test.xlsx")
    print(f"✅ 1월 데이터 로드: {len(df_jan)}행")
    
    # 2. 2~6월 데이터 생성
    dfs = [df_jan]  # 1월 데이터
    
    for month in range(2, 7):  # 2~6월
        df_month = df_jan.copy()
        
        # 평가월 변경
        df_month['평가월'] = pd.to_datetime(f'2026-{month:02d}-01')
        
        # 지표 값들을 랜덤하게 조금씩 변경 (누적 효과)
        rate_cols = ['안전점검실점검율', '중점고객안전점검율', '사용계약율', 
                     '상담응대율', '상담기여도']
        
        for col in rate_cols:
            # 월별 누적 증가 (1월 대비 +10~20%)
            growth_factor = 1 + (month - 1) * 0.15 + np.random.uniform(-0.05, 0.05, len(df_month))
            df_month[col] = (df_jan[col] * growth_factor).clip(0, 1)  # 0~1 범위 유지
        
        # 만족도도 소폭 변경
        df_month['고객서비스만족도'] = (df_jan['고객서비스만족도'] + 
                                      np.random.randint(-3, 4, len(df_month))).clip(0, 100)
        
        dfs.append(df_month)
        print(f"✅ {month}월 데이터 생성")
    
    # 3. 전체 합치기
    df_all = pd.concat(dfs, ignore_index=True)
    print(f"\n✅ 전체 데이터 생성 완료: {len(df_all)}행")
    
    # 4. 저장
    output_file = "test_6months_full.xlsx"
    df_all.to_excel(output_file, index=False)
    print(f"✅ 저장 완료: {output_file}")
    
    # 5. 요약 정보
    print("\n📊 데이터 요약:")
    print(f"- 총 행수: {len(df_all):,}")
    print(f"- 센터 수: {df_all['센터명'].nunique()}")
    print(f"- 평가 기간: {df_all['평가월'].min().strftime('%Y-%m')} ~ {df_all['평가월'].max().strftime('%Y-%m')}")
    print(f"- 월별 분포:")
    print(df_all.groupby(df_all['평가월'].dt.to_period('M')).size())

if __name__ == "__main__":
    generate_test_data()
