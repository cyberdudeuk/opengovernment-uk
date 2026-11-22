"""Committed outputs must match a fresh build (OG-D76). On a difference, show where it is, so the cause is plain.

  python tools/fresh_check.py   (after the build steps; exits 1 if any generated file differs from the commit)
"""
import subprocess, sys

PATHS = ["docs", "data"]
SKIP = {"docs/opengovernment-uk.db"}  # its bytes depend on the SQLite version; its content is fingerprinted instead


def git(*a): return subprocess.run(["git", *a], capture_output=True, check=True).stdout  # noqa: S603,S607  fixed program and arguments


def ctx(b, i): return b[max(0, i - 120):i + 120].decode("utf-8", "replace").replace("\n", "\\n")


def main():
    changed = [f for f in git("diff", "--name-only", "--", *PATHS).decode().split() if f not in SKIP]
    if not changed: print("fresh: committed outputs match a fresh build"); return
    for f in changed:
        old, new = git("show", f"HEAD:{f}"), open(f, "rb").read()
        i = next((k for k in range(min(len(old), len(new))) if old[k] != new[k]), min(len(old), len(new)))
        print(f"{f}: first difference at byte {i} (sizes {len(old)} -> {len(new)})\n  committed: …{ctx(old, i)}…\n  rebuilt:   …{ctx(new, i)}…")
    sys.exit(f"fresh: {len(changed)} generated file(s) differ from the commit")


if __name__ == "__main__":
    main()
