# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6480**
- Robustness score, lower is better: **37.1478**
- Overall position RMSE: **29.0571 m**
- Overall max position error: **58.1148 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.738081` → `1723528521.662569`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.4267 m, x=0.2383 m, y=0.3038 m, z=0.1818 m, yaw=0.4601 deg, dominant=yaw, samples=2272 | pos=0.4281 m, x=0.2374 m, y=0.3057 m, z=0.1828 m, yaw=0.4813 deg, dominant=yaw, samples=2272 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1157 m, x=0.0682 m, y=0.0893 m, z=0.0273 m, yaw=0.2561 deg, dominant=yaw, samples=160 | pos=0.1406 m, x=0.0903 m, y=0.1052 m, z=0.0232 m, yaw=0.2677 deg, dominant=yaw, samples=160 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2340 m, x=0.1056 m, y=0.2078 m, z=0.0196 m, yaw=0.8973 deg, dominant=yaw, samples=120 | pos=0.1490 m, x=0.0949 m, y=0.1123 m, z=0.0242 m, yaw=1.2404 deg, dominant=yaw, samples=120 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6131 m, x=0.5831 m, y=0.1581 m, z=0.1045 m, yaw=0.3094 deg, dominant=x, samples=264 | pos=0.5165 m, x=0.4982 m, y=0.0705 m, z=0.1167 m, yaw=0.3235 deg, dominant=x, samples=264 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1361 m, x=0.0936 m, y=0.0778 m, z=0.0608 m, yaw=0.2814 deg, dominant=yaw, samples=220 | pos=0.3058 m, x=0.1314 m, y=0.0870 m, z=0.2621 m, yaw=0.4153 deg, dominant=yaw, samples=220 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1652 m, x=0.1547 m, y=0.0499 m, z=0.0298 m, yaw=0.2000 deg, dominant=yaw, samples=148 | pos=0.4178 m, x=0.1697 m, y=0.1933 m, z=0.3292 m, yaw=0.3252 deg, dominant=z, yaw, samples=148 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.1785 m, x=0.1579 m, y=0.0821 m, z=0.0132 m, yaw=0.4831 deg, dominant=yaw, samples=102 | pos=0.4488 m, x=0.1447 m, y=0.2463 m, z=0.3462 m, yaw=0.4859 deg, dominant=yaw, samples=102 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2837 m, x=0.2101 m, y=0.1475 m, z=0.1208 m, yaw=0.3295 deg, dominant=yaw, samples=458 | pos=0.5302 m, x=0.1378 m, y=0.4495 m, z=0.2450 m, yaw=0.5041 deg, dominant=yaw, samples=458 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.1855 m, x=0.1282 m, y=0.1054 m, z=0.0828 m, yaw=0.2686 deg, dominant=yaw, samples=218 | pos=0.7102 m, x=0.3489 m, y=0.6154 m, z=0.0625 m, yaw=0.4557 deg, dominant=y, samples=218 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6783 m, x=0.5652 m, y=0.3617 m, z=0.0992 m, yaw=4.1383 deg, dominant=yaw, samples=356 | pos=0.9925 m, x=0.5263 m, y=0.8320 m, z=0.1260 m, yaw=3.8835 deg, dominant=yaw, samples=356 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2772 m, x=0.2720 m, y=0.0459 m, z=0.0272 m, yaw=1.0809 deg, dominant=yaw, samples=40 | pos=1.6392 m, x=0.1697 m, y=1.6227 m, z=0.1583 m, yaw=8.3344 deg, dominant=yaw, samples=40 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2858 m, x=1.7604 m, y=3.9073 m, z=0.0419 m, yaw=9.2278 deg, dominant=yaw, samples=436 | pos=5.6549 m, x=1.7959 m, y=5.3609 m, z=0.1202 m, yaw=3.6865 deg, dominant=y, samples=436 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8649 m, x=2.7384 m, y=0.8392 m, z=0.0659 m, yaw=20.7272 deg, dominant=yaw, samples=110 | pos=9.9313 m, x=6.4287 m, y=7.5693 m, z=0.0894 m, yaw=27.7363 deg, dominant=yaw, samples=110 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9079 m, x=7.1083 m, y=3.4620 m, z=0.1513 m, yaw=24.7284 deg, dominant=yaw, samples=330 | pos=16.2582 m, x=15.9029 m, y=3.3778 m, z=0.1291 m, yaw=15.8730 deg, dominant=x, yaw, samples=330 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9079 m and dominant component(s): yaw.

## Perturbation-window analysis

No perturbation windows configured for this case.

## Generated files

- **trajectory CSV:** `trajectory.csv`
- **error over time CSV:** `error_timeseries.csv`
- **segment metrics CSV:** `segment_metrics.csv`
- **perturbation window metrics CSV:** `perturbation_window_metrics.csv`
- **segment per-window error CSV directory:** `segment_error_timeseries`
- **trajectory XY plot:** `trajectory_xy.png`
- **error over time plot:** `error_over_time.png`
- **yaw error over time plot:** `yaw_error_over_time.png`
- **segment position RMSE bar graph:** `segment_position_rmse_bar.png`
- **segment component RMSE bar graph:** `segment_component_rmse_bar.png`
- **machine-readable metrics JSON:** `metrics.json`
