# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4784**
- Overall position RMSE: **29.3635 m**
- Overall max position error: **58.6133 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217014` → `1723528521.443593`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0686 m, x=0.2783 m, y=0.1636 m, z=1.0187 m, yaw=0.7478 deg, dominant=z, samples=536 | pos=1.0686 m, x=0.2783 m, y=0.1636 m, z=1.0187 m, yaw=0.7478 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2306 m, x=0.0200 m, y=0.0669 m, z=0.2198 m, yaw=0.4826 deg, dominant=yaw, samples=37 | pos=0.7702 m, x=0.2528 m, y=0.2026 m, z=0.6987 m, yaw=0.4182 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3733 m, x=0.2484 m, y=0.2721 m, z=0.0599 m, yaw=1.3832 deg, dominant=yaw, samples=29 | pos=1.0070 m, x=0.1242 m, y=0.3162 m, z=0.9480 m, yaw=2.7477 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6667 m, x=0.6326 m, y=0.1090 m, z=0.1801 m, yaw=0.4368 deg, dominant=x, samples=64 | pos=1.0503 m, x=0.6313 m, y=0.1475 m, z=0.8264 m, yaw=0.3096 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2252 m, x=0.0327 m, y=0.0684 m, z=0.2121 m, yaw=0.1589 deg, dominant=z, samples=54 | pos=0.4978 m, x=0.1067 m, y=0.1808 m, z=0.4514 m, yaw=0.3872 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1878 m, x=0.1384 m, y=0.0402 m, z=0.1204 m, yaw=0.1770 deg, dominant=yaw, samples=33 | pos=0.4007 m, x=0.2504 m, y=0.2195 m, z=0.2229 m, yaw=0.2124 deg, dominant=x, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2454 m, x=0.1866 m, y=0.0411 m, z=0.1540 m, yaw=0.4849 deg, dominant=yaw, samples=24 | pos=0.3403 m, x=0.2918 m, y=0.1320 m, z=0.1150 m, yaw=0.8929 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8442 m, x=0.0537 m, y=0.0665 m, z=0.8399 m, yaw=0.3873 deg, dominant=z, samples=104 | pos=1.0696 m, x=0.1066 m, y=0.1408 m, z=1.0550 m, yaw=0.2435 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.7476 m, x=0.0306 m, y=0.1171 m, z=0.7378 m, yaw=0.1296 deg, dominant=z, samples=51 | pos=2.0381 m, x=0.1893 m, y=0.1407 m, z=2.0244 m, yaw=0.1385 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9115 m, x=0.6957 m, y=0.5689 m, z=0.1520 m, yaw=4.7298 deg, dominant=yaw, samples=88 | pos=2.6262 m, x=0.5991 m, y=0.6167 m, z=2.4815 m, yaw=4.6503 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2538 m, x=0.2384 m, y=0.0736 m, z=0.0466 m, yaw=1.2860 deg, dominant=yaw, samples=9 | pos=2.7617 m, x=0.4879 m, y=1.4790 m, z=2.2807 m, yaw=9.2171 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4390 m, x=1.6945 m, y=3.9906 m, z=0.9532 m, yaw=9.8473 deg, dominant=yaw, samples=101 | pos=5.9516 m, x=1.9624 m, y=5.3618 m, z=1.6797 m, yaw=3.8918 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8370 m, x=2.7094 m, y=0.8301 m, z=0.1357 m, yaw=20.3449 deg, dominant=yaw, samples=26 | pos=10.3113 m, x=6.7176 m, y=7.7816 m, z=0.8030 m, yaw=27.8042 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8537 m, x=7.0221 m, y=3.4428 m, z=0.7195 m, yaw=24.5171 deg, dominant=yaw, samples=80 | pos=16.5251 m, x=16.1521 m, y=3.4725 m, z=0.3583 m, yaw=16.2010 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8537 m and dominant component(s): yaw.

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
