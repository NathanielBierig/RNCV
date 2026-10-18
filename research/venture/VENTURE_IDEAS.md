# Venture ideas: the entrepreneur's pass

> Written 2026-10-18 by the venture session. It only adds to `docs/DIRECTIONS.md` and `docs/PLAN.md`; nothing there is changed.
> All scores are **judgement calls**. All market numbers are from the linked pages and were not independently checked. No one was contacted, no account was made, nothing was paid for.

## The reframe in one paragraph

DIRECTIONS.md rates profit low because it assumes **UFC footage** and **VICOS data**. Both assumptions are optional. The *technology* in PLAN.md (pose → back-control → choke detection → finish/danger probability → overlay) runs on any grappling video. And plenty of grappling video is **owned by people who would want this built on it**: grappling promotions that stream free (CJI on YouTube, [100k+ concurrent viewers in 2024](https://en.wikipedia.org/wiki/Craig_Jones_Invitational)), local tournament organisers, gyms, instructional creators, and sports-medicine researchers. So the move is to **keep the UFC set for private research and the public benchmark (labels only)**, and point the product at footage someone can legally hand you. The second blind spot is **safety**. A system that times a choke and flags a limp defender is something referees, commissions and ringside doctors care about, and in our searches nobody seems to have built it from video.

---

## Table 1: all ideas (20)

Scores 1–5. Profit = realistic money for a solo learner within 1–2 years. Effort 5 = hardest. Portfolio = value to a CV/ML hiring manager.

| # | Idea | Who pays | Data path | Profit | Effort | Portfolio | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **Submission Danger Meter for grappling promotions**: a live or VOD overlay on events the promotion owns | Promotion (license / sponsor slot) | Promotion's own footage | 2 | 3 | 5 | **Shortlist** |
| 2 | **Choke-safety analytics**: time-to-lock, time-to-tap, limp-onset flag, for referees, commissions and researchers | Grants, research collaborations, later commissions/promotions | Labels-only from public footage (research); promoter footage | 2 | 4 | 5 | **Shortlist** |
| 3 | **Tournament auto-highlights**: every submission at a local BJJ event auto-clipped; competitors and parents buy their clips | Organiser (rev share), competitors | Organiser films its own mats | 3 | 3 | 3 | **Shortlist** |
| 4 | **"Veo for BJJ" open-mat auto-clipper**: a phone on a tripod, auto-splits rolls, tags taps and positions | Gym monthly fee | Gym films its own members, with consent | 3 | 4 | 4 | **Shortlist** |
| 5 | **Instructional auto-indexing**: chapters and position tags for instructional sellers | Instructional creators / sellers | Creator's own footage | 3 | 2 | 3 | **Shortlist** |
| 6 | In-play submission-risk data feed for sportsbooks | Sportsbooks / data suppliers | Needs official promotion data rights | 2* | 5 | 4 | Reject for now (see below) |
| 7 | Fantasy/DFS MMA "grappling danger" stats newsletter | Subscribers / sponsors | Stats are facts; no clips | 1 | 2 | 2 | Content side-effect of #2 |
| 8 | Broadcast graphics module sold to small production houses | Production vendor | Their client's footage | 2 | 4 | 4 | Merge into #1 (it's the delivery channel) |
| 9 | Judo osaekomi (pin) timer + shime-waza (choke) flag for referee support | Federations, clubs | Club footage | 2 | 4 | 4 | Good transfer test, later |
| 10 | Wrestling near-fall / back-exposure counter | HS/college coaches | Team film | 2 | 4 | 3 | Crowded ([Wrestle AI](https://apps.apple.com/us/app/6751189075), [Mat Coach](https://apps.apple.com/app/id6759972415)) |
| 11 | Sambo / combat-sambo submission danger | Federations | Federation footage | 1 | 4 | 3 | Too small |
| 12 | Police defensive-tactics training analytics (control quality, time-to-control) | Police academies | Academy training-room footage | 2 | 5 | 3 | Reject: slow procurement, high scrutiny, sensitive |
| 13 | Women's self-defence course progress analytics | Studios | Own footage | 1 | 4 | 2 | Reject |
| 14 | Labels-only benchmark + MMSports paper (already Direction D) | Nobody directly; it's a career asset | Facts/timestamps only | 1 | 3 | 5 | Keep: the backbone of #1 and #2 |
| 15 | Grappling labeling-as-a-service (tag positions and submissions for analytics firms) | Analytics / betting-data firms | Client's footage | 2 | 2 | 2 | Fallback freelance income |
| 16 | Developer API: two-person grappling pose + position classifier | Devs building BJJ apps | Needs own commercial training data | 1 | 4 | 4 | Crowded app layer; [Piranha Vision](https://claudemarketplaces.com/mcp/io.github.albermm/piranha-vision) already exists as an open MCP |
| 17 | Creator tool for BJJ breakdown YouTubers (danger bar on their own match footage) | Creators | Creator's own matches | 1 | 3 | 3 | Fold into #5 |
| 18 | Referee-training quiz from "danger" clips (when to stop a choke) | Ref seminars ($40–60 each, e.g. [Claudio França seminar](https://www.bjjheroes.com/bjj-news/bjj-referee-course)) | Consented / promoter clips | 1 | 2 | 3 | Fold into #2 |
| 19 | Scouting reports on BJJ competitors from public match video | Competitors / coaches | Grey (others' footage) | 2 | 3 | 2 | Reject: rights + privacy of amateurs |
| 20 | "Hire me" funnel: target SWA, Sportradar, Jabbr with the benchmark | Employer (salary) | n/a | **3** | 1 | n/a | Not a venture, but the most likely money; do it anyway |

\*Betting looks like the only big pool of money, but a solo learner can't reach it (see "Why not betting").

## Table 2: the shortlist

| Rank | Idea | Profit | Effort | Portfolio | Reuses PLAN | First $ milestone | Biggest risk |
|---|---|---|---|---|---|---|---|
| 1 | Submission Danger Meter for grappling promotions | 2 | 3 | **5** | Phases 2–6 almost 1:1 | One promotion pays (or sponsors) one event overlay, ~$200–1,000 (est.) | No promotion says yes; it stays a demo |
| 2 | Choke-safety analytics (time-to-lock, limp flag) | 2 | 4 | **5** | Phases 3–5 + new "limp" label | Co-authored paper / small grant; paid commission pilot is years out | Safety-critical errors; needs a medical co-author for credibility |
| 3 | Tournament auto-highlights | **3** | 3 | 3 | Phase 4 detector + Phase 6 renderer | First local event: clips sold at $5–15 each (est.), rev share | Organisers' filming is poor; one-man ops work at weekends |
| 4 | "Veo for BJJ" open-mat clipper | **3** | 4 | 4 | Phases 2, 4, 6 on consented gym video | 3 gyms at $20–40/month (est.) | Crowded consumer BJJ-AI apps; churn |
| 5 | Instructional auto-indexing | **3** | 2 | 3 | Phase 2 position model + scene cuts | One creator pays $50–150 to have a course chaptered (est.) | LLM/VLM tools (e.g. Gemini-based [RollPlan](https://rollplan.ai/)) do "good enough" tagging cheaply |

**Top 3 overall: #1, #2, #3.** #1 and #2 share one codebase and one dataset with the existing PLAN. #3 is the fastest honest path to actual dollars.

---

## Market signals found (with links)

| Signal | Why it matters | Source |
|---|---|---|
| CJI streamed free on YouTube; 100k+ concurrent viewers in 2024; CJI 2 (Aug 2025) free on FloGrappling's YouTube | Submission-only grappling has a big free-streaming audience and owners who control the footage | [Wikipedia](https://en.wikipedia.org/wiki/Craig_Jones_Invitational), [FloSports release](https://www.flosports.tv/2025/08/29/flosports-to-exclusively-stream-the-craig-jones-invitational-2-cji-2-for-free-on-flograppling-august-30-31) |
| Polaris has put full events / prelims on its own YouTube; main cards on UFC Fight Pass | A mid-size promotion with its own footage and a YouTube channel. Current deal **not verified** | [Bloody Elbow 2015](https://bloodyelbow.com/2015/10/18/watch-polaris-pro-invitational-1-full-replay), [MMA Sucka, Polaris 21](https://mmasucka.com/2022/09/24/polaris-21-results/) |
| Brave CF streams full events free on YouTube and runs its own Brave TV | An MMA promotion that owns and freely distributes footage; a possible partner for a VOD overlay | [Brave 4 (Wikipedia)](https://en.wikipedia.org/wiki/Brave_4:_Unstoppable), [Brave CF on Black Belt Mag](https://www.blackbeltmag.com/post/watch-brave-cf-87-live-for-free-on-black-belt-magazine-kubanychbek-defends-title-against-tutarauli) |
| SWA + Sportradar launched an "industry first" in-play MMA model on official UFC and PFL data, and called MMA "the most complex sport to model in-play" | Money and demand exist for live MMA probabilities. It also shows the data rights are already locked up by incumbents, and it's a hiring target | [Intergame](https://www.intergameonline.com/igaming/news/swa-sportradar-combine-to-launch-in-play-mma-betting-model), [G3](https://g3newswire.com/swa-partners-with-sportradar-in-play-mma-betting-product/), [Sportradar–PFL](https://www.intergameonline.com/igaming/news/sportradar-signs-betting-data-and-streaming-deal-with-pfl) |
| A physician panel hand-timed 81 MMA choke-outs (mean ~9 s to unconsciousness); the same author reviewed every UFC choke finish (904) | Sports medicine already does this work **by hand from fight video**. Automating it is a real research contribution and a natural collaboration | [Combat Sports Law summary](https://combatsportslaw.com/2020/06/17/study-locked-in-chokes-take-9-seconds-to-full-unconsciousness/), [UFC choke review](https://combatsportslaw.com/2020/12/26/physician-reviews-and-analyzes-all-choke-submissions-in-ufc-history/), [2025 safety-profile study](https://combatsportslaw.com/2025/04/11/study-strangulation-in-mma-has-an-acceptable-safety-profile/) |
| Documented referee misses: fighters left unconscious in chokes (e.g. Fury FC 76) | A concrete, emotive safety problem that commissions and promoters get blamed for | [Low Kick MMA](https://www.lowkickmma.com/video-referee-botches-fighter-choke/), [The Comeback](https://amp.thecomeback.com/mma/referee-misses-unconscious-fighter-leading-to-injury.html) |
| Searches found no video-based "unconscious in a choke" detector | White space (absence of evidence, not proof) | Two searches this session |
| BJJ-AI study apps are multiplying: GrappleX (launched 2026, footage source not stated), BJJ OS (claims 6,000+ indexed instructionals), RollPlan (Gemini-based) | The consumer app layer is crowded and cheap; don't compete there head-on | [GrappleX](https://www.producthunt.com/products/grapplex), [BJJ OS](https://apps.apple.com/ec/app/id6757207452), [RollPlan](https://rollplan.ai/) |
| BJJ Fanatics pays instructors 50% revenue share; thousands of sellers own their footage | A B2B customer base that owns its video and earns from discoverability | [BJJ Fanatics overview](https://usecart.com/store/bjjfanatics.com) |
| Police BJJ programmes report big drops in injuries (Marietta: −48% officer injuries, self-reported; St. Paul: −37% use of force) | A real adjacent market, but self-reported data and heavy scrutiny; buyers are slow | [Marshall Project](https://www.themarshallproject.org/2021/10/22/police-say-jiu-jitsu-can-make-them-less-violent-during-arrests), [Sheriffs' white paper](https://sheriffs.org/sites/default/files/Grappling%20White%20paper%20updated.pdf) |
| Judo: video analysis is manual tagging (JudoData for British Judo); AI camera tracking was tested at IJF events | Federations pay for analysis; pose-based automation isn't visible yet | [British Judo × JudoData](https://www.britishjudo.org.uk/?p=417906), [Judo Inside](https://judo-inside.com/news/2636/Judo_analytics_starting_to_get_traction_at_Federations_and_clubs) |
| MMSports 2026 runs at ACM MM, Rio, 10 Nov 2026 (2027 is the realistic target) | Venue for the benchmark paper | [ACM MM 2026 programme](https://2026.acmmm.org/site/technical-programme.html) |

Couldn't confirm: Smoothcomp pricing or API, current Polaris/ADCC streaming deals, FloGrappling data licensing.

---

## Shortlist in detail

### 1. Submission Danger Meter for grappling promotions

**Pitch.** Grappling events are long, slow-looking to casual viewers, and a submission can be "close" for 20 seconds without the audience knowing. A live "danger meter" (how deep is the choke, how likely is the tap) turns a stalemate into a countdown, the way win-probability graphics did for other sports. Submission-only rules make this *easier* than MMA: no striking, fewer camera cuts, and every match is ground work. Start with VOD (post-event highlight packages with the meter burned in). Live comes later.

- **Customer / who pays.** Mid-size grappling and regional MMA promotions that stream their own events (Polaris-, CJI-, Brave-type, plus smaller local pro shows). They pay a per-event fee, or a sponsor pays for a branded graphic ("Danger Meter presented by X"). Small broadcast production vendors (idea #8) are the channel for reaching several promotions at once.
- **Legal data path.** The promotion grants a written licence to use its own event video for model training and for the overlay. The UFC-derived model stays private and research-only; the commercial model is fine-tuned on the promotion's footage plus consented gym footage. No VICOS (NC) weights in the commercial model: retrain Phase 2 on own labels.
- **$0 MVP by one learner.** The existing `tools/overlay` + Phase 4 rule baseline ("back control > 3 s + wrist near neck") on **your own consented gym rolls**, rendered with the probability bar. Then a 60–90 s sizzle reel. For the pitch, show it privately on one of the promotion's *own* free YouTube matches (show only, don't post). Kaggle GPU covers pose.
- **First-$ milestone.** One promotion pays $200–1,000 (est.) or swaps a sponsor slot for a highlight package from one event.
- **Moat.** The labeled attempt-outcome dataset (nobody has one), the leak-free evaluation story, and being first with an always-the-same graphic a promotion's audience learns to read. Honestly a thin moat: a funded firm (SWA, Jabbr) could copy it if the market proved out.
- **Biggest risk.** Promotions have tiny budgets and many asks. The likely result is "cool, do it for free". Pose on tangled no-gi bodies may fail (that's the Phase 2b gate).
- **Scores.** Profit 2 · Effort 3 · Portfolio 5.

### 2. Choke-safety analytics (referee assist and research tool)

**Pitch.** Sports-medicine researchers already sit and hand-time choke-outs frame by frame from fight video. A tool that outputs *lock time, tap/stop time, and the first frame the defender's limbs go limp* automates their method, scales it from 81 cases to all of them, and opens the question regulators actually care about: **how long after unconsciousness did the referee stop it?** Later, the same signal becomes a ringside "check the fighter" alert for referees and commission doctors at events the promotion owns.

- **Customer / who pays.** Short term: nobody pays cash. The value is a co-authored paper with a sports-medicine group and possibly small research grants through a university partner. Medium term: athletic commissions, promotions (liability), and referee-training bodies ("did the ref stop it in time" review packages, folding in idea #18).
- **Legal data path.** Research: **labels only** (timestamps of lock, limp, stop) on publicly viewable fights, the same model as PLAN Phase 3. Your schema already has `SUCCESS_UNCONSCIOUS` and a limp-frame rule. Product: promotion-owned footage under licence.
- **$0 MVP by one learner.** (a) Add 3 columns to the Phase 3 labels: `lock_s`, `limp_s`, `stop_s`. (b) A "limpness" score from pose: wrist/arm keypoint velocity collapsing while the head drops, during an RNC segment. (c) A table: ref reaction time after limp onset, across the 677 UFC RNC finishes you already have candidates for (`phase3_labels/rnc_successes.csv`). Even 40 hand-labeled choke-outs replicate and extend a published study.
- **First-$ milestone.** Not dollars at first. The milestone is an accepted workshop paper or a researcher agreeing to co-author. Real dollars (commission or promotion pilot) are 1–2 years away, if ever.
- **Moat.** Credibility: a medical co-author plus a public, rigorous benchmark. Hard to copy fast.
- **Biggest risk.** It's **safety-critical**. A missed limp is harmful; frame it as post-hoc review and research, never as a replacement for the referee. Pose often fails exactly when the bodies are most entangled. Making claims about referees' performance can upset people, so word findings carefully.
- **Scores.** Profit 2 · Effort 4 · Portfolio 5.

### 3. Tournament auto-highlights (local BJJ events)

**Pitch.** Local BJJ tournaments run 4–12 mats all day, and every competitor (and every parent of a kid competitor) wants the clip of their submission. Organisers rarely deliver one. Put a phone or cheap camera on each mat, run the detector after the event, and auto-cut every submission (and every "near submission") into a 20 s vertical clip with the danger bar. Sell clips or a "your day" package, revenue-shared with the organiser.

- **Customer / who pays.** Competitors and parents pay per clip ($5–15 est.) or per package; organisers get a rev share and a marketing asset. Event-photography businesses are the pricing comparable.
- **Legal data path.** The organiser films its own mats and includes a video/media consent clause in registration (most events already have a media release; check per event). Minors need extra care: parent consent, no public posting without opt-in.
- **$0 MVP by one learner.** Gym in-house tournament or open-mat "mock comp", 1 phone, one mat. Pipeline = scene/match splitting + Phase 4 detector (start with "tap" detection: a sudden stop and separation after back or submission control) + `tools/overlay` render → a folder of clips. A Google Drive link is the "store" for the first test.
- **First-$ milestone.** One local event: ≥ 20 clips sold, or the organiser pays a flat fee ($100–300 est.).
- **Moat.** Low technically; it's an ops business. The moat is organiser relationships, plus detection accuracy so that nobody has to scrub 10 hours of mat video.
- **Biggest risk.** Weekend ops work, bad camera angles, minors' privacy, and the risk that Smoothcomp/Flo bundle it themselves.
- **Scores.** Profit 3 · Effort 3 · Portfolio 3.

### 4. "Veo for BJJ": open-mat auto-clipper for gyms

**Pitch.** Football clubs pay for AI cameras that film and auto-cut matches. Gyms have no equivalent: open mat is 90 minutes of untagged footage nobody watches. A phone on a tripod plus overnight processing gives each member their rolls, their taps given and received, and time in each position. The gym pays monthly and members get the clips.

- **Customer / who pays.** Gym owner (monthly fee); possibly members via an add-on.
- **Legal data path.** Gym films its own members with a written opt-in; members can opt out. This is also the **clean commercial training set** to replace VICOS.
- **$0 MVP by one learner.** Your own gym, one phone, one week of open mats, processed on Kaggle. Output: a shared folder per member. Same pipeline as #3.
- **First-$ milestone.** 3 gyms paying $20–40/month (est.).
- **Moat.** Accuracy on submissions (the incumbents' weak spot, per DIRECTIONS.md) and a dataset of consented rolls that grows with every gym.
- **Biggest risk.** A crowded consumer BJJ-AI market (Ground CTRL, KAYYO, RollPlan, GrappleX), cheap VLM-based rivals, privacy and consent at scale, multi-pair tracking on a busy mat (much harder than 2 people on camera).
- **Scores.** Profit 3 · Effort 4 · Portfolio 4.

### 5. Instructional auto-indexing for creators

**Pitch.** Instructional sellers upload 4–8 hour courses with weak chapters. Auto-chapter by position and technique ("0:42:10 back take from turtle → RNC finish"), output a searchable index and short promo clips. The creator owns the footage and gets more sales from better discoverability.

- **Customer / who pays.** Instructional creators (per-course fee), later marketplaces.
- **Legal data path.** The creator's own footage, under a simple processing permission.
- **$0 MVP by one learner.** Phase 2 position classifier + PySceneDetect + a small vocabulary of submissions → a chapter list. Demo on a free instructional you recorded yourself or one you have permission to use.
- **First-$ milestone.** One creator pays $50–150 (est.) for a chaptered course.
- **Moat.** Weak. Generic video-LLMs already do "good enough" tagging. Your edge would be grappling-specific accuracy, which you'd have to prove.
- **Biggest risk.** Commoditised by VLMs within a year.
- **Scores.** Profit 3 · Effort 2 · Portfolio 3.

---

## Why not betting (idea #6), honestly

It's the only market here with large, proven spend (SWA–Sportradar, PFL official data deals). But:
1. **Data rights are taken.** In-play products run on *official* promotion data under exclusive deals ([Stifel on data suppliers](https://www.legalsportsreport.com/?p=252042)). An unofficial video-derived feed would be unlicensed, and latency on scraped streams makes it useless for pricing anyway.
2. **Regulation.** Selling data to US sportsbooks generally means state vendor or supplier registration, plus integrity scrutiny. That's not a solo learner's job.
3. **Ethics.** Monetising "probability he goes unconscious" for gamblers sits badly next to idea #2's safety mission, and could hurt the credibility of the safety work.
**Use it as a career target instead:** SWA and Sportradar's MMA teams are exactly the employers a finish-probability benchmark speaks to (idea #20).

---

## What to build first, this month (reuses PLAN)

The good news: **nothing in PLAN.md needs to be thrown away.** Ideas #1–#4 all run on the same pipeline. The changes are about *which footage* and *two extra label columns*.

| Week | Do this | PLAN link | Why it helps the venture |
|---|---|---|---|
| 1 | Finish Phase 2 as planned (VICOS baseline). **In parallel, film 3–5 consented rolls at your own gym** (one phone, side-on, both athletes signing a one-line consent) | Phase 2 | Starts the commercially clean dataset that replaces VICOS |
| 2 | Run the Phase 2b smoke test on **three footage types**: 2 UFC clips (private), 2 free submission-only grappling matches watched via their official YouTube (private, show-only), your 3 gym rolls | Phase 2b | Answers the real question: does pose survive no-gi tangles? If it works on gym and grappling video, the venture paths open |
| 3 | Add `lock_s`, `limp_s`, `stop_s` to `phase3_labels/LABEL_SCHEMA.md` (ask the label owner; I don't own that file). Label the first 15 RNC *finishes* from `rnc_successes.csv` with those columns | Phase 3 pilot | Cheap. It's the seed of idea #2, and it replicates a published method |
| 4 | Render the existing `tools/overlay` "danger bar" (Phase 4 rule baseline, no ML yet) on your **own gym rolls**. Cut a 60 s reel | Phase 6 early | The one asset you can show publicly: it's the pitch for #1, #3 and #4 and the CV demo |

**The single first move:** this week, film 3–5 consented rolls at your own gym and add them to the Phase 2b smoke test. One afternoon tells you if the commercial path is real, and it gives you the only footage you can ever show publicly.

**Decision gate at the end of the month.** If ≥ 60% of back-control frames are usable on gym/grappling footage → pursue #1 (promotion pitch) using the reel, and keep #2 as the research track. If not → the venture paths wait on the Phase 2b fallbacks; keep the benchmark (D) as the main asset.

---

## USER_ACTIONS (drafts only; nothing has been sent)

You decide whether and when to send any of these. Fill in the blanks; check each recipient's current contact page yourself.

1. **Gym consent (do first, in person or on paper).**
   > "I'm building a student computer-vision project that analyses grappling from video. Can I film a few of our rolls from the side of the mat? The video stays private on my machine; I'd only ever show a short clip publicly if you say yes separately. You can withdraw at any time. Sign here if OK: ______"

2. **Grappling promotion (after the reel exists; e.g. a mid-size promotion with its own YouTube channel).**
   > Subject: A "submission danger meter" for your broadcasts — free pilot
   > "Hi [name], I train BJJ and build computer-vision models. I've built an overlay that reads the athletes' body positions and shows, live, how close a choke is to finishing (60-second demo on my gym footage: [link]). I'd like to run it on one of your past events, at no cost, to produce a highlight package you can post. All I'd need is written permission to process that event's video. Would you be open to a 15-minute call?"

3. **Sports-medicine researcher (after ~15 labeled finishes; e.g. the author of the 2020 time-to-unconsciousness study).**
   > Subject: Automating the timing in your sportive-choke study
   > "Dr [name], your 2020 study timed 81 MMA choke-outs by hand. I'm building an open pose-based pipeline that outputs choke lock time and the first frame of limpness, and I've labeled [N] RNC finishes with your definitions. Would you be interested in checking my labels against yours, or advising on a short workshop paper? Labels and code would be public; no video would be redistributed."

4. **Local tournament organiser (after a gym "mock comp" test).**
   > "Hi [name], I can auto-cut every submission from your mats into short clips the next day. For your next event I'd like to try one mat for free, filmed under your existing media release, and send you the clips. If competitors like them we can talk about selling them, with a revenue split. Interested?"

5. **Employers (after the benchmark is public).** A short note to the MMA data teams at SWA, Sportradar and Jabbr, linking the repo, the leak-free evaluation results, and the reel.

## Sources

Every link in the tables above was found during this session (2026-10-18). Also: [Stellpflug et al. 2020 citation summary](https://combatsportslaw.com/2020/06/17/study-locked-in-chokes-take-9-seconds-to-full-unconsciousness/), [IBJJF referee path](https://help.ibjjf.com/rules/), [DraftKings MMA scoring (old)](https://www.rotowire.com/mma/article.php?id=54707), [Dunwoody PD report](https://www.dunwoodyga.gov/home/showpublisheddocument/3961/638884233608070000), [JAB AI](https://apps.apple.com/app/id6751054115).
