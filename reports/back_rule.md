# Back control: geometry rule vs classifier (VICOS, time-block folds)

13219 back frames of 120279. Both athletes have a pose in 49% of back frames (the rule can't fire otherwise).

| Method | Back recall | Precision | F1 |
|---|---|---|---|
| Geometry rule, thresholds tuned on train blocks | 0.407 | 0.586 | 0.480 |
| Geometry rule, default thresholds (no tuning) | 0.330 | 0.683 | 0.445 |

Rule picks the right attacker in 84.3% of its correct back detections (back1 = pose1 is behind).

Caveat: every VICOS back frame comes from one session of one athlete pair, so none of these numbers show that back detection generalizes. The real test is hand-tagged UFC frames (critique #1a).
