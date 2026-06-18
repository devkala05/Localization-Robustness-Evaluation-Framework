# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6482**
- Robustness score, lower is better: **37.2868**
- Overall position RMSE: **29.1627 m**
- Overall max position error: **58.4417 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.735389` → `1723528521.661438`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=3.2558 m, x=0.2737 m, y=0.3452 m, z=3.2258 m, yaw=0.5031 deg, dominant=z, samples=2276 | pos=3.2569 m, x=0.2721 m, y=0.3473 m, z=3.2269 m, yaw=0.5245 deg, dominant=z, samples=2276 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1373 m, x=0.0937 m, y=0.0969 m, z=0.0262 m, yaw=0.2840 deg, dominant=yaw, samples=164 | pos=0.1304 m, x=0.0920 m, y=0.0885 m, z=0.0264 m, yaw=0.2532 deg, dominant=yaw, samples=164 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2288 m, x=0.1102 m, y=0.1997 m, z=0.0178 m, yaw=0.9537 deg, dominant=yaw, samples=122 | pos=0.1381 m, x=0.0782 m, y=0.1099 m, z=0.0296 m, yaw=1.4121 deg, dominant=yaw, samples=122 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6113 m, x=0.5663 m, y=0.1414 m, z=0.1817 m, yaw=0.3058 deg, dominant=x, samples=266 | pos=0.5384 m, x=0.5011 m, y=0.0634 m, z=0.1863 m, yaw=0.2878 deg, dominant=x, samples=266 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=1.4904 m, x=0.2548 m, y=0.0953 m, z=1.4653 m, yaw=0.3869 deg, dominant=z, samples=220 | pos=0.9630 m, x=0.2135 m, y=0.1115 m, z=0.9324 m, yaw=0.5723 deg, dominant=z, samples=220 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=1.0296 m, x=0.1271 m, y=0.0644 m, z=1.0197 m, yaw=0.3029 deg, dominant=z, samples=152 | pos=2.7628 m, x=0.1602 m, y=0.2502 m, z=2.7468 m, yaw=0.3858 deg, dominant=z, samples=152 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.5540 m, x=0.1563 m, y=0.0827 m, z=0.5250 m, yaw=0.5396 deg, dominant=yaw, z, samples=102 | pos=4.0803 m, x=0.1854 m, y=0.3121 m, z=4.0641 m, yaw=0.5601 deg, dominant=z, samples=102 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8499 m, x=0.1935 m, y=0.1491 m, z=0.8140 m, yaw=0.2536 deg, dominant=z, samples=452 | pos=5.1956 m, x=0.1760 m, y=0.5291 m, z=5.1656 m, yaw=0.4714 deg, dominant=z, samples=452 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2430 m, x=0.1466 m, y=0.1079 m, z=0.1610 m, yaw=0.2007 deg, dominant=yaw, samples=218 | pos=5.5424 m, x=0.4377 m, y=0.6751 m, z=5.4837 m, yaw=0.5559 deg, dominant=z, samples=218 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.5897 m, x=0.5181 m, y=0.3500 m, z=1.4615 m, yaw=4.3279 deg, dominant=yaw, samples=360 | pos=4.1465 m, x=0.5996 m, y=0.8440 m, z=4.0152 m, yaw=4.0107 deg, dominant=z, yaw, samples=360 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2813 m, x=0.2710 m, y=0.0453 m, z=0.0605 m, yaw=1.0461 deg, dominant=yaw, samples=38 | pos=3.1296 m, x=0.1602 m, y=1.6180 m, z=2.6740 m, yaw=8.1541 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.3022 m, x=1.7808 m, y=3.8916 m, z=0.4393 m, yaw=9.3101 deg, dominant=yaw, samples=436 | pos=6.0697 m, x=1.6280 m, y=5.3587 m, z=2.3398 m, yaw=3.6969 deg, dominant=y, samples=436 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8235 m, x=2.6707 m, y=0.8423 m, z=0.3611 m, yaw=20.5348 deg, dominant=yaw, samples=106 | pos=9.8122 m, x=6.1096 m, y=7.5558 m, z=1.3647 m, yaw=27.6531 deg, dominant=yaw, samples=106 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=8.0347 m, x=7.0255 m, y=3.3769 m, z=1.9483 m, yaw=24.4486 deg, dominant=yaw, samples=334 | pos=15.8852 m, x=15.4852 m, y=3.3499 m, z=1.1527 m, yaw=16.1306 deg, dominant=yaw, x, samples=334 |

**Most affected segment:** `straight_road` with relative position RMSE 8.0347 m and dominant component(s): yaw.

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
