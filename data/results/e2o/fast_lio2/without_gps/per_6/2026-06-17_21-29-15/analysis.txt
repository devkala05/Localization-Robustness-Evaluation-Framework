# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **37.0621**
- Overall position RMSE: **28.9293 m**
- Overall max position error: **58.2405 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521346` → `1723528521.647227`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.9604 m, x=0.3153 m, y=0.3413 m, z=0.8405 m, yaw=0.7489 deg, dominant=z, samples=2136 | pos=0.9605 m, x=0.3174 m, y=0.3390 m, z=0.8408 m, yaw=0.7498 deg, dominant=z, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2062 m, x=0.0339 m, y=0.0502 m, z=0.1971 m, yaw=0.6090 deg, dominant=yaw, samples=148 | pos=0.6411 m, x=0.2592 m, y=0.2229 m, z=0.5423 m, yaw=0.3448 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3409 m, x=0.1456 m, y=0.2419 m, z=0.1911 m, yaw=1.3750 deg, dominant=yaw, samples=118 | pos=1.1200 m, x=0.2431 m, y=0.3560 m, z=1.0337 m, yaw=2.4213 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9656 m, x=0.7263 m, y=0.1148 m, z=0.6258 m, yaw=0.3274 deg, dominant=x, samples=254 | pos=0.7453 m, x=0.5515 m, y=0.2455 m, z=0.4372 m, yaw=0.3383 deg, dominant=x, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3128 m, x=0.0434 m, y=0.0954 m, z=0.2948 m, yaw=0.1128 deg, dominant=z, samples=204 | pos=0.5381 m, x=0.0349 m, y=0.3213 m, z=0.4303 m, yaw=0.4587 deg, dominant=yaw, z, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2722 m, x=0.1227 m, y=0.0153 m, z=0.2426 m, yaw=0.1542 deg, dominant=z, samples=144 | pos=0.9858 m, x=0.1521 m, y=0.4189 m, z=0.8794 m, yaw=0.1630 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2435 m, x=0.1982 m, y=0.0494 m, z=0.1325 m, yaw=0.4850 deg, dominant=yaw, samples=96 | pos=1.2805 m, x=0.2023 m, y=0.3923 m, z=1.2020 m, yaw=0.6892 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2145 m, x=0.1892 m, y=0.0765 m, z=0.0661 m, yaw=0.4791 deg, dominant=yaw, samples=416 | pos=1.4254 m, x=0.1756 m, y=0.4627 m, z=1.3367 m, yaw=0.6312 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3323 m, x=0.1662 m, y=0.1116 m, z=0.2653 m, yaw=0.1113 deg, dominant=z, samples=206 | pos=1.2552 m, x=0.5203 m, y=0.4950 m, z=1.0294 m, yaw=0.5964 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.0667 m, x=0.5774 m, y=0.4416 m, z=0.7806 m, yaw=4.5471 deg, dominant=yaw, samples=350 | pos=1.0352 m, x=0.6106 m, y=0.7488 m, z=0.3715 m, yaw=4.1701 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.3091 m, x=0.2966 m, y=0.0585 m, z=0.0643 m, yaw=1.3769 deg, dominant=yaw, samples=38 | pos=1.6601 m, x=0.1591 m, y=1.5702 m, z=0.5151 m, yaw=8.3537 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5724 m, x=2.0631 m, y=4.0801 m, z=0.0579 m, yaw=9.7036 deg, dominant=yaw, samples=404 | pos=5.8688 m, x=1.9200 m, y=5.5202 m, z=0.5325 m, yaw=4.0479 deg, dominant=y, samples=404 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9690 m, x=2.8191 m, y=0.8980 m, z=0.2483 m, yaw=20.5761 deg, dominant=yaw, samples=104 | pos=10.3015 m, x=6.7929 m, y=7.6965 m, z=0.8601 m, yaw=28.6805 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9399 m, x=6.8510 m, y=3.8543 m, z=1.1185 m, yaw=24.3808 deg, dominant=yaw, samples=320 | pos=16.4961 m, x=16.0463 m, y=3.1421 m, z=2.1831 m, yaw=16.8034 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9399 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | lidar_off_window | lidar/sensor_off | 1621218790.000000 → 1621218895.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
