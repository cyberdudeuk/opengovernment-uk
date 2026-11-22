"""The licence REUSE.toml gives a path: the last matching override wins. Shared so every check reads licences one way (OG-D65)."""
import fnmatch, pathlib, tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def licence_of(rel):
    lic = None
    for a in tomllib.loads((ROOT / "REUSE.toml").read_text())["annotations"]:
        pats = a["path"] if isinstance(a["path"], list) else [a["path"]]
        if any(fnmatch.fnmatch(rel, p.replace("**", "*")) for p in pats): lic = a["SPDX-License-Identifier"]
    return lic
