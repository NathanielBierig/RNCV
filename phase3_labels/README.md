# phase3_labels

Candidate lists for hand-labeling rear-naked-choke (RNC) attempts in UFC fights. Derived stats only; no video is downloaded or stored.

## Files

| file | what |
|---|---|
| `rnc_successes.csv` | Every UFC fight finished by "Submission (Rear Naked Choke)": attacker (winner), round, finish time, weight class, ufcstats URL. 677 rows |
| `failed_attempt_candidates.csv` | Fighter-rounds with `SUB.ATT > 0` where the round did **not** end in a submission. 3,330 rows in 2,351 fights. **Attempt type is unknown** (any submission counts), so video review decides whether an RNC happened |
| `LABEL_SCHEMA.md` | Labeling CSV schema, definitions, review priority |
| `build_candidates.py` | Rebuilds the CSVs and `summary_stats.json` from `raw_sources/` (`.venv/Scripts/python -I build_candidates.py`) |
| `raw_sources/` | Input snapshot (taken 2026-10-18) of the Greco1899 CSVs |
| `.venv/` | CPU-only venv (requests, beautifulsoup4, pandas). Not needed to run the build except pandas |

## Summary stats (snapshot 2026-10-18, UFC 1994 to Oct 2026)

- Fights in source: 8,962. Submission finishes: 1,733. **RNC finishes: 677** (39% of submissions); 659 plain, 18 labelled "Technical Submission" (`rnc_variant` column).
- Year range: **1994 to 2026**; 452 of them since 2015, around 35-45 a year since 2014.
- **Median finish round: 2** (R1 297, R2 245, R3 120, R4 11, R5 4). Median finish time in round: 2:57.
- **Estimated** attempts per finish: UFC-scored submission attempts in non-finishing rounds are 4,347 vs 1,733 submission finishes, i.e. about **2.5 failed attempts per submission finish** (any type). If RNC has the same share of attempts as of finishes this gives roughly 1,700 failed RNC attempts, about 2.5 per finish. *Estimate only:* ufcstats "sub att" is the scorer's judgment, includes every submission type, probably undercounts chokes that are quickly shrugged off, and RNC finishes are likely more common than RNC attempts among all attempts. Plan for far fewer real, labelable RNC attempts among the candidates (a rough guess is 1 in 3 candidate rows holds an RNC; unverified).
- Candidate rows from 2020 onward: 992. Rounds that ended in an RNC may also hold earlier failed attempts in the same round; those are not in the candidates file (not countable from stats).

## Sources and licenses

| source | use | license |
|---|---|---|
| [Greco1899/scrape_ufc_stats](https://github.com/Greco1899/scrape_ufc_stats) CSV snapshot (daily-refreshed scrape of ufcstats.com) | **Used** (event, fight results, per-round fight stats) | GPL-3.0 on the repository; the CSV data are facts scraped from ufcstats.com, which publishes no data license. Fine for private/portfolio use; keep the attribution and do not claim the data as your own. License copy: `raw_sources/LICENSE_Greco1899` |
| [Kaggle: neelagiriaditya/ufc-datasets-1994-2025](https://www.kaggle.com/datasets/neelagiriaditya/ufc-datasets-1994-2025) (fight.csv, round.csv) | Checked, not used; better-licensed backup (needs a Kaggle login to download) | CC0 |
| [Kaggle: rajeevw/ufcdata](https://www.kaggle.com/datasets/rajeevw/ufcdata) | Not used (stops in 2021, no per-round attempts by round) | unlisted in the page, not verified |
| ufcstats.com directly | Not scraped (not needed) | no license published; robots/ToS not reviewed |

No scraping was done by this folder, so there is no `cache/`. If you scrape, keep to 1 request/s and cache HTML there.

Data quirks: ufcstats has no per-round data for some older fights (42 empty rows dropped), and older UFC events may be missing sub counts. Stats are from ufcstats, not video.
