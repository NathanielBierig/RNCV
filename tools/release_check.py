"""Pre-public release check (docs/ROADMAP.md, "Public release" item 4). Read-only.

    python tools/release_check.py

Scans every git-tracked file, and every file ever committed in history, for:
- video / footage files (the UFC footage rule)
- personal local paths (C:/Users/<name>, .venvs) and the owner's email
- things that look like secrets (Kaggle / API tokens, private keys)
- large files (> 5 MB)
- internal agent files that should move out or be cleaned before going public
Prints a list of findings; exit code 1 if anything blocks a public flip.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEO = re.compile(r"\.(mp4|webm|mkv|mov|avi|m4v)$", re.I)
LOCAL = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+\w+|\.venvs[\\/]|AppData[\\/]", re.I)
SECRET = re.compile(r"(KGAT_[A-Za-z0-9]{16,}|\"key\"\s*:\s*\"[0-9a-f]{32}\"|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,})")
EMAIL = re.compile(r"[\w.+-]+@gmail\.com", re.I)
INTERNAL = {"CLAUDE.md", "HUMAN_TASKS.md", "docs/BRIEF.md", "docs/DECISIONS.md", "docs/ALIGNMENT.md", "docs/OPERATIONS.md"}
TEXT = {".py", ".md", ".txt", ".csv", ".json", ".html", ".js", ".ipynb", ".yml", ".yaml", ".toml", ".cfg", ".ps1", ".sh", ".patch"}


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def main():
    block, warn = [], []
    files = git("ls-files").splitlines()
    for f in files:
        p = ROOT / f
        if VIDEO.search(f):
            block.append(f"video file tracked: {f}")
        if p.exists() and p.stat().st_size > 5e6:
            warn.append(f"large file ({p.stat().st_size / 1e6:.1f} MB): {f}")
        if f in INTERNAL:
            warn.append(f"internal file (move out or clean before public): {f}")
        if p.suffix.lower() in TEXT and p.exists():
            txt = p.read_text(encoding="utf-8", errors="replace")
            for rx, kind, lst in ((SECRET, "possible secret", block), (LOCAL, "local path", warn), (EMAIL, "email address", warn)):
                hits = {m.group(0) for m in rx.finditer(txt)}
                if hits:
                    lst.append(f"{kind} in {f}: {', '.join(sorted(hits)[:3])}")
    hist = {x for x in git("log", "--all", "--pretty=format:", "--name-only").splitlines() if x}
    for f in sorted(hist):
        if VIDEO.search(f):
            block.append(f"video file in git HISTORY (needs history rewrite): {f}")
    for s in git("log", "--all", "-p", "-G", SECRET.pattern, "--pretty=format:%h").splitlines():
        if SECRET.search(s):
            block.append(f"possible secret in git HISTORY: {s.strip()[:60]}")
    print(f"{len(files)} tracked files, {len(hist)} paths in history\n")
    for kind, lst in (("BLOCKS public release", block), ("Fix or decide before public", warn)):
        print(f"## {kind}: {len(lst)}")
        for x in lst:
            print("  -", x)
        print()
    sys.exit(1 if block else 0)


if __name__ == "__main__":
    main()
