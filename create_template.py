import pandas as pd
import numpy as np

# 24개 센터
centers = [
    '자양', '휘경', '중부', '구의', '금호', '면목', '행당', '구리',
    '중화', '제기', '삼선', '중곡', '신내', '종로', '금곡/경기동부',
    '용산', '퇴계원', '장안', '상봉', '성수', '정릉', '서부', '덕소/양평', '별내'
]

# 데이터 생성
data = []

for center in centers:
    # 상반기 (1~6월)
    for month in range(1, 7):
        # 당월 실적 (점진적 증가)
        base_safety = 8000 + month * 1500
        base_priority = 1500 + month * 250
        base_contract = 800 + month * 80
        base_counseling = 18000 + month * 300
        base_contribution = 17000 + month * 400
        base_satisfaction = 85 + month * 1
        
        # 센터별 변동
        np.random.seed(hash(center) % 1000 + month)
        variation = np.random.uniform(0.9, 1.1)
        
        row = {
            '센터명': center,
            '평가월': f'2024-{month:02d}-01',
            
            # 안전점검
            '안전점검총오더수': 50000,
            '당월안전점검완료': int(base_safety * variation),
            
            # 중점고객
            '중점고객총오더수': 10000,
            '당월중점고객점검완료': int(base_priority * variation),
            
            # 사용계약
            '사용계약총오더수': 5000,
            '당월사용계약체결': int(base_contract * variation),
            
            # 상담응대
            '상담응대총건수': 20000,
            '당월상담응대완료': int(base_counseling * variation),
            
            # 상담기여
            '상담기여총건수': 20000,
            '당월상담기여완료': int(base_contribution * variation),
            
            # 고객만족도
            '당월만족도': round(base_satisfaction + np.random.uniform(-3, 3), 1),
            
            # 감점/가점
            '민원대응적정성': np.random.choice([0, 0, 0, -5], p=[0.8, 0.1, 0.05, 0.05]),
            '주의경고': np.random.choice([0, 0, 0, -10], p=[0.9, 0.05, 0.03, 0.02]),
            '가점': np.random.choice([0, 0, 0, 10], p=[0.85, 0.1, 0.03, 0.02])
        }
        
        data.append(row)

# DataFrame 생성
df = pd.DataFrame(data)

# 엑셀로 저장
df.to_excel('cumulative_template.xlsx', index=False)

print("✅ cumulative_template.xlsx 생성 완료!")
print(f"📊 총 {len(df)}행 데이터 (24개 센터 × 6개월)")
print("\n샘플 데이터:")
print(df.head(10))
