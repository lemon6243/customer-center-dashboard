with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add Material Symbols font import at top of CSS
old_import = "@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');"
new_import = """@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');"""

if old_import in text:
    text = text.replace(old_import, new_import)
    print("Added Google Material Symbols web font @import!")

# Update Icon Preservation CSS
old_icon_css = """    /* Preserve Streamlit Material Icons (Prevents _arrow_ text leak and overlap) */
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

new_icon_css = """    /* Material Symbols & Icon Font Protection (Eliminates _arrow_ text leaks and overlap) */
    .material-symbols-rounded,
    .material-icons,
    [class*="material-symbols"],
    [class*="material-icons"],
    [data-testid="stExpanderToggleIcon"],
    span[data-testid*="Icon"] {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
        font-style: normal !important;
        font-weight: 400 !important;
        font-size: 18px !important;
        line-height: 1 !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        text-rendering: optimizeLegibility !important;
        flex-shrink: 0 !important;
        width: 20px !important;
        height: 20px !important;
    }

    [data-testid="stSidebar"] details summary {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 10px 14px !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
        cursor: pointer !important;
        min-height: 44px !important;
        box-sizing: border-box !important;
    }

    [data-testid="stSidebar"] details summary p {
        margin: 0 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        color: #172B4D !important;
        white-space: nowrap !important;
    }"""

if old_icon_css in text:
    text = text.replace(old_icon_css, new_icon_css)
    print("Enhanced Material Symbols CSS!")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("patch_font_material.py finished successfully!")
