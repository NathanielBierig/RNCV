"""Build the pilot report PDF: docs/paper/PILOT_REPORT.md -> docs/paper/RNCV_pilot_report.pdf

    python tools/build_report.py

Markdown -> styled HTML -> PDF with headless Chrome (no extra software). Figures are embedded.
"""
import base64
import re
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/paper/PILOT_REPORT.md"
OUT = ROOT / "docs/paper/RNCV_pilot_report.pdf"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ITEM = re.compile(r"\s*(- |\d+\. )")
CSS = """
@page { size: A4; margin: 20mm 19mm; }
body { font: 10.5pt/1.5 "Segoe UI", Arial, sans-serif; color: #1c2128; }
h1 { font-size: 23pt; line-height: 1.15; margin: 0 0 2pt; }
h3:first-of-type { font-weight: 400; color: #57606a; margin-top: 0; }
h2 { font-size: 14pt; margin: 18pt 0 5pt; border-bottom: 1px solid #d0d7de; padding-bottom: 3pt; }
h3 { font-size: 11.5pt; margin: 12pt 0 3pt; }
blockquote { background: #f6f3ec; border-left: 4px solid #d97706; margin: 10pt 0; padding: 6pt 12pt; }
ul, ol { margin: 4pt 0; padding-left: 18pt; }
table { border-collapse: collapse; width: 100%; font-size: 9.5pt; margin: 7pt 0; page-break-inside: avoid; }
th, td { border-bottom: 1px solid #d0d7de; text-align: left; padding: 3pt 6pt; }
th { background: #f6f8fa; }
img { max-width: 78%; display: block; margin: 8pt auto; }
hr { border: 0; border-top: 1px solid #d0d7de; margin: 12pt 0; }
a { color: #0b5cad; text-decoration: none; }
"""


def lists_ok(md):
    """python-markdown needs a blank line before a list and 4-space nesting; GitHub doesn't."""
    out, prev = [], ""
    for line in md.split("\n"):
        quoted = line.startswith(">")
        body = line[1:].lstrip(" ") if quoted else line
        indent = len(line[1:]) - len(line[1:].lstrip(" ")) if quoted else len(line) - len(line.lstrip(" "))
        nested = ITEM.match(body) and indent >= (3 if quoted else 2)
        prefix = "> " if quoted else ""
        prev_body = prev[1:].strip() if prev.startswith(">") else prev.strip()
        if ITEM.match(body) and prev_body and not ITEM.match(prev_body):
            out.append(prefix.rstrip())
        out.append(prefix + ("    " if nested else "") + body)
        prev = line
    return "\n".join(out)


def main():
    md = lists_ok(SRC.read_text(encoding="utf-8"))
    html = markdown.markdown(md, extensions=["tables", "sane_lists"])

    def embed(m):
        p = (SRC.parent / m.group(1)).resolve()
        return 'src="data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode() + '"'
    html = re.sub(r'src="([^"]+\.png)"', embed, html)
    html = re.sub(r'<a href="(?!http)[^"]*">(.*?)</a>', r"\1", html)      # repo links read as plain text in the PDF
    page = f'<!doctype html><html><head><meta charset="utf-8"><title>RNCV pilot report</title><style>{CSS}</style></head><body>{html}</body></html>'
    tmp = ROOT / "data/_report.html"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_text(page, encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT}", tmp.as_uri()],
                   check=True, capture_output=True, timeout=120)
    tmp.unlink()
    print("wrote", OUT, f"{OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
