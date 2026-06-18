# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **36.7615**
- Overall position RMSE: **28.6695 m**
- Overall max position error: **57.7894 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521517` → `1723528521.604704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7825 m, x=0.3411 m, y=0.5234 m, z=0.4712 m, yaw=0.6254 deg, dominant=yaw, samples=1068 | pos=0.7816 m, x=0.3422 m, y=0.5213 m, z=0.4713 m, yaw=0.6327 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1633 m, x=0.0859 m, y=0.0980 m, z=0.0985 m, yaw=0.1735 deg, dominant=yaw, samples=74 | pos=0.3567 m, x=0.1948 m, y=0.1124 m, z=0.2769 m, yaw=0.3763 deg, dominant=yaw, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1598 m, x=0.0576 m, y=0.1051 m, z=0.1057 m, yaw=0.8336 deg, dominant=yaw, samples=59 | pos=0.6107 m, x=0.3294 m, y=0.1910 m, z=0.4775 m, yaw=1.0524 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6032 m, x=0.5735 m, y=0.1096 m, z=0.1515 m, yaw=0.3559 deg, dominant=x, samples=127 | pos=0.5622 m, x=0.3953 m, y=0.2355 m, z=0.3229 m, yaw=0.3545 deg, dominant=x, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3847 m, x=0.2872 m, y=0.0649 m, z=0.2476 m, yaw=0.1411 deg, dominant=x, samples=102 | pos=0.4331 m, x=0.2638 m, y=0.3213 m, z=0.1214 m, yaw=0.4783 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1892 m, x=0.1424 m, y=0.0927 m, z=0.0833 m, yaw=0.1997 deg, dominant=yaw, samples=73 | pos=0.5586 m, x=0.2128 m, y=0.5103 m, z=0.0795 m, yaw=0.5701 deg, dominant=yaw, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2173 m, x=0.1754 m, y=0.1275 m, z=0.0137 m, yaw=0.6147 deg, dominant=yaw, samples=47 | pos=0.6544 m, x=0.1775 m, y=0.6123 m, z=0.1477 m, yaw=0.5952 deg, dominant=y, yaw, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7114 m, x=0.3351 m, y=0.1310 m, z=0.6137 m, yaw=0.1353 deg, dominant=z, samples=209 | pos=1.0021 m, x=0.2100 m, y=0.8295 m, z=0.5216 m, yaw=0.8620 deg, dominant=yaw, y, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2944 m, x=0.2085 m, y=0.1749 m, z=0.1124 m, yaw=0.2213 deg, dominant=yaw, x, samples=103 | pos=1.4586 m, x=0.6672 m, y=0.8563 m, z=0.9742 m, yaw=0.9099 deg, dominant=z, yaw, samples=103 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6751 m, x=0.5777 m, y=0.3358 m, z=0.0962 m, yaw=4.3186 deg, dominant=yaw, samples=174 | pos=1.5656 m, x=0.8012 m, y=0.8958 m, z=1.0034 m, yaw=3.8448 deg, dominant=yaw, samples=174 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2724 m, x=0.2587 m, y=0.0839 m, z=0.0150 m, yaw=1.0275 deg, dominant=yaw, samples=19 | pos=1.8464 m, x=0.3548 m, y=1.6107 m, z=0.8300 m, yaw=7.6651 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5182 m, x=2.1015 m, y=3.9934 m, z=0.2248 m, yaw=9.0520 deg, dominant=yaw, samples=202 | pos=5.7945 m, x=1.8000 m, y=5.4682 m, z=0.6599 m, yaw=3.9874 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8741 m, x=2.7171 m, y=0.9321 m, z=0.0947 m, yaw=20.6266 deg, dominant=yaw, samples=52 | pos=10.1440 m, x=6.5911 m, y=7.7043 m, z=0.3191 m, yaw=28.2792 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9511 m, x=6.9306 m, y=3.8953 m, z=0.1129 m, yaw=24.0181 deg, dominant=yaw, samples=160 | pos=16.1799 m, x=15.8718 m, y=3.1386 m, z=0.1591 m, yaw=17.0239 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9511 m and dominant component(s): yaw.

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
