# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **36.9837**
- Overall position RMSE: **28.8630 m**
- Overall max position error: **58.1710 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521210` → `1723528521.646914`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.1275 m, x=0.3562 m, y=0.4120 m, z=0.9872 m, yaw=0.7706 deg, dominant=z, samples=2136 | pos=1.1276 m, x=0.3584 m, y=0.4097 m, z=0.9875 m, yaw=0.7725 deg, dominant=z, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2446 m, x=0.0373 m, y=0.0525 m, z=0.2360 m, yaw=0.6291 deg, dominant=yaw, samples=148 | pos=0.7082 m, x=0.2818 m, y=0.2301 m, z=0.6076 m, yaw=0.3504 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3547 m, x=0.1474 m, y=0.2541 m, z=0.1988 m, yaw=1.3630 deg, dominant=yaw, samples=118 | pos=1.2176 m, x=0.2692 m, y=0.3571 m, z=1.1325 m, yaw=2.3681 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9994 m, x=0.7416 m, y=0.1228 m, z=0.6586 m, yaw=0.3277 deg, dominant=x, samples=254 | pos=0.7859 m, x=0.5342 m, y=0.2658 m, z=0.5115 m, yaw=0.3532 deg, dominant=x, z, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3466 m, x=0.0584 m, y=0.1121 m, z=0.3228 m, yaw=0.1244 deg, dominant=z, samples=204 | pos=0.5455 m, x=0.0257 m, y=0.3537 m, z=0.4145 m, yaw=0.4977 deg, dominant=yaw, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2886 m, x=0.1275 m, y=0.0130 m, z=0.2586 m, yaw=0.1525 deg, dominant=z, samples=144 | pos=1.0093 m, x=0.1358 m, y=0.4673 m, z=0.8842 m, yaw=0.1935 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2527 m, x=0.1906 m, y=0.0585 m, z=0.1553 m, yaw=0.4643 deg, dominant=yaw, samples=96 | pos=1.3439 m, x=0.1878 m, y=0.4676 m, z=1.2459 m, yaw=0.5943 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.3353 m, x=0.2479 m, y=0.0981 m, z=0.2033 m, yaw=0.4823 deg, dominant=yaw, samples=416 | pos=1.6546 m, x=0.2329 m, y=0.5860 m, z=1.5297 m, yaw=0.7395 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2763 m, x=0.1930 m, y=0.1120 m, z=0.1629 m, yaw=0.1028 deg, dominant=x, samples=206 | pos=1.7023 m, x=0.6538 m, y=0.6366 m, z=1.4371 m, yaw=0.7277 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9790 m, x=0.5754 m, y=0.4066 m, z=0.6797 m, yaw=4.5681 deg, dominant=yaw, samples=350 | pos=1.3171 m, x=0.7299 m, y=0.8286 m, z=0.7179 m, yaw=4.1043 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.3205 m, x=0.3048 m, y=0.0646 m, z=0.0748 m, yaw=1.3524 deg, dominant=yaw, samples=38 | pos=1.6728 m, x=0.3096 m, y=1.6406 m, z=0.1047 m, yaw=8.2139 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5761 m, x=2.1315 m, y=4.0488 m, z=0.0710 m, yaw=9.7510 deg, dominant=yaw, samples=404 | pos=5.8635 m, x=1.8699 m, y=5.5569 m, z=0.0755 m, yaw=4.1268 deg, dominant=y, samples=404 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9862 m, x=2.8343 m, y=0.9081 m, z=0.2442 m, yaw=20.5956 deg, dominant=yaw, samples=104 | pos=10.2614 m, x=6.7682 m, y=7.7045 m, z=0.3590 m, yaw=28.8886 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9993 m, x=6.8846 m, y=3.9318 m, z=1.0638 m, yaw=24.4421 deg, dominant=yaw, samples=320 | pos=16.4451 m, x=16.0680 m, y=3.0993 m, z=1.6293 m, yaw=16.9582 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9993 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | imu_gaussian_noise | imu/gaussian_noise | 1621218788.000000 → 1621218794.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | imu_message_dropout | imu/dropout | 1621218812.000000 → 1621218817.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
