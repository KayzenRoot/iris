"""Read immutable pre-transition Git provenance without an installed context service.

Only the old exact commit is materialized, in a disposable private directory.
This is a source-integrity audit adapter, not a fallback for live IRIS context.
"""
from __future__ import annotations

from functools import lru_cache
import io
from pathlib import Path
import subprocess
import tarfile
from tempfile import mkdtemp
import shutil
import atexit

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_MAIN = "95d58dd7a3b1275f4aaff4f147f2be852ecad588"
ORIGINAL_TREE = "0412ab77db6159f7a9f3da6a66db3c5950845605"


@lru_cache(maxsize=1)
def trusted_original_root() -> Path:
    """Materialize the exact immutable original Git tree; reject unsafe archive entries."""
    tree = subprocess.check_output(["git", "rev-parse", f"{ORIGINAL_MAIN}^{{tree}}"],
                                   cwd=ROOT, text=True).strip()
    if tree != ORIGINAL_TREE:
        raise RuntimeError("Original historical Git commit/tree proof unavailable")
    archive = subprocess.check_output(["git", "archive", "--format=tar", ORIGINAL_MAIN],
                                      cwd=ROOT)
    dest = Path(mkdtemp(prefix="iris-original-git-proof-")).resolve()
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tar:
            for entry in tar:
                path = (dest / entry.name).resolve()
                if not path.is_relative_to(dest):
                    raise ValueError("Unsafe historical Git archive path")
                if entry.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                elif entry.isfile():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    fileobj = tar.extractfile(entry)
                    if fileobj is None:
                        raise ValueError("Missing original Git object")
                    path.write_bytes(fileobj.read())
                else:
                    raise ValueError("Unsupported historical Git entry kind")
    except Exception:
        shutil.rmtree(dest, ignore_errors=True)
        raise
    atexit.register(shutil.rmtree, dest, ignore_errors=True)
    return dest
