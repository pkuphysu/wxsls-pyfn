"""
This is a helper script to generate base64 encoded secret.

The administrator is supposed keep a copy of `secrets.toml` locally.
Whenever secrets need an update, run this script by:

```sh
# No extra packages needed, thus no need for activating venv.
python .github/secret_encoder.py
```

Then update GitHub actions' secret with printed base64 string.
"""
from base64 import b64encode
from pathlib import Path

SECRET_FILE = (
    Path(__file__).parent.parent
    / "src"
    / "pkuphysu_wechat"
    / "config"
    / ".secrets.toml"
)

if not SECRET_FILE.exists():
    raise OSError(f"{SECRET_FILE} does not exist")

with open(SECRET_FILE, "rb") as f:
    print(b64encode(f.read()).decode())
