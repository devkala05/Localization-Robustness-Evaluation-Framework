# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4432**
- Overall position RMSE: **29.2573 m**
- Overall max position error: **58.6201 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217141` → `1723528521.441953`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0893 m, x=0.2789 m, y=0.1619 m, z=1.0404 m, yaw=0.7497 deg, dominant=z, samples=1072 | pos=1.0893 m, x=0.2789 m, y=0.1619 m, z=1.0404 m, yaw=0.7497 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2320 m, x=0.0197 m, y=0.0662 m, z=0.2215 m, yaw=0.4843 deg, dominant=yaw, samples=74 | pos=0.7728 m, x=0.2522 m, y=0.2006 m, z=0.7024 m, yaw=0.4189 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3689 m, x=0.2439 m, y=0.2711 m, z=0.0557 m, yaw=1.3785 deg, dominant=yaw, samples=58 | pos=1.0092 m, x=0.1240 m, y=0.3142 m, z=0.9510 m, yaw=2.7399 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6699 m, x=0.6362 m, y=0.1095 m, z=0.1790 m, yaw=0.4319 deg, dominant=x, samples=128 | pos=1.0552 m, x=0.6331 m, y=0.1461 m, z=0.8315 m, yaw=0.3105 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1794 m, x=0.0335 m, y=0.0711 m, z=0.1613 m, yaw=0.1578 deg, dominant=z, yaw, samples=102 | pos=0.5123 m, x=0.1087 m, y=0.1790 m, z=0.4675 m, yaw=0.3803 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1992 m, x=0.1291 m, y=0.0406 m, z=0.1462 m, yaw=0.1798 deg, dominant=yaw, samples=72 | pos=0.4062 m, x=0.2461 m, y=0.2190 m, z=0.2377 m, yaw=0.2083 deg, dominant=x, z, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2441 m, x=0.1852 m, y=0.0419 m, z=0.1533 m, yaw=0.4901 deg, dominant=yaw, samples=48 | pos=0.3393 m, x=0.2935 m, y=0.1268 m, z=0.1137 m, yaw=0.8989 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8568 m, x=0.0511 m, y=0.0669 m, z=0.8527 m, yaw=0.3833 deg, dominant=z, samples=208 | pos=1.0788 m, x=0.1046 m, y=0.1361 m, z=1.0650 m, yaw=0.2397 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4158 m, x=0.0281 m, y=0.0867 m, z=0.4057 m, yaw=0.1262 deg, dominant=z, samples=102 | pos=2.1176 m, x=0.1819 m, y=0.1334 m, z=2.1056 m, yaw=0.1356 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9139 m, x=0.6948 m, y=0.5715 m, z=0.1612 m, yaw=4.7339 deg, dominant=yaw, samples=176 | pos=2.6635 m, x=0.6012 m, y=0.6170 m, z=2.5204 m, yaw=4.6624 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2528 m, x=0.2365 m, y=0.0765 m, z=0.0459 m, yaw=1.2911 deg, dominant=yaw, samples=18 | pos=2.8144 m, x=0.4926 m, y=1.4840 m, z=2.3401 m, yaw=9.2403 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5095 m, x=1.7632 m, y=4.0870 m, z=0.7233 m, yaw=9.7083 deg, dominant=yaw, samples=202 | pos=6.0976 m, x=2.0347 m, y=5.4601 m, z=1.7966 m, yaw=3.7844 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8457 m, x=2.7256 m, y=0.8067 m, z=0.1357 m, yaw=20.4063 deg, dominant=yaw, samples=52 | pos=10.3438 m, x=6.7169 m, y=7.8084 m, z=0.9517 m, yaw=27.8409 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8795 m, x=7.0367 m, y=3.4493 m, z=0.8201 m, yaw=24.4852 deg, dominant=yaw, samples=160 | pos=16.5238 m, x=16.1479 m, y=3.4786 m, z=0.4243 m, yaw=16.2032 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8795 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | lidar_off_window | lidar/sensor_off | 1621218790.000000 → 1621218895.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
