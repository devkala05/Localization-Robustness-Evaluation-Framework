# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6492**
- Robustness score, lower is better: **37.2225**
- Overall position RMSE: **29.1074 m**
- Overall max position error: **58.3213 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.734542` → `1723528521.661798`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=2.1259 m, x=0.2478 m, y=0.3246 m, z=2.0864 m, yaw=0.4754 deg, dominant=z, samples=2282 | pos=2.1271 m, x=0.2463 m, y=0.3268 m, z=2.0874 m, yaw=0.4930 deg, dominant=z, samples=2282 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1267 m, x=0.0785 m, y=0.0962 m, z=0.0253 m, yaw=0.2776 deg, dominant=yaw, samples=166 | pos=0.1413 m, x=0.0990 m, y=0.0977 m, z=0.0247 m, yaw=0.2746 deg, dominant=yaw, samples=166 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.2200 m, x=0.1066 m, y=0.1918 m, z=0.0152 m, yaw=0.9139 deg, dominant=yaw, samples=120 | pos=0.1459 m, x=0.0908 m, y=0.1106 m, z=0.0283 m, yaw=1.3412 deg, dominant=yaw, samples=120 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6120 m, x=0.5703 m, y=0.1572 m, z=0.1570 m, yaw=0.3191 deg, dominant=x, samples=272 | pos=0.5252 m, x=0.4961 m, y=0.0657 m, z=0.1594 m, yaw=0.3171 deg, dominant=x, samples=272 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=1.0850 m, x=0.2175 m, y=0.0581 m, z=1.0614 m, yaw=0.4686 deg, dominant=z, samples=222 | pos=0.6607 m, x=0.1563 m, y=0.1453 m, z=0.6253 m, yaw=0.4846 deg, dominant=z, samples=222 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.7359 m, x=0.1361 m, y=0.0554 m, z=0.7211 m, yaw=0.2477 deg, dominant=z, samples=154 | pos=1.9139 m, x=0.1449 m, y=0.2576 m, z=1.8909 m, yaw=0.3295 deg, dominant=z, samples=154 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.3682 m, x=0.1391 m, y=0.0839 m, z=0.3304 m, yaw=0.4388 deg, dominant=yaw, samples=102 | pos=2.8021 m, x=0.1710 m, y=0.3169 m, z=2.7788 m, yaw=0.4468 deg, dominant=z, samples=102 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.4566 m, x=0.1987 m, y=0.1175 m, z=0.3939 m, yaw=0.4026 deg, dominant=yaw, z, samples=452 | pos=3.3861 m, x=0.1735 m, y=0.4935 m, z=3.3455 m, yaw=0.5253 deg, dominant=z, samples=452 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.1761 m, x=0.0982 m, y=0.1106 m, z=0.0956 m, yaw=0.1453 deg, dominant=yaw, samples=216 | pos=3.5579 m, x=0.3608 m, y=0.6291 m, z=3.4832 m, yaw=0.3740 deg, dominant=z, samples=216 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.1296 m, x=0.5640 m, y=0.3701 m, z=0.9060 m, yaw=4.2394 deg, dominant=yaw, samples=362 | pos=2.7463 m, x=0.5279 m, y=0.8265 m, z=2.5653 m, yaw=4.0140 deg, dominant=yaw, samples=362 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2805 m, x=0.2745 m, y=0.0394 m, z=0.0419 m, yaw=1.1129 deg, dominant=yaw, samples=36 | pos=2.3811 m, x=0.1435 m, y=1.6184 m, z=1.7407 m, yaw=8.2092 deg, dominant=yaw, samples=36 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2873 m, x=1.7069 m, y=3.9232 m, z=0.2752 m, yaw=9.2707 deg, dominant=yaw, samples=436 | pos=5.8695 m, x=1.7193 m, y=5.3991 m, z=1.5313 m, yaw=3.6498 deg, dominant=y, samples=436 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8148 m, x=2.6772 m, y=0.8430 m, z=0.2128 m, yaw=20.7026 deg, dominant=yaw, samples=110 | pos=9.9083 m, x=6.2742 m, y=7.6124 m, z=0.9276 m, yaw=27.8017 deg, dominant=yaw, samples=110 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=8.0291 m, x=7.1973 m, y=3.4812 m, z=0.7391 m, yaw=24.6343 deg, dominant=yaw, samples=330 | pos=16.1730 m, x=15.8118 m, y=3.3874 m, z=0.2776 m, yaw=16.0055 deg, dominant=yaw, x, samples=330 |

**Most affected segment:** `straight_road` with relative position RMSE 8.0291 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | yaw_gyro_bias | imu/bias | 1621218780.000000 → 1621218785.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | forward_accel_bias | imu/bias | 1621218800.000000 → 1621218805.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
