# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `off`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **6112**
- Robustness score, lower is better: **37.1338**
- Overall position RMSE: **28.9918 m**
- Overall max position error: **58.2079 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.521414` → `1723528521.644931`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.9651 m, x=0.3490 m, y=0.4480 m, z=0.7803 m, yaw=0.7640 deg, dominant=z, yaw, samples=2136 | pos=0.9651 m, x=0.3513 m, y=0.4457 m, z=0.7806 m, yaw=0.7661 deg, dominant=z, yaw, samples=2136 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1870 m, x=0.0374 m, y=0.0494 m, z=0.1765 m, yaw=0.6485 deg, dominant=yaw, samples=148 | pos=0.6296 m, x=0.2513 m, y=0.2287 m, z=0.5300 m, yaw=0.3314 deg, dominant=z, samples=148 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3308 m, x=0.1275 m, y=0.2372 m, z=0.1921 m, yaw=1.3716 deg, dominant=yaw, samples=118 | pos=1.0944 m, x=0.2727 m, y=0.3459 m, z=1.0019 m, yaw=2.3080 deg, dominant=yaw, samples=118 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.9708 m, x=0.7743 m, y=0.1533 m, z=0.5651 m, yaw=0.3011 deg, dominant=x, samples=254 | pos=0.7713 m, x=0.5490 m, y=0.2857 m, z=0.4603 m, yaw=0.3791 deg, dominant=x, samples=254 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.3084 m, x=0.0543 m, y=0.1151 m, z=0.2809 m, yaw=0.1275 deg, dominant=z, samples=204 | pos=0.5225 m, x=0.0285 m, y=0.4014 m, z=0.3333 m, yaw=0.5353 deg, dominant=yaw, samples=204 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2770 m, x=0.1286 m, y=0.0165 m, z=0.2447 m, yaw=0.1497 deg, dominant=z, samples=144 | pos=0.9378 m, x=0.1427 m, y=0.5261 m, z=0.7631 m, yaw=0.2199 deg, dominant=z, samples=144 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2433 m, x=0.1912 m, y=0.0554 m, z=0.1399 m, yaw=0.5207 deg, dominant=yaw, samples=96 | pos=1.2347 m, x=0.1988 m, y=0.5191 m, z=1.1025 m, yaw=0.6260 deg, dominant=z, samples=96 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.2791 m, x=0.2516 m, y=0.1009 m, z=0.0664 m, yaw=0.5019 deg, dominant=yaw, samples=416 | pos=1.4276 m, x=0.2229 m, y=0.6354 m, z=1.2588 m, yaw=0.7415 deg, dominant=z, samples=416 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3487 m, x=0.1908 m, y=0.1018 m, z=0.2735 m, yaw=0.1055 deg, dominant=z, samples=206 | pos=1.3113 m, x=0.6303 m, y=0.6910 m, z=0.9191 m, yaw=0.7047 deg, dominant=z, samples=206 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=1.0972 m, x=0.5775 m, y=0.4326 m, z=0.8266 m, yaw=4.6280 deg, dominant=yaw, samples=350 | pos=1.2128 m, x=0.6970 m, y=0.9016 m, z=0.4152 m, yaw=4.1744 deg, dominant=yaw, samples=350 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2936 m, x=0.2797 m, y=0.0522 m, z=0.0725 m, yaw=1.3261 deg, dominant=yaw, samples=36 | pos=1.9190 m, x=0.2857 m, y=1.7574 m, z=0.7157 m, yaw=8.4135 deg, dominant=yaw, samples=36 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5900 m, x=2.0538 m, y=4.1031 m, z=0.1221 m, yaw=9.7378 deg, dominant=yaw, samples=406 | pos=6.0422 m, x=1.8017 m, y=5.7039 m, z=0.8524 m, yaw=4.0554 deg, dominant=y, samples=406 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9556 m, x=2.8020 m, y=0.9040 m, z=0.2589 m, yaw=20.5712 deg, dominant=yaw, samples=104 | pos=10.4002 m, x=6.6270 m, y=7.9147 m, z=1.2668 m, yaw=28.6561 deg, dominant=yaw, samples=104 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.9440 m, x=6.8515 m, y=3.8466 m, z=1.1698 m, yaw=24.3995 deg, dominant=yaw, samples=320 | pos=16.4460 m, x=15.8877 m, y=3.3333 m, z=2.6348 m, yaw=16.7808 deg, dominant=yaw, x, samples=320 |

**Most affected segment:** `straight_road` with relative position RMSE 7.9440 m and dominant component(s): yaw.

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
