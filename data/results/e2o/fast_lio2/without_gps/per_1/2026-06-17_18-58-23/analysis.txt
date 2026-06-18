# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **37.0609**
- Overall position RMSE: **28.9291 m**
- Overall max position error: **58.1902 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.518620` → `1723528521.644760`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.9694 m, x=0.3254 m, y=0.3860 m, z=0.8275 m, yaw=0.7480 deg, dominant=z, yaw, samples=2136 | pos=0.9694 m, x=0.3277 m, y=0.3837 m, z=0.8278 m, yaw=0.7491 deg, dominant=z, yaw, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2020 m, x=0.0338 m, y=0.0511 m, z=0.1925 m, yaw=0.6342 deg, dominant=yaw, samples=148 | pos=0.6407 m, x=0.2530 m, y=0.2521 m, z=0.5319 m, yaw=0.3315 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3372 m, x=0.1382 m, y=0.2328 m, z=0.2010 m, yaw=1.3734 deg, dominant=yaw, samples=118 | pos=1.1208 m, x=0.2479 m, y=0.3825 m, z=1.0239 m, yaw=2.3640 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9538 m, x=0.7399 m, y=0.1076 m, z=0.5922 m, yaw=0.3120 deg, dominant=x, samples=254 | pos=0.7645 m, x=0.5540 m, y=0.2835 m, z=0.4440 m, yaw=0.3545 deg, dominant=x, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3011 m, x=0.0440 m, y=0.1046 m, z=0.2789 m, yaw=0.1130 deg, dominant=z, samples=204 | pos=0.5231 m, x=0.0407 m, y=0.3637 m, z=0.3737 m, yaw=0.4809 deg, dominant=yaw, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2648 m, x=0.1194 m, y=0.0157 m, z=0.2358 m, yaw=0.1594 deg, dominant=z, samples=144 | pos=0.9449 m, x=0.1516 m, y=0.4651 m, z=0.8084 m, yaw=0.1857 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2417 m, x=0.1918 m, y=0.0513 m, z=0.1379 m, yaw=0.4973 deg, dominant=yaw, samples=96 | pos=1.2340 m, x=0.2016 m, y=0.4468 m, z=1.1324 m, yaw=0.6671 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2386 m, x=0.2025 m, y=0.0805 m, z=0.0970 m, yaw=0.4860 deg, dominant=yaw, samples=416 | pos=1.4318 m, x=0.1901 m, y=0.5280 m, z=1.3173 m, yaw=0.6612 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3161 m, x=0.1723 m, y=0.1168 m, z=0.2379 m, yaw=0.1051 deg, dominant=z, samples=206 | pos=1.3208 m, x=0.5532 m, y=0.5553 m, z=1.0631 m, yaw=0.6070 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.0777 m, x=0.5766 m, y=0.4448 m, z=0.7945 m, yaw=4.6013 deg, dominant=yaw, samples=350 | pos=1.0977 m, x=0.6292 m, y=0.8095 m, z=0.3922 m, yaw=4.2036 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2996 m, x=0.2873 m, y=0.0556 m, z=0.0641 m, yaw=1.3890 deg, dominant=yaw, samples=38 | pos=1.7297 m, x=0.1862 m, y=1.6439 m, z=0.5048 m, yaw=8.3900 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5658 m, x=2.0509 m, y=4.0785 m, z=0.0779 m, yaw=9.7271 deg, dominant=yaw, samples=404 | pos=5.9205 m, x=1.8861 m, y=5.5908 m, z=0.4870 m, yaw=4.0364 deg, dominant=y, samples=404 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9635 m, x=2.8131 m, y=0.8989 m, z=0.2460 m, yaw=20.5913 deg, dominant=yaw, samples=104 | pos=10.3403 m, x=6.7462 m, y=7.7955 m, z=0.7999 m, yaw=28.6781 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9457 m, x=6.8601 m, y=3.8450 m, z=1.1354 m, yaw=24.4297 deg, dominant=yaw, samples=320 | pos=16.4785 m, x=16.0164 m, y=3.2308 m, z=2.1397 m, yaw=16.7717 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9457 m and dominant component(s): yaw.

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
