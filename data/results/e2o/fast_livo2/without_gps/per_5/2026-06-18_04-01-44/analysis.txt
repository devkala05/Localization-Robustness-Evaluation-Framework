# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6470**
- Robustness score, lower is better: **37.1632**
- Overall position RMSE: **29.0689 m**
- Overall max position error: **58.3932 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.734611` → `1723528521.661225`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=2.6262 m, x=0.3431 m, y=0.3738 m, z=2.5767 m, yaw=0.5128 deg, dominant=z, samples=2268 | pos=2.6273 m, x=0.3414 m, y=0.3760 m, z=2.5778 m, yaw=0.5416 deg, dominant=z, samples=2268 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1146 m, x=0.0590 m, y=0.0909 m, z=0.0372 m, yaw=0.2959 deg, dominant=yaw, samples=158 | pos=0.1273 m, x=0.0883 m, y=0.0890 m, z=0.0219 m, yaw=0.2839 deg, dominant=yaw, samples=158 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2292 m, x=0.1000 m, y=0.2050 m, z=0.0222 m, yaw=0.8993 deg, dominant=yaw, samples=120 | pos=0.1378 m, x=0.0841 m, y=0.1068 m, z=0.0224 m, yaw=1.3470 deg, dominant=yaw, samples=120 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6324 m, x=0.5871 m, y=0.1365 m, z=0.1910 m, yaw=0.3383 deg, dominant=x, samples=268 | pos=0.5539 m, x=0.5152 m, y=0.0607 m, z=0.1942 m, yaw=0.3151 deg, dominant=x, samples=268 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=1.3501 m, x=0.2010 m, y=0.1128 m, z=1.3303 m, yaw=0.3031 deg, dominant=z, samples=222 | pos=0.7884 m, x=0.1903 m, y=0.1217 m, z=0.7553 m, yaw=0.5606 deg, dominant=z, samples=222 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.9620 m, x=0.1501 m, y=0.0587 m, z=0.9484 m, yaw=0.3911 deg, dominant=z, samples=152 | pos=2.3790 m, x=0.1737 m, y=0.2743 m, z=2.3568 m, yaw=0.4430 deg, dominant=z, samples=152 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.4782 m, x=0.1490 m, y=0.0934 m, z=0.4447 m, yaw=0.3887 deg, dominant=z, samples=98 | pos=3.5216 m, x=0.1714 m, y=0.3619 m, z=3.4987 m, yaw=0.3768 deg, dominant=z, samples=98 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.5646 m, x=0.2753 m, y=0.1482 m, z=0.4701 m, yaw=0.1822 deg, dominant=z, samples=452 | pos=4.2692 m, x=0.2788 m, y=0.5844 m, z=4.2198 m, yaw=0.5517 deg, dominant=z, samples=452 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3312 m, x=0.1720 m, y=0.1064 m, z=0.2623 m, yaw=0.1393 deg, dominant=z, samples=218 | pos=4.2711 m, x=0.6343 m, y=0.7099 m, z=4.1637 m, yaw=0.6614 deg, dominant=z, samples=218 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.5792 m, x=0.5329 m, y=0.3399 m, z=1.4471 m, yaw=4.4036 deg, dominant=yaw, samples=360 | pos=2.8712 m, x=0.7608 m, y=0.8585 m, z=2.6321 m, yaw=4.0098 deg, dominant=yaw, samples=360 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2803 m, x=0.2730 m, y=0.0421 m, z=0.0475 m, yaw=1.0419 deg, dominant=yaw, samples=38 | pos=2.1527 m, x=0.3532 m, y=1.6121 m, z=1.3822 m, yaw=8.0124 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.3722 m, x=1.8457 m, y=3.9588 m, z=0.1939 m, yaw=9.2408 deg, dominant=yaw, samples=436 | pos=5.7712 m, x=1.5594 m, y=5.4115 m, z=1.2615 m, yaw=3.7226 deg, dominant=y, samples=436 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8076 m, x=2.6647 m, y=0.8376 m, z=0.2835 m, yaw=20.6127 deg, dominant=yaw, samples=106 | pos=9.7129 m, x=6.0215 m, y=7.5948 m, z=0.6332 m, yaw=27.7751 deg, dominant=yaw, samples=106 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9878 m, x=6.8787 m, y=3.5272 m, z=2.0115 m, yaw=24.6434 deg, dominant=yaw, samples=332 | pos=15.7702 m, x=15.3206 m, y=3.3127 m, z=1.7331 m, yaw=16.2040 deg, dominant=yaw, x, samples=332 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9878 m and dominant component(s): yaw.

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
