# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3232**
- Robustness score, lower is better: **37.0509**
- Overall position RMSE: **28.9388 m**
- Overall max position error: **57.9098 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.738809` → `1723528521.593704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7063 m, x=0.2735 m, y=0.4491 m, z=0.4716 m, yaw=0.5004 deg, dominant=yaw, z, samples=1133 | pos=0.7071 m, x=0.2732 m, y=0.4508 m, z=0.4713 m, yaw=0.5572 deg, dominant=yaw, samples=1133 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1953 m, x=0.1165 m, y=0.1218 m, z=0.0986 m, yaw=0.8048 deg, dominant=yaw, samples=82 | pos=0.3802 m, x=0.0654 m, y=0.2521 m, z=0.2770 m, yaw=0.3878 deg, dominant=yaw, samples=82 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1453 m, x=0.0876 m, y=0.0481 m, z=0.1055 m, yaw=0.5311 deg, dominant=yaw, samples=61 | pos=0.5276 m, x=0.1503 m, y=0.1670 m, z=0.4774 m, yaw=0.5709 deg, dominant=yaw, samples=61 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.4682 m, x=0.4228 m, y=0.1333 m, z=0.1506 m, yaw=0.2608 deg, dominant=x, samples=134 | pos=0.4930 m, x=0.3641 m, y=0.0717 m, z=0.3246 m, yaw=0.3212 deg, dominant=x, samples=134 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3807 m, x=0.2864 m, y=0.0429 m, z=0.2471 m, yaw=0.2703 deg, dominant=x, yaw, samples=107 | pos=0.3788 m, x=0.3559 m, y=0.0479 m, z=0.1205 m, yaw=0.3955 deg, dominant=yaw, samples=107 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2023 m, x=0.1376 m, y=0.1233 m, z=0.0825 m, yaw=0.2391 deg, dominant=yaw, samples=76 | pos=0.4277 m, x=0.3584 m, y=0.2198 m, z=0.0787 m, yaw=0.6684 deg, dominant=yaw, samples=76 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2040 m, x=0.1477 m, y=0.1401 m, z=0.0137 m, yaw=0.7354 deg, dominant=yaw, samples=50 | pos=0.4790 m, x=0.2337 m, y=0.3914 m, z=0.1470 m, yaw=0.8547 deg, dominant=yaw, samples=50 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7261 m, x=0.1988 m, y=0.3186 m, z=0.6214 m, yaw=1.3588 deg, dominant=yaw, samples=227 | pos=0.8922 m, x=0.1699 m, y=0.6987 m, z=0.5281 m, yaw=0.6500 deg, dominant=y, yaw, samples=227 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3380 m, x=0.2148 m, y=0.2359 m, z=0.1116 m, yaw=0.2123 deg, dominant=y, x, samples=107 | pos=1.3685 m, x=0.4058 m, y=0.8724 m, z=0.9732 m, yaw=0.6926 deg, dominant=z, samples=107 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6794 m, x=0.5834 m, y=0.3348 m, z=0.0956 m, yaw=4.0868 deg, dominant=yaw, samples=180 | pos=1.4769 m, x=0.6114 m, y=0.8948 m, z=1.0034 m, yaw=3.7827 deg, dominant=yaw, samples=180 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2505 m, x=0.2473 m, y=0.0367 m, z=0.0149 m, yaw=0.7657 deg, dominant=yaw, samples=20 | pos=1.7839 m, x=0.0972 m, y=1.5762 m, z=0.8298 m, yaw=7.6880 deg, dominant=yaw, samples=20 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2226 m, x=1.7422 m, y=3.8399 m, z=0.2239 m, yaw=8.4997 deg, dominant=yaw, samples=215 | pos=5.5741 m, x=1.6955 m, y=5.2685 m, z=0.6621 m, yaw=3.5927 deg, dominant=y, samples=215 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.7256 m, x=2.5402 m, y=0.9833 m, z=0.0963 m, yaw=20.5093 deg, dominant=yaw, samples=55 | pos=9.8014 m, x=6.2386 m, y=7.5529 m, z=0.3173 m, yaw=27.2566 deg, dominant=yaw, samples=55 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9042 m, x=7.1295 m, y=3.4109 m, z=0.1115 m, yaw=24.9643 deg, dominant=yaw, samples=166 | pos=16.0450 m, x=15.6806 m, y=3.3966 m, z=0.1597 m, yaw=16.0250 deg, dominant=yaw, x, samples=166 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9042 m and dominant component(s): yaw.

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
