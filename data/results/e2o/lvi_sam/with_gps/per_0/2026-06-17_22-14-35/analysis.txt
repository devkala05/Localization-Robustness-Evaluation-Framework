# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4080**
- Overall position RMSE: **29.2976 m**
- Overall max position error: **58.6161 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217219` → `1723528521.445402`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0704 m, x=0.2795 m, y=0.1604 m, z=1.0207 m, yaw=0.7483 deg, dominant=z, samples=536 | pos=1.0704 m, x=0.2795 m, y=0.1604 m, z=1.0207 m, yaw=0.7483 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2309 m, x=0.0204 m, y=0.0654 m, z=0.2204 m, yaw=0.4841 deg, dominant=yaw, samples=37 | pos=0.7702 m, x=0.2521 m, y=0.2012 m, z=0.6994 m, yaw=0.4188 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3706 m, x=0.2464 m, y=0.2708 m, z=0.0570 m, yaw=1.3805 deg, dominant=yaw, samples=29 | pos=1.0065 m, x=0.1230 m, y=0.3151 m, z=0.9479 m, yaw=2.7494 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6688 m, x=0.6358 m, y=0.1076 m, z=0.1776 m, yaw=0.4352 deg, dominant=x, samples=64 | pos=1.0519 m, x=0.6325 m, y=0.1456 m, z=0.8278 m, yaw=0.3099 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2249 m, x=0.0322 m, y=0.0669 m, z=0.2123 m, yaw=0.1555 deg, dominant=z, samples=54 | pos=0.5000 m, x=0.1088 m, y=0.1758 m, z=0.4552 m, yaw=0.3801 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1897 m, x=0.1404 m, y=0.0415 m, z=0.1206 m, yaw=0.1750 deg, dominant=yaw, samples=33 | pos=0.4015 m, x=0.2543 m, y=0.2104 m, z=0.2286 m, yaw=0.2173 deg, dominant=x, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2457 m, x=0.1866 m, y=0.0420 m, z=0.1542 m, yaw=0.4871 deg, dominant=yaw, samples=24 | pos=0.3370 m, x=0.2942 m, y=0.1223 m, z=0.1099 m, yaw=0.8995 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8558 m, x=0.0534 m, y=0.0649 m, z=0.8517 m, yaw=0.3974 deg, dominant=z, samples=104 | pos=1.0715 m, x=0.1089 m, y=0.1342 m, z=1.0574 m, yaw=0.2438 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.7485 m, x=0.0318 m, y=0.1163 m, z=0.7387 m, yaw=0.1292 deg, dominant=z, samples=51 | pos=2.0426 m, x=0.1934 m, y=0.1373 m, z=2.0288 m, yaw=0.1387 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9103 m, x=0.6955 m, y=0.5674 m, z=0.1515 m, yaw=4.7274 deg, dominant=yaw, samples=88 | pos=2.6256 m, x=0.5969 m, y=0.6129 m, z=2.4823 m, yaw=4.6515 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2535 m, x=0.2376 m, y=0.0753 m, z=0.0465 m, yaw=1.2889 deg, dominant=yaw, samples=9 | pos=2.7569 m, x=0.4839 m, y=1.4724 m, z=2.2800 m, yaw=9.2181 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4340 m, x=1.6946 m, y=3.9935 m, z=0.9171 m, yaw=9.8512 deg, dominant=yaw, samples=101 | pos=5.9610 m, x=1.9629 m, y=5.3598 m, z=1.7187 m, yaw=3.8958 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8397 m, x=2.7173 m, y=0.8112 m, z=0.1493 m, yaw=20.3487 deg, dominant=yaw, samples=26 | pos=10.3234 m, x=6.7250 m, y=7.7832 m, z=0.8764 m, yaw=27.8244 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8590 m, x=7.0225 m, y=3.4452 m, z=0.7613 m, yaw=24.4972 deg, dominant=yaw, samples=80 | pos=16.5251 m, x=16.1522 m, y=3.4691 m, z=0.3867 m, yaw=16.1930 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8590 m and dominant component(s): yaw.

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
