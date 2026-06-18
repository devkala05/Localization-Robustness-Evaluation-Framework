# Localization Run Analysis

**Algorithm note:** FAST-LIVO2 uses point_time_scale=1000000.0 only in the benchmark adapter path. --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3248**
- Robustness score, lower is better: **36.9204**
- Overall position RMSE: **28.8288 m**
- Overall max position error: **57.9368 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.733483` → `1723528521.623703`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7209 m, x=0.2841 m, y=0.4659 m, z=0.4711 m, yaw=0.5086 deg, dominant=yaw, z, y, samples=1145 | pos=0.7218 m, x=0.2838 m, y=0.4677 m, z=0.4708 m, yaw=0.5681 deg, dominant=yaw, samples=1145 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2083 m, x=0.1309 m, y=0.1300 m, z=0.0967 m, yaw=0.7182 deg, dominant=yaw, samples=80 | pos=0.3946 m, x=0.0695 m, y=0.2741 m, z=0.2752 m, yaw=0.4728 deg, dominant=yaw, samples=80 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1413 m, x=0.0873 m, y=0.0327 m, z=0.1062 m, yaw=0.3769 deg, dominant=yaw, samples=60 | pos=0.5353 m, x=0.1540 m, y=0.1851 m, z=0.4781 m, yaw=0.4188 deg, dominant=z, samples=60 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.4801 m, x=0.4322 m, y=0.1439 m, z=0.1518 m, yaw=0.3023 deg, dominant=x, samples=136 | pos=0.4992 m, x=0.3720 m, y=0.0797 m, z=0.3233 m, yaw=0.3671 deg, dominant=x, yaw, samples=136 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2686 m, x=0.0908 m, y=0.0824 m, z=0.2390 m, yaw=0.2667 deg, dominant=yaw, samples=110 | pos=0.4028 m, x=0.3781 m, y=0.0691 m, z=0.1206 m, yaw=0.4106 deg, dominant=yaw, x, samples=110 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2296 m, x=0.1730 m, y=0.1270 m, z=0.0815 m, yaw=0.3309 deg, dominant=yaw, samples=78 | pos=0.4466 m, x=0.3650 m, y=0.2452 m, z=0.0777 m, yaw=0.6593 deg, dominant=yaw, samples=78 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2020 m, x=0.1517 m, y=0.1327 m, z=0.0143 m, yaw=0.6213 deg, dominant=yaw, samples=50 | pos=0.4979 m, x=0.2412 m, y=0.4100 m, z=0.1469 m, yaw=0.7550 deg, dominant=yaw, samples=50 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7204 m, x=0.2401 m, y=0.2773 m, z=0.6200 m, yaw=1.0581 deg, dominant=yaw, samples=231 | pos=0.9118 m, x=0.1848 m, y=0.7208 m, z=0.5269 m, yaw=0.6973 deg, dominant=y, yaw, samples=231 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3599 m, x=0.2197 m, y=0.2628 m, z=0.1104 m, yaw=0.2074 deg, dominant=y, samples=110 | pos=1.3898 m, x=0.4200 m, y=0.8996 m, z=0.9726 m, yaw=0.7124 deg, dominant=z, y, samples=110 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6506 m, x=0.5559 m, y=0.3227 m, z=0.1005 m, yaw=4.1531 deg, dominant=yaw, samples=180 | pos=1.5007 m, x=0.6224 m, y=0.9275 m, z=1.0023 m, yaw=3.8720 deg, dominant=yaw, samples=180 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2450 m, x=0.2382 m, y=0.0555 m, z=0.0143 m, yaw=0.7401 deg, dominant=yaw, samples=20 | pos=1.8185 m, x=0.1003 m, y=1.6146 m, z=0.8304 m, yaw=7.6514 deg, dominant=yaw, samples=20 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.2726 m, x=1.7865 m, y=3.8746 m, z=0.2254 m, yaw=8.6189 deg, dominant=yaw, samples=220 | pos=5.6405 m, x=1.6951 m, y=5.3392 m, z=0.6597 m, yaw=3.5892 deg, dominant=y, samples=220 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.7341 m, x=2.5415 m, y=1.0035 m, z=0.0961 m, yaw=20.3404 deg, dominant=yaw, samples=57 | pos=9.8468 m, x=6.2487 m, y=7.6035 m, z=0.3173 m, yaw=27.3830 deg, dominant=yaw, samples=57 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8596 m, x=7.0681 m, y=3.4356 m, z=0.1125 m, yaw=24.9738 deg, dominant=yaw, samples=165 | pos=16.0164 m, x=15.6478 m, y=3.4128 m, z=0.1589 m, yaw=16.2196 deg, dominant=yaw, x, samples=165 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8596 m and dominant component(s): yaw.

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
