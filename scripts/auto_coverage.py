from pathlib import Path

import coverage
import pytest

from pkuphysu_wechat.api import modules

API_ROOT_PATH = Path(__file__).parent.parent / "src" / "pkuphysu_wechat" / "api"
OMIT_MODULES = [
    f"*/api/{path.name}/*"
    for path in API_ROOT_PATH.iterdir()
    if path.is_dir() and path.name not in modules
]

print(OMIT_MODULES)

cov = coverage.Coverage(source_pkgs=["pkuphysu_wechat"], omit=OMIT_MODULES)
cov.start()
pytest.main()
cov.stop()
cov.save()

cov.xml_report()
