# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **36.8523**
- Overall position RMSE: **28.7462 m**
- Overall max position error: **57.9653 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521687` → `1723528521.604704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7390 m, x=0.3236 m, y=0.4685 m, z=0.4712 m, yaw=0.5842 deg, dominant=yaw, samples=1068 | pos=0.7385 m, x=0.3252 m, y=0.4664 m, z=0.4713 m, yaw=0.5910 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1620 m, x=0.0749 m, y=0.1046 m, z=0.0985 m, yaw=0.1673 deg, dominant=yaw, samples=74 | pos=0.3405 m, x=0.1591 m, y=0.1182 m, z=0.2769 m, yaw=0.3041 deg, dominant=yaw, z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1797 m, x=0.0561 m, y=0.1343 m, z=0.1054 m, yaw=0.8590 deg, dominant=yaw, samples=59 | pos=0.5941 m, x=0.2920 m, y=0.1999 m, z=0.4772 m, yaw=1.0681 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.5866 m, x=0.5589 m, y=0.0934 m, z=0.1516 m, yaw=0.3386 deg, dominant=x, samples=127 | pos=0.5772 m, x=0.4241 m, y=0.2216 m, z=0.3228 m, yaw=0.3375 deg, dominant=x, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3795 m, x=0.2827 m, y=0.0520 m, z=0.2478 m, yaw=0.1288 deg, dominant=x, samples=102 | pos=0.3814 m, x=0.2131 m, y=0.2921 m, z=0.1215 m, yaw=0.4439 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1893 m, x=0.1471 m, y=0.0852 m, z=0.0831 m, yaw=0.2089 deg, dominant=yaw, samples=73 | pos=0.4946 m, x=0.1665 m, y=0.4589 m, z=0.0793 m, yaw=0.4931 deg, dominant=yaw, y, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2213 m, x=0.1845 m, y=0.1214 m, z=0.0137 m, yaw=0.6069 deg, dominant=yaw, samples=47 | pos=0.5968 m, x=0.1857 m, y=0.5476 m, z=0.1477 m, yaw=0.5843 deg, dominant=yaw, y, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7011 m, x=0.3148 m, y=0.1247 m, z=0.6139 m, yaw=0.1172 deg, dominant=z, samples=209 | pos=0.9345 m, x=0.2011 m, y=0.7488 m, z=0.5218 m, yaw=0.7959 deg, dominant=yaw, y, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2762 m, x=0.1933 m, y=0.1622 m, z=0.1122 m, yaw=0.2054 deg, dominant=yaw, x, samples=103 | pos=1.3815 m, x=0.6323 m, y=0.7484 m, z=0.9740 m, yaw=0.8264 deg, dominant=z, samples=103 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6822 m, x=0.5809 m, y=0.3444 m, z=0.0963 m, yaw=4.3218 deg, dominant=yaw, samples=174 | pos=1.5085 m, x=0.7608 m, y=0.8312 m, z=1.0029 m, yaw=3.8880 deg, dominant=yaw, samples=174 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2717 m, x=0.2577 m, y=0.0847 m, z=0.0150 m, yaw=1.0537 deg, dominant=yaw, samples=19 | pos=1.7838 m, x=0.3057 m, y=1.5491 m, z=0.8300 m, yaw=7.7178 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5079 m, x=2.0807 m, y=3.9927 m, z=0.2247 m, yaw=9.0520 deg, dominant=yaw, samples=202 | pos=5.7559 m, x=1.8100 m, y=5.4239 m, z=0.6601 m, yaw=3.9572 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9080 m, x=2.7960 m, y=0.7932 m, z=0.0976 m, yaw=20.6339 deg, dominant=yaw, samples=52 | pos=10.0889 m, x=6.5743 m, y=7.6461 m, z=0.3191 m, yaw=28.1910 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9308 m, x=6.9305 m, y=3.8539 m, z=0.1129 m, yaw=24.0245 deg, dominant=yaw, samples=160 | pos=16.1598 m, x=15.8532 m, y=3.1287 m, z=0.1591 m, yaw=16.9270 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9308 m and dominant component(s): yaw.

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
