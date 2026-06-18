# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6466**
- Robustness score, lower is better: **37.0311**
- Overall position RMSE: **28.9273 m**
- Overall max position error: **58.0800 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.734534` → `1723528521.661696`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.4829 m, x=0.2625 m, y=0.3690 m, z=0.1677 m, yaw=0.4939 deg, dominant=yaw, samples=2276 | pos=0.4843 m, x=0.2616 m, y=0.3710 m, z=0.1687 m, yaw=0.5241 deg, dominant=yaw, samples=2276 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1191 m, x=0.0720 m, y=0.0920 m, z=0.0234 m, yaw=0.3213 deg, dominant=yaw, samples=162 | pos=0.1441 m, x=0.0874 m, y=0.1120 m, z=0.0246 m, yaw=0.3433 deg, dominant=yaw, samples=162 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2123 m, x=0.0901 m, y=0.1908 m, z=0.0239 m, yaw=0.9239 deg, dominant=yaw, samples=118 | pos=0.1505 m, x=0.1009 m, y=0.1078 m, z=0.0292 m, yaw=1.2529 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6140 m, x=0.5860 m, y=0.1582 m, z=0.0926 m, yaw=0.3811 deg, dominant=x, samples=270 | pos=0.5174 m, x=0.5005 m, y=0.0733 m, z=0.1090 m, yaw=0.3852 deg, dominant=x, samples=270 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1365 m, x=0.0934 m, y=0.0855 m, z=0.0508 m, yaw=0.2836 deg, dominant=yaw, samples=220 | pos=0.3026 m, x=0.1405 m, y=0.1087 m, z=0.2450 m, yaw=0.4510 deg, dominant=yaw, samples=220 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1628 m, x=0.1486 m, y=0.0613 m, z=0.0258 m, yaw=0.2492 deg, dominant=yaw, samples=156 | pos=0.4179 m, x=0.1609 m, y=0.2353 m, z=0.3056 m, yaw=0.3681 deg, dominant=yaw, samples=156 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.1847 m, x=0.1595 m, y=0.0921 m, z=0.0139 m, yaw=0.4107 deg, dominant=yaw, samples=100 | pos=0.4678 m, x=0.1375 m, y=0.3164 m, z=0.3160 m, yaw=0.4074 deg, dominant=yaw, samples=100 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.3419 m, x=0.2810 m, y=0.1655 m, z=0.1028 m, yaw=0.2560 deg, dominant=x, yaw, samples=452 | pos=0.6220 m, x=0.1600 m, y=0.5585 m, z=0.2221 m, yaw=0.5786 deg, dominant=yaw, y, samples=452 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.1943 m, x=0.1504 m, y=0.1079 m, z=0.0591 m, yaw=0.1617 deg, dominant=yaw, x, samples=214 | pos=0.8615 m, x=0.4280 m, y=0.7443 m, z=0.0706 m, yaw=0.5749 deg, dominant=y, samples=214 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6543 m, x=0.5571 m, y=0.3420 m, z=0.0281 m, yaw=4.1883 deg, dominant=yaw, samples=354 | pos=1.0642 m, x=0.5812 m, y=0.8913 m, z=0.0142 m, yaw=3.8827 deg, dominant=yaw, samples=354 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2753 m, x=0.2702 m, y=0.0420 m, z=0.0312 m, yaw=1.0885 deg, dominant=yaw, samples=40 | pos=1.6649 m, x=0.1034 m, y=1.6614 m, z=0.0274 m, yaw=8.2027 deg, dominant=yaw, samples=40 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2998 m, x=1.7958 m, y=3.9067 m, z=0.0334 m, yaw=9.2185 deg, dominant=yaw, samples=432 | pos=5.6776 m, x=1.7441 m, y=5.4030 m, z=0.0286 m, yaw=3.7164 deg, dominant=y, samples=432 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8672 m, x=2.7397 m, y=0.8435 m, z=0.0586 m, yaw=20.6952 deg, dominant=yaw, samples=112 | pos=9.9367 m, x=6.3916 m, y=7.6082 m, z=0.0434 m, yaw=27.7871 deg, dominant=yaw, samples=112 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9105 m, x=7.1163 m, y=3.4492 m, z=0.1920 m, yaw=24.7572 deg, dominant=yaw, samples=330 | pos=16.2308 m, x=15.8720 m, y=3.3916 m, z=0.1256 m, yaw=15.8462 deg, dominant=x, yaw, samples=330 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9105 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | lidar_point_dropout_turn | lidar/point_dropout | 1621218790.000000 → 1621218795.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | lidar_rain_noise | lidar/rain | 1621218805.000000 → 1621218810.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
