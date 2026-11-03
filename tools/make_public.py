"""Export a clean public copy of the repo (for the pilot release). Nothing here publishes anything.

    python tools/make_public.py <target folder>

Copies only git-tracked files, minus the internal ones below, into a NEW folder, then scans the copy for video
files, secrets, local paths and email addresses, and prints what it found. The private repo is untouched. A public
repo created from this folder starts with a fresh git history, so no internal notes or old commits go public.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INTERNAL = {"CLAUDE.md", "docs/internal/HUMAN_TASKS.md", "docs/internal/PROGRESS.md"}
INTERNAL_PREFIX = ("docs/internal/",
                   "docs/PLAN", "research/critique/", "research/venture/", "phase3_labels/pilot_15_RETIRED",
                   "phase3_labels/NEXT_SESSION", "tools/make_public.py")
VIDEO = re.compile(r"^(?!docs/media/rncv_reel\.mp4$).*\.(mp4|webm|mkv|mov|avi|m4v)$", re.I)   # the reel has no broadcast pixels
LOCAL = re.compile(r"[A-Za-z]:[\\/]+Users[\\/]+\w+|\.venvs[\\/]|AppData[\\/]", re.I)
SECRET = re.compile(r"KGAT_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9_-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,}")
EMAIL = re.compile(r"[\w.+-]+@gmail\.com", re.I)
TEXT = {".py", ".md", ".txt", ".csv", ".json", ".html", ".js", ".ipynb", ".yml", ".yaml", ".toml", ".cfg", ".ps1", ".sh", ".patch"}


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: python tools/make_public.py <target folder>")
    dst = Path(sys.argv[1]).resolve()
    if dst.exists() and any(dst.iterdir()):
        raise SystemExit(f"{dst} is not empty; choose a new folder")
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    keep = [f for f in files if f not in INTERNAL and not f.startswith(INTERNAL_PREFIX)]
    for f in keep:
        (dst / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / f, dst / f)
    print(f"copied {len(keep)} of {len(files)} tracked files to {dst}\n")
    issues = []
    for f in keep:
        p = dst / f
        if VIDEO.search(f):
            issues.append(f"VIDEO: {f}")
        if p.suffix.lower() in TEXT:
            txt = p.read_text(encoding="utf-8", errors="replace")
            for rx, kind in ((SECRET, "SECRET"), (LOCAL, "local path"), (EMAIL, "email")):
                hits = sorted({m.group(0) for m in rx.finditer(txt)})
                if hits:
                    issues.append(f"{kind} in {f}: {', '.join(hits[:2])}")
    links = re.findall(r"\]\(([^)#]+\.(?:md|html|csv|txt|py))", (dst / "README.md").read_text(encoding="utf-8"))
    for lk in sorted(set(links)):
        if not lk.startswith("http") and not (dst / lk).exists():
            issues.append(f"README link to a file not in the public copy: {lk}")
    print(f"{len(issues)} issue(s):")
    for x in issues:
        print(" -", x)


if __name__ == "__main__":
    main()
