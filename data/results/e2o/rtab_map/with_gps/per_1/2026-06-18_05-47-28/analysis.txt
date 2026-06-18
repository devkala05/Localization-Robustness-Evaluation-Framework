# Localization Run Analysis

**Algorithm note:** RTAB-Map visual+ICP pipeline: raw/perturbed scan_cloud is sanitized, RTAB-Map icp_odometry produces /rtabmap/icp_odom, and the mapper consumes that odometry together with the right camera image/camera_info. It no longer launches FAST-LIO2 and does not subscribe to FAST-LIO2 /Odometry.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **613**
- Robustness score, lower is better: **104.4311**
- Overall position RMSE: **87.0479 m**
- Overall max position error: **141.6134 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.216938` → `1723528521.604704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=74.0928 m, x=58.6809 m, y=45.2336 m, z=0.4706 m, yaw=84.9810 deg, dominant=yaw, samples=216 | pos=74.0928 m, x=58.6809 m, y=45.2336 m, z=0.4706 m, yaw=84.9810 deg, dominant=yaw, samples=216 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=13.4431 m, x=12.9099 m, y=3.7470 m, z=0.0975 m, yaw=5.0427 deg, dominant=x, samples=15 | pos=48.9580 m, x=45.6552 m, y=17.6753 m, z=0.2753 m, yaw=55.5882 deg, dominant=yaw, samples=15 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=8.8007 m, x=4.7105 m, y=7.4331 m, z=0.1064 m, yaw=27.2161 deg, dominant=yaw, samples=12 | pos=62.2542 m, x=61.7789 m, y=7.6629 m, z=0.4762 m, yaw=81.1793 deg, dominant=yaw, samples=12 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=22.4440 m, x=12.9900 m, y=18.3022 m, z=0.1403 m, yaw=33.4981 deg, dominant=yaw, samples=25 | pos=56.0655 m, x=52.7812 m, y=18.9047 m, z=0.3212 m, yaw=68.5639 deg, dominant=yaw, samples=25 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=21.4168 m, x=13.4435 m, y=16.6701 m, z=0.2477 m, yaw=7.1067 deg, dominant=y, samples=20 | pos=57.1115 m, x=24.8471 m, y=51.4231 m, z=0.1203 m, yaw=36.4569 deg, dominant=y, samples=20 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=14.7767 m, x=10.8079 m, y=10.0763 m, z=0.0836 m, yaw=21.5004 deg, dominant=yaw, samples=15 | pos=74.6190 m, x=7.1821 m, y=74.2725 m, z=0.0799 m, yaw=44.3288 deg, dominant=y, samples=15 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=9.1608 m, x=8.7993 m, y=2.5480 m, z=0.0296 m, yaw=9.7817 deg, dominant=yaw, samples=9 | pos=86.4306 m, x=17.2382 m, y=84.6939 m, z=0.1523 m, yaw=22.8986 deg, dominant=y, samples=9 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=44.9612 m, x=40.0362 m, y=20.4510 m, z=0.6113 m, yaw=131.3950 deg, dominant=yaw, samples=42 | pos=94.9531 m, x=63.3067 m, y=70.7678 m, z=0.5199 m, yaw=126.9231 deg, dominant=yaw, samples=42 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=32.4292 m, x=19.8191 m, y=25.6680 m, z=0.1190 m, yaw=147.8587 deg, dominant=yaw, samples=21 | pos=117.1773 m, x=114.5549 m, y=24.6319 m, z=0.9759 m, yaw=134.6560 deg, dominant=yaw, samples=21 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=15.2691 m, x=7.5042 m, y=13.2974 m, z=0.1062 m, yaw=66.7909 deg, dominant=yaw, samples=34 | pos=122.6680 m, x=121.9860 m, y=12.8778 m, z=1.0030 m, yaw=117.2488 deg, dominant=x, yaw, samples=34 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=1.3546 m, x=1.2261 m, y=0.5756 m, z=0.0160 m, yaw=1.6134 deg, dominant=yaw, samples=4 | pos=111.5561 m, x=110.0077 m, y=18.5039 m, z=0.8268 m, yaw=106.3509 deg, dominant=x, yaw, samples=4 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=27.2879 m, x=22.5186 m, y=15.4112 m, z=0.2013 m, yaw=32.9819 deg, dominant=yaw, samples=40 | pos=91.6343 m, x=91.1528 m, y=9.3576 m, z=0.6626 m, yaw=81.4360 deg, dominant=x, samples=40 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=8.6304 m, x=7.8582 m, y=3.5670 m, z=0.0986 m, yaw=6.9982 deg, dominant=x, samples=11 | pos=58.9555 m, x=57.5314 m, y=12.8756 m, z=0.3200 m, yaw=118.0583 deg, dominant=yaw, samples=11 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=31.4967 m, x=30.0832 m, y=9.3289 m, z=0.1283 m, yaw=92.0098 deg, dominant=yaw, samples=32 | pos=31.6291 m, x=29.2154 m, y=12.1176 m, z=0.1577 m, yaw=93.9962 deg, dominant=yaw, samples=32 |

**Most affected segment:** `straight_road` with relative position RMSE 74.0928 m and dominant component(s): yaw.

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
