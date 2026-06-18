# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6452**
- Robustness score, lower is better: **37.1739**
- Overall position RMSE: **29.0515 m**
- Overall max position error: **58.3504 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.733569` → `1723528521.661654`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.3573 m, x=0.2077 m, y=0.1973 m, z=0.2135 m, yaw=0.4895 deg, dominant=yaw, samples=2260 | pos=0.3585 m, x=0.2069 m, y=0.1991 m, z=0.2146 m, yaw=0.4959 deg, dominant=yaw, samples=2260 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1326 m, x=0.0817 m, y=0.1020 m, z=0.0224 m, yaw=0.3272 deg, dominant=yaw, samples=168 | pos=0.1334 m, x=0.0956 m, y=0.0873 m, z=0.0322 m, yaw=0.3135 deg, dominant=yaw, samples=168 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2172 m, x=0.1136 m, y=0.1841 m, z=0.0198 m, yaw=0.9090 deg, dominant=yaw, samples=120 | pos=0.1409 m, x=0.0806 m, y=0.1043 m, z=0.0498 m, yaw=1.4074 deg, dominant=yaw, samples=120 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.5580 m, x=0.5290 m, y=0.1283 m, z=0.1228 m, yaw=0.3313 deg, dominant=x, samples=262 | pos=0.4977 m, x=0.4807 m, y=0.0592 m, z=0.1146 m, yaw=0.2566 deg, dominant=x, samples=262 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1376 m, x=0.0940 m, y=0.0650 m, z=0.0766 m, yaw=0.2781 deg, dominant=yaw, samples=216 | pos=0.3153 m, x=0.1159 m, y=0.0620 m, z=0.2866 m, yaw=0.3775 deg, dominant=yaw, samples=216 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1571 m, x=0.1512 m, y=0.0243 m, z=0.0350 m, yaw=0.4609 deg, dominant=yaw, samples=152 | pos=0.4290 m, x=0.1457 m, y=0.1284 m, z=0.3825 m, yaw=0.3954 deg, dominant=yaw, z, samples=152 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.1791 m, x=0.1627 m, y=0.0738 m, z=0.0134 m, yaw=0.3583 deg, dominant=yaw, samples=100 | pos=0.4481 m, x=0.1418 m, y=0.1465 m, z=0.3991 m, yaw=0.4428 deg, dominant=yaw, z, samples=100 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2201 m, x=0.1546 m, y=0.1082 m, z=0.1134 m, yaw=0.2904 deg, dominant=yaw, samples=452 | pos=0.4360 m, x=0.0987 m, y=0.3031 m, z=0.2975 m, yaw=0.3970 deg, dominant=yaw, samples=452 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.1622 m, x=0.0995 m, y=0.1066 m, z=0.0711 m, yaw=0.1592 deg, dominant=yaw, samples=216 | pos=0.4823 m, x=0.2509 m, y=0.3899 m, z=0.1328 m, yaw=0.3637 deg, dominant=y, yaw, samples=216 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6878 m, x=0.5765 m, y=0.3727 m, z=0.0420 m, yaw=4.1261 deg, dominant=yaw, samples=364 | pos=0.7951 m, x=0.5028 m, y=0.6141 m, z=0.0464 m, yaw=3.8894 deg, dominant=yaw, samples=364 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2888 m, x=0.2838 m, y=0.0470 m, z=0.0252 m, yaw=1.2066 deg, dominant=yaw, samples=36 | pos=1.4098 m, x=0.2973 m, y=1.3765 m, z=0.0660 m, yaw=8.1799 deg, dominant=yaw, samples=36 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2826 m, x=1.7064 m, y=3.9279 m, z=0.0267 m, yaw=9.2586 deg, dominant=yaw, samples=440 | pos=5.4994 m, x=1.8565 m, y=5.1761 m, z=0.0698 m, yaw=3.5946 deg, dominant=y, samples=440 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8931 m, x=2.7655 m, y=0.8479 m, z=0.0539 m, yaw=20.9234 deg, dominant=yaw, samples=108 | pos=9.8857 m, x=6.5206 m, y=7.4300 m, z=0.0582 m, yaw=27.7767 deg, dominant=yaw, samples=108 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8030 m, x=7.0131 m, y=3.3841 m, z=0.4999 m, yaw=24.6373 deg, dominant=yaw, samples=332 | pos=16.1653 m, x=15.8131 m, y=3.3301 m, z=0.4128 m, yaw=15.8109 deg, dominant=x, yaw, samples=332 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8030 m and dominant component(s): yaw.

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
