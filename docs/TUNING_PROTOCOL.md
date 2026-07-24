# Leak-free tuning protocol

This repository uses chronological, non-overlapping windows for parameter
development.  Ground truth from a holdout window must not be inspected until
the algorithm configuration has been frozen after validation.

| Dataset | Tuning window | Validation window | Holdout window |
| --- | ---: | ---: | ---: |
| UrbanLoco `ca_20190828184706` | 0--60 s | 60--120 s | 180 s--end |
| Boreas `boreas_2024_12_04_14_44` | 0--45 s | 45--90 s | 120 s--end |

The 120--180 s UrbanLoco and 90--120 s Boreas intervals are guard bands. They
are not used for choosing parameters.

## Rules

1. Tune algorithm parameters only on the tuning window.
2. Select among tuning candidates before running the validation window.
3. A validation regression returns the algorithm to tuning; validation is not
   treated as another parameter sweep.
4. Freeze the selected configuration before opening the holdout result.
5. Use SE(3) alignment for metric lidar-inertial and visual-inertial modes.
   Sim(3) is permitted only for a genuinely scale-unobservable monocular mode.
6. Never derive calibration, time offsets, trajectory corrections, or wrapper
   re-anchoring from reference poses. Ground truth is used only by evaluation.
7. Preserve failed and rejected runs; do not replace measured metrics with
   placeholders or hand-edited trajectories.

Validation and holdout runs replay the sensor prefix from sequence start so
stateful estimators receive a realistic warm-up. The evaluator excludes that
prefix and scores only `--start-offset` through `--duration`; it does not use
warm-up ground truth in the reported metric.

Example:

```bash
./run_benchmark.sh --dataset urbanloco --sequence ca_20190828184706 \
  --algorithm rtabmap --rate 0.5 --start-offset 0 --duration 60 --phase tuning
./run_benchmark.sh --dataset urbanloco --sequence ca_20190828184706 \
  --algorithm rtabmap --rate 0.5 --start-offset 60 --duration 60 --phase validation
```

Historical full-sequence runs predate this protocol, so the final segments are
not pristine in the strict experimental sense for this repository state. The
split still prevents any new optimization pass from using holdout ground truth,
and future sequences should be split before their first evaluation.
