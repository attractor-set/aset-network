# First push

From the extracted repository directory:

```bash
git init -b main
git remote add origin https://github.com/attractor-set/aset-network-extension.git
python -m pip install -r requirements-ci.txt
python tools/validate_extension.py
python tools/model_check_network.py
python tools/run_conformance.py
python -m pytest -q
ruff check .
git add .
git commit -m "feat: bootstrap ASET network extension canon"
git push -u origin main
```

Do not tag `v0.1.0-alpha.1` until CI is green on the pushed commit and the package digest is independently rechecked.
