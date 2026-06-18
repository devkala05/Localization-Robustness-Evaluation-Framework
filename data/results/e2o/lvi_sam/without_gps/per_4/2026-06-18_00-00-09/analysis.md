# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3058**
- Robustness score, lower is better: **37.4407**
- Overall position RMSE: **29.2552 m**
- Overall max position error: **58.6123 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217208` → `1723528521.443991`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0792 m, x=0.2772 m, y=0.1641 m, z=1.0300 m, yaw=0.7502 deg, dominant=z, samples=1072 | pos=1.0792 m, x=0.2772 m, y=0.1641 m, z=1.0300 m, yaw=0.7502 deg, dominant=z, samples=1072 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2301 m, x=0.0202 m, y=0.0658 m, z=0.2196 m, yaw=0.4798 deg, dominant=yaw, samples=74 | pos=0.7701 m, x=0.2540 m, y=0.2014 m, z=0.6985 m, yaw=0.4148 deg, dominant=z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3717 m, x=0.2492 m, y=0.2700 m, z=0.0563 m, yaw=1.3831 deg, dominant=yaw, samples=58 | pos=1.0055 m, x=0.1245 m, y=0.3147 m, z=0.9468 m, yaw=2.7409 deg, dominant=yaw, samples=58 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6664 m, x=0.6333 m, y=0.1090 m, z=0.1765 m, yaw=0.4339 deg, dominant=x, samples=128 | pos=1.0499 m, x=0.6303 m, y=0.1476 m, z=0.8265 m, yaw=0.3096 deg, dominant=z, samples=128 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.1804 m, x=0.0331 m, y=0.0717 m, z=0.1622 m, yaw=0.1522 deg, dominant=z, yaw, samples=102 | pos=0.5135 m, x=0.1056 m, y=0.1833 m, z=0.4679 m, yaw=0.3827 deg, dominant=z, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1985 m, x=0.1300 m, y=0.0397 m, z=0.1447 m, yaw=0.1798 deg, dominant=yaw, samples=72 | pos=0.4077 m, x=0.2414 m, y=0.2242 m, z=0.2401 m, yaw=0.2056 deg, dominant=x, z, y, samples=72 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2465 m, x=0.1875 m, y=0.0418 m, z=0.1545 m, yaw=0.4923 deg, dominant=yaw, samples=48 | pos=0.3367 m, x=0.2889 m, y=0.1331 m, z=0.1103 m, yaw=0.9009 deg, dominant=yaw, samples=48 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8498 m, x=0.0496 m, y=0.0663 m, z=0.8457 m, yaw=0.3914 deg, dominant=z, samples=208 | pos=1.0668 m, x=0.1005 m, y=0.1395 m, z=1.0529 m, yaw=0.2381 deg, dominant=z, samples=208 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.4115 m, x=0.0301 m, y=0.0949 m, z=0.3993 m, yaw=0.1264 deg, dominant=z, samples=102 | pos=2.0956 m, x=0.1786 m, y=0.1395 m, z=2.0833 m, yaw=0.1351 deg, dominant=z, samples=102 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9151 m, x=0.6981 m, y=0.5721 m, z=0.1510 m, yaw=4.7377 deg, dominant=yaw, samples=176 | pos=2.6274 m, x=0.6058 m, y=0.6200 m, z=2.4803 m, yaw=4.6621 deg, dominant=yaw, samples=176 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2521 m, x=0.2362 m, y=0.0736 m, z=0.0485 m, yaw=1.2811 deg, dominant=yaw, samples=18 | pos=2.7703 m, x=0.5005 m, y=1.4864 m, z=2.2836 m, yaw=9.2369 deg, dominant=yaw, samples=18 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5056 m, x=1.7611 m, y=4.0738 m, z=0.7765 m, yaw=9.7091 deg, dominant=yaw, samples=202 | pos=6.0627 m, x=2.0410 m, y=5.4494 m, z=1.7016 m, yaw=3.7832 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8399 m, x=2.7151 m, y=0.8209 m, z=0.1390 m, yaw=20.3604 deg, dominant=yaw, samples=52 | pos=10.3298 m, x=6.7233 m, y=7.7998 m, z=0.8157 m, yaw=27.8125 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8530 m, x=7.0163 m, y=3.4510 m, z=0.7284 m, yaw=24.4940 deg, dominant=yaw, samples=160 | pos=16.5210 m, x=16.1467 m, y=3.4779 m, z=0.3641 m, yaw=16.1973 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8530 m and dominant component(s): yaw.

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
