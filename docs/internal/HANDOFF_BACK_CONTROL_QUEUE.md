# Handoff: a proper back-control queue (written 2026-11-26)

Owner's words: the last session went poorly. Most clips are short; the useful ones are the **long back-control rounds**
(Aljamain Sterling "Aljo", many Brazilian fighters: Oliveira, Almeida, Barcelos, Moicano, Figueiredo, Pantoja). Build a queue of
proper long videos. Re-downloading is allowed (official sources only: the owner said "Official only" on 2026-11-22).

## Where things stand (labels.csv: rows / rows with a K mark = 119 9)
- The K key (back control began) is the missing ingredient for odds and timing. The owner is doing the K pass in the labeler.
- Owner-facing list: `phase3_labels/K_PASS_TODO.md` (rebuilt from labels.csv; videos in `data/clips/ALL_TO_LABEL`, hard links, names unchanged because the labeler matches videos to labels by file name). Loadable fight list: `phase3_labels/back_control_queue.csv`.
- Labeler keys for the K pass: N jump to next un-K'd attempt, K back control began, L reuse the last K moment in this video (long control, several attempts). No end mark exists or is needed. Speed: [ and ].
- 16 labeled videos are not on disk (incl. **Sterling-Sandhagen**, Pantoja-Kara-France, Maia-Askren, Figueiredo-Benavidez). Their attempts cannot get a K until a video is found. Almeida-Rozenstruik is "not a real fight video" (owner): skip.
- New clip with no labels: `oliveira_chandler.mp4` (UFC 262, 2021) in `to_label/` and ALL_TO_LABEL; it is in the fight list as entry 0.5.

## What went wrong (so the next session does not repeat it)
1. Per-fight YouTube searches by name: about 1 usable official video per 10 to 300 searches. Fetch reruns on 2026-11-24 searched about 290 fights and got 1 clip.
2. I took "Aljo" to mean Jailton Almeida; it means **Aljamain Sterling**. Ask or check nicknames before building priority lists.
3. A fetched video can be the wrong fight (Oliveira-Chandler: UFC's only uploads are the 2021 fight, not the 2024 rematch; one "UFC289" title was the 2021 fight). Always check a contact sheet of frames (ffmpeg `fps=1/70,tile`) and the scoreboard before labeling.
4. Most official uploads are 7 to 14 minute "FULL FIGHT" cuts (finishes, highlights) with the long control trimmed away. They are short, as the owner saw.
5. I wrote a queue file the labeler could not read (no fight_id column). The loader skips rows without fight_id. Always test with the real loader columns (queue_rank, fight_id, date, attacker, defender, round).
6. Moving files broke nothing, but renaming would: the labeler matches `video_url` in labels.csv to the exact file name.

## Findings from this session (data, 2026-11-26)
- `phase3_labels/labeling_queue_long.csv`: 225 rounds with 3 min or more of control; 208 still todo; 78 with 4 min or more.
- Of the 28 todo rounds by Aljo/Brazilian back-riders, 25 were already searched with **no official video** and none are left unsearched.
- Inverted search: I listed the first 6000 uploads of the official UFC channel (`data/drafts/ufc_channel_uploads.tsv`, git-ignored): 383 look like fight videos (4 to 53 min). Matched to the long queue by both surnames: only 4 hits, and none is a usable long round (Pantoja-Royval is only a "Fight Day Focus" show, Allen-Duncan is "Behind The Scenes", Vinicius Oliveira-Said Nurmagomedov is already downloaded, Hokit-Lewis is a 10-minute 2026 upload). Official YouTube does not carry most long-control rounds.
- Conclusion: the supply problem is the source, not the tool. yt-dlp is current (2026.10.26; update with `yt-dlp -U`; winget fails on this install).

## The queue
`phase3_labels/back_control_long_queue.csv`: 59 rounds (28 Aljo/Brazilian back-riders first, then rounds with 4:30+ of control by anyone), each with the official-video search status and a next step. It is a to-find list, not a to-watch list: almost every row needs a source.

## What to do next (in this order)
1. **Owner decision needed:** where may long rounds come from? Options: (a) UFC Fight Pass or any copy the owner legally has, saved by the owner into `data/clips/restored/` (the owner supplied the Holloway clip this way: `~/olivera_hoolowar_r1.mp4`); (b) keep official-only and accept a small set (about 40 videos on disk now); (c) fan uploads (the owner said no on 2026-11-22). Do not assume (c).
2. For anything the owner supplies: align to the labels. The labels are in the original upload's seconds, so a different upload may be offset. Use `tools/restore_shift.py` (CLIP fingerprints); check the scoreboard clock at two points (earlier Oliveira clips were 10 s off).
3. Priority videos to recover (they already have labeled attempts waiting for K): Sterling-Sandhagen (3 attempts), Pantoja-Kara-France (1), Figueiredo-Benavidez (4), Maia-Askren (2), Smith-Gustafsson (2), Anthony Smith-Spann, Allen-Silva (3), Sterling-others if any.
4. For long rounds with no labels yet (the new queue), the labeler "G" pass and the K pass apply: label every RNC attempt, then K.
5. Do not delete labeled clips until the owner finishes the K pass, then run `tools/cleanup_clips.py --delete` (it scans labeled/ and to_label/; keeps clips whose features and neck crops are not both saved).
6. Commit piece by piece; the repo is public: never push footage or personal paths.

## Not touched / still open
- Uncommitted: nothing important at handoff time except data/ (git-ignored).
- PREREG frozen. Round times on `clock_unreliable` rows are blank. Fatigue idea logged only.
- Almeida-Turkalj: first attempt (241.9 s) had no K at last check; the owner asked whether the earlier long control was unbroken.
