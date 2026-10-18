# Decision: how far to take Phase 5 (prediction) and Phase 6 (overlay)

The time and accuracy figures here are **estimates**. Pick one option for each phase. My recommendation is in **bold**.

## Phase 5: how the finish probability is computed

| Option | What it is, in plain words | Extra effort | Risk | Portfolio value |
|---|---|---|---|---|
| **5-A: Factor model only** | One table: "chokes under the chin finish X× more often (95% range a–b)", computed from your hand labels at the 2-s mark. The overlay shows one fixed probability per attempt. | Lowest: ~1 day after labels are frozen | Low. The only risk is wide ranges, which is still an honest result | High for the **science story**; weak as a "live" demo |
| **5-B: Factor model + live hazard model** ⭐ | 5-A, plus a second model that updates every second: "given the grip and position *right now*, the chance of a tap in the next seconds". The same factors, refit on what the pose model detects. | +3–5 days | Medium. Depends on pose detecting the factors well (κ check). If it doesn't, fall back to 5-A. | **Highest**: science you can trust *and* a probability that moves on screen with reasons attached |
| 5-C: LightGBM (a black-box "boosted trees" model) | Throws many pose features into a flexible model to squeeze out accuracy | +2–4 days | High. With ~150 attempts it will likely overfit (learn noise), and its explanations are less trustworthy | Medium; it reads as a "Kaggle trick", not insight |

**Recommendation: 5-B.** It's the only option where the live number and the science result share a model, so the overlay's "▲ under chin" arrows mean the same as the published finding. Build 5-A first (it's a sub-step anyway). Treat 5-C only as a comparison row in the results table, and adopt it only if it clearly beats 5-B on the harness.

## Phase 6: how the overlay is shown

| Option | What it is | Extra effort | Risk | Portfolio value |
|---|---|---|---|---|
| **6-A: Offline renderer on recorded clips** ⭐ | Process a clip on the laptop and get an MP4 with the banner, the probability bar and the top factors. Already prototyped in `tools/overlay/`. | Lowest: ~1–2 days to wire to real model output | Low | High in interviews (shown privately; UFC frames can't be posted) |
| 6-B: Near-real-time (live) | Process video as it plays, a few seconds behind | +1–2 weeks | High. The laptop CPU runs pose at ~1–3 fps (est.), far below the 30 fps of video, so this needs a GPU you don't have | Impressive, but it adds no science, and it's hard to demo legally |
| **6-C: Skeleton-only public renders** ⭐ (add-on to 6-A) | The same overlay drawn over stick-figure skeletons on a blank background. No UFC pixels. | +1 day | Low. It's derived data, so it's postable (see FOOTAGE.md) | **High for public reach**: the only version you can put on GitHub, LinkedIn or Instagram |

**Recommendation: 6-A + 6-C.** Real-frame overlays are for private interviews; skeleton versions go public. Skip 6-B: it costs the most, is the most likely to fail on a CPU, and adds nothing to the core result.

## What you're deciding

| Phase 5 | Phase 6 | Effort after labels (est.) |
|---|---|---|
| 5-A only | 6-A | ~3 days |
| **5-B** | **6-A + 6-C** | **~1–1.5 weeks** |
| 5-B + 5-C comparison | 6-A + 6-C | ~2 weeks |
