"""Re-run the rejected MVP 0.1 finish-% math (tools/mvp/demo.py) on the labels and print what it showed.

    C:/Users/netan/.venvs/ufc-cv/Scripts/python -I research/model/diagnose_mvp01.py

Imports fit/finish_prob/state_at straight from tools/mvp/demo.py so the numbers are the real ones.
"""
import csv, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/mvp"))
import demo  # noqa: E402

rows = [r for r in csv.DictReader(open(ROOT / "phase3_labels/labels.csv", encoding="utf-8")) if "excluded_" not in r["notes"]]
FPS = 30.0


def replay(row):
    """Frame-by-frame: what MVP 0.1 drew for this attempt (shown = EMA of p x ramp)."""
    m = demo.fit([r for r in rows if r["fight_id"] != row["fight_id"]])
    dur = float(row["video_time_end"]) - float(row["video_time_start"])
    shown, out = 0.0, []
    for i in range(int(dur * FPS) + 1):
        el = i / FPS
        st = demo.state_at(row, el)
        p = demo.finish_prob(m, st) if el >= 2 else m["base"]
        ramp = 1 - math.exp(-el / max(m["tau"], 1))
        shown += (p * ramp - shown) * 0.15
        out.append((el, p, ramp, shown))
    return m, out


if __name__ == "__main__":
    for r in rows:
        if r["video_url"].startswith("pantoja_asakura"):
            m, out = replay(r)
            print("model fit without this fight:", {k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()})
            print(" t(s)  state-p  ramp  shown")
            for el, p, ramp, shown in out:
                if abs(el - round(el)) < 1e-6 or abs(el - 6.6) < .02:
                    print(f"{el:5.1f}  {p:6.3f}  {ramp:5.2f}  {shown:6.3f}")
            print("labeled end:", r["outcome"], f"at {float(r['video_time_end']) - float(r['video_time_start']):.1f}s; last shown {out[-1][3]:.3f}")
    print("\nlast value shown before the labeled end, every attempt:")
    for r in rows:
        m, out = replay(r)
        print(f"{r['attacker'][:18]:18s} {r['outcome']:15s} dur {out[-1][0]:5.1f}s  base {m['base']:.2f}  shown@2s {out[min(60, len(out)-1)][3]:.3f}  shown@end {out[-1][3]:.3f}")
