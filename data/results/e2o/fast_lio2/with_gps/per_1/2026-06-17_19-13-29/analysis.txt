# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **36.8499**
- Overall position RMSE: **28.7439 m**
- Overall max position error: **57.9482 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.520784` → `1723528521.593704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7454 m, x=0.3223 m, y=0.4793 m, z=0.4712 m, yaw=0.5830 deg, dominant=yaw, samples=1068 | pos=0.7449 m, x=0.3240 m, y=0.4772 m, z=0.4713 m, yaw=0.5900 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1643 m, x=0.0768 m, y=0.1064 m, z=0.0988 m, yaw=0.1655 deg, dominant=yaw, samples=74 | pos=0.3476 m, x=0.1676 m, y=0.1262 m, z=0.2772 m, yaw=0.3060 deg, dominant=yaw, z, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1683 m, x=0.0566 m, y=0.1182 m, z=0.1057 m, yaw=0.8195 deg, dominant=yaw, samples=59 | pos=0.5927 m, x=0.2934 m, y=0.1930 m, z=0.4775 m, yaw=1.0415 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.5912 m, x=0.5633 m, y=0.0958 m, z=0.1515 m, yaw=0.3666 deg, dominant=x, samples=127 | pos=0.5706 m, x=0.4186 m, y=0.2146 m, z=0.3229 m, yaw=0.3617 deg, dominant=x, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3716 m, x=0.2714 m, y=0.0575 m, z=0.2472 m, yaw=0.1431 deg, dominant=x, z, samples=102 | pos=0.3819 m, x=0.2089 m, y=0.2957 m, z=0.1213 m, yaw=0.4735 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1934 m, x=0.1490 m, y=0.0910 m, z=0.0833 m, yaw=0.1927 deg, dominant=yaw, samples=73 | pos=0.5079 m, x=0.1647 m, y=0.4739 m, z=0.0795 m, yaw=0.5313 deg, dominant=yaw, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2179 m, x=0.1803 m, y=0.1217 m, z=0.0137 m, yaw=0.6088 deg, dominant=yaw, samples=47 | pos=0.6238 m, x=0.1838 m, y=0.5775 m, z=0.1477 m, yaw=0.5741 deg, dominant=y, yaw, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6963 m, x=0.3077 m, y=0.1156 m, z=0.6139 m, yaw=0.1012 deg, dominant=z, samples=209 | pos=0.9525 m, x=0.2042 m, y=0.7703 m, z=0.5217 m, yaw=0.7956 deg, dominant=yaw, y, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2692 m, x=0.1911 m, y=0.1526 m, z=0.1125 m, yaw=0.1834 deg, dominant=x, yaw, samples=103 | pos=1.3886 m, x=0.6340 m, y=0.7595 m, z=0.9744 m, yaw=0.7899 deg, dominant=z, samples=103 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6821 m, x=0.5789 m, y=0.3476 m, z=0.0963 m, yaw=4.2898 deg, dominant=yaw, samples=174 | pos=1.5148 m, x=0.7565 m, y=0.8467 m, z=1.0027 m, yaw=3.8748 deg, dominant=yaw, samples=174 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2687 m, x=0.2526 m, y=0.0905 m, z=0.0150 m, yaw=1.0308 deg, dominant=yaw, samples=19 | pos=1.8120 m, x=0.3046 m, y=1.5816 m, z=0.8300 m, yaw=7.7530 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5279 m, x=2.0546 m, y=4.0286 m, z=0.2247 m, yaw=9.0409 deg, dominant=yaw, samples=202 | pos=5.7988 m, x=1.7895 m, y=5.4761 m, z=0.6600 m, yaw=3.9469 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8617 m, x=2.7077 m, y=0.9210 m, z=0.0948 m, yaw=20.5910 deg, dominant=yaw, samples=52 | pos=10.1271 m, x=6.5407 m, y=7.7249 m, z=0.3193 m, yaw=28.1449 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8769 m, x=6.8876 m, y=3.8203 m, z=0.1129 m, yaw=24.1052 deg, dominant=yaw, samples=160 | pos=16.1011 m, x=15.7789 m, y=3.2012 m, z=0.1592 m, yaw=16.8640 deg, dominant=yaw, x, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8769 m and dominant component(s): yaw.

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
