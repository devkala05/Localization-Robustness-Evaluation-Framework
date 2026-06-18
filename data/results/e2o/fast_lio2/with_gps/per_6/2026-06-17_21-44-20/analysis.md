# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **36.8927**
- Overall position RMSE: **28.7798 m**
- Overall max position error: **58.1110 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521479` → `1723528521.593704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7662 m, x=0.3409 m, y=0.4989 m, z=0.4711 m, yaw=0.6097 deg, dominant=yaw, samples=1068 | pos=0.7656 m, x=0.3423 m, y=0.4968 m, z=0.4712 m, yaw=0.6166 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1570 m, x=0.0801 m, y=0.0925 m, z=0.0984 m, yaw=0.1780 deg, dominant=yaw, samples=74 | pos=0.3562 m, x=0.1971 m, y=0.1069 m, z=0.2768 m, yaw=0.3212 deg, dominant=yaw, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1629 m, x=0.0550 m, y=0.1111 m, z=0.1057 m, yaw=0.8196 deg, dominant=yaw, samples=59 | pos=0.6095 m, x=0.3271 m, y=0.1911 m, z=0.4774 m, yaw=1.0657 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6118 m, x=0.5821 m, y=0.1117 m, z=0.1516 m, yaw=0.3471 deg, dominant=x, samples=127 | pos=0.5710 m, x=0.4063 m, y=0.2381 m, z=0.3228 m, yaw=0.3395 deg, dominant=x, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3936 m, x=0.3003 m, y=0.0575 m, z=0.2479 m, yaw=0.1537 deg, dominant=x, samples=102 | pos=0.4045 m, x=0.2350 m, y=0.3060 m, z=0.1214 m, yaw=0.4543 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1969 m, x=0.1572 m, y=0.0846 m, z=0.0830 m, yaw=0.2034 deg, dominant=yaw, samples=73 | pos=0.5207 m, x=0.1873 m, y=0.4794 m, z=0.0792 m, yaw=0.5165 deg, dominant=yaw, y, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2190 m, x=0.1777 m, y=0.1273 m, z=0.0137 m, yaw=0.5969 deg, dominant=yaw, samples=47 | pos=0.6275 m, x=0.1759 m, y=0.5840 m, z=0.1477 m, yaw=0.5922 deg, dominant=yaw, y, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7113 m, x=0.3379 m, y=0.1238 m, z=0.6136 m, yaw=0.1205 deg, dominant=z, samples=209 | pos=0.9739 m, x=0.2153 m, y=0.7939 m, z=0.5214 m, yaw=0.8335 deg, dominant=yaw, y, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2894 m, x=0.2055 m, y=0.1699 m, z=0.1124 m, yaw=0.2130 deg, dominant=yaw, x, samples=103 | pos=1.4349 m, x=0.6721 m, y=0.8112 m, z=0.9742 m, yaw=0.9035 deg, dominant=z, yaw, samples=103 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6748 m, x=0.5725 m, y=0.3442 m, z=0.0962 m, yaw=4.3347 deg, dominant=yaw, samples=174 | pos=1.5486 m, x=0.8044 m, y=0.8624 m, z=1.0036 m, yaw=3.8553 deg, dominant=yaw, samples=174 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2774 m, x=0.2632 m, y=0.0862 m, z=0.0150 m, yaw=1.0258 deg, dominant=yaw, samples=19 | pos=1.8230 m, x=0.3683 m, y=1.5808 m, z=0.8300 m, yaw=7.6774 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5236 m, x=2.1146 m, y=3.9926 m, z=0.2249 m, yaw=9.0555 deg, dominant=yaw, samples=202 | pos=5.7651 m, x=1.8028 m, y=5.4361 m, z=0.6600 m, yaw=3.9979 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9140 m, x=2.7972 m, y=0.8107 m, z=0.0978 m, yaw=20.6536 deg, dominant=yaw, samples=52 | pos=10.0968 m, x=6.5897 m, y=7.6432 m, z=0.3191 m, yaw=28.2939 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9453 m, x=6.9346 m, y=3.8765 m, z=0.1129 m, yaw=24.0573 deg, dominant=yaw, samples=160 | pos=16.1781 m, x=15.8770 m, y=3.1031 m, z=0.1591 m, yaw=17.0127 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9453 m and dominant component(s): yaw.

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
