with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix global font CSS to protect Material Icons
old_font_css = """    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }"""

new_font_css = """    /* Global Font with Icon Font Protection */
    html, body, p, div, span, label, input, button, select, textarea {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Preserve Streamlit Material Icons (Prevents _arrow_ text leak and overlap) */
    [class*="material-symbols"], 
    [class*="material-icons"], 
    span[data-testid*="Icon"], 
    [data-testid="stExpanderToggleIcon"] {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        line-height: 1 !important;
        font-size: 1.1rem !important;
    }"""

if old_font_css in text:
    text = text.replace(old_font_css, new_font_css)
    print("Fixed global font CSS!")

# 2. Update sidebar CSS for clean, non-overlapping layout
old_sidebar_css = """    /* Sidebar Layout & Overlap Prevention (Match React Preview) */
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
    }"""

new_sidebar_css = """    /* Sidebar Layout & Overlap Prevention (Match React Preview) */
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
        margin-top: 12px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebar"] details summary {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 10px 14px !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
        cursor: pointer !important;
        border-bottom: 1px solid transparent !important;
    }
    [data-testid="stSidebar"] details[open] summary {
        border-bottom: 1px solid #E2E8F0 !important;
        background: #F8FAFC !important;
    }
    [data-testid="stSidebar"] details summary p {
        margin: 0 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
    }
    [data-testid="stSidebar"] .stFileUploader {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 6px !important;
        font-weight: 600 !important;
    }"""

if old_sidebar_css in text:
    text = text.replace(old_sidebar_css, new_sidebar_css)
    print("Updated sidebar CSS!")

# 3. Update get_score_badge function with Interim Progress logic
old_badge_func = """def get_score_badge(score):
    if score >= 930:
        return "S", "score-badge-s", "최우수"
    elif score >= 911:
        return "A", "score-badge-a", "우수"
    elif score >= 900:
        return "B", "score-badge-b", "보통"
    elif score >= 880:
        return "C", "score-badge-c", "주의"
    return "D", "score-badge-d", "미달" """

# Let's inspect get_score_badge in text
idx_badge = text.find('def get_score_badge(')
idx_badge_end = text.find('@st.cache_data\ndef load_data_from_path')
if idx_badge != -1 and idx_badge_end != -1:
    new_badge_func = '''def get_score_badge(score, expected_score=None, is_interim=False):
    """
    고객센터 평가 등급 판정:
    - 반기 마감(6월/12월, 즉 최종 확정월): 당월 총점 기준으로 최종 판정
    - 반기 진행 중(1~5개월차, 예: 9월=하반기 3개월차 50% 진행):
      누적 오더 진행 속도 및 12월말(또는 6월말) 예상 총점을 기준으로 현시점 평가 등급 산출
      (예: 50% 시점 총점 824.5점은 1,000점 만점 기준 960~1,000점 페이스이므로 S등급 최우수 판정)
    """
    eval_s = expected_score if (is_interim and expected_score is not None and not (isinstance(expected_score, float) and math.isnan(expected_score))) else score

    if eval_s >= 930:
        return "S", "score-badge-s", "최우수" if not is_interim else "최우수 (유력)"
    elif eval_s >= 911:
        return "A", "score-badge-a", "우수" if not is_interim else "우수 (달성유력)"
    elif eval_s >= 895:
        return "B", "score-badge-b", "보통" if not is_interim else "보통 (정상궤도)"
    elif eval_s >= 875:
        return "C", "score-badge-c", "주의" if not is_interim else "주의 (오더보강)"
    return "D", "score-badge-d", "미달" if not is_interim else "미달 위험"

'''
    text = text[:idx_badge] + new_badge_func + text[idx_badge_end:]
    print("Replaced get_score_badge with interim-aware logic!")

# 4. Update Performance Page table call to pass expected_score and is_interim
old_perf_call = """    for rank, (_, r) in enumerate(sorted_table.iterrows(), start=1):
        g, cls, desc = get_score_badge(r['총점'])"""

new_perf_call = """    is_interim = (month_in_half < 6)
    for rank, (_, r) in enumerate(sorted_table.iterrows(), start=1):
        exp_score = r.get('예상반기총점', r['총점'])
        g, cls, desc = get_score_badge(r['총점'], expected_score=exp_score, is_interim=is_interim)"""

if old_perf_call in text:
    text = text.replace(old_perf_call, new_perf_call)
    print("Updated Performance Page table row score badge call!")

# 5. Also update table header/subtitle to clarify interim evaluation
old_table_desc = '<div class="studio-box-desc">전체 {len(cur_df)}개 센터 실적 데이터 및 6대 KPI 달성 현황</div>'
new_table_desc = '<div class="studio-box-desc">전체 {len(cur_df)}개 센터 실적 데이터 및 6대 KPI 달성 현황 (진행월 평가는 연말 누적 페이스 기준 적용)</div>'
if old_table_desc in text:
    text = text.replace(old_table_desc, new_table_desc)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("patch_grade_and_sidebar.py successfully finished!")
