# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4105**
- Overall position RMSE: **29.2959 m**
- Overall max position error: **58.6167 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.216999` → `1723528521.442393`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0709 m, x=0.2758 m, y=0.1638 m, z=1.0217 m, yaw=0.7459 deg, dominant=z, samples=536 | pos=1.0709 m, x=0.2758 m, y=0.1638 m, z=1.0217 m, yaw=0.7459 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2298 m, x=0.0202 m, y=0.0652 m, z=0.2195 m, yaw=0.4818 deg, dominant=yaw, samples=37 | pos=0.7693 m, x=0.2545 m, y=0.2018 m, z=0.6973 m, yaw=0.4160 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3697 m, x=0.2453 m, y=0.2711 m, z=0.0547 m, yaw=1.3777 deg, dominant=yaw, samples=29 | pos=1.0036 m, x=0.1256 m, y=0.3145 m, z=0.9447 m, yaw=2.7364 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6699 m, x=0.6358 m, y=0.1136 m, z=0.1778 m, yaw=0.4209 deg, dominant=x, samples=64 | pos=1.0488 m, x=0.6291 m, y=0.1480 m, z=0.8259 m, yaw=0.3092 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2239 m, x=0.0320 m, y=0.0692 m, z=0.2105 m, yaw=0.1579 deg, dominant=z, samples=54 | pos=0.4996 m, x=0.1038 m, y=0.1832 m, z=0.4530 m, yaw=0.3919 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1879 m, x=0.1391 m, y=0.0392 m, z=0.1200 m, yaw=0.1787 deg, dominant=yaw, samples=33 | pos=0.4027 m, x=0.2467 m, y=0.2224 m, z=0.2277 m, yaw=0.2152 deg, dominant=x, z, y, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2469 m, x=0.1874 m, y=0.0420 m, z=0.1552 m, yaw=0.4897 deg, dominant=yaw, samples=24 | pos=0.3364 m, x=0.2877 m, y=0.1340 m, z=0.1116 m, yaw=0.9033 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8546 m, x=0.0492 m, y=0.0681 m, z=0.8504 m, yaw=0.3902 deg, dominant=z, samples=104 | pos=1.0707 m, x=0.0980 m, y=0.1392 m, z=1.0571 m, yaw=0.2359 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.7506 m, x=0.0319 m, y=0.1176 m, z=0.7406 m, yaw=0.1326 deg, dominant=z, samples=51 | pos=2.0442 m, x=0.1764 m, y=0.1376 m, z=2.0319 m, yaw=0.1396 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9175 m, x=0.7008 m, y=0.5706 m, z=0.1583 m, yaw=4.7315 deg, dominant=yaw, samples=88 | pos=2.6503 m, x=0.6092 m, y=0.6161 m, z=2.5046 m, yaw=4.6611 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2493 m, x=0.2322 m, y=0.0757 m, z=0.0498 m, yaw=1.2909 deg, dominant=yaw, samples=9 | pos=2.8020 m, x=0.5089 m, y=1.4804 m, z=2.3239 m, yaw=9.2405 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4394 m, x=1.6829 m, y=3.9958 m, z=0.9537 m, yaw=9.8530 deg, dominant=yaw, samples=101 | pos=5.9716 m, x=1.9718 m, y=5.3658 m, z=1.7263 m, yaw=3.8889 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8393 m, x=2.7175 m, y=0.8105 m, z=0.1410 m, yaw=20.3745 deg, dominant=yaw, samples=26 | pos=10.3304 m, x=6.7303 m, y=7.7909 m, z=0.8496 m, yaw=27.8287 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8600 m, x=7.0249 m, y=3.4451 m, z=0.7494 m, yaw=24.4909 deg, dominant=yaw, samples=80 | pos=16.5313 m, x=16.1575 m, y=3.4752 m, z=0.3782 m, yaw=16.1965 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8600 m and dominant component(s): yaw.

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
