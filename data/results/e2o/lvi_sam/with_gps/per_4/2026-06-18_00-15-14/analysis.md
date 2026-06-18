# Localization Run Analysis

**Algorithm note:** Visual subsystem enabled using UrbanNav ZED2 right-camera intrinsics/extrinsics, but final mapping stays LiDAR-IMU dominant only when VINS is unhealthy. VINS graph constraints are enabled so the final graph uses camera-derived relative pose factors.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **1529**
- Robustness score, lower is better: **37.4678**
- Overall position RMSE: **29.3139 m**
- Overall max position error: **58.6160 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217031` → `1723528521.442302`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=1.0704 m, x=0.2778 m, y=0.1636 m, z=1.0207 m, yaw=0.7475 deg, dominant=z, samples=536 | pos=1.0704 m, x=0.2778 m, y=0.1636 m, z=1.0207 m, yaw=0.7475 deg, dominant=z, samples=536 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.2303 m, x=0.0201 m, y=0.0653 m, z=0.2200 m, yaw=0.4817 deg, dominant=yaw, samples=37 | pos=0.7696 m, x=0.2530 m, y=0.2007 m, z=0.6986 m, yaw=0.4172 deg, dominant=z, samples=37 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.3721 m, x=0.2498 m, y=0.2700 m, z=0.0565 m, yaw=1.3844 deg, dominant=yaw, samples=29 | pos=1.0053 m, x=0.1241 m, y=0.3148 m, z=0.9467 m, yaw=2.7451 deg, dominant=yaw, samples=29 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.6653 m, x=0.6321 m, y=0.1092 m, z=0.1764 m, yaw=0.4367 deg, dominant=x, samples=64 | pos=1.0488 m, x=0.6300 m, y=0.1476 m, z=0.8253 m, yaw=0.3097 deg, dominant=z, samples=64 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2257 m, x=0.0330 m, y=0.0694 m, z=0.2122 m, yaw=0.1587 deg, dominant=z, samples=54 | pos=0.5007 m, x=0.1059 m, y=0.1817 m, z=0.4544 m, yaw=0.3873 deg, dominant=z, samples=54 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.1885 m, x=0.1392 m, y=0.0397 m, z=0.1208 m, yaw=0.1783 deg, dominant=yaw, samples=33 | pos=0.4030 m, x=0.2494 m, y=0.2207 m, z=0.2269 m, yaw=0.2143 deg, dominant=x, z, samples=33 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.2470 m, x=0.1866 m, y=0.0426 m, z=0.1561 m, yaw=0.4886 deg, dominant=yaw, samples=24 | pos=0.3387 m, x=0.2908 m, y=0.1318 m, z=0.1131 m, yaw=0.8969 deg, dominant=yaw, samples=24 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.8545 m, x=0.0546 m, y=0.0661 m, z=0.8502 m, yaw=0.3916 deg, dominant=z, samples=104 | pos=1.0756 m, x=0.1053 m, y=0.1409 m, z=1.0611 m, yaw=0.2437 deg, dominant=z, samples=104 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.8357 m, x=0.0335 m, y=0.1297 m, z=0.8249 m, yaw=0.1295 deg, dominant=z, samples=51 | pos=2.0324 m, x=0.1912 m, y=0.1400 m, z=2.0185 m, yaw=0.1373 deg, dominant=z, samples=51 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.9117 m, x=0.6963 m, y=0.5687 m, z=0.1514 m, yaw=4.7259 deg, dominant=yaw, samples=88 | pos=2.6434 m, x=0.6001 m, y=0.6153 m, z=2.4998 m, yaw=4.6526 deg, dominant=yaw, samples=88 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2520 m, x=0.2355 m, y=0.0756 m, z=0.0484 m, yaw=1.2822 deg, dominant=yaw, samples=9 | pos=2.7770 m, x=0.4902 m, y=1.4786 m, z=2.2989 m, yaw=9.2226 deg, dominant=yaw, samples=9 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.4404 m, x=1.6902 m, y=3.9933 m, z=0.9563 m, yaw=9.8455 deg, dominant=yaw, samples=101 | pos=5.9556 m, x=1.9614 m, y=5.3624 m, z=1.6931 m, yaw=3.8901 deg, dominant=y, samples=101 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.8404 m, x=2.7153 m, y=0.8219 m, z=0.1387 m, yaw=20.3627 deg, dominant=yaw, samples=26 | pos=10.3211 m, x=6.7211 m, y=7.7908 m, z=0.8101 m, yaw=27.8200 deg, dominant=yaw, samples=26 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.8594 m, x=7.0268 m, y=3.4453 m, z=0.7238 m, yaw=24.5048 deg, dominant=yaw, samples=80 | pos=16.5279 m, x=16.1548 m, y=3.4733 m, z=0.3615 m, yaw=16.2025 deg, dominant=yaw, x, samples=80 |

**Most affected segment:** `straight_road` with relative position RMSE 7.8594 m and dominant component(s): yaw.

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
