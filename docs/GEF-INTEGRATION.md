# GEF v1.0.0 Integration - IRIS

IRIS adopts stable GEF Bootstrap v1.0.0 at commit `866fe3af8cccc65c929aaf6a47a924401fa448b3`.

GEF v1.0.0 is distributed as a source workspace, not a published global CLI. IRIS therefore does **not** vendor the GEF workspace or claim `npm install -g` support.

## Local GEF checkout
Recommended side-by-side layout:
```text
workspace/
  gef-bootstrap/
  hive/
  iris/
```

Checkout and validate the stable GEF source independently:
```powershell
git -C ..\gef-bootstrap checkout v1.0.0
npm --prefix ..\gef-bootstrap ci
npm --prefix ..\gef-bootstrap run validate
python scripts/gef_preflight.py
```

`GEF_REPO_PATH` may point to a different checkout. The IRIS preflight requires the exact v1.0.0 release commit and fails closed on drift.

GEF authority in IRIS is represented by `.engineering/gef/*`, the Source Pack, Work Orders, Context Locks, Evidence Bundles and exact-head review lifecycle.
