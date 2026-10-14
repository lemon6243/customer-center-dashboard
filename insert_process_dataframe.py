with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = "# 사이드바 데이터 상태 관리 (커스텀 업로드 레코드 유지)"

process_dataframe_code = '''@st.cache_data
def process_dataframe(raw_list):
    df = pd.DataFrame(raw_list)
    # 날짜 정규화
    df['정규평가월'] = df['평가월'].apply(normalize_date_string)
    df['평가연월'] = df['정규평가월'].str.slice(0, 7)
    df['연도'] = df['정규평가월'].apply(lambda x: int(x[:4]))
    df['월'] = df['정규평가월'].apply(lambda x: int(x[5:7]))
    df['반기'] = df['월'].apply(lambda m: '상반기' if m <= 6 else '하반기')
    df['반기월차'] = df['월'].apply(lambda m: m if m <= 6 else m - 6)

    # 비율 지표 to_percentage() 적용 (0.15 -> 15.0%)
    df['안전점검실점검율'] = df['안전점검실점검율'].apply(to_percentage)
    df['중점고객안전점검율'] = df['중점고객안전점검율'].apply(to_percentage)
    df['사용계약율'] = df['사용계약율'].apply(to_percentage)
    df['상담응대율'] = df['상담응대율'].apply(to_percentage)
    df['상담기여도'] = df['상담기여도'].apply(to_percentage)
    df['고객서비스만족도'] = pd.to_numeric(df.get('고객서비스만족도', 0), errors='coerce').fillna(0)

    # 배점 산출
    df['안전점검_점수'] = (df['안전점검실점검율'] / 100.0) * 550.0
    df['중점고객_점수'] = (df['중점고객안전점검율'] / 100.0) * 100.0
    df['사용계약_점수'] = df['사용계약율'].apply(calc_contract_score)
    df['상담응대_점수'] = (df['상담응대율'] / 100.0) * 100.0
    df['상담기여_점수'] = (df['상담기여도'] / 100.0) * 100.0
    df['만족도_점수'] = df['고객서비스만족도']
        
    calc_total = (
        df['안전점검_점수'] +
        df['중점고객_점수'] +
        df['사용계약_점수'] +
        df['상담응대_점수'] +
        df['상담기여_점수'] +
        df['만족도_점수']
    )
    # 원시 데이터에 신뢰할 수 있는 총점이 있으면 우선 유지, 없으면 계산값 적용
    if '총점' in df.columns:
        df['총점'] = pd.to_numeric(df['총점'], errors='coerce')
        df['총점'] = df['총점'].fillna(calc_total)
    else:
        df['총점'] = calc_total

    # 전년 동월 및 반기말 비교 벤치마크 맵 구축
    all_recs = df.to_dict(orient='records')
    yoy_map = {}
    py_half_end_map = {}
    for r in all_recs:
        key = (r['연도'], r['월'], r['센터명'])
        yoy_map[key] = r['총점']
        if r['월'] in [6, 12]:
            py_half_end_map[(r['연도'], r['월'], r['센터명'])] = r['총점']

    def calc_realistic_projected_score(row):
        """전년 12월말(또는 6월말) 실적 및 전년 동월 대비 누적 증감(YoY) 페이스를 100% 기준으로 하는 직관적/고신뢰성 예측 모델"""
        cur_s = float(row['총점'])
        m = row['반기월차']
        if m >= 6:
            return round(cur_s, 1)
        
        target_m = 6 if row['월'] <= 6 else 12
        py_end = py_half_end_map.get((row['연도'] - 1, target_m, row['센터명']))
        py_cur = yoy_map.get((row['연도'] - 1, row['월'], row['센터명']))
        
        # 1순위: 전년 12월말 실적(py_end)과 전년 동월 대비 증감(yoy_d)이 있는 경우
        # 예: 용산센터 (전년 12월말 929.4점, 전년 8월대비 -24.1점) -> 12월말 예상 = 929.4 - 24.1 = 905.3점 (미달 위험)
        if py_end is not None and py_cur is not None:
            yoy_d = cur_s - py_cur
            predicted = py_end + yoy_d
            return round(min(1000.0, max(0.0, predicted)), 1)
        
        # 2순위: 전년 반기말 실적만 있는 경우
        if py_end is not None:
            return round(min(1000.0, max(0.0, py_end)), 1)
        
        # 3순위: 신규 센터 등 전년 벤치마크가 없는 경우 진도율 기반 추정
        pace_ratio = max(0.1, m / 6.0)
        non_cum = row['사용계약_점수'] + row['상담응대_점수'] + row['상담기여_점수'] + row['만족도_점수']
        projected_safety = min(550.0, row['안전점검_점수'] / pace_ratio)
        projected_key = min(100.0, row['중점고객_점수'] / pace_ratio)
        base_extrapolation = projected_safety + projected_key + non_cum
        return round(min(1000.0, max(0.0, base_extrapolation)), 1)

    df['예상반기총점'] = df.apply(calc_realistic_projected_score, axis=1)

    def enrich(row):
        py = yoy_map.get((row['연도'] - 1, row['월'], row['센터명']))
        target_m = 6 if row['월'] <= 6 else 12
        py_end = py_half_end_map.get((row['연도'] - 1, target_m, row['센터명']))
        yoy_diff = (row['총점'] - py) if py is not None else None
        
        # 도달 판정
        if row['예상반기총점'] < 905:
            judgment = '위험'
        elif row['예상반기총점'] < 915:
            judgment = '주의'
        else:
            judgment = '정상궤도'

        # 오더 진척 상태
        m_in_h = row['반기월차']
        bm = (m_in_h / 6.0) * 92.0
        if row['안전점검실점검율'] < bm - 3.0:
            order_status = '지연'
        elif row['안전점검실점검율'] < bm:
            order_status = '보통'
        else:
            order_status = '양호'

        return pd.Series([py, yoy_diff, py_end, judgment, order_status])

    df[['전년동월_총점', '전년동월대비_증감', '전년반기말_총점', '도달판정', '오더진척상태']] = df.apply(enrich, axis=1)
    return df

'''

text = text.replace(target, process_dataframe_code + '\n' + target)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('process_dataframe successfully inserted into app.py!')
