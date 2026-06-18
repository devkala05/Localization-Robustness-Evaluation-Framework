# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3241**
- Robustness score, lower is better: **37.0682**
- Overall position RMSE: **28.9576 m**
- Overall max position error: **58.0698 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.733421` → `1723528521.623703`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.6544 m, x=0.2593 m, y=0.3702 m, z=0.4732 m, yaw=0.4527 deg, dominant=z, yaw, samples=1134 | pos=0.6550 m, x=0.2589 m, y=0.3719 m, z=0.4729 m, yaw=0.5079 deg, dominant=yaw, z, samples=1134 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2143 m, x=0.1267 m, y=0.1422 m, z=0.0983 m, yaw=0.7933 deg, dominant=yaw, samples=85 | pos=0.3683 m, x=0.0735 m, y=0.2316 m, z=0.2768 m, yaw=0.4914 deg, dominant=yaw, samples=85 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1456 m, x=0.0882 m, y=0.0467 m, z=0.1060 m, yaw=0.4746 deg, dominant=yaw, samples=60 | pos=0.5208 m, x=0.1385 m, y=0.1541 m, z=0.4778 m, yaw=0.5059 deg, dominant=yaw, z, samples=60 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6243 m, x=0.5847 m, y=0.1626 m, z=0.1462 m, yaw=0.7523 deg, dominant=yaw, samples=133 | pos=0.5121 m, x=0.3916 m, y=0.0639 m, z=0.3237 m, yaw=0.2614 deg, dominant=x, samples=133 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2731 m, x=0.1088 m, y=0.0647 m, z=0.2420 m, yaw=0.2724 deg, dominant=yaw, samples=111 | pos=0.3578 m, x=0.3350 m, y=0.0379 m, z=0.1199 m, yaw=0.3576 deg, dominant=yaw, x, samples=111 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2175 m, x=0.1697 m, y=0.1088 m, z=0.0817 m, yaw=0.2713 deg, dominant=yaw, samples=76 | pos=0.3775 m, x=0.3340 m, y=0.1578 m, z=0.0779 m, yaw=0.5945 deg, dominant=yaw, samples=76 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.3246 m, x=0.2755 m, y=0.1708 m, z=0.0171 m, yaw=0.7586 deg, dominant=yaw, samples=49 | pos=0.3991 m, x=0.1981 m, y=0.3137 m, z=0.1471 m, yaw=0.6741 deg, dominant=yaw, samples=49 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6971 m, x=0.2560 m, y=0.1771 m, z=0.6238 m, yaw=0.2596 deg, dominant=z, samples=226 | pos=0.8122 m, x=0.1564 m, y=0.5947 m, z=0.5306 m, yaw=0.6002 deg, dominant=yaw, y, samples=226 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2984 m, x=0.1941 m, y=0.1956 m, z=0.1147 m, yaw=0.2310 deg, dominant=yaw, samples=110 | pos=1.2498 m, x=0.3541 m, y=0.6991 m, z=0.9736 m, yaw=0.6297 deg, dominant=z, samples=110 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6439 m, x=0.5555 m, y=0.3103 m, z=0.0986 m, yaw=3.9108 deg, dominant=yaw, samples=180 | pos=1.3627 m, x=0.5707 m, y=0.7231 m, z=1.0042 m, yaw=3.6898 deg, dominant=yaw, samples=180 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2463 m, x=0.2430 m, y=0.0376 m, z=0.0145 m, yaw=0.7672 deg, dominant=yaw, samples=19 | pos=1.6300 m, x=0.1466 m, y=1.3949 m, z=0.8305 m, yaw=7.5794 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2347 m, x=1.7480 m, y=3.8507 m, z=0.2228 m, yaw=8.4729 deg, dominant=yaw, samples=217 | pos=5.4498 m, x=1.7676 m, y=5.1125 m, z=0.6621 m, yaw=3.5155 deg, dominant=y, samples=217 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.7968 m, x=2.7171 m, y=0.6559 m, z=0.0970 m, yaw=20.7022 deg, dominant=yaw, samples=56 | pos=9.7641 m, x=6.3064 m, y=7.4475 m, z=0.3189 m, yaw=27.1353 deg, dominant=yaw, samples=56 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8813 m, x=7.1615 m, y=3.2886 m, z=0.1118 m, yaw=24.1113 deg, dominant=yaw, samples=164 | pos=16.0545 m, x=15.7005 m, y=3.3487 m, z=0.1595 m, yaw=16.0363 deg, dominant=yaw, x, samples=164 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8813 m and dominant component(s): yaw.

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
