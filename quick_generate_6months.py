# quick_generate_6months.py 파일 전체 코드

import pandas as pd
import numpy as np

def generate_6months_from_current(input_file='test.xlsx', output_file='test_6months.xlsx'):
    """
    현재 1월 데이터를 기반으로 1~6월 데이터 자동 생성
    """
    # 1월 데이터 읽기
    df_jan = pd.read_excel(input_file)
    
    print(f"📂 {input_file} 로드 완료")
    print(f"📊 센터 수: {df_jan['센터명'].nunique()}개")
    
    all_data = []
    
    for month in range(1, 7):
        df_month = df_jan.copy()
        df_month['평가월'] = pd.to_datetime(f'2026-{month:02d}-01')
        
        # 누적 비율 점진적 증가
        progress_factor = month / 6
        
        # 안전점검: 1월 평균 18% → 6월 목표 96%
        base_safety = df_month['안전점검실점검율']
        target_safety = 0.96
        df_month['안전점검실점검율'] = base_safety + (target_safety - base_safety.mean()) * progress_factor
        df_month['안전점검실점검율'] = np.clip(df_month['안전점검실점검율'], 0.1, 1.0)
        
        # 중점고객: 1월 평균 → 6월 목표 94%
        base_priority = df_month['중점고객안전점검율']
        target_priority = 0.94
        df_month['중점고객안전점검율'] = base_priority + (target_priority - base_priority.mean()) * progress_factor
        df_month['중점고객안전점검율'] = np.clip(df_month['중점고객안전점검율'], 0.3, 1.0)
        
        # 사용계약: 점진적 증가
        df_month['사용계약율'] = np.clip(df_month['사용계약율'] + month * 0.015, 0.7, 1.0)
        
        # 상담응대: 이미 높으므로 소폭 증가
        df_month['상담응대율'] = np.clip(df_month['상담응대율'] + month * 0.002, 0.8, 1.0)
        
        # 상담기여: 소폭 증가
        df_month['상담기여도'] = np.clip(df_month['상담기여도'] + month * 0.001, 0.9, 1.0)
        
        # 만족도: 점진적 증가
        df_month['고객서비스만족도'] = df_month['고객서비스만족도'] + month * 0.6
        df_month['고객서비스만족도'] = np.clip(df_month['고객서비스만족도'], 80, 98)
        
        # 감점 (일부 월에만)
        np.random.seed(month * 100)
        if month in [2, 4]:
            n_complaints = np.random.randint(1, 4)
            complaint_centers = np.random.choice(df_month.index, size=n_complaints, replace=False)
            df_month.loc[complaint_centers, '민원대응적정성'] = -5
        
        if month in [5]:
            n_warnings = np.random.randint(1, 3)
            warning_centers = np.random.choice(df_month.index, size=n_warnings, replace=False)
            df_month.loc[warning_centers, '주의경고'] = -10
        
        # 가점 (6월에 일부)
        if month == 6:
            n_bonus = np.random.randint(2, 5)
            bonus_centers = np.random.choice(df_month.index, size=n_bonus, replace=False)
            df_month.loc[bonus_centers, '가점'] = 10
        
        # 소수점 정리
        for col in ['안전점검실점검율', '중점고객안전점검율', '사용계약율', '상담응대율', '상담기여도']:
            df_month[col] = df_month[col].round(4)
        
        df_month['고객서비스만족도'] = df_month['고객서비스만족도'].round(1)
        
        all_data.append(df_month)
    
    # 합치기
    df_all = pd.concat(all_data, ignore_index=True)
    
    # 정렬
    df_all = df_all.sort_values(['센터명', '평가월'])
    
    # 저장
    df_all.to_excel(output_file, index=False)
    
    print(f"\n✅ {output_file} 생성 완료!")
    print(f"📊 총 {len(df_all)}행 (24센터 × 6개월)")
    
    # 샘플 출력
    print("\n🔍 자양센터 1~6월 안전점검율:")
    sample = df_all[df_all['센터명'] == '자양'][['평가월', '안전점검실점검율']]
    for idx, row in sample.iterrows():
        month = row['평가월'].month
        rate = row['안전점검실점검율']
        print(f"  {month}월: {rate:.1%} ({rate * 550:.1f}점)")
    
    return df_all

if __name__ == "__main__":
    df = generate_6months_from_current()
    print("\n✅ 완료! test_6months.xlsx 파일을 대시보드에 업로드하세요.")
