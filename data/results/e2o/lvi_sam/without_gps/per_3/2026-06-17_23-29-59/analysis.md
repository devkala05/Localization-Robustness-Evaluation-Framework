# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4434**
- Overall position RMSE: **29.2577 m**
- Overall max position error: **58.6259 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.216936` → `1723528521.442533`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0875 m, x=0.2774 m, y=0.1613 m, z=1.0391 m, yaw=0.7505 deg, dominant=z, samples=1072 | pos=1.0875 m, x=0.2774 m, y=0.1613 m, z=1.0391 m, yaw=0.7505 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2303 m, x=0.0199 m, y=0.0658 m, z=0.2198 m, yaw=0.4820 deg, dominant=yaw, samples=74 | pos=0.7696 m, x=0.2522 m, y=0.2001 m, z=0.6990 m, yaw=0.4172 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3704 m, x=0.2471 m, y=0.2704 m, z=0.0547 m, yaw=1.3803 deg, dominant=yaw, samples=58 | pos=1.0043 m, x=0.1236 m, y=0.3146 m, z=0.9457 m, yaw=2.7440 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6691 m, x=0.6350 m, y=0.1097 m, z=0.1801 m, yaw=0.4349 deg, dominant=x, samples=128 | pos=1.0477 m, x=0.6309 m, y=0.1454 m, z=0.8237 m, yaw=0.3102 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1804 m, x=0.0319 m, y=0.0706 m, z=0.1629 m, yaw=0.1530 deg, dominant=z, yaw, samples=102 | pos=0.5058 m, x=0.1066 m, y=0.1797 m, z=0.4606 m, yaw=0.3806 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1988 m, x=0.1288 m, y=0.0415 m, z=0.1456 m, yaw=0.1801 deg, dominant=yaw, samples=72 | pos=0.4003 m, x=0.2441 m, y=0.2182 m, z=0.2303 m, yaw=0.2097 deg, dominant=x, z, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2467 m, x=0.1866 m, y=0.0422 m, z=0.1558 m, yaw=0.4878 deg, dominant=yaw, samples=48 | pos=0.3391 m, x=0.2920 m, y=0.1259 m, z=0.1179 m, yaw=0.9045 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8559 m, x=0.0480 m, y=0.0674 m, z=0.8519 m, yaw=0.3860 deg, dominant=z, samples=208 | pos=1.0811 m, x=0.1010 m, y=0.1335 m, z=1.0681 m, yaw=0.2384 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4159 m, x=0.0291 m, y=0.0952 m, z=0.4038 m, yaw=0.1257 deg, dominant=z, samples=102 | pos=2.1166 m, x=0.1771 m, y=0.1299 m, z=2.1051 m, yaw=0.1329 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9145 m, x=0.6956 m, y=0.5715 m, z=0.1605 m, yaw=4.7336 deg, dominant=yaw, samples=176 | pos=2.6604 m, x=0.6049 m, y=0.6129 m, z=2.5172 m, yaw=4.6621 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2518 m, x=0.2348 m, y=0.0773 m, z=0.0480 m, yaw=1.2985 deg, dominant=yaw, samples=18 | pos=2.8099 m, x=0.5013 m, y=1.4755 m, z=2.3382 m, yaw=9.2392 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5015 m, x=1.7600 m, y=4.0797 m, z=0.7225 m, yaw=9.7102 deg, dominant=yaw, samples=202 | pos=6.0869 m, x=2.0402 m, y=5.4459 m, z=1.7972 m, yaw=3.7845 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8400 m, x=2.7143 m, y=0.8243 m, z=0.1369 m, yaw=20.3736 deg, dominant=yaw, samples=52 | pos=10.3328 m, x=6.7182 m, y=7.7927 m, z=0.9523 m, yaw=27.8105 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8680 m, x=7.0264 m, y=3.4448 m, z=0.8182 m, yaw=24.5009 deg, dominant=yaw, samples=160 | pos=16.5224 m, x=16.1476 m, y=3.4735 m, z=0.4243 m, yaw=16.2011 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8680 m and dominant component(s): yaw.

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
