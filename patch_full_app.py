import re
import textwrap

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update imports with Safe Plotly import
old_imports = """import plotly.express as px
import plotly.graph_objects as go
import textwrap"""

new_imports = """try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    px = None
    go = None
import textwrap"""

if old_imports in text:
    text = text.replace(old_imports, new_imports)
elif 'import plotly.express as px' in text and 'HAS_PLOTLY' not in text:
    text = re.sub(
        r'import plotly\.express as px\s+import plotly\.graph_objects as go',
        """try:\n    import plotly.express as px\n    import plotly.graph_objects as go\n    HAS_PLOTLY = True\nexcept ImportError:\n    HAS_PLOTLY = False\n    px = None\n    go = None""",
        text
    )

# 2. Add Sidebar specific CSS
sidebar_css = """
    /* Sidebar Layout & Overlap Prevention (Match React Preview) */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #DCE3EA !important;
    }
    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background-color: #FFFFFF !important;
        border: 1px solid #DCE3EA !important;
        border-radius: 8px !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] details {
        border: none !important;
    }
    [data-testid="stSidebar"] .stFileUploader {
        margin-top: 6px !important;
    }
"""

if '/* Sidebar Layout & Overlap Prevention' not in text:
    text = text.replace('</style>', sidebar_css + '\n</style>')

# 3. Enhance load_local_records to PRIORITIZE xlsx over json
old_load_section_start = text.find('def load_data_from_path')
old_load_section_end = text.find('# 사이드바 데이터 로더')

if old_load_section_start != -1 and old_load_section_end != -1:
    old_loader_code = text[old_load_section_start:old_load_section_end]
    
    new_loader_code = '''def load_data_from_path(file_path):
    if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        try:
            df = pd.read_excel(file_path)
            return df.to_dict(orient='records')
        except Exception:
            # zipfile fallback for xlsx
            import zipfile
            import xml.etree.ElementTree as ET
            with zipfile.ZipFile(file_path, 'r') as z:
                sst = ET.fromstring(z.read('xl/sharedStrings.xml'))
                ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
                strings = []
                for si in sst.findall(f'{ns}si'):
                    t = si.find(f'{ns}t')
                    if t is not None:
                        strings.append(t.text or '')
                    else:
                        strings.append(''.join([elem.text or '' for elem in si.iter(f'{ns}t')]))
                sheet = ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
                rows = sheet.findall(f'.//{ns}row')
                header_row = rows[0]
                col_map = {}
                for c in header_row.findall(f'{ns}c'):
                    ref = c.attrib.get('r', '')
                    col = ''.join([ch for ch in ref if ch.isalpha()])
                    t = c.attrib.get('t')
                    v = c.find(f'{ns}v')
                    val = v.text if v is not None else ''
                    if t == 's':
                        val = strings[int(val)] if val.isdigit() and int(val) < len(strings) else val
                    col_map[col] = val
                recs = []
                for r in rows[1:]:
                    rec = {}
                    for c in r.findall(f'{ns}c'):
                        ref = c.attrib.get('r', '')
                        col = ''.join([ch for ch in ref if ch.isalpha()])
                        h = col_map.get(col)
                        if not h:
                            continue
                        t = c.attrib.get('t')
                        v = c.find(f'{ns}v')
                        val = v.text if v is not None else ''
                        if t == 's':
                            val = strings[int(val)] if val.isdigit() and int(val) < len(strings) else val
                        else:
                            try:
                                val = float(val) if '.' in val else int(val)
                            except ValueError:
                                pass
                        rec[h] = val
                    if rec:
                        recs.append(rec)
                return recs
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

def load_local_records():
    """
    [데이터 우선순위 정책]
    1순위: 사용자가 항상 업로드/커밋하는 data/latest_data.xlsx 파일을 최우선으로 탐색 및 로드합니다.
    2순위: data/latest_data.json 백업 파일
    3순위: 내장 기본 데이터
    """
    # 1순위: latest_data.xlsx 탐색 (엑셀 파일 최우선)
    excel_candidates = [
        os.path.join(os.path.dirname(__file__), 'data', 'latest_data.xlsx'),
        os.path.join(os.path.dirname(__file__), 'latest_data.xlsx'),
        'data/latest_data.xlsx',
        'latest_data.xlsx',
        os.path.join(os.path.dirname(__file__), 'data', 'latest_data.xls'),
        'data/latest_data.xls',
    ]
    for p in excel_candidates:
        if os.path.exists(p):
            try:
                data = load_data_from_path(p)
                if data and len(data) > 0:
                    return data
            except Exception:
                continue

    # 2순위: JSON 데이터 파일 탐색
    json_candidates = [
        os.path.join(os.path.dirname(__file__), 'data', 'latest_data.json'),
        os.path.join(os.path.dirname(__file__), 'src', 'data', 'latest_data.json'),
        os.path.join(os.path.dirname(__file__), 'latest_data.json'),
        'data/latest_data.json',
        'src/data/latest_data.json',
        'latest_data.json',
    ]
    for p in json_candidates:
        if os.path.exists(p):
            try:
                data = load_data_from_path(p)
                if data and len(data) > 0:
                    return data
            except Exception:
                continue

    # 3순위: 비상용 내장 목업 데이터
    centers = ["자양", "휘경", "중부", "동부", "서대문", "마포", "용산", "성동", "광진", "노원", "도봉", "강북", "성북", "중랑", "동대문", "남양주", "구리", "가평", "양평", "포천", "덕소/양평", "퇴계원/별내", "의정부"]
    fallback = []
    for c in centers:
        fallback.append({
            "센터명": c,
            "평가월": "2026-09-01",
            "안전점검실점검율": 0.48,
            "중점고객안전점검율": 0.52,
            "사용계약율": 0.93,
            "상담응대율": 1.0,
            "상담기여도": 1.0,
            "고객서비스만족도": 94.5,
            "민원대응적정성": 0,
            "주의경고": 0,
            "가점": 0,
            "총점": 650.0
        })
    return fallback

'''
    text = text[:old_load_section_start] + new_loader_code + text[old_load_section_end:]

# 4. Reorder Sidebar UI: Logo -> Radio -> Selectbox -> Status Card -> Excel Management Expander -> Rules Expander
old_sidebar_block_start = text.find('# 사이드바 데이터 로더')
old_sidebar_block_end = text.find('if menu == "🏠 홈":')

if old_sidebar_block_start != -1 and old_sidebar_block_end != -1:
    new_sidebar_block = '''# 사이드바 데이터 상태 관리 (커스텀 업로드 레코드 유지)
if 'custom_records' not in st.session_state:
    st.session_state.custom_records = None

if st.session_state.custom_records is not None:
    raw_records = st.session_state.custom_records
else:
    raw_records = load_local_records()

df_all = process_dataframe(raw_records)

# -----------------------------------------------------------------------------
# 4. 사이드바 네비게이션 및 평가월 선택 (Studio 프리뷰와 100% 동일한 순서 & 디자인)
# -----------------------------------------------------------------------------
all_months = sorted(list(df_all['평가연월'].unique()))
latest_month = all_months[-1] if all_months else "2026-09"

# [1] 사이드바 최상단 브랜드 로고 (프리뷰와 동일)
render_html("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:18px; padding-bottom:12px; border-bottom:1px solid #E2E8F0;">
    <div style="background:#0B4EA2; color:white; width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; font-weight:800; font-size:16px; box-shadow:0 1px 3px rgba(0,0,0,0.1);">
        Y
    </div>
    <div>
        <div style="font-size:14px; font-weight:800; color:#0B4EA2; line-height:1.2;">예스코 고객센터</div>
        <div style="font-size:11px; color:#64748B;">성과 평가 관리 시스템</div>
    </div>
</div>
""", in_sidebar=True)

# [2] 메인 메뉴 라디오 버튼 (프리뷰와 1:1 일치)
menu = st.sidebar.radio(
    "메인 메뉴",
    ["🏠 홈", "📊 성과 분석", "🎯 센터 진단", "⚠️ 위험 관리", "🌡️ KPI 히트맵", "🔬 심화 분석", "📑 상반기 보고"]
)

# [3] 평가월 선택 (2026년 9월 등 최신월 자동 기본 선택)
default_idx = len(all_months) - 1 if all_months else 0
month_display_map = {m: f"{m} (★최신)" if m == latest_month else m for m in all_months}

selected_month = st.sidebar.selectbox(
    "📅 평가월 선택",
    options=all_months,
    index=default_idx,
    format_func=lambda m: month_display_map.get(m, m)
)

cur_df = df_all[df_all['평가연월'] == selected_month].copy()
if cur_df.empty:
    cur_df = df_all.copy()

cur_year = cur_df['연도'].iloc[0]
cur_month = cur_df['월'].iloc[0]
half_name = "상반기" if cur_month <= 6 else "하반기"
month_in_half = cur_month if cur_month <= 6 else cur_month - 6
target_end_text = "6월말" if cur_month <= 6 else "12월말"
progress_pct = int((month_in_half / 6) * 100)
benchmark_safety = (month_in_half / 6) * 92.0

# [4] 데이터 현황 정보 카드 (프리뷰와 100% 일치)
render_html(f"""
<div style="background:white; border:1px solid #DCE3EA; border-radius:10px; padding:12px; margin-top:12px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
    <div style="font-size:12px; font-weight:700; color:#172B4D; display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
        <span>📊 데이터 현황</span>
        <span style="width:8px; height:8px; border-radius:50%; background:#10B981; display:inline-block;"></span>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>기준월:</span> <strong style="color:#172B4D;">{cur_year}년 {cur_month}월</strong>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>진행 경과:</span> <span style="color:#0B4EA2; font-weight:600;">{half_name} {month_in_half}/6개월차 ({progress_pct}%)</span>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between; margin-bottom:4px;">
        <span>대상 센터:</span> <strong style="color:#172B4D;">{len(cur_df)}개소</strong>
    </div>
    <div style="font-size:11px; color:#5E6C84; display:flex; justify-content:space-between;">
        <span>전체 레코드:</span> <span>{len(df_all):,}건</span>
    </div>
</div>
""", in_sidebar=True)

# [5] 엑셀 데이터 관리 섹션 (프리뷰와 동일하게 데이터 현황 카드 하단에 독립 배치)
with st.sidebar.expander("📁 엑셀 데이터 교체 & 관리", expanded=False):
    uploaded_file = st.file_uploader(
        "데이터 파일 교체 (.xlsx / .json)",
        type=['xlsx', 'xls', 'json'],
        key="sidebar_data_uploader",
        help="최신 엑셀 또는 JSON 데이터를 직접 업로드하여 분석할 수 있습니다."
    )
    if uploaded_file is not None:
        try:
            custom_data = parse_uploaded_bytes(uploaded_file.getvalue(), uploaded_file.name)
            if custom_data:
                st.session_state.custom_records = custom_data
                st.success(f"✅ 파일 로드 성공: {len(custom_data)}건")
                st.rerun()
        except Exception as e:
            st.error(f"파일 파싱 실패: {e}")

    if st.button("기본 데이터로 복원", use_container_width=True, key="restore_default_btn"):
        st.session_state.custom_records = None
        st.cache_data.clear()
        st.success("기본 데이터로 복원되었습니다.")
        st.rerun()

# [6] 배점 규칙 & 기준 안내 (사이드바 하단에 깔끔하게 배치하여 겹침 차단)
with st.sidebar.expander("⚖️ 배점 규칙 & 기준 안내", expanded=False):
    st.markdown("""
    **🎯 종합 합격 및 재계약 기준**
    - 반기 합격: **911점 이상** (1,000점 만점)
    - 연간 재계약: 상·하반기 합산 **1,822점 이상**
    - 판정: 911점 이상(안전/달성), 895~910점(주의), 895점 미만(위험)

    ---
    **📊 6대 핵심 KPI 배점**
    - **안전점검실점검율**: 550점 (누적형)
    - **중점고객안전점검율**: 100점 (누적형)
    - **사용계약율**: 50점 (A:50, B:45, C:40, D:35)
    - **상담응대율**: 100점 (당월형)
    - **상담기여도**: 100점 (당월형)
    - **고객서비스만족도**: 100점 (당월형)
    - *가감점: 민원대응(±5), 주의경고(-1~-5), 가점(+5)*
    """)

# [7] 사이드바 푸터 버전 표기
render_html("""
<div style="text-align:center; font-size:10px; color:#94A3B8; margin-top:16px; padding-top:8px; border-top:1px solid #E2E8F0;">
    YESCO Customer Dashboard v2.1
</div>
""", in_sidebar=True)

'''
    text = text[:old_sidebar_block_start] + new_sidebar_block + text[old_sidebar_block_end:]

# 5. Add PAGE 7: 📑 상반기 보고 if not present
if 'elif menu == "📑 상반기 보고":' not in text:
    half_report_page_code = '''
# =============================================================================
# PAGE 7: 📑 상반기 보고 (2026년 상반기 6월 마감 실적 종합 리포트)
# =============================================================================
elif menu == "📑 상반기 보고":
    # 2026년 상반기 마감인 6월 데이터 및 전년(2025년) 6월 벤치마크 추출
    h1_df = df_all[(df_all['연도'] == 2026) & (df_all['월'] == 6)].copy()
    if h1_df.empty:
        # 혹시 2026년 6월이 없으면 상반기 중 가장 늦은 월 사용
        h1_df = df_all[(df_all['연도'] == 2026) & (df_all['월'] <= 6)].copy()
        if not h1_df.empty:
            max_m = h1_df['월'].max()
            h1_df = h1_df[h1_df['월'] == max_m].copy()
        else:
            h1_df = cur_df.copy()

    py_h1_df = df_all[(df_all['연도'] == 2025) & (df_all['월'] == 6)].copy()
    py_h1_map = dict(zip(py_h1_df['센터명'], py_h1_df['총점'])) if not py_h1_df.empty else {}

    total_h1_centers = len(h1_df)
    avg_h1_score = h1_df['총점'].mean() if total_h1_centers > 0 else 0.0
    pass_h1_count = len(h1_df[h1_df['총점'] >= 911])
    pass_h1_rate = (pass_h1_count / total_h1_centers * 100) if total_h1_centers > 0 else 0.0
    under_h1_count = total_h1_centers - pass_h1_count

    py_avg_h1 = py_h1_df['총점'].mean() if not py_h1_df.empty else 0.0
    yoy_h1_diff = (avg_h1_score - py_avg_h1) if py_avg_h1 > 0 else 0.0

    # 배너
    render_html(f"""
    <div style="background:linear-gradient(135deg, #0B4EA2 0%, #073874 100%); color:white; padding:22px 28px; border-radius:14px; margin-bottom:22px; box-shadow:0 4px 16px rgba(11,78,162,0.18); display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
        <div>
            <h1 style="margin:0; font-size:22px; font-weight:800; letter-spacing:-0.5px; color:#FFFFFF !important;">📑 2026년 상반기 종합 평가 결과 리포트</h1>
            <p style="margin:6px 0 0 0; font-size:13px; opacity:0.9; color:#E2E8F0 !important;">2026년 상반기(1~6월) 최종 마감 실적 및 전년(2025년) 상반기 대비 증감 종합 분석</p>
        </div>
        <div style="display:flex; gap:8px;">
            <span style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35); color:#FFFFFF; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">2026년 06월 마감 확정</span>
            <span style="background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35); color:#FFFFFF; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">총 23개 센터 평가 완료</span>
        </div>
    </div>
    """)

    # 3대 핵심 KPI 카드
    diff_color = "#166534" if yoy_h1_diff >= 0 else "#991B1B"
    diff_symbol = "+" if yoy_h1_diff >= 0 else ""
    render_html(f"""
    <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px; margin-bottom:22px;">
        <div class="metric-grid-card" style="border-left:4px solid #0B4EA2;">
            <div class="metric-title"><span>상반기 평균 총점</span> <span>📊</span></div>
            <div class="metric-value" style="color:#0B4EA2;">{avg_h1_score:.1f}점</div>
            <div class="metric-sub" style="color:{diff_color}; font-weight:700;">전년 대비 {diff_symbol}{yoy_h1_diff:.1f}점 (기준 목표 911.0점)</div>
        </div>
        <div class="metric-grid-card" style="border-left:4px solid #10B981;">
            <div class="metric-title"><span>911점 달성률</span> <span>🎯</span></div>
            <div class="metric-value" style="color:#10B981;">{pass_h1_rate:.1f}%</div>
            <div class="metric-sub" style="color:#10B981; font-weight:700;">{pass_h1_count}개 센터 달성 / 총 {total_h1_centers}개소</div>
        </div>
        <div class="metric-grid-card" style="border-left:4px solid #EF4444;">
            <div class="metric-title"><span>미달 센터 현황</span> <span>⚠️</span></div>
            <div class="metric-value" style="color:#EF4444;">{under_h1_count}개소</div>
            <div class="metric-sub" style="color:#64748B;">하반기 재계약 종합 관리 대상</div>
        </div>
    </div>
    """)

    # 권역 조정 및 센터 통합 안내
    render_html("""
    <div style="background:#FFFDF5; border:1px solid #FDE68A; border-radius:12px; padding:16px 20px; margin-bottom:22px; color:#92400E; font-size:12px; line-height:1.6;">
        <div style="font-weight:800; font-size:13px; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
            <span>ℹ️</span> 권역 조정 및 센터 통합 안내사항
        </div>
        <div>• <strong>퇴계원/별내</strong>: 2026년 통합 운영 센터로 단일 실적으로 집계 평가되었습니다.</div>
        <div>• <strong>구리</strong>: 2026년 4월 권역조정으로 행정동을 흡수하였으나, 안전점검은 기존 관리세대 기준으로 공정하게 산정되었습니다.</div>
    </div>
    """)

    # 센터별 종합 평가 순위 테이블
    h1_sorted = h1_df.sort_values(by='총점', ascending=False).reset_index(drop=True)
    h1_rows_html = ""
    for idx, row in h1_sorted.iterrows():
        rank = idx + 1
        cname = row['센터명']
        total_s = float(row['총점'])
        target_gap = total_s - 911.0
        gap_style = "color:#166534; font-weight:700;" if target_gap >= 0 else "color:#991B1B; font-weight:700;"
        gap_text = f"+{target_gap:.1f}" if target_gap >= 0 else f"{target_gap:.1f}"
        
        py_s = py_h1_map.get(cname)
        if py_s is not None:
            py_diff = total_s - py_s
            py_text = f"+{py_diff:.1f}" if py_diff >= 0 else f"{py_diff:.1f}"
            py_style = "color:#166534; font-weight:700;" if py_diff >= 0 else "color:#991B1B; font-weight:700;"
        else:
            py_text = "-"
            py_style = "color:#94A3B8;"

        h1_rows_html += f"""
        <tr>
            <td style="font-weight:700; color:#64748B;">{rank}</td>
            <td style="font-weight:800; color:#1E293B;">{cname}</td>
            <td style="text-align:right; font-weight:800; color:#0B4EA2;">{total_s:.1f}</td>
            <td style="text-align:right; {gap_style}">{gap_text}</td>
            <td style="text-align:right; {py_style}">{py_text}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('안전점검_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('중점고객_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('사용계약_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('상담응대_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('상담기여_점수', 0)):.1f}</td>
            <td style="text-align:right; color:#475569;">{float(row.get('만족도_점수', 0)):.1f}</td>
        </tr>
        """

    h1_table_html = f"""
    <div class="studio-box">
        <div class="studio-box-header">
            <div>
                <div class="studio-box-title">🏢 센터별 2026년 상반기 평가 종합 순위</div>
                <div class="studio-box-desc">2026년 6월 마감 기준 총점 및 6대 핵심 평가지표 배점 내역</div>
            </div>
        </div>
        <div style="overflow-x:auto;">
            <table class="studio-table">
                <thead>
                    <tr>
                        <th>순위</th>
                        <th>센터명</th>
                        <th style="text-align:right;">상반기 총점</th>
                        <th style="text-align:right;">목표(911) 대비</th>
                        <th style="text-align:right;">전년 대비</th>
                        <th style="text-align:right;">안전점검(550)</th>
                        <th style="text-align:right;">중점고객(100)</th>
                        <th style="text-align:right;">사용계약(50)</th>
                        <th style="text-align:right;">상담응대(100)</th>
                        <th style="text-align:right;">상담기여(100)</th>
                        <th style="text-align:right;">만족도(100)</th>
                    </tr>
                </thead>
                <tbody>
                    {h1_rows_html}
                </tbody>
            </table>
        </div>
    </div>
    """
    render_html(h1_table_html)
'''
    text = text + '\n' + half_report_page_code

# Save updated code
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('app.py successfully patched!')
