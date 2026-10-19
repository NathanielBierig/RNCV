# Back control: geometry rule vs classifier (VICOS, time-block folds)

13219 back frames of 120279. Both athletes have a pose in 49% of back frames (the rule can't fire otherwise).

| Method | Back recall | Recall, both athletes visible | Precision | F1 |
|---|---|---|---|---|
| Geometry rule, thresholds tuned on train blocks | 0.407 | 0.827 | 0.586 | 0.480 |
| Geometry rule, default thresholds (no tuning) | 0.330 | 0.672 | 0.683 | 0.445 |
| Classifier `gbm` (18-class, back1|back2) | 0.648 | 0.699 | 0.732 | 0.687 |
| Classifier `gbm_rolinv` (18-class, back1|back2) | 0.771 | 0.906 | 0.823 | 0.796 |
| Classifier `gbm_swapaug` (18-class, back1|back2) | 0.783 | 0.918 | 0.846 | 0.813 |
| Classifier `mlp` (18-class, back1|back2) | 0.645 | 0.739 | 0.741 | 0.690 |
| Classifier `mlp_rolinv` (18-class, back1|back2) | 0.740 | 0.877 | 0.805 | 0.771 |
| Classifier `mlp_rolinv_swapaug` (18-class, back1|back2) | 0.738 | 0.874 | 0.808 | 0.771 |
| Classifier `mlp_swapaug` (18-class, back1|back2) | 0.741 | 0.885 | 0.784 | 0.762 |

Rule picks the right attacker in 84.3% of its correct back detections (back1 = pose1 is behind).

Caveat: every VICOS back frame comes from one session of one athlete pair, so none of these numbers show that back detection generalizes. The real test is hand-tagged UFC frames (critique #1a).
