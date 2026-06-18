# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4404**
- Overall position RMSE: **29.2548 m**
- Overall max position error: **58.6147 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217497` → `1723528521.445424`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0891 m, x=0.2776 m, y=0.1624 m, z=1.0405 m, yaw=0.7487 deg, dominant=z, samples=1072 | pos=1.0891 m, x=0.2776 m, y=0.1624 m, z=1.0405 m, yaw=0.7487 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2297 m, x=0.0191 m, y=0.0661 m, z=0.2192 m, yaw=0.4806 deg, dominant=yaw, samples=74 | pos=0.7679 m, x=0.2538 m, y=0.1962 m, z=0.6977 m, yaw=0.4186 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3685 m, x=0.2453 m, y=0.2695 m, z=0.0547 m, yaw=1.3806 deg, dominant=yaw, samples=58 | pos=1.0027 m, x=0.1237 m, y=0.3092 m, z=0.9458 m, yaw=2.7351 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6665 m, x=0.6324 m, y=0.1102 m, z=0.1791 m, yaw=0.4297 deg, dominant=x, samples=128 | pos=1.0471 m, x=0.6295 m, y=0.1438 m, z=0.8243 m, yaw=0.3103 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1799 m, x=0.0332 m, y=0.0718 m, z=0.1616 m, yaw=0.1509 deg, dominant=z, yaw, samples=102 | pos=0.5089 m, x=0.1038 m, y=0.1810 m, z=0.4642 m, yaw=0.3860 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1984 m, x=0.1293 m, y=0.0394 m, z=0.1452 m, yaw=0.1798 deg, dominant=yaw, samples=72 | pos=0.4041 m, x=0.2410 m, y=0.2226 m, z=0.2359 m, yaw=0.2053 deg, dominant=x, z, y, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2472 m, x=0.1882 m, y=0.0413 m, z=0.1549 m, yaw=0.4851 deg, dominant=yaw, samples=48 | pos=0.3375 m, x=0.2892 m, y=0.1319 m, z=0.1136 m, yaw=0.8946 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8563 m, x=0.0544 m, y=0.0660 m, z=0.8520 m, yaw=0.3961 deg, dominant=z, samples=208 | pos=1.0804 m, x=0.1046 m, y=0.1411 m, z=1.0660 m, yaw=0.2440 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4193 m, x=0.0287 m, y=0.0946 m, z=0.4075 m, yaw=0.1257 deg, dominant=z, samples=102 | pos=2.1219 m, x=0.1862 m, y=0.1373 m, z=2.1092 m, yaw=0.1339 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9138 m, x=0.6959 m, y=0.5705 m, z=0.1589 m, yaw=4.7299 deg, dominant=yaw, samples=176 | pos=2.6627 m, x=0.5999 m, y=0.6179 m, z=2.5195 m, yaw=4.6570 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2524 m, x=0.2354 m, y=0.0764 m, z=0.0492 m, yaw=1.2905 deg, dominant=yaw, samples=18 | pos=2.7995 m, x=0.4900 m, y=1.4856 m, z=2.3217 m, yaw=9.2322 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5114 m, x=1.7611 m, y=4.0863 m, z=0.7442 m, yaw=9.7016 deg, dominant=yaw, samples=202 | pos=6.0849 m, x=2.0312 m, y=5.4593 m, z=1.7597 m, yaw=3.7811 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8419 m, x=2.7193 m, y=0.8132 m, z=0.1426 m, yaw=20.3924 deg, dominant=yaw, samples=52 | pos=10.3296 m, x=6.7108 m, y=7.8028 m, z=0.8848 m, yaw=27.8304 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8739 m, x=7.0339 m, y=3.4536 m, z=0.7708 m, yaw=24.4851 deg, dominant=yaw, samples=160 | pos=16.5201 m, x=16.1448 m, y=3.4795 m, z=0.3928 m, yaw=16.2049 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8739 m and dominant component(s): yaw.

## Perturbation-window analysis

No perturbation windows configured for this case.

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
