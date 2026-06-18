# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4415**
- Overall position RMSE: **29.3124 m**
- Overall max position error: **58.6023 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217084` → `1723528521.444185`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0931 m, x=0.2795 m, y=0.1630 m, z=1.0441 m, yaw=0.7491 deg, dominant=z, samples=536 | pos=1.0931 m, x=0.2795 m, y=0.1630 m, z=1.0441 m, yaw=0.7491 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2311 m, x=0.0200 m, y=0.0657 m, z=0.2206 m, yaw=0.4813 deg, dominant=yaw, samples=37 | pos=0.7702 m, x=0.2536 m, y=0.2018 m, z=0.6987 m, yaw=0.4157 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3705 m, x=0.2482 m, y=0.2693 m, z=0.0563 m, yaw=1.3833 deg, dominant=yaw, samples=29 | pos=1.0066 m, x=0.1247 m, y=0.3160 m, z=0.9476 m, yaw=2.7451 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6690 m, x=0.6355 m, y=0.1084 m, z=0.1788 m, yaw=0.4307 deg, dominant=x, samples=64 | pos=1.0511 m, x=0.6310 m, y=0.1473 m, z=0.8276 m, yaw=0.3092 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2424 m, x=0.0336 m, y=0.0665 m, z=0.2307 m, yaw=0.1565 deg, dominant=z, samples=54 | pos=0.4959 m, x=0.1064 m, y=0.1770 m, z=0.4508 m, yaw=0.3893 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1902 m, x=0.1404 m, y=0.0403 m, z=0.1218 m, yaw=0.1790 deg, dominant=yaw, samples=33 | pos=0.4005 m, x=0.2506 m, y=0.2164 m, z=0.2252 m, yaw=0.2173 deg, dominant=x, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2468 m, x=0.1866 m, y=0.0420 m, z=0.1561 m, yaw=0.4910 deg, dominant=yaw, samples=24 | pos=0.3385 m, x=0.2909 m, y=0.1290 m, z=0.1155 m, yaw=0.9009 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8585 m, x=0.0542 m, y=0.0624 m, z=0.8545 m, yaw=0.3907 deg, dominant=z, samples=104 | pos=1.0977 m, x=0.1090 m, y=0.1432 m, z=1.0828 m, yaw=0.2492 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.7674 m, x=0.0369 m, y=0.1246 m, z=0.7563 m, yaw=0.1331 deg, dominant=z, samples=51 | pos=2.0967 m, x=0.1999 m, y=0.1519 m, z=2.0816 m, yaw=0.1479 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9026 m, x=0.6901 m, y=0.5543 m, z=0.1762 m, yaw=4.7371 deg, dominant=yaw, samples=88 | pos=2.7145 m, x=0.5885 m, y=0.6131 m, z=2.5781 m, yaw=4.6484 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2487 m, x=0.2376 m, y=0.0599 m, z=0.0426 m, yaw=1.2749 deg, dominant=yaw, samples=9 | pos=2.8165 m, x=0.4598 m, y=1.4890 m, z=2.3460 m, yaw=9.2246 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4853 m, x=1.7122 m, y=4.0332 m, z=0.9587 m, yaw=9.8290 deg, dominant=yaw, samples=101 | pos=5.9880 m, x=1.9557 m, y=5.3994 m, z=1.6963 m, yaw=3.8720 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8415 m, x=2.7139 m, y=0.8303 m, z=0.1399 m, yaw=20.3565 deg, dominant=yaw, samples=26 | pos=10.2995 m, x=6.6857 m, y=7.7983 m, z=0.7533 m, yaw=27.8088 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8696 m, x=7.0380 m, y=3.4534 m, z=0.6868 m, yaw=24.5047 deg, dominant=yaw, samples=80 | pos=16.5132 m, x=16.1387 m, y=3.4805 m, z=0.3363 m, yaw=16.2103 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8696 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | yaw_gyro_bias | imu/bias | 1621218780.000000 → 1621218785.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | forward_accel_bias | imu/bias | 1621218800.000000 → 1621218805.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
