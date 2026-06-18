# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6452**
- Robustness score, lower is better: **37.2815**
- Overall position RMSE: **29.1387 m**
- Overall max position error: **58.2931 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.734632` → `1723528521.664298`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.3690 m, x=0.2295 m, y=0.2388 m, z=0.1626 m, yaw=0.4630 deg, dominant=yaw, samples=2252 | pos=0.3702 m, x=0.2286 m, y=0.2407 m, z=0.1638 m, yaw=0.4760 deg, dominant=yaw, samples=2252 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1264 m, x=0.0727 m, y=0.0991 m, z=0.0295 m, yaw=0.2659 deg, dominant=yaw, samples=160 | pos=0.1212 m, x=0.0751 m, y=0.0909 m, z=0.0283 m, yaw=0.2605 deg, dominant=yaw, samples=160 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2149 m, x=0.0938 m, y=0.1921 m, z=0.0224 m, yaw=0.9853 deg, dominant=yaw, samples=120 | pos=0.1381 m, x=0.0798 m, y=0.1071 m, z=0.0348 m, yaw=1.3399 deg, dominant=yaw, samples=120 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6045 m, x=0.5787 m, y=0.1466 m, z=0.0954 m, yaw=0.2907 deg, dominant=x, samples=266 | pos=0.5227 m, x=0.5089 m, y=0.0655 m, z=0.0998 m, yaw=0.2827 deg, dominant=x, samples=266 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1363 m, x=0.1043 m, y=0.0730 m, z=0.0486 m, yaw=0.2601 deg, dominant=yaw, samples=218 | pos=0.2573 m, x=0.1096 m, y=0.0688 m, z=0.2224 m, yaw=0.3636 deg, dominant=yaw, samples=218 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1605 m, x=0.1552 m, y=0.0355 m, z=0.0203 m, yaw=0.1982 deg, dominant=yaw, samples=148 | pos=0.3451 m, x=0.1674 m, y=0.1482 m, z=0.2628 m, yaw=0.2972 deg, dominant=yaw, samples=148 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.1737 m, x=0.1572 m, y=0.0727 m, z=0.0130 m, yaw=0.6370 deg, dominant=yaw, samples=100 | pos=0.3636 m, x=0.1381 m, y=0.1859 m, z=0.2803 m, yaw=0.6739 deg, dominant=yaw, samples=100 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2357 m, x=0.1863 m, y=0.1356 m, z=0.0495 m, yaw=0.2638 deg, dominant=yaw, samples=446 | pos=0.4508 m, x=0.1183 m, y=0.3659 m, z=0.2353 m, yaw=0.4177 deg, dominant=yaw, samples=446 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.1603 m, x=0.1147 m, y=0.0963 m, z=0.0572 m, yaw=0.1703 deg, dominant=yaw, samples=216 | pos=0.5849 m, x=0.3072 m, y=0.4816 m, z=0.1257 m, yaw=0.4220 deg, dominant=y, samples=216 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.7112 m, x=0.6073 m, y=0.3653 m, z=0.0594 m, yaw=4.2372 deg, dominant=yaw, samples=358 | pos=0.8576 m, x=0.5246 m, y=0.6776 m, z=0.0311 m, yaw=4.0027 deg, dominant=yaw, samples=358 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2832 m, x=0.2776 m, y=0.0495 m, z=0.0262 m, yaw=1.2169 deg, dominant=yaw, samples=36 | pos=1.4500 m, x=0.2473 m, y=1.4284 m, z=0.0309 m, yaw=8.1600 deg, dominant=yaw, samples=36 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2858 m, x=1.7383 m, y=3.9174 m, z=0.0279 m, yaw=9.3364 deg, dominant=yaw, samples=428 | pos=5.5379 m, x=1.8511 m, y=5.2192 m, z=0.0373 m, yaw=3.6755 deg, dominant=y, samples=428 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9100 m, x=2.7805 m, y=0.8569 m, z=0.0497 m, yaw=20.8359 deg, dominant=yaw, samples=110 | pos=9.9117 m, x=6.5404 m, y=7.4474 m, z=0.0378 m, yaw=27.8601 deg, dominant=yaw, samples=110 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.7653 m, x=6.9601 m, y=3.4174 m, z=0.4230 m, yaw=24.6296 deg, dominant=yaw, samples=336 | pos=16.1560 m, x=15.8047 m, y=3.3315 m, z=0.3601 m, yaw=15.8670 deg, dominant=yaw, x, samples=336 |

**Most affected segment:** `straight_road` with relative position RMSE 7.7653 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | low_light_section | camera_right/low_light | 1621218780.000000 → 1621218788.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | rain_streaks_section | camera_right/rain | 1621218800.000000 → 1621218808.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
