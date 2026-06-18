# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **36.9182**
- Overall position RMSE: **28.8039 m**
- Overall max position error: **57.9328 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521471` → `1723528521.593704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7323 m, x=0.2975 m, y=0.4752 m, z=0.4712 m, yaw=0.5568 deg, dominant=yaw, samples=1068 | pos=0.7315 m, x=0.2986 m, y=0.4731 m, z=0.4713 m, yaw=0.5636 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1636 m, x=0.0794 m, y=0.1037 m, z=0.0985 m, yaw=0.1684 deg, dominant=yaw, samples=74 | pos=0.3522 m, x=0.1818 m, y=0.1195 m, z=0.2770 m, yaw=0.3059 deg, dominant=yaw, z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1640 m, x=0.0555 m, y=0.1125 m, z=0.1057 m, yaw=0.8137 deg, dominant=yaw, samples=59 | pos=0.6043 m, x=0.3085 m, y=0.2049 m, z=0.4775 m, yaw=1.0310 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6052 m, x=0.5769 m, y=0.1022 m, z=0.1516 m, yaw=0.3237 deg, dominant=x, samples=127 | pos=0.5747 m, x=0.4101 m, y=0.2404 m, z=0.3228 m, yaw=0.3529 deg, dominant=x, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3852 m, x=0.2906 m, y=0.0535 m, z=0.2472 m, yaw=0.1241 deg, dominant=x, samples=102 | pos=0.3980 m, x=0.2186 m, y=0.3097 m, z=0.1215 m, yaw=0.4443 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1920 m, x=0.1521 m, y=0.0824 m, z=0.0833 m, yaw=0.2121 deg, dominant=yaw, samples=73 | pos=0.5128 m, x=0.1763 m, y=0.4749 m, z=0.0795 m, yaw=0.5081 deg, dominant=yaw, y, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2156 m, x=0.1783 m, y=0.1205 m, z=0.0135 m, yaw=0.5919 deg, dominant=yaw, samples=47 | pos=0.6119 m, x=0.1767 m, y=0.5670 m, z=0.1475 m, yaw=0.5688 deg, dominant=yaw, y, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6863 m, x=0.2841 m, y=0.1154 m, z=0.6139 m, yaw=0.0982 deg, dominant=z, samples=209 | pos=0.9323 m, x=0.1753 m, y=0.7524 m, z=0.5218 m, yaw=0.7391 deg, dominant=y, yaw, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2663 m, x=0.1842 m, y=0.1560 m, z=0.1124 m, yaw=0.1986 deg, dominant=yaw, x, samples=103 | pos=1.3501 m, x=0.5531 m, y=0.7535 m, z=0.9742 m, yaw=0.7649 deg, dominant=z, samples=103 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6895 m, x=0.5837 m, y=0.3543 m, z=0.0963 m, yaw=4.3372 deg, dominant=yaw, samples=174 | pos=1.4774 m, x=0.6734 m, y=0.8506 m, z=1.0029 m, yaw=3.9224 deg, dominant=yaw, samples=174 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2668 m, x=0.2512 m, y=0.0886 m, z=0.0150 m, yaw=1.0612 deg, dominant=yaw, samples=19 | pos=1.8178 m, x=0.2095 m, y=1.6036 m, z=0.8300 m, yaw=7.8555 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5150 m, x=2.0109 m, y=4.0363 m, z=0.2248 m, yaw=9.0106 deg, dominant=yaw, samples=202 | pos=5.8405 m, x=1.8232 m, y=5.5093 m, z=0.6599 m, yaw=3.8913 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8496 m, x=2.6968 m, y=0.9156 m, z=0.0948 m, yaw=20.5939 deg, dominant=yaw, samples=52 | pos=10.1921 m, x=6.5643 m, y=7.7902 m, z=0.3195 m, yaw=28.0247 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8677 m, x=6.9126 m, y=3.7554 m, z=0.1129 m, yaw=24.0627 deg, dominant=yaw, samples=160 | pos=16.1534 m, x=15.8132 m, y=3.2940 m, z=0.1591 m, yaw=16.7730 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8677 m and dominant component(s): yaw.

## Perturbation-window analysis

| # | Window | Sensor/type | Time window | Relative RMSE summary |
|---:|---|---|---|---|
| 1 | imu_gaussian_noise | imu/gaussian_noise | 1621218788.000000 → 1621218794.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 2 | imu_message_dropout | imu/dropout | 1621218812.000000 → 1621218817.000000 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |


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
