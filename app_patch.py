"""
app.py 에 KPI 히트맵을 추가하기 위한 패치 스크립트
실행: python app_patch.py
결과: app_patched.py 가 생성됩니다 (원본 app.py 는 그대로 유지)
"""

import re
import sys

SRC = "app.py"          # 원본
DST = "app_patched.py"  # 출력

with open(SRC, "r", encoding="utf-8") as f:
    code = f.read()


# ────────────────────────────────────────────────
# PATCH 1 : import 추가 (로컬 모듈 import 블록 직후)
# ────────────────────────────────────────────────
OLD_IMPORT = "from score_calculator import calculate_scores"
NEW_IMPORT = (
    "from score_calculator import calculate_scores\n"
    "from kpi_heatmap import show_kpi_heatmap  # ✅ KPI 히트맵 모듈"
)

if "from kpi_heatmap import show_kpi_heatmap" in code:
    print("[SKIP] import already patched")
else:
    code = code.replace(OLD_IMPORT, NEW_IMPORT, 1)
    print("[OK]  PATCH 1 - import 추가")


# ────────────────────────────────────────────────
# PATCH 2 : 사이드바 메뉴에 항목 추가
# ────────────────────────────────────────────────
OLD_MENU = '''\
        menu_options = [
            "📊 전체 현황",
            "📈 월별 추이", 
            "🎯 센터별 상세",
            "⚠️ 위험 관리",
            "📊 데이터 분석",
            "📋 원본 데이터"
        ]'''

NEW_MENU = '''\
        menu_options = [
            "📊 전체 현황",
            "📈 월별 추이", 
            "🎯 센터별 상세",
            "⚠️ 위험 관리",
            "🌡️ KPI 히트맵",     # ✅ 신규 추가
            "📊 데이터 분석",
            "📋 원본 데이터"
        ]'''

if "🌡️ KPI 히트맵" in code:
    print("[SKIP] menu already patched")
else:
    if OLD_MENU in code:
        code = code.replace(OLD_MENU, NEW_MENU, 1)
        print("[OK]  PATCH 2 - 메뉴 항목 추가")
    else:
        print("[WARN] PATCH 2 - 메뉴 블록을 찾지 못했습니다. 수동으로 추가하세요.")


# ────────────────────────────────────────────────
# PATCH 3 : 페이지 라우팅에 elif 추가
# ────────────────────────────────────────────────
OLD_ROUTING = '            elif selected_page == "⚠️ 위험 관리":\n                show_risk_management(df)'
NEW_ROUTING = (
    '            elif selected_page == "⚠️ 위험 관리":\n'
    '                show_risk_management(df)\n'
    '            elif selected_page == "🌡️ KPI 히트맵":   # ✅ 신규 추가\n'
    '                show_kpi_heatmap(df)'
)

if "🌡️ KPI 히트맵" in code and "show_kpi_heatmap(df)" in code:
    print("[SKIP] routing already patched")
else:
    if OLD_ROUTING in code:
        code = code.replace(OLD_ROUTING, NEW_ROUTING, 1)
        print("[OK]  PATCH 3 - 라우팅 elif 추가")
    else:
        # 대안 탐색
        alt = 'elif selected_page == "⚠️ 위험 관리":'
        if alt in code:
            lines = code.split('\n')
            new_lines = []
            for i, line in enumerate(lines):
                new_lines.append(line)
                if '⚠️ 위험 관리' in line and 'selected_page' in line:
                    # 다음 줄도 추가하고 나서 elif 삽입
                    indent = len(line) - len(line.lstrip())
                    new_lines.append(lines[i+1])  # show_risk_management 줄
                    new_lines.append(' ' * indent + 'elif selected_page == "🌡️ KPI 히트맵":   # ✅ 신규 추가')
                    new_lines.append(' ' * (indent + 4) + 'show_kpi_heatmap(df)')
                    del lines[i+1]  # 이미 추가했으므로 건너뜀
            # 중복 방지 단순 처리
            code = '\n'.join(new_lines)
            print("[OK]  PATCH 3 (alt) - 라우팅 elif 추가")
        else:
            print("[WARN] PATCH 3 - 라우팅 블록을 찾지 못했습니다. 수동으로 추가하세요.")


# ────────────────────────────────────────────────
# 저장
# ────────────────────────────────────────────────
with open(DST, "w", encoding="utf-8") as f:
    f.write(code)

print(f"\n✅ 패치 완료 → {DST}")
print("   원본 app.py 는 변경되지 않았습니다.")
print("\n📋 다음 단계:")
print("   1. app_patched.py 를 검토 후 app.py 로 교체")
print("   2. kpi_heatmap.py 를 같은 폴더에 추가")
print("   3. streamlit run app.py")
