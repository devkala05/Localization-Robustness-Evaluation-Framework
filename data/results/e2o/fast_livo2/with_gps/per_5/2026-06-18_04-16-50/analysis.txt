# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3236**
- Robustness score, lower is better: **40.9527**
- Overall position RMSE: **30.6488 m**
- Overall max position error: **81.7755 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.738081` → `1723528521.604704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.5985 m, x=0.2328 m, y=0.2893 m, z=0.4694 m, yaw=0.3868 deg, dominant=z, samples=1135 | pos=0.5993 m, x=0.2336 m, y=0.2908 m, z=0.4690 m, yaw=0.4347 deg, dominant=z, yaw, samples=1135 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1735 m, x=0.0944 m, y=0.1069 m, z=0.0989 m, yaw=0.6690 deg, dominant=yaw, samples=80 | pos=0.3766 m, x=0.0626 m, y=0.2472 m, z=0.2771 m, yaw=0.3910 deg, dominant=yaw, samples=80 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1503 m, x=0.0960 m, y=0.0470 m, z=0.1057 m, yaw=0.5461 deg, dominant=yaw, samples=59 | pos=0.5246 m, x=0.1518 m, y=0.1558 m, z=0.4774 m, yaw=0.6082 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.5798 m, x=0.5459 m, y=0.1285 m, z=0.1469 m, yaw=0.6294 deg, dominant=yaw, samples=135 | pos=0.4980 m, x=0.3735 m, y=0.0631 m, z=0.3232 m, yaw=0.2898 deg, dominant=x, samples=135 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2656 m, x=0.0849 m, y=0.0659 m, z=0.2429 m, yaw=0.2448 deg, dominant=yaw, z, samples=110 | pos=0.3741 m, x=0.3526 m, y=0.0343 m, z=0.1201 m, yaw=0.3318 deg, dominant=x, yaw, samples=110 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1922 m, x=0.1380 m, y=0.1047 m, z=0.0833 m, yaw=0.2573 deg, dominant=yaw, samples=77 | pos=0.3963 m, x=0.3603 m, y=0.1445 m, z=0.0795 m, yaw=0.5628 deg, dominant=yaw, samples=77 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.1983 m, x=0.1503 m, y=0.1285 m, z=0.0147 m, yaw=0.6054 deg, dominant=yaw, samples=50 | pos=0.4125 m, x=0.2606 m, y=0.2836 m, z=0.1478 m, yaw=0.6855 deg, dominant=yaw, samples=50 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6487 m, x=0.1351 m, y=0.1409 m, z=0.6186 m, yaw=0.2994 deg, dominant=z, samples=224 | pos=0.7470 m, x=0.2168 m, y=0.4841 m, z=0.5260 m, yaw=0.3952 deg, dominant=z, y, samples=224 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3326 m, x=0.1309 m, y=0.2847 m, z=0.1115 m, yaw=0.2150 deg, dominant=y, samples=108 | pos=1.0896 m, x=0.0456 m, y=0.4874 m, z=0.9734 m, yaw=0.3833 deg, dominant=z, samples=108 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.7060 m, x=0.6113 m, y=0.3402 m, z=0.0947 m, yaw=3.9746 deg, dominant=yaw, samples=180 | pos=1.2962 m, x=0.5583 m, y=0.5988 m, z=1.0049 m, yaw=3.7903 deg, dominant=yaw, samples=180 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2556 m, x=0.2528 m, y=0.0349 m, z=0.0150 m, yaw=0.7985 deg, dominant=yaw, samples=19 | pos=1.6594 m, x=0.5736 m, y=1.3174 m, z=0.8300 m, yaw=7.8904 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2176 m, x=1.6174 m, y=3.8886 m, z=0.2253 m, yaw=8.5471 deg, dominant=yaw, samples=215 | pos=5.4984 m, x=1.9980 m, y=5.0798 m, z=0.6604 m, yaw=3.4170 deg, dominant=y, samples=215 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.7386 m, x=2.6213 m, y=0.7868 m, z=0.0981 m, yaw=20.3146 deg, dominant=yaw, samples=54 | pos=9.8737 m, x=6.5053 m, y=7.4209 m, z=0.3178 m, yaw=27.0404 deg, dominant=yaw, samples=54 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.7483 m, x=7.0049 m, y=3.3098 m, z=0.1125 m, yaw=23.8206 deg, dominant=yaw, samples=165 | pos=16.0818 m, x=15.7263 m, y=3.3591 m, z=0.1591 m, yaw=16.0731 deg, dominant=yaw, x, samples=165 |

**Most affected segment:** `straight_road` with relative position RMSE 7.7483 m and dominant component(s): yaw.

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
