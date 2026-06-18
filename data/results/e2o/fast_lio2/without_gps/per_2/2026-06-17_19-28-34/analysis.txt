# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **37.0175**
- Overall position RMSE: **28.8925 m**
- Overall max position error: **57.9874 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521296` → `1723528521.647515`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.9454 m, x=0.3181 m, y=0.3858 m, z=0.8023 m, yaw=0.7423 deg, dominant=z, yaw, samples=2136 | pos=0.9454 m, x=0.3202 m, y=0.3835 m, z=0.8026 m, yaw=0.7438 deg, dominant=z, yaw, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1951 m, x=0.0356 m, y=0.0544 m, z=0.1839 m, yaw=0.6517 deg, dominant=yaw, samples=148 | pos=0.6434 m, x=0.2586 m, y=0.2132 m, z=0.5491 m, yaw=0.3503 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3465 m, x=0.1390 m, y=0.2412 m, z=0.2064 m, yaw=1.3599 deg, dominant=yaw, samples=118 | pos=1.1287 m, x=0.2550 m, y=0.3495 m, z=1.0424 m, yaw=2.3384 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9733 m, x=0.7286 m, y=0.1227 m, z=0.6335 m, yaw=0.3254 deg, dominant=x, samples=254 | pos=0.7406 m, x=0.5391 m, y=0.2586 m, z=0.4371 m, yaw=0.3674 deg, dominant=x, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3179 m, x=0.0556 m, y=0.1133 m, z=0.2918 m, yaw=0.1108 deg, dominant=z, samples=204 | pos=0.5499 m, x=0.0266 m, y=0.3510 m, z=0.4225 m, yaw=0.5029 deg, dominant=yaw, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2710 m, x=0.1281 m, y=0.0153 m, z=0.2383 m, yaw=0.1510 deg, dominant=z, samples=144 | pos=0.9931 m, x=0.1364 m, y=0.4648 m, z=0.8670 m, yaw=0.1875 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2335 m, x=0.1939 m, y=0.0547 m, z=0.1179 m, yaw=0.4952 deg, dominant=yaw, samples=96 | pos=1.2647 m, x=0.1872 m, y=0.4489 m, z=1.1674 m, yaw=0.6409 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2264 m, x=0.2055 m, y=0.0850 m, z=0.0427 m, yaw=0.4828 deg, dominant=yaw, samples=416 | pos=1.3764 m, x=0.1808 m, y=0.5393 m, z=1.2533 m, yaw=0.6613 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3166 m, x=0.1731 m, y=0.1131 m, z=0.2398 m, yaw=0.1217 deg, dominant=z, samples=206 | pos=1.2367 m, x=0.5412 m, y=0.5772 m, z=0.9505 m, yaw=0.6031 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.0017 m, x=0.5797 m, y=0.4412 m, z=0.6876 m, yaw=4.5821 deg, dominant=yaw, samples=350 | pos=1.0804 m, x=0.6196 m, y=0.8223 m, z=0.3276 m, yaw=4.1938 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.3087 m, x=0.2929 m, y=0.0514 m, z=0.0830 m, yaw=1.4090 deg, dominant=yaw, samples=38 | pos=1.7292 m, x=0.1790 m, y=1.6705 m, z=0.4092 m, yaw=8.3987 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5937 m, x=2.0551 m, y=4.1075 m, z=0.0825 m, yaw=9.7002 deg, dominant=yaw, samples=404 | pos=5.9693 m, x=1.8920 m, y=5.6400 m, z=0.4933 m, yaw=4.0345 deg, dominant=y, samples=404 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9574 m, x=2.8033 m, y=0.9092 m, z=0.2480 m, yaw=20.5634 deg, dominant=yaw, samples=104 | pos=10.3808 m, x=6.7487 m, y=7.8410 m, z=0.8572 m, yaw=28.6615 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9706 m, x=6.8835 m, y=3.8771 m, z=1.0557 m, yaw=24.3480 deg, dominant=yaw, samples=320 | pos=16.5081 m, x=16.0452 m, y=3.2611 m, z=2.1056 m, yaw=16.8425 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9706 m and dominant component(s): yaw.

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
