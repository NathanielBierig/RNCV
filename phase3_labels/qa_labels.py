"""Read-only quality check for phase3_labels/labels.csv -> reports/labels_qa.md.

Never edits labels.csv (the labeler may have it linked). Flags, per row:
  - duplicate attempts (same fight, round, start)
  - overlapping attempts in the same fight + round
  - start >= end, or round times outside 0-300 s
  - finishes whose end is > 3 s from the ufcstats finish time
  - missing landmark fields (unless view_blocked)
  - missing found_via, out-of-scope fights (women's, before 2018), no "pilot" tag
Rows whose notes contain the token "compilation" come from a compilation video with
an unreliable on-screen clock: their round-time checks are skipped, and the analysis
treats their round-time fields (attempt_start_s, attempt_end_s, fight_time_s) as missing.

    C:/Users/netan/.venvs/ufc-cv/Scripts/python -I phase3_labels/qa_labels.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LANDMARK = ["choke_arm_position", "forearm_placement", "rnc_style_at_L", "choking_hand_tucked",
            "second_hand_on_traps", "squeeze_direction", "control", "defender_two_on_one",
            "chin_tucked", "opponent_flattened", "back_context", "attacker_side"]
SUCCESS = {"tap", "ref_stop", "unconscious"}
FINISH_TOL_S = 3.0


def load_fight_info():
    succ = pd.read_csv(ROOT / "phase3_labels/rnc_successes.csv", dtype=str, keep_default_na=False)
    cand = pd.read_csv(ROOT / "phase3_labels/failed_attempt_candidates.csv", dtype=str, keep_default_na=False)
    info = pd.concat([succ[["fight_id", "date", "weight_class"]], cand[["fight_id", "date", "weight_class"]]])
    info = info.drop_duplicates("fight_id").set_index("fight_id")
    finish = succ.set_index("fight_id")[["round", "finish_time_in_round_s"]]
    return info, finish


def check(df, info, finish):
    issues = []   # (row_number, severity, message)
    num = lambda c: pd.to_numeric(df[c], errors="coerce")
    df = df.assign(_s=num("attempt_start_s"), _e=num("attempt_end_s"), _r=num("round"),
                   _comp=df["notes"].str.contains(r"\bcompilation\b", case=False))
    for i, r in df.iterrows():
        n = i + 1   # 1-based data row, as shown in a spreadsheet below the header
        if r._s >= r._e:
            issues.append((n, "🔴", f"start {r._s} >= end {r._e}"))
        if pd.isna(r._s) or pd.isna(r._e):
            issues.append((n, "⚪", "round times blank (no clock sync and no finish anchor yet); durations from video times are still valid"))
        if not r._comp and (r._s < 0 or r._e > 300):
            issues.append((n, "🔴", f"round time {r._s}-{r._e} s is outside 0-300 s; if the source is a compilation, add `compilation` to notes"))
        if r.outcome in SUCCESS and r.fight_id in finish.index and not r._comp:
            fr, fs = finish.loc[r.fight_id]
            if str(fr) == str(r["round"]) and fs and abs(r._e - float(fs)) > FINISH_TOL_S:
                issues.append((n, "🟡", f"end {r._e} s is {r._e - float(fs):+.1f} s from the ufcstats finish ({fs} s); check the clock sync (C)"))
        if r.get("view_blocked", "") != "True":
            blank = [c for c in LANDMARK if not r.get(c, "")]
            if len(blank) == len(LANDMARK):
                issues.append((n, "🔴", "all landmark fields blank but view_blocked is not set"))
            elif blank:
                issues.append((n, "⚪", f"{len(blank)} landmark field(s) blank: {', '.join(blank)} (fine if not visible)"))
        if not r.get("found_via", ""):
            issues.append((n, "🔴", "found_via is missing (PREREG §2)"))
        if r.fight_id in info.index:
            wc, date = info.loc[r.fight_id, "weight_class"], info.loc[r.fight_id, "date"]
            if "women" in wc.lower():
                issues.append((n, "🔴", f"women's fight ({wc}): out of scope (PREREG A1)"))
            if date and date < "2018":
                issues.append((n, "🟡", f"fight date {date} is before 2018 (outside the study window)"))
        else:
            issues.append((n, "🟡", f"fight_id {r.fight_id} not found in the stats lists"))
        if "pilot" not in r.notes.lower():
            issues.append((n, "⚪", "no `pilot` tag in notes (first 15 attempts should have it)"))
    # duplicates and overlaps within fight + round
    for (fid, rnd), g in df.groupby(["fight_id", "round"]):
        g = g.sort_values("_s")
        for a in range(len(g)):
            for b in range(a + 1, len(g)):
                ra, rb = g.iloc[a], g.iloc[b]
                if ra._s == rb._s:
                    issues.append((rb.name + 1, "🔴", f"duplicate of row {ra.name + 1} (same fight, round, start)"))
                elif rb._s < ra._e:
                    issues.append((rb.name + 1, "🔴", f"overlaps row {ra.name + 1} ({ra._s}-{ra._e} s vs {rb._s}-{rb._e} s), "
                                   "same fight + round; keep one, or make them consecutive attempts"))
    return issues


def main():
    path = ROOT / "phase3_labels/labels.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    info, finish = load_fight_info()
    issues = check(df, info, finish)
    mins = df["notes"].str.extract(r"label_min=([\d.]+)")[0].astype(float)
    lines = ["# labels.csv quality check", "",
             f"Rows: **{len(df)}** · fights: **{df.fight_id.nunique()}** · outcomes: "
             + ", ".join(f"{k} {v}" for k, v in df.outcome.value_counts().items())
             + f" · found_via: " + ", ".join(f"{k or 'blank'} {v}" for k, v in df.found_via.value_counts().items()),
             f"Label time per attempt (minutes): median **{mins.median():.1f}**, total {mins.sum():.0f} (from `label_min` in notes)." if mins.notna().any() else "",
             "", "🔴 fix before analysis · 🟡 check · ⚪ info", ""]
    if not issues:
        lines.append("🟢 No issues found.")
    else:
        lines += ["| Row | | Issue |", "|---|---|---|"]
        lines += [f"| {n} ({df.iloc[n - 1].fight_id[:8]}, R{df.iloc[n - 1]['round']}, {df.iloc[n - 1].attempt_start_s}-{df.iloc[n - 1].attempt_end_s} s) | {sev} | {msg} |"
                  for n, sev, msg in sorted(issues)]
    lines += ["", "Row numbers count data rows from 1 (the header isn't counted). This script never edits labels.csv: fix rows in the labeler (U = undo last row) or ask Main.",
              "Compilation sources: put the word `compilation` in notes, so round-time checks are skipped and the analysis treats round times as missing."]
    out = ROOT / "reports/labels_qa.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}: {len(issues)} issue(s), {sum(s == '🔴' for _, s, _ in issues)} red")


if __name__ == "__main__":
    main()
