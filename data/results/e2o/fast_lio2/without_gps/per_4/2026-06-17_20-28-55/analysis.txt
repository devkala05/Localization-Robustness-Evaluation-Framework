# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **37.1292**
- Overall position RMSE: **28.9896 m**
- Overall max position error: **58.3825 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.518232` → `1723528521.647570`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.3034 m, x=0.3444 m, y=0.4295 m, z=1.1814 m, yaw=0.7706 deg, dominant=z, samples=2136 | pos=1.3034 m, x=0.3465 m, y=0.4272 m, z=1.1817 m, yaw=0.7725 deg, dominant=z, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2478 m, x=0.0333 m, y=0.0547 m, z=0.2394 m, yaw=0.6345 deg, dominant=yaw, samples=148 | pos=0.7228 m, x=0.2788 m, y=0.2412 m, z=0.6217 m, yaw=0.3439 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3632 m, x=0.1520 m, y=0.2486 m, z=0.2168 m, yaw=1.3718 deg, dominant=yaw, samples=118 | pos=1.2494 m, x=0.2573 m, y=0.3702 m, z=1.1653 m, yaw=2.3739 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9996 m, x=0.7284 m, y=0.1269 m, z=0.6727 m, yaw=0.3236 deg, dominant=x, z, samples=254 | pos=0.8032 m, x=0.5306 m, y=0.2870 m, z=0.5303 m, yaw=0.3533 deg, dominant=x, z, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3629 m, x=0.0504 m, y=0.1098 m, z=0.3422 m, yaw=0.1263 deg, dominant=z, samples=204 | pos=0.5691 m, x=0.0272 m, y=0.3717 m, z=0.4301 m, yaw=0.4975 deg, dominant=yaw, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.3054 m, x=0.1205 m, y=0.0143 m, z=0.2802 m, yaw=0.1498 deg, dominant=z, samples=144 | pos=1.0562 m, x=0.1278 m, y=0.4895 m, z=0.9271 m, yaw=0.2226 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2682 m, x=0.1918 m, y=0.0639 m, z=0.1762 m, yaw=0.5023 deg, dominant=yaw, samples=96 | pos=1.4283 m, x=0.1786 m, y=0.4976 m, z=1.3269 m, yaw=0.6045 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.4711 m, x=0.2439 m, y=0.0891 m, z=0.3930 m, yaw=0.4816 deg, dominant=yaw, samples=416 | pos=1.9254 m, x=0.2114 m, y=0.6093 m, z=1.8142 m, yaw=0.7354 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.2463 m, x=0.1911 m, y=0.1103 m, z=0.1094 m, yaw=0.1207 deg, dominant=x, samples=206 | pos=2.1242 m, x=0.6238 m, y=0.6554 m, z=1.9219 m, yaw=0.7140 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9955 m, x=0.5683 m, y=0.4160 m, z=0.7036 m, yaw=4.6028 deg, dominant=yaw, samples=350 | pos=1.6337 m, x=0.6990 m, y=0.8583 m, z=1.2015 m, yaw=4.1338 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.3035 m, x=0.2911 m, y=0.0538 m, z=0.0672 m, yaw=1.3856 deg, dominant=yaw, samples=38 | pos=1.7817 m, x=0.2828 m, y=1.6753 m, z=0.5364 m, yaw=8.2781 deg, dominant=yaw, samples=38 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5792 m, x=2.1129 m, y=4.0608 m, z=0.1211 m, yaw=9.7329 deg, dominant=yaw, samples=404 | pos=5.9212 m, x=1.8720 m, y=5.6008 m, z=0.4335 m, yaw=4.0995 deg, dominant=y, samples=404 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9828 m, x=2.8293 m, y=0.9032 m, z=0.2766 m, yaw=20.5823 deg, dominant=yaw, samples=104 | pos=10.2935 m, x=6.7605 m, y=7.7605 m, z=0.1638 m, yaw=28.8133 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=8.0101 m, x=6.8845 m, y=3.9161 m, z=1.1954 m, yaw=24.3915 deg, dominant=yaw, samples=320 | pos=16.4271 m, x=16.0490 m, y=3.1577 m, z=1.5183 m, yaw=16.9249 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 8.0101 m and dominant component(s): yaw.

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
