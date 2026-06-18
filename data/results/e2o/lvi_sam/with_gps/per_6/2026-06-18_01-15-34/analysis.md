# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4254**
- Overall position RMSE: **29.3073 m**
- Overall max position error: **58.6246 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217199` → `1723528521.445382`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0740 m, x=0.2774 m, y=0.1607 m, z=1.0250 m, yaw=0.7472 deg, dominant=z, samples=536 | pos=1.0740 m, x=0.2774 m, y=0.1607 m, z=1.0250 m, yaw=0.7472 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2308 m, x=0.0199 m, y=0.0663 m, z=0.2202 m, yaw=0.4824 deg, dominant=yaw, samples=37 | pos=0.7701 m, x=0.2528 m, y=0.2004 m, z=0.6993 m, yaw=0.4184 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3695 m, x=0.2471 m, y=0.2695 m, z=0.0537 m, yaw=1.3792 deg, dominant=yaw, samples=29 | pos=1.0049 m, x=0.1239 m, y=0.3140 m, z=0.9465 m, yaw=2.7439 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6688 m, x=0.6346 m, y=0.1106 m, z=0.1800 m, yaw=0.4309 deg, dominant=x, samples=64 | pos=1.0490 m, x=0.6313 m, y=0.1453 m, z=0.8251 m, yaw=0.3094 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2245 m, x=0.0321 m, y=0.0687 m, z=0.2113 m, yaw=0.1573 deg, dominant=z, samples=54 | pos=0.4958 m, x=0.1071 m, y=0.1779 m, z=0.4503 m, yaw=0.3858 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1889 m, x=0.1401 m, y=0.0406 m, z=0.1200 m, yaw=0.1777 deg, dominant=yaw, samples=33 | pos=0.3983 m, x=0.2516 m, y=0.2146 m, z=0.2220 m, yaw=0.2170 deg, dominant=x, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2469 m, x=0.1861 m, y=0.0419 m, z=0.1568 m, yaw=0.4913 deg, dominant=yaw, samples=24 | pos=0.3390 m, x=0.2928 m, y=0.1251 m, z=0.1164 m, yaw=0.9045 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8540 m, x=0.0496 m, y=0.0669 m, z=0.8499 m, yaw=0.3885 deg, dominant=z, samples=104 | pos=1.0793 m, x=0.1026 m, y=0.1341 m, z=1.0660 m, yaw=0.2386 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.7507 m, x=0.0298 m, y=0.1168 m, z=0.7410 m, yaw=0.1289 deg, dominant=z, samples=51 | pos=2.0516 m, x=0.1804 m, y=0.1335 m, z=2.0393 m, yaw=0.1338 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9138 m, x=0.6975 m, y=0.5707 m, z=0.1517 m, yaw=4.7275 deg, dominant=yaw, samples=88 | pos=2.6399 m, x=0.6064 m, y=0.6134 m, z=2.4951 m, yaw=4.6607 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2533 m, x=0.2368 m, y=0.0756 m, z=0.0486 m, yaw=1.2882 deg, dominant=yaw, samples=9 | pos=2.7719 m, x=0.5026 m, y=1.4737 m, z=2.2933 m, yaw=9.2344 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4589 m, x=1.7088 m, y=4.0166 m, z=0.9104 m, yaw=9.8155 deg, dominant=yaw, samples=101 | pos=5.9838 m, x=1.9912 m, y=5.3811 m, z=1.6987 m, yaw=3.8631 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8402 m, x=2.7163 m, y=0.8180 m, z=0.1408 m, yaw=20.3634 deg, dominant=yaw, samples=26 | pos=10.3224 m, x=6.7275 m, y=7.7861 m, z=0.8173 m, yaw=27.8138 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8488 m, x=7.0156 m, y=3.4434 m, z=0.7270 m, yaw=24.4997 deg, dominant=yaw, samples=80 | pos=16.5221 m, x=16.1493 m, y=3.4711 m, z=0.3642 m, yaw=16.1951 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8488 m and dominant component(s): yaw.

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
