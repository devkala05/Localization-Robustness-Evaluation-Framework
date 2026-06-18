# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3147**
- Robustness score, lower is better: **77.9174**
- Overall position RMSE: **64.9062 m**
- Overall max position error: **141.6083 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.734890` → `1723528521.593704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.6370 m, x=0.2500 m, y=0.3470 m, z=0.4721 m, yaw=0.4697 deg, dominant=z, yaw, samples=1136 | pos=0.6375 m, x=0.2496 m, y=0.3486 m, z=0.4718 m, yaw=0.5196 deg, dominant=yaw, z, samples=1136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1907 m, x=0.1094 m, y=0.1228 m, z=0.0965 m, yaw=0.7786 deg, dominant=yaw, samples=80 | pos=0.3739 m, x=0.0687 m, y=0.2441 m, z=0.2748 m, yaw=0.4066 deg, dominant=yaw, samples=80 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1404 m, x=0.0838 m, y=0.0389 m, z=0.1058 m, yaw=0.5001 deg, dominant=yaw, samples=60 | pos=0.5184 m, x=0.1259 m, y=0.1571 m, z=0.4777 m, yaw=0.5374 deg, dominant=yaw, samples=60 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.4598 m, x=0.4236 m, y=0.0971 m, z=0.1504 m, yaw=0.2376 deg, dominant=x, samples=134 | pos=0.5076 m, x=0.3852 m, y=0.0624 m, z=0.3246 m, yaw=0.2492 deg, dominant=x, samples=134 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3726 m, x=0.2742 m, y=0.0324 m, z=0.2502 m, yaw=0.3772 deg, dominant=yaw, samples=107 | pos=0.3504 m, x=0.3269 m, y=0.0350 m, z=0.1213 m, yaw=0.4254 deg, dominant=yaw, samples=107 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1960 m, x=0.1514 m, y=0.0942 m, z=0.0815 m, yaw=0.3870 deg, dominant=yaw, samples=78 | pos=0.3414 m, x=0.3069 m, y=0.1277 m, z=0.0777 m, yaw=0.5809 deg, dominant=yaw, samples=78 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2286 m, x=0.1785 m, y=0.1422 m, z=0.0142 m, yaw=0.7544 deg, dominant=yaw, samples=52 | pos=0.3741 m, x=0.2083 m, y=0.2734 m, z=0.1477 m, yaw=0.8223 deg, dominant=yaw, samples=52 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.6877 m, x=0.2485 m, y=0.1792 m, z=0.6157 m, yaw=0.3168 deg, dominant=z, samples=230 | pos=0.7742 m, x=0.1517 m, y=0.5501 m, z=0.5233 m, yaw=0.5729 deg, dominant=yaw, y, z, samples=230 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3567 m, x=0.2049 m, y=0.2699 m, z=0.1112 m, yaw=0.2095 deg, dominant=y, samples=108 | pos=1.2224 m, x=0.3359 m, y=0.6594 m, z=0.9729 m, yaw=0.6351 deg, dominant=z, samples=108 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6993 m, x=0.5945 m, y=0.3560 m, z=0.0944 m, yaw=3.9664 deg, dominant=yaw, samples=184 | pos=1.3361 m, x=0.5464 m, y=0.6916 m, z=1.0042 m, yaw=3.6771 deg, dominant=yaw, samples=184 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2591 m, x=0.2563 m, y=0.0346 m, z=0.0149 m, yaw=0.7651 deg, dominant=yaw, samples=20 | pos=1.6324 m, x=0.1793 m, y=1.3943 m, z=0.8298 m, yaw=7.7560 deg, dominant=yaw, samples=20 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2248 m, x=1.6995 m, y=3.8615 m, z=0.2229 m, yaw=8.5362 deg, dominant=yaw, samples=218 | pos=5.4526 m, x=1.7506 m, y=5.1213 m, z=0.6622 m, yaw=3.5180 deg, dominant=y, samples=218 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.7109 m, x=2.5376 m, y=0.9488 m, z=0.0958 m, yaw=20.2382 deg, dominant=yaw, samples=55 | pos=9.7801 m, x=6.3140 m, y=7.4621 m, z=0.3176 m, yaw=27.2682 deg, dominant=yaw, samples=55 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=6.8645 m, x=4.3827 m, y=5.2821 m, z=0.1121 m, yaw=31.2127 deg, dominant=yaw, samples=166 | pos=10.9177 m, x=10.3871 m, y=3.3583 m, z=0.1594 m, yaw=14.1141 deg, dominant=yaw, samples=166 |

**Most affected segment:** `straight_road` with relative position RMSE 6.8645 m and dominant component(s): yaw.

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
