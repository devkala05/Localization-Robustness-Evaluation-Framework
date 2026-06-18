# Localization Run Analysis

**Algorithm note:** RTAB-Map visual+ICP pipeline: raw/perturbed scan_cloud is sanitized, RTAB-Map icp_odometry produces /rtabmap/icp_odom, and the mapper consumes that odometry together with the right camera image/camera_info. It no longer launches FAST-LIO2 and does not subscribe to FAST-LIO2 /Odometry.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1192**
- Robustness score, lower is better: **36.4999**
- Overall position RMSE: **28.4848 m**
- Overall max position error: **60.4229 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.225290` → `1723528521.243394`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=2.4531 m, x=1.1124 m, y=1.9877 m, z=0.9107 m, yaw=2.1369 deg, dominant=yaw, y, samples=420 | pos=2.4531 m, x=1.1124 m, y=1.9877 m, z=0.9107 m, yaw=2.1369 deg, dominant=yaw, y, samples=420 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.5153 m, x=0.1993 m, y=0.2092 m, z=0.4267 m, yaw=0.5010 deg, dominant=yaw, samples=28 | pos=1.3216 m, x=0.1515 m, y=0.7123 m, z=1.1029 m, yaw=1.6765 deg, dominant=yaw, samples=28 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3726 m, x=0.1576 m, y=0.2280 m, z=0.2491 m, yaw=1.3049 deg, dominant=yaw, samples=24 | pos=2.0914 m, x=0.5538 m, y=0.7292 m, z=1.8803 m, yaw=1.2859 deg, dominant=z, samples=24 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=1.0387 m, x=0.4453 m, y=0.4961 m, z=0.7965 m, yaw=0.6049 deg, dominant=z, samples=50 | pos=1.3201 m, x=0.6690 m, y=0.5440 m, z=0.9995 m, yaw=2.7560 deg, dominant=yaw, samples=50 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.7084 m, x=0.1750 m, y=0.6500 m, z=0.2207 m, yaw=0.2594 deg, dominant=y, samples=40 | pos=1.8023 m, x=1.6054 m, y=0.7667 m, z=0.2885 m, yaw=2.7580 deg, dominant=yaw, samples=40 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.3742 m, x=0.0898 m, y=0.3231 m, z=0.1659 m, yaw=0.3969 deg, dominant=yaw, samples=26 | pos=2.3832 m, x=1.7240 m, y=1.5275 m, z=0.6116 m, yaw=1.9783 deg, dominant=yaw, samples=26 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.4602 m, x=0.3392 m, y=0.2818 m, z=0.1315 m, yaw=0.5073 deg, dominant=yaw, samples=20 | pos=2.8754 m, x=1.8861 m, y=1.9815 m, z=0.8856 m, yaw=1.0709 deg, dominant=y, x, samples=20 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=1.1359 m, x=0.7057 m, y=0.8751 m, z=0.1625 m, yaw=0.9951 deg, dominant=yaw, samples=80 | pos=3.5854 m, x=1.6150 m, y=3.0956 m, z=0.8151 m, yaw=2.5708 deg, dominant=y, samples=80 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.8997 m, x=0.8577 m, y=0.1464 m, z=0.2289 m, yaw=0.1392 deg, dominant=x, samples=40 | pos=3.9148 m, x=0.4987 m, y=3.6467 m, z=1.3336 m, yaw=2.8756 deg, dominant=y, samples=40 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.8687 m, x=0.4866 m, y=0.3988 m, z=1.7595 m, yaw=4.8972 deg, dominant=yaw, samples=68 | pos=3.5594 m, x=1.2427 m, y=3.1652 m, z=1.0521 m, yaw=3.7001 deg, dominant=yaw, samples=68 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2181 m, x=0.1361 m, y=0.1554 m, z=0.0699 m, yaw=1.3827 deg, dominant=yaw, samples=8 | pos=4.0384 m, x=0.8483 m, y=3.4496 m, z=1.9207 m, yaw=6.4366 deg, dominant=yaw, samples=8 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.6543 m, x=2.8850 m, y=3.6199 m, z=0.4852 m, yaw=9.9273 deg, dominant=yaw, samples=78 | pos=7.5576 m, x=2.1585 m, y=6.8429 m, z=2.3733 m, yaw=5.3731 deg, dominant=y, samples=78 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8598 m, x=2.6575 m, y=1.0190 m, z=0.2792 m, yaw=19.1624 deg, dominant=yaw, samples=20 | pos=11.6921 m, x=7.2907 m, y=8.6641 m, z=2.9126 m, yaw=29.4829 deg, dominant=yaw, samples=20 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=8.2868 m, x=6.9423 m, y=4.1825 m, z=1.7271 m, yaw=23.8606 deg, dominant=yaw, samples=62 | pos=17.7938 m, x=16.7487 m, y=3.4512 m, z=4.9180 m, yaw=18.1316 deg, dominant=yaw, x, samples=62 |

**Most affected segment:** `straight_road` with relative position RMSE 8.2868 m and dominant component(s): yaw.

## Perturbation-window analysis

No perturbation windows configured for this case.

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
