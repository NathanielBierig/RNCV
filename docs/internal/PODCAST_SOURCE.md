# RNCV: the pitch, in plain language (source for a NotebookLM audio overview)

Status date: 2026-10-25. Written for a sharp, non-technical listener. Everything below is true to the project as it stands today, including what doesn't work.

## 1. The one-sentence pitch

RNCV is a study of what actually makes a rear-naked choke finish in the UFC, plus a prototype that watches a fight and shows a live "chance this choke finishes" number on screen, the way a broadcast shows win probability in baseball.

Two products in one:
- **The science:** which visible details (where the choking arm sits, whether the second hand locks, whether the defender fights the arm with two hands, whether the legs are hooked in) separate chokes that end the fight from chokes that get escaped? Nobody has measured this properly on UFC footage. The study is pre-registered: the hypotheses and the analysis plan were written down and frozen before any results, so the findings can't be quietly massaged afterward.
- **The overlay:** a live graphic on the video: attempt detected, finish probability, and the main factors pushing it up or down.

The owner is a BJJ practitioner, which matters: the expert knowledge of what to look for comes from the mat, and the engineering is there to measure it at scale.

## 2. Why this is hard (the honest version)

A human who knows jiu-jitsu watches a clip and says "he's got the second hand locked, chin is tucked, that's getting finished." Teaching a computer to see the same thing means solving several separate problems, and each one is a place the project can stall:

1. **Seeing the bodies.** Turn video into a stick-figure skeleton for each fighter.
2. **Knowing who is who.** Two sweaty, tangled people, plus a referee, plus a crowd. Keep the right two skeletons and keep their identities straight.
3. **Knowing what position it is.** Back control? Mount? Half guard?
4. **Knowing a choke attempt has started.**
5. **Reading the details** that predict a finish.
6. **Turning all of it into a probability** that is honest, meaning that when it says 70%, about 7 in 10 of those situations really do finish.

And a seventh problem sits under all of them: **data**. The computer has to learn from examples, and examples of "UFC choke attempts, carefully labeled" don't exist. The owner has to create them by hand.

## 3. Basic computer-vision ideas, explained plainly

**A video is a stack of pictures.** At 30 frames per second, a 5-minute round is 9,000 images. Computers don't "watch"; they look at each picture, one after another.

**A pixel is a number.** An image is a grid of numbers describing color. The computer starts with nothing but those numbers and has to work out "that's a person."

**Pose estimation / keypoints.** A pose model looks at one picture and marks where each person's joints are: nose, shoulders, elbows, wrists, hips, knees, ankles. That's 17 points per person, called keypoints. Connect them and you get a stick figure. The model here is called RTMO and it runs on an ordinary laptop, no graphics card. This is attractive because the skeleton is a tiny summary of the picture: 34 numbers instead of millions of pixels.

**Confidence score.** Every detection comes with the model's own 0-to-1 belief that it's right. You choose a cutoff. Too high and you throw away real fighters who are tangled up and hard to see; too low and you keep junk. A key early finding in this project: the default cutoff of 0.7 was silently deleting the second fighter. Lowering it to 0.3 brought him back, along with the referee and the crowd.

**NMS (non-maximum suppression).** When a model finds overlapping detections, NMS deletes the weaker one, assuming it's a duplicate of the same person. That's great for a crowd and terrible for grappling, where two real people overlap by definition.

**Tracking.** Picking two skeletons in one frame isn't enough; you need the same two in the next frame, and to know which is which. The project matches skeletons between frames, and if a fighter vanishes for half a second it fills in from his last known pose and flags it as "filled."

**The referee problem.** The referee wears black and stands near the action. The filter first tried a "dark shirt" rule and it failed: it deleted fighters in shadow and dark-skinned fighters, and kept the referee. The better idea was to look at skin color, not brightness: fighters are shirtless, the referee is covered. That helped, and a later review found a bug (a black shirt is mostly "too dark to judge" pixels, so the referee was being judged on his bare forearm).

**Fine-tuning.** Take a model trained on general people and keep training it on grappling and MMA images so it gets good at tangled bodies. The project did this on a free GPU service, using only public datasets, never UFC footage, because UFC video can't be uploaded anywhere.

**An image "fingerprint" (embedding).** There are general-purpose models that turn any picture into a list of a few hundred numbers capturing what's in it. You never need to say what's in it. Similar pictures get similar fingerprints. The attempt detector uses this: no skeletons at all, just "does this frame's fingerprint look like the fingerprints of frames inside choke attempts?"

## 4. Basic machine-learning ideas, explained plainly

**A classifier** is a function that takes numbers in and gives a category out. Here: skeleton numbers in, "this is back control" out. It's not programmed with rules; it adjusts itself to match labeled examples.

**Training vs. testing.** You show the model labeled examples (training), then check it on examples it has never seen (testing). If you test it on things it already saw, you've measured memory, not skill. Most of the care in this project is about stopping that from sneaking in.

**Leakage: the way good-looking numbers lie.** The position dataset (VICOS) has 16 videos, but they are really 6 sparring sessions filmed from up to 3 phones at once. A random split would put the same moment, from camera A, in training and, from camera B, in the test. The model would look brilliant and be useless. So the project holds out whole stretches of time and removes a buffer around them. The same logic applies to fights: a fight is either entirely in test or entirely out, decided by a fixed hash of its ID so it never changes sides, and fighters who appear on both sides are purged too.

**Macro-F1.** A single accuracy number can flatter a model that just guesses the most common class. Macro-F1 scores each position separately (balancing "did you catch the real ones" against "did you cry wolf") and averages, so rare positions like half guard count as much as common ones. The position classifier scores 0.63 on that scale. Honest reading: good on the easy positions, weak on half guard, takedowns, and some top positions, and it was tested only on gym footage with the same athletes in train and test, so it says nothing yet about UFC.

**Swap augmentation / role-invariance.** The tracker labels fighters arbitrarily. If the model learned "athlete 1 is usually on top," it would break. So the training data includes every frame twice, with the two athletes swapped and labels flipped. This took macro-F1 from 0.46 to 0.63.

**ROC-AUC.** A score for "can the model rank true cases above false ones?" 0.5 is a coin flip, 1.0 is perfect. The attempt detector is at 0.70 on fighter crops (0.72 with smoothing). That's better than chance and nowhere near usable. The target is 0.80.

**Leave-one-fight-out.** To score a model on a fight, train it on all the other fights. Repeat for every fight. It's the most honest test available when you have few fights, but it makes every number noisy at this size.

**Calibration.** A probability is only worth showing if it's honest. "70%" should come true about 70% of the time. The final model is judged on exactly that, with uncertainty ranges calculated by resampling whole fights, not individual frames.

**Censoring.** If the bell rings with the choke still on, you don't know the outcome. That is not a failure; it's missing information, and it's excluded rather than counted wrong.

## 5. Basic coding principles, as they show up in this repo

- **Pipeline thinking.** Each script does one job and writes a file the next one reads. Video → pose file → fighter file → features → classifier → predictions → overlay. If something is wrong, you can open the file between two stages and see which stage broke it. This is why a recent review could pinpoint that skeletons were being mixed before selection even started.
- **Reproducibility.** Every random choice uses a fixed seed. Test-set membership is decided by a hash, not a coin flip, so it's identical every run. Anyone can rerun the number.
- **Tests that guard the rules.** The evaluation rules are written as code with 11 automated tests, so a future change can't quietly break "no leakage" or "bell is censored."
- **Separating data from code.** Raw UFC video never enters git, the cloud, Kaggle or social media. Only derived data (skeletons, timestamps, labels) is kept. That is a legal and ethical line, enforced by a rule file that every working session reads first.
- **Pre-registration as a coding principle.** The science plan is frozen at v1.0, and later changes are dated amendments (the latest, A4, changed a cap on attempts per fight from 3 to 5). You can see the history; nothing is edited silently.
- **Honest reporting built in.** Every report carries its caveats. A number that flatters is flagged as an upper bound.
- **Small tools that match the user.** The labeling tool is a single offline web page. No server, no install, the video never leaves the laptop.

## 6. What actually works today (and what doesn't)

**Works:**
- A position classifier at macro-F1 0.63 on gym footage. Not yet shown to work on UFC.
- A back-control detector made from plain geometry, no machine learning: both fighters facing the same way, close together, attacker's chest on defender's back, head next to the neck. About 78 to 83% recall and 85% precision on gym footage.
- The labeling tool. Real use so far: 36 labeled choke attempts across about 20 fights, a median of 1.4 minutes per attempt (the target was 4).
- The data pipeline from official fight stats to prioritized lists of fights to watch, with a leak test on the fighter-record features.
- The evaluation harness with tests.
- A replay demo (MVP 0.1) that renders the overlay on a labeled clip: a finish percentage for the attacker, a health bar for the defender, live state, and the final result.

**Does not work yet, and this is the important part:**
- **Skeleton tracking in real UFC choke footage.** A fresh-eye review checked 48 real frames by hand. The system reports "both fighters tracked" in 64 to 94% of frames, but both skeletons were actually the right two people in only 1 to 4 of 48. The common failure is one skeleton that stretches across both fighters, because in a tangled choke the detector never proposes a clean skeleton on the choker. Fixing the filtering doesn't help when the right answer was never proposed. The review's verdict was no-go for building the signal on current pose output.
- **The attempt detector** is at 0.70, not usable. It deliberately avoids skeletons.
- **The finish probability in the demo is a stand-in.** The attempt windows and factors in the demo come from the owner's hand labels, not from automatic detection. The percentage comes from a small model on other fights' labels, built so it can't peek at the clip's own outcome. It's a demonstration of the product's shape, not of working perception.
- **The science analysis** hasn't run, because 36 attempts aren't enough. The plan calls for about 150 attempts and a second rater on about 30 to check that two people label the same way.

## 7. The strategy and the bottleneck

The road to a first version, in the project's own roadmap:
1. Get the attempt detector to 0.80 (needs roughly 40 labeled fights, now 20, plus footage with more "nothing is happening" stretches).
2. Add one visible-factor detector, again with the image-fingerprint trick instead of skeletons.
3. Reach about 150 labeled attempts and run the frozen analysis plan, with a short write-up.
4. Fit a calibrated finish-probability model.
5. Wire it all into the renderer.

**The critical path is the owner's labeling time.** Each sitting is about 20 to 30 minutes. Most of the remaining engineering is a day or two of work each, but it all waits on labels.

Strategic point worth stressing: when skeletons failed, the project didn't keep tuning them. It changed approach, and put the pose track on hold (parked, to revisit with a different kind of pose model), while moving the work that doesn't depend on it. That's the main lesson of the project so far: **the review that said no-go saved weeks of building on a signal that wasn't there.**

## 8. Honest risks

- The labeled dataset is small, so every model number has wide error bars.
- Labeling is a one-person job (inter-rater agreement, measured as kappa, isn't established yet).
- Broadcast footage has camera cuts, cage close-ups and replays that confuse any vision system.
- UFC footage can't be shared or uploaded, so no cloud GPU can ever be used on it: everything runs on a laptop CPU.
- The science finding could turn out null: it's possible that the visible details don't predict finishes much beyond how long the choke has been on. That would still be a publishable, honest result, and the pre-registration makes it credible either way.

## 9. Instructions for the audio overview hosts

Tone: two smart people talking to an intelligent adult who is smart but not technical and who has no patience for fluff. No hype. No "revolutionary." No filler analogies that don't explain anything. Pitch it as a business case that is candid about weaknesses, like an investor update.

Structure:
1. Open with the product in two sentences and why it's interesting (a probability graphic for grappling, grounded in real measurement).
2. Walk the chain of problems (see, identify, classify, detect, read, estimate) and explain each computer-vision and machine-learning term the first time it is used, in one plain sentence with a concrete jiu-jitsu example (for instance: keypoints are the joints, confidence is the model's own certainty, leakage is testing a student on the exact roll he drilled).
3. Spend real time on leakage and honest evaluation; that is the heart of the project's credibility.
4. Give a frank scoreboard: what works, what doesn't. Make the pose-tracking failure (1 to 4 of 48 frames right, versus 64 to 94% "tracked") a centerpiece, with what it taught.
5. Close on strategy: the bottleneck is labeled data, the roadmap, and the one decision that matters next (keep labeling).

Keep it to roughly 15 to 20 minutes. Don't invent numbers; use only the ones in this document.
