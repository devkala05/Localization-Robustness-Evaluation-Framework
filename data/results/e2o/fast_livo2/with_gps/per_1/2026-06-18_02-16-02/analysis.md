# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3243**
- Robustness score, lower is better: **40.9143**
- Overall position RMSE: **30.6731 m**
- Overall max position error: **82.3500 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.734563` → `1723528521.613704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.5976 m, x=0.2157 m, y=0.3011 m, z=0.4689 m, yaw=0.4105 deg, dominant=z, samples=1134 | pos=0.5981 m, x=0.2157 m, y=0.3027 m, z=0.4686 m, yaw=0.4556 deg, dominant=z, yaw, samples=1134 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1849 m, x=0.0927 m, y=0.1252 m, z=0.0995 m, yaw=0.7016 deg, dominant=yaw, samples=80 | pos=0.3601 m, x=0.0671 m, y=0.2192 m, z=0.2778 m, yaw=0.3931 deg, dominant=yaw, samples=80 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1485 m, x=0.0915 m, y=0.0501 m, z=0.1057 m, yaw=0.5322 deg, dominant=yaw, samples=59 | pos=0.5100 m, x=0.1236 m, y=0.1297 m, z=0.4774 m, yaw=0.5617 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.4596 m, x=0.4210 m, y=0.1036 m, z=0.1523 m, yaw=0.2612 deg, dominant=x, samples=133 | pos=0.5025 m, x=0.3813 m, y=0.0574 m, z=0.3221 m, yaw=0.2528 deg, dominant=x, samples=133 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3674 m, x=0.2679 m, y=0.0339 m, z=0.2492 m, yaw=0.2732 deg, dominant=yaw, x, z, samples=110 | pos=0.3263 m, x=0.3009 m, y=0.0339 m, z=0.1216 m, yaw=0.3581 deg, dominant=yaw, samples=110 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2078 m, x=0.1651 m, y=0.0945 m, z=0.0835 m, yaw=0.2931 deg, dominant=yaw, samples=80 | pos=0.3319 m, x=0.2915 m, y=0.1371 m, z=0.0797 m, yaw=0.5199 deg, dominant=yaw, samples=80 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2213 m, x=0.1798 m, y=0.1283 m, z=0.0145 m, yaw=0.6768 deg, dominant=yaw, samples=51 | pos=0.3658 m, x=0.2068 m, y=0.2631 m, z=0.1477 m, yaw=0.7175 deg, dominant=yaw, samples=51 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6642 m, x=0.1682 m, y=0.1672 m, z=0.6205 m, yaw=0.3290 deg, dominant=z, samples=227 | pos=0.7435 m, x=0.1399 m, y=0.5047 m, z=0.5278 m, yaw=0.5014 deg, dominant=z, y, yaw, samples=227 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2676 m, x=0.1343 m, y=0.2000 m, z=0.1165 m, yaw=0.1948 deg, dominant=y, yaw, samples=107 | pos=1.1254 m, x=0.1822 m, y=0.5315 m, z=0.9751 m, yaw=0.4310 deg, dominant=z, samples=107 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6912 m, x=0.5846 m, y=0.3554 m, z=0.0983 m, yaw=3.9404 deg, dominant=yaw, samples=181 | pos=1.2973 m, x=0.5217 m, y=0.6347 m, z=1.0040 m, yaw=3.8038 deg, dominant=yaw, samples=181 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2606 m, x=0.2574 m, y=0.0378 m, z=0.0150 m, yaw=0.7998 deg, dominant=yaw, samples=19 | pos=1.6326 m, x=0.3988 m, y=1.3481 m, z=0.8300 m, yaw=7.8134 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.1868 m, x=1.6193 m, y=3.8546 m, z=0.2230 m, yaw=8.4914 deg, dominant=yaw, samples=216 | pos=5.4442 m, x=1.8532 m, y=5.0760 m, z=0.6624 m, yaw=3.4442 deg, dominant=y, samples=216 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.7617 m, x=2.6826 m, y=0.6486 m, z=0.0972 m, yaw=20.7494 deg, dominant=yaw, samples=56 | pos=9.7856 m, x=6.3423 m, y=7.4453 m, z=0.3188 m, yaw=26.9707 deg, dominant=yaw, samples=56 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8608 m, x=7.1345 m, y=3.2983 m, z=0.1119 m, yaw=24.0727 deg, dominant=yaw, samples=167 | pos=16.0618 m, x=15.7050 m, y=3.3629 m, z=0.1595 m, yaw=15.8940 deg, dominant=yaw, x, samples=167 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8608 m and dominant component(s): yaw.

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
