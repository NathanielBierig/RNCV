# RNCV: what finishes a UFC rear-naked choke, and can a computer see it?

**Commentators say a choke is "in deep". This project measures it.** RNCV (RNC + computer vision) has two parts: a pre-registered study of 75 hand-labeled rear-naked choke attempts from 43 UFC fights, and an honest test of how much of that a computer can read from broadcast video on its own. No UFC footage is published: only labels, numbers and code.

<img src="docs/media/oliveira_gamrot_nopixels.gif" width="640" alt="Footage-free replay of Oliveira vs Gamrot: layered pose keypoints, neck reticle and the side tab">

*Oliveira vs Gamrot, drawn only from derived data. The detector (trained without this fight) flags the back attack, the finish chance climbs as the figure-four goes in, and Gamrot's HP drains to the tap.* **[Watch the 30-second reel](docs/media/rncv_reel.mp4)** · **[Read the pilot report (PDF)](docs/paper/RNCV_pilot_report.pdf)** · **[Try the model in your browser](docs/explorer/index.html)**

## In 30 seconds

- **What lines up with finishes:** the arm under the chin (59% finished vs 40% over the jaw), a better grip (figure-four 68%, wrist pull 44%, one arm 38%), a hidden choking hand (75% vs 46%) and a flattened defender (63% vs 48%).
- **Strongest lead:** each step up the grip ladder multiplied the odds by about ×2.1 (95% range 1.2–3.9). It was named after seeing the data, so it's now a fourth hypothesis tested only on new attempts.
- **The surprise:** strong leg control didn't help any single attempt finish.
- **A check against physiology:** finished chokes took a median 9.6 s on the neck; a published study of MMA choke-outs found 9.0 s.
- **Can a computer do it alone? Not yet.** It finds back attacks on full broadcasts and picks the attacker 96% of the time, but it can't see the choke start or read the arm and grip, and from video alone its odds are no better than guessing.
- **The honest part:** it's a pilot. The sample is small and tilted toward finishes, and the confirmatory test runs at ~150 attempts ([why 150](research/rnc_science/POWER_NOTE.md)).

| | Status |
|---|---|
| 🟢 Works | Hand-labeled dataset with blind coding and automated QA; pre-registration with dated amendments; finish model and HP meter; replay overlay; back-attack detector on full broadcasts; picking the attacker from public stats |
| 🟡 Partly | The finish model beats a base-rate guess slightly from one snapshot, and clearly when it follows the position; reading the defender's two-on-one from neck crops shows a first hint (κ 0.24, bar 0.4) |
| 🔴 Not yet | Spotting the second a choke starts; reading arm, grip and legs; odds and time to a finish from video alone; edited highlight reels |

## Results (honest numbers)

All model numbers are on fights left out of training.

| Piece | Result | What it means |
|---|---|---|
| Labeled data | 75 attempts from 43 men's UFC fights | Too few for the pre-registered test yet (~150) |
| Finish model v0.8 (expert priors + labels) | Brier 0.244 at 2 s vs 0.256 for guessing the average; 0.223 vs 0.256 as the position changes | Following the position adds real information; the 2-s snapshot alone is within noise |
| Attempt detector | Frame ROC-AUC ~0.75; overlaps 72 of 74 attempts; ~0.5 false alarms per minute | Finds the back-control position, not the moment the choke starts |
| Fully automatic pipeline | Attacker right 96%; odds Brier 0.258 vs 0.259; end-time error 23 s | No position labels: it can flag the attack but can't give useful odds yet ([details](reports/auto_demo.md)) |
| Reading details from video | Best κ 0.24 (two-on-one); arm, grip and legs near chance | Needs many more labeled fights ([details](reports/factor_pilot.md)) |
| HP meter | Only 8 of 40 finishes reached HP 0 | Fighters usually tap before going out; HP is a readable estimate, not a measurement ([details](reports/hp_check.md)) |

### The science so far

<img src="docs/media/effects.png" width="620" alt="Odds multipliers per choke factor in model v0.8">

Odds multipliers in model v0.8, which blends expert estimates with the labels. With the labels alone, every single-factor effect still has a range that includes "no effect"; the grip ladder is the one trend whose range excludes it. Full write-up: [pilot report](docs/paper/PILOT_REPORT.md) · [pre-registration](research/rnc_science/PREREG.md) · [code book](research/rnc_science/FACTORS.md) · [model spec](docs/MODEL_SPEC.md).

<img src="docs/media/calibration.png" width="380" align="right" alt="Calibration of the finish chance on held-out fights">

On fights it never saw, positions the model rated ~80% finished ~80% of the time. Lower down its numbers run too extreme (calibration slope 0.55, where 1.0 is perfect); a correction fixes the bins but not overall accuracy, so the raw numbers are kept and disclosed.

<br clear="right">

## How the readouts work

- **Finish chance (attacker):** given the position visible right now (arm, grip, legs, the defender's hand fight), what share of similar UFC attempts finished? It jumps when the grip locks and drops when the defender fights the hands. There's no time ramp, because finishes don't get steadily likelier with time: after the first 5 s the rate per 5-s block stays roughly flat ([details](reports/time_curve.md)).
- **HP (defender):** an estimate of blood flow left to the brain. It drains with squeeze strength, empties after ~9 s of a full squeeze, and refills between attempts. It's an average over fighters, so some fighters reach 0 and fight on.
- **Back attack detected:** the image-based detector, trained without the fight on screen.

<img src="docs/media/pantoja_asakura_panel.gif" width="315" align="right" alt="Readout panel replaying Pantoja vs Asakura">

**Example:** Pantoja vs Asakura, round 2, scored by models that never saw this fight. The finish chance sits near 26% while the arm is over the jaw, then jumps to ~89% when the figure-four locks under the chin. The boxes show what decides it (gold = very helpful, purple = helpful, blue = small, red = against). The readouts come from hand labels in replay; the computer can't read these positions yet.

<br clear="right">

## Try it

- **Model explorer:** open [docs/explorer/index.html](docs/explorer/index.html), set the arm, grip, legs and hand fight, and watch the finish chance and HP. No footage; runs in the page.
- **Detector app:** `python -I tools/app/serve.py` starts a local app: drop in a clip you have, and replay it with the detector's readouts ([how](tools/app/README.md)).
- **Labeler:** [tools/labeler/](tools/labeler/) is the browser tool used for every label: blind coding at a 2-s landmark, a position change log and keyboard-only flow.

## Repo map

| Folder | What's in it |
|---|---|
| [docs/paper/](docs/paper/) | Pilot report (markdown and PDF) |
| [research/rnc_science/](research/rnc_science/) | Pre-registration, code book, power analysis |
| [research/model/](research/model/) | Finish model, priors, validation and exploratory analyses |
| [research/attempt_clf/](research/attempt_clf/) | Attempt detector and detail-reading experiments |
| [phase3_labels/](phase3_labels/) | `labels.csv`, fight queues, schema, QA |
| [tools/](tools/) | Labeler, overlay demos, local app, clip fetching and checks |
| [src/](src/) | Pose, two-fighter tracking, referee filter |
| [reports/](reports/) | Every result as markdown ([older VICOS side experiment](reports/vicos_baseline/)) |
| [docs/](docs/) | [Roadmap](docs/ROADMAP.md), [model spec](docs/MODEL_SPEC.md), [how-tos](docs/OPERATIONS.md), [code tour](docs/CODE_TOUR.md); working notes in [docs/internal/](docs/internal/) |
| `data/`, `models/` | Local only (git-ignored): clips, datasets, weights |

## Setup

```bash
python -m venv .venv
python -m pip install -r requirements.txt
```
On Windows, put the venv at a short path if OpenCV DLLs fail to load. Three environments are used in practice: pose and training (`requirements.txt`), tools (OpenCV, pandas, Pillow), and image features (open_clip, torch CPU). Datasets and model downloads: [docs/DOWNLOADS.md](docs/DOWNLOADS.md).

## Footage and licenses

- **UFC footage** stays on one local laptop and is never uploaded, committed or shared; only derived data is published ([footage policy](docs/FOOTAGE.md)). Public fight statistics come from ufcstats.com via the Greco1899 scrape (GPL-3.0).
- **Third-party:** VICOS CC BY-NC-SA 4.0 (Hudovernik & Skočaj, MMSports'22), YOLO11 AGPL-3.0, RTMO/MMPose/rtmlib Apache-2.0 ([full table](docs/DOWNLOADS.md)).
- **This repo:** no license chosen yet, so all rights are reserved for now.
