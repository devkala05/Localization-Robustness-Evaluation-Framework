# Localization Run Analysis

**Algorithm note:** RTAB-Map visual+ICP pipeline: raw/perturbed scan_cloud is sanitized, RTAB-Map icp_odometry produces /rtabmap/icp_odom, and the mapper consumes that odometry together with the right camera image/camera_info. It no longer launches FAST-LIO2 and does not subscribe to FAST-LIO2 /Odometry.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **490**
- Robustness score, lower is better: **3.0833**
- Overall position RMSE: **2.6384 m**
- Overall max position error: **4.9319 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.224834` → `1723528339.495102`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=2.4069 m, x=1.1071 m, y=1.9305 m, z=0.9169 m, yaw=2.1079 deg, dominant=yaw, y, samples=418 | pos=2.4069 m, x=1.1071 m, y=1.9305 m, z=0.9169 m, yaw=2.1079 deg, dominant=yaw, y, samples=418 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.5765 m, x=0.2437 m, y=0.2013 m, z=0.4821 m, yaw=0.5517 deg, dominant=yaw, samples=30 | pos=1.3448 m, x=0.1866 m, y=0.6957 m, z=1.1356 m, yaw=1.6162 deg, dominant=yaw, samples=30 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2926 m, x=0.1203 m, y=0.2001 m, z=0.1764 m, yaw=1.3861 deg, dominant=yaw, samples=22 | pos=2.1112 m, x=0.5633 m, y=0.7377 m, z=1.8962 m, yaw=1.3787 deg, dominant=z, samples=22 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=1.0222 m, x=0.4443 m, y=0.4727 m, z=0.7900 m, yaw=0.5905 deg, dominant=z, samples=50 | pos=1.3286 m, x=0.6681 m, y=0.5544 m, z=1.0057 m, yaw=2.6850 deg, dominant=yaw, samples=50 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.6799 m, x=0.1700 m, y=0.6185 m, z=0.2252 m, yaw=0.2021 deg, dominant=y, samples=38 | pos=1.7700 m, x=1.5935 m, y=0.7173 m, z=0.2815 m, yaw=2.6823 deg, dominant=yaw, samples=38 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.3996 m, x=0.0873 m, y=0.3379 m, z=0.1947 m, yaw=0.3462 deg, dominant=yaw, y, samples=28 | pos=2.3268 m, x=1.7158 m, y=1.4487 m, z=0.6092 m, yaw=1.9438 deg, dominant=yaw, samples=28 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.3848 m, x=0.2860 m, y=0.2202 m, z=0.1333 m, yaw=0.6091 deg, dominant=yaw, samples=18 | pos=2.7452 m, x=1.8280 m, y=1.8459 m, z=0.8873 m, yaw=0.9109 deg, dominant=y, x, samples=18 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=1.1167 m, x=0.6677 m, y=0.8811 m, z=0.1576 m, yaw=0.8196 deg, dominant=y, yaw, samples=80 | pos=3.5041 m, x=1.6372 m, y=2.9857 m, z=0.8270 m, yaw=2.5375 deg, dominant=y, samples=80 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.9064 m, x=0.8606 m, y=0.1245 m, z=0.2561 m, yaw=0.1770 deg, dominant=x, samples=40 | pos=3.8379 m, x=0.4824 m, y=3.5582 m, z=1.3550 m, yaw=2.8517 deg, dominant=y, samples=40 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.8413 m, x=0.4968 m, y=0.3590 m, z=1.7362 m, yaw=4.7211 deg, dominant=yaw, samples=68 | pos=3.4905 m, x=1.2423 m, y=3.0958 m, z=1.0276 m, yaw=3.6396 deg, dominant=yaw, samples=68 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2096 m, x=0.1675 m, y=0.1074 m, z=0.0660 m, yaw=1.3952 deg, dominant=yaw, samples=8 | pos=3.9244 m, x=0.7938 m, y=3.3560 m, z=1.8730 m, yaw=6.6071 deg, dominant=yaw, samples=8 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=0.6283 m, x=0.1153 m, y=0.6018 m, z=0.1389 m, yaw=2.7638 deg, dominant=yaw, samples=12 | pos=4.3557 m, x=0.9415 m, y=3.7524 m, z=2.0013 m, yaw=3.9104 deg, dominant=yaw, y, samples=12 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |

**Most affected segment:** `straight_road` with relative position RMSE 2.4069 m and dominant component(s): yaw, y.

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
