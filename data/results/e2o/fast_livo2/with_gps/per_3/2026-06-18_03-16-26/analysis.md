# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3223**
- Robustness score, lower is better: **56.6928**
- Overall position RMSE: **47.4382 m**
- Overall max position error: **124.0178 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.736961` → `1723528521.633703`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.6754 m, x=0.2597 m, y=0.4063 m, z=0.4730 m, yaw=0.4734 deg, dominant=yaw, z, samples=1128 | pos=0.6762 m, x=0.2597 m, y=0.4080 m, z=0.4727 m, yaw=0.5308 deg, dominant=yaw, samples=1128 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1895 m, x=0.1088 m, y=0.1194 m, z=0.0990 m, yaw=0.7342 deg, dominant=yaw, samples=80 | pos=0.3978 m, x=0.0656 m, y=0.2777 m, z=0.2772 m, yaw=0.4433 deg, dominant=yaw, samples=80 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1446 m, x=0.0916 m, y=0.0367 m, z=0.1057 m, yaw=0.4836 deg, dominant=yaw, samples=59 | pos=0.5296 m, x=0.1523 m, y=0.1713 m, z=0.4775 m, yaw=0.5419 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.4493 m, x=0.4083 m, y=0.1107 m, z=0.1513 m, yaw=0.2617 deg, dominant=x, samples=132 | pos=0.4818 m, x=0.3501 m, y=0.0706 m, z=0.3234 m, yaw=0.3246 deg, dominant=x, yaw, z, samples=132 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3900 m, x=0.2964 m, y=0.0438 m, z=0.2497 m, yaw=0.3057 deg, dominant=yaw, x, samples=109 | pos=0.3914 m, x=0.3699 m, y=0.0422 m, z=0.1207 m, yaw=0.3913 deg, dominant=yaw, x, samples=109 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1997 m, x=0.1381 m, y=0.1182 m, z=0.0827 m, yaw=0.2407 deg, dominant=yaw, samples=76 | pos=0.4334 m, x=0.3793 m, y=0.1945 m, z=0.0789 m, yaw=0.6139 deg, dominant=yaw, samples=76 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.1899 m, x=0.1290 m, y=0.1386 m, z=0.0144 m, yaw=0.5714 deg, dominant=yaw, samples=48 | pos=0.4558 m, x=0.2497 m, y=0.3513 m, z=0.1481 m, yaw=0.6925 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7116 m, x=0.3068 m, y=0.1591 m, z=0.6221 m, yaw=0.2986 deg, dominant=z, samples=226 | pos=0.8540 m, x=0.1724 m, y=0.6476 m, z=0.5292 m, yaw=0.6170 deg, dominant=y, yaw, samples=226 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2907 m, x=0.1862 m, y=0.1907 m, z=0.1161 m, yaw=0.2516 deg, dominant=yaw, samples=108 | pos=1.2779 m, x=0.3341 m, y=0.7560 m, z=0.9747 m, yaw=0.6190 deg, dominant=z, samples=108 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6975 m, x=0.5971 m, y=0.3475 m, z=0.0954 m, yaw=4.0475 deg, dominant=yaw, samples=179 | pos=1.3993 m, x=0.5516 m, y=0.8041 m, z=1.0036 m, yaw=3.7850 deg, dominant=yaw, samples=179 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2541 m, x=0.2511 m, y=0.0359 m, z=0.0150 m, yaw=0.7883 deg, dominant=yaw, samples=19 | pos=1.7338 m, x=0.1731 m, y=1.5124 m, z=0.8300 m, yaw=7.7247 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2539 m, x=1.7175 m, y=3.8852 m, z=0.2262 m, yaw=8.4983 deg, dominant=yaw, samples=221 | pos=5.5823 m, x=1.7626 m, y=5.2555 m, z=0.6597 m, yaw=3.4885 deg, dominant=y, samples=221 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.6578 m, x=2.4759 m, y=0.9617 m, z=0.0943 m, yaw=20.0778 deg, dominant=yaw, samples=54 | pos=9.7647 m, x=6.2174 m, y=7.5228 m, z=0.3186 m, yaw=27.0518 deg, dominant=yaw, samples=54 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9530 m, x=7.2154 m, y=3.3431 m, z=0.1116 m, yaw=24.0942 deg, dominant=yaw, samples=166 | pos=16.0435 m, x=15.6822 m, y=3.3820 m, z=0.1596 m, yaw=16.0312 deg, dominant=yaw, x, samples=166 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9530 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | imu_gaussian_noise | imu/gaussian_noise | 1621218788.000000 → 1621218794.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | imu_message_dropout | imu/dropout | 1621218812.000000 → 1621218817.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
