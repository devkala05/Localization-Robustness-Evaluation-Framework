# Localization Run Analysis

**Algorithm note:** RTAB-Map visual+ICP pipeline: raw/perturbed scan_cloud is sanitized, RTAB-Map icp_odometry produces /rtabmap/icp_odom, and the mapper consumes that odometry together with the right camera image/camera_info. It no longer launches FAST-LIO2 and does not subscribe to FAST-LIO2 /Odometry.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **864**
- Robustness score, lower is better: **19.0475**
- Overall position RMSE: **14.6971 m**
- Overall max position error: **37.2182 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.225335` → `1723528435.718487`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=2.4217 m, x=1.1051 m, y=1.9441 m, z=0.9294 m, yaw=2.1157 deg, dominant=yaw, y, samples=422 | pos=2.4217 m, x=1.1051 m, y=1.9441 m, z=0.9294 m, yaw=2.1157 deg, dominant=yaw, y, samples=422 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.5438 m, x=0.2332 m, y=0.1974 m, z=0.4498 m, yaw=0.4543 deg, dominant=yaw, z, samples=28 | pos=1.3279 m, x=0.1754 m, y=0.6943 m, z=1.1183 m, yaw=1.6221 deg, dominant=yaw, samples=28 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3359 m, x=0.1405 m, y=0.2104 m, z=0.2210 m, yaw=1.3661 deg, dominant=yaw, samples=24 | pos=2.0893 m, x=0.5501 m, y=0.7240 m, z=1.8810 m, yaw=1.3750 deg, dominant=z, samples=24 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=1.0296 m, x=0.4603 m, y=0.4854 m, z=0.7827 m, yaw=0.5580 deg, dominant=z, samples=50 | pos=1.3242 m, x=0.6821 m, y=0.5486 m, z=0.9936 m, yaw=2.7252 deg, dominant=yaw, samples=50 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.6793 m, x=0.1678 m, y=0.6195 m, z=0.2225 m, yaw=0.2183 deg, dominant=y, samples=38 | pos=1.7650 m, x=1.5821 m, y=0.7271 m, z=0.2890 m, yaw=2.6796 deg, dominant=yaw, samples=38 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.4036 m, x=0.0855 m, y=0.3380 m, z=0.2033 m, yaw=0.3583 deg, dominant=yaw, y, samples=28 | pos=2.3307 m, x=1.7019 m, y=1.4619 m, z=0.6312 m, yaw=1.9356 deg, dominant=yaw, samples=28 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.4281 m, x=0.3242 m, y=0.2503 m, z=0.1244 m, yaw=0.5663 deg, dominant=yaw, samples=18 | pos=2.8020 m, x=1.8576 m, y=1.8875 m, z=0.9154 m, yaw=0.9314 deg, dominant=y, x, samples=18 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=1.1446 m, x=0.6907 m, y=0.8982 m, z=0.1622 m, yaw=0.8541 deg, dominant=y, yaw, samples=82 | pos=3.5218 m, x=1.6147 m, y=3.0112 m, z=0.8536 m, yaw=2.5596 deg, dominant=y, samples=82 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.9148 m, x=0.8701 m, y=0.1493 m, z=0.2398 m, yaw=0.1620 deg, dominant=x, samples=40 | pos=3.8690 m, x=0.5175 m, y=3.5734 m, z=1.3899 m, yaw=2.9052 deg, dominant=y, samples=40 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.8817 m, x=0.4833 m, y=0.4027 m, z=1.7735 m, yaw=4.7047 deg, dominant=yaw, samples=68 | pos=3.4985 m, x=1.2758 m, y=3.0904 m, z=1.0300 m, yaw=3.5754 deg, dominant=yaw, samples=68 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2354 m, x=0.1133 m, y=0.1951 m, z=0.0669 m, yaw=1.3335 deg, dominant=yaw, samples=8 | pos=3.9183 m, x=0.8966 m, y=3.3374 m, z=1.8469 m, yaw=6.1789 deg, dominant=yaw, samples=8 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.6696 m, x=2.9473 m, y=3.5858 m, z=0.5100 m, yaw=9.9376 deg, dominant=yaw, samples=78 | pos=7.4600 m, x=2.1848 m, y=6.7503 m, z=2.3046 m, yaw=5.4473 deg, dominant=y, samples=78 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8052 m, x=2.6026 m, y=1.0095 m, z=0.2762 m, yaw=18.8444 deg, dominant=yaw, samples=20 | pos=11.5418 m, x=7.2576 m, y=8.5091 m, z=2.8522 m, yaw=29.2185 deg, dominant=yaw, samples=20 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=8.3995 m, x=6.9897 m, y=4.3260 m, z=1.7266 m, yaw=24.2364 deg, dominant=yaw, samples=62 | pos=17.7606 m, x=16.7544 m, y=3.3623 m, z=4.8397 m, yaw=18.3417 deg, dominant=yaw, x, samples=62 |

**Most affected segment:** `straight_road` with relative position RMSE 8.3995 m and dominant component(s): yaw.

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
