# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4411**
- Overall position RMSE: **29.2561 m**
- Overall max position error: **58.6164 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217161` → `1723528521.445387`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0875 m, x=0.2794 m, y=0.1624 m, z=1.0384 m, yaw=0.7514 deg, dominant=z, samples=1072 | pos=1.0875 m, x=0.2794 m, y=0.1624 m, z=1.0384 m, yaw=0.7514 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2311 m, x=0.0197 m, y=0.0662 m, z=0.2206 m, yaw=0.4827 deg, dominant=yaw, samples=74 | pos=0.7695 m, x=0.2525 m, y=0.1999 m, z=0.6989 m, yaw=0.4194 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3694 m, x=0.2458 m, y=0.2703 m, z=0.0547 m, yaw=1.3812 deg, dominant=yaw, samples=58 | pos=1.0092 m, x=0.1230 m, y=0.3145 m, z=0.9510 m, yaw=2.7454 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6697 m, x=0.6361 m, y=0.1112 m, z=0.1775 m, yaw=0.4284 deg, dominant=x, samples=128 | pos=1.0551 m, x=0.6317 m, y=0.1451 m, z=0.8325 m, yaw=0.3104 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1774 m, x=0.0351 m, y=0.0702 m, z=0.1591 m, yaw=0.1571 deg, dominant=z, yaw, samples=102 | pos=0.5203 m, x=0.1076 m, y=0.1785 m, z=0.4767 m, yaw=0.3800 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1981 m, x=0.1294 m, y=0.0399 m, z=0.1446 m, yaw=0.1787 deg, dominant=yaw, samples=72 | pos=0.4120 m, x=0.2445 m, y=0.2183 m, z=0.2496 m, yaw=0.2072 deg, dominant=z, x, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2460 m, x=0.1853 m, y=0.0434 m, z=0.1559 m, yaw=0.4854 deg, dominant=yaw, samples=48 | pos=0.3364 m, x=0.2924 m, y=0.1286 m, z=0.1056 m, yaw=0.9006 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8643 m, x=0.0539 m, y=0.0650 m, z=0.8601 m, yaw=0.3973 deg, dominant=z, samples=208 | pos=1.0721 m, x=0.1077 m, y=0.1399 m, z=1.0575 m, yaw=0.2453 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4202 m, x=0.0301 m, y=0.0938 m, z=0.4085 m, yaw=0.1263 deg, dominant=z, samples=102 | pos=2.1157 m, x=0.1929 m, y=0.1360 m, z=2.1025 m, yaw=0.1364 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9117 m, x=0.6948 m, y=0.5698 m, z=0.1544 m, yaw=4.7298 deg, dominant=yaw, samples=176 | pos=2.6492 m, x=0.5967 m, y=0.6169 m, z=2.5063 m, yaw=4.6555 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2543 m, x=0.2376 m, y=0.0765 m, z=0.0483 m, yaw=1.2881 deg, dominant=yaw, samples=18 | pos=2.7857 m, x=0.4846 m, y=1.4814 m, z=2.3088 m, yaw=9.2262 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5155 m, x=1.7667 m, y=4.0817 m, z=0.7800 m, yaw=9.7066 deg, dominant=yaw, samples=202 | pos=6.0654 m, x=2.0328 m, y=5.4497 m, z=1.7198 m, yaw=3.7893 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8403 m, x=2.7143 m, y=0.8231 m, z=0.1499 m, yaw=20.3297 deg, dominant=yaw, samples=52 | pos=10.3174 m, x=6.7126 m, y=7.7919 m, z=0.8232 m, yaw=27.8125 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8606 m, x=7.0254 m, y=3.4502 m, z=0.7264 m, yaw=24.4949 deg, dominant=yaw, samples=160 | pos=16.5224 m, x=16.1493 m, y=3.4723 m, z=0.3638 m, yaw=16.1968 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8606 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | motion_blur | camera_right/motion_blur | 1621218792.000000 → 1621218800.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | camera_frame_dropout | camera_right/frame_dropout | 1621218810.000000 → 1621218815.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
