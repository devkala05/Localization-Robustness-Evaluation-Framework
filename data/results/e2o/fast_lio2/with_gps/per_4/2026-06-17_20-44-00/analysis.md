# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **36.9295**
- Overall position RMSE: **28.8113 m**
- Overall max position error: **58.0151 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521703` → `1723528521.653703`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.6976 m, x=0.2830 m, y=0.4295 m, z=0.4712 m, yaw=0.5206 deg, dominant=yaw, z, samples=1068 | pos=0.6967 m, x=0.2839 m, y=0.4274 m, z=0.4713 m, yaw=0.5269 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1781 m, x=0.0967 m, y=0.1120 m, z=0.0990 m, yaw=0.1791 deg, dominant=yaw, samples=74 | pos=0.3748 m, x=0.2146 m, y=0.1321 m, z=0.2774 m, yaw=0.3165 deg, dominant=yaw, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1589 m, x=0.0537 m, y=0.1056 m, z=0.1059 m, yaw=0.8207 deg, dominant=yaw, samples=59 | pos=0.6169 m, x=0.3386 m, y=0.1941 m, z=0.4777 m, yaw=1.0792 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6167 m, x=0.5888 m, y=0.1033 m, z=0.1515 m, yaw=0.3612 deg, dominant=x, samples=127 | pos=0.5659 m, x=0.4000 m, y=0.2364 m, z=0.3230 m, yaw=0.3279 deg, dominant=x, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3702 m, x=0.2691 m, y=0.0598 m, z=0.2471 m, yaw=0.1291 deg, dominant=x, z, samples=102 | pos=0.3912 m, x=0.2220 m, y=0.2980 m, z=0.1221 m, yaw=0.4302 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2256 m, x=0.1925 m, y=0.0836 m, z=0.0828 m, yaw=0.2881 deg, dominant=yaw, samples=73 | pos=0.4871 m, x=0.1796 m, y=0.4459 m, z=0.0790 m, yaw=0.4393 deg, dominant=y, yaw, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.3571 m, x=0.3258 m, y=0.1452 m, z=0.0170 m, yaw=0.5080 deg, dominant=yaw, samples=47 | pos=0.5793 m, x=0.1731 m, y=0.5328 m, z=0.1475 m, yaw=0.4472 deg, dominant=y, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6825 m, x=0.2720 m, y=0.1236 m, z=0.6137 m, yaw=0.1510 deg, dominant=z, samples=209 | pos=0.8680 m, x=0.1590 m, y=0.6753 m, z=0.5216 m, yaw=0.6761 deg, dominant=yaw, y, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3496 m, x=0.2130 m, y=0.2525 m, z=0.1146 m, yaw=0.1772 deg, dominant=y, samples=102 | pos=1.2804 m, x=0.4957 m, y=0.6683 m, z=0.9732 m, yaw=0.6748 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6986 m, x=0.5920 m, y=0.3572 m, z=0.0995 m, yaw=4.3640 deg, dominant=yaw, samples=175 | pos=1.4251 m, x=0.6320 m, y=0.7906 m, z=1.0031 m, yaw=3.9624 deg, dominant=yaw, samples=175 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2736 m, x=0.2600 m, y=0.0840 m, z=0.0145 m, yaw=1.0082 deg, dominant=yaw, samples=19 | pos=1.7590 m, x=0.1407 m, y=1.5442 m, z=0.8305 m, yaw=7.9088 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4946 m, x=2.0159 m, y=4.0109 m, z=0.2249 m, yaw=9.0497 deg, dominant=yaw, samples=202 | pos=5.7770 m, x=1.8793 m, y=5.4228 m, z=0.6598 m, yaw=3.8968 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8437 m, x=2.6899 m, y=0.9177 m, z=0.0948 m, yaw=20.5897 deg, dominant=yaw, samples=52 | pos=10.1784 m, x=6.6426 m, y=7.7054 m, z=0.3195 m, yaw=28.0241 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8807 m, x=6.9238 m, y=3.7621 m, z=0.1130 m, yaw=24.0961 deg, dominant=yaw, samples=160 | pos=16.2191 m, x=15.8970 m, y=3.2122 m, z=0.1589 m, yaw=16.7520 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8807 m and dominant component(s): yaw.

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
