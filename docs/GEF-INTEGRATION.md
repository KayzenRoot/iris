# GEF v1.0.0 Integration - IRIS

IRIS adopts stable GEF Bootstrap v1.0.0 at commit `866fe3af8cccc65c929aaf6a47a924401fa448b3`.

GEF v1.0.0 is distributed as a source workspace, not a published global CLI. IRIS therefore does **not** vendor the GEF workspace or claim `npm install -g` support.

## Local GEF checkout
Recommended side-by-side layout:
```text
workspace/
  gef-bootstrap/
  iris/
```

Checkout and validate the stable GEF source independently:
```powershell
git -C ..\gef-bootstrap checkout v1.0.0
npm --prefix ..\gef-bootstrap ci
npm --prefix ..\gef-bootstrap run validate
python scripts/gef_preflight.py
```

`GEF_REPO_PATH` may point to a different checkout. The IRIS verifies the exact v1.0.0 GEF source release when that optional checkout is explicitly used, and fails closed on drift. Repository Governance CI does not require a separate GEF checkout or any external context service.

GEF authority in IRIS is represented by `.engineering/gef/*`, the Source Pack, Work Orders, Context Locks, Evidence Bundles and exact-head review lifecycle.
