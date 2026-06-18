# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **37.0663**
- Overall position RMSE: **28.9343 m**
- Overall max position error: **58.0949 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521703` → `1723528521.644120`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.1699 m, x=0.3470 m, y=0.4762 m, z=1.0107 m, yaw=0.7674 deg, dominant=z, samples=2136 | pos=1.1698 m, x=0.3489 m, y=0.4740 m, z=1.0110 m, yaw=0.7696 deg, dominant=z, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2506 m, x=0.0371 m, y=0.0546 m, z=0.2418 m, yaw=0.6628 deg, dominant=yaw, samples=148 | pos=0.7328 m, x=0.2855 m, y=0.2369 m, z=0.6320 m, yaw=0.3515 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3449 m, x=0.1451 m, y=0.2434 m, z=0.1967 m, yaw=1.3717 deg, dominant=yaw, samples=118 | pos=1.2306 m, x=0.2720 m, y=0.3485 m, z=1.1484 m, yaw=2.3001 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9974 m, x=0.7346 m, y=0.1605 m, z=0.6554 m, yaw=0.3108 deg, dominant=x, samples=254 | pos=0.8034 m, x=0.5247 m, y=0.2950 m, z=0.5320 m, yaw=0.3953 deg, dominant=z, x, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3528 m, x=0.0551 m, y=0.1270 m, z=0.3245 m, yaw=0.1249 deg, dominant=z, samples=204 | pos=0.5858 m, x=0.0373 m, y=0.4167 m, z=0.4100 m, yaw=0.5397 deg, dominant=yaw, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.3064 m, x=0.1270 m, y=0.0289 m, z=0.2773 m, yaw=0.1492 deg, dominant=z, samples=144 | pos=1.0601 m, x=0.1182 m, y=0.5557 m, z=0.8950 m, yaw=0.2290 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2696 m, x=0.1940 m, y=0.0626 m, z=0.1764 m, yaw=0.5138 deg, dominant=yaw, samples=96 | pos=1.4116 m, x=0.1646 m, y=0.5549 m, z=1.2874 m, yaw=0.6133 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.3314 m, x=0.2655 m, y=0.0984 m, z=0.1723 m, yaw=0.4850 deg, dominant=yaw, samples=416 | pos=1.7215 m, x=0.2159 m, y=0.6808 m, z=1.5664 m, yaw=0.7604 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2756 m, x=0.1941 m, y=0.1024 m, z=0.1667 m, yaw=0.1152 deg, dominant=x, samples=206 | pos=1.7622 m, x=0.6351 m, y=0.7391 m, z=1.4682 m, yaw=0.7141 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9854 m, x=0.5813 m, y=0.4212 m, z=0.6751 m, yaw=4.6011 deg, dominant=yaw, samples=350 | pos=1.3931 m, x=0.7033 m, y=0.9386 m, z=0.7518 m, yaw=4.1640 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2952 m, x=0.2780 m, y=0.0518 m, z=0.0848 m, yaw=1.3926 deg, dominant=yaw, samples=38 | pos=1.8121 m, x=0.2795 m, y=1.7847 m, z=0.1438 m, yaw=8.3191 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5796 m, x=2.0780 m, y=4.0768 m, z=0.1853 m, yaw=9.7209 deg, dominant=yaw, samples=404 | pos=6.0115 m, x=1.8334 m, y=5.7235 m, z=0.1356 m, yaw=4.0665 deg, dominant=y, samples=404 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9698 m, x=2.8151 m, y=0.9090 m, z=0.2622 m, yaw=20.5628 deg, dominant=yaw, samples=104 | pos=10.3779 m, x=6.6876 m, y=7.9166 m, z=0.5523 m, yaw=28.7395 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9729 m, x=6.8932 m, y=3.8543 m, z=1.0933 m, yaw=24.3791 deg, dominant=yaw, samples=320 | pos=16.4285 m, x=15.9831 m, y=3.3139 m, z=1.8589 m, yaw=16.8231 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9729 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | motion_blur | camera_right/motion_blur | 1621218792.000000 → 1621218800.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | camera_frame_dropout | camera_right/frame_dropout | 1621218810.000000 → 1621218815.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
