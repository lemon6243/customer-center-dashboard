import importlib

import pytest


PAGE_MODULES = [
    "pages_modules.sidebar",
    "pages_modules.home",
    "pages_modules.performance",
    "pages_modules.center_detail",
    "pages_modules.risk",
    "pages_modules.heatmap",
    "pages_modules.deep_analysis",
    "pages_modules.half_report",
]


@pytest.mark.parametrize("module_name", PAGE_MODULES)
def test_page_module_imports(module_name):
    """app.py에서 사용하는 모든 페이지 모듈이 정상 import되어야 한다."""
    module = importlib.import_module(module_name)
    assert module is not None
