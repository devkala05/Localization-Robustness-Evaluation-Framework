# Localization Run Analysis

**Algorithm note:** RTAB-Map visual+ICP pipeline: raw/perturbed scan_cloud is sanitized, RTAB-Map icp_odometry produces /rtabmap/icp_odom, and the mapper consumes that odometry together with the right camera image/camera_info. It no longer launches FAST-LIO2 and does not subscribe to FAST-LIO2 /Odometry.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **613**
- Robustness score, lower is better: **104.2744**
- Overall position RMSE: **87.0747 m**
- Overall max position error: **141.6203 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.217067` → `1723528521.423702`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=73.9490 m, x=58.4743 m, y=45.2657 m, z=0.4680 m, yaw=87.0743 deg, dominant=yaw, samples=216 | pos=73.9490 m, x=58.4743 m, y=45.2657 m, z=0.4680 m, yaw=87.0743 deg, dominant=yaw, samples=216 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=13.4519 m, x=12.9378 m, y=3.6822 m, z=0.0976 m, yaw=5.3374 deg, dominant=x, samples=15 | pos=48.9275 m, x=45.6116 m, y=17.7034 m, z=0.2754 m, yaw=55.2725 deg, dominant=yaw, samples=15 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=8.7942 m, x=4.7333 m, y=7.4110 m, z=0.1051 m, yaw=27.1972 deg, dominant=yaw, samples=12 | pos=62.2504 m, x=61.7743 m, y=7.6693 m, z=0.4751 m, yaw=80.7595 deg, dominant=yaw, samples=12 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=22.2915 m, x=12.8252 m, y=18.2321 m, z=0.1367 m, yaw=31.8848 deg, dominant=yaw, samples=25 | pos=56.1700 m, x=52.9806 m, y=18.6554 m, z=0.3233 m, yaw=70.0476 deg, dominant=yaw, samples=25 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=22.4595 m, x=14.1299 m, y=17.4562 m, z=0.2390 m, yaw=4.6166 deg, dominant=y, samples=21 | pos=57.2879 m, x=24.8728 m, y=51.6065 m, z=0.1252 m, yaw=43.6189 deg, dominant=y, samples=21 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=14.2059 m, x=10.4171 m, y=9.6584 m, z=0.0658 m, yaw=24.3772 deg, dominant=yaw, samples=14 | pos=74.8966 m, x=6.8098 m, y=74.5864 m, z=0.0764 m, yaw=51.4442 deg, dominant=y, samples=14 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=10.2100 m, x=9.8326 m, y=2.7505 m, z=0.0148 m, yaw=14.5009 deg, dominant=yaw, samples=10 | pos=86.5965 m, x=17.8680 m, y=84.7329 m, z=0.1454 m, yaw=21.4415 deg, dominant=y, samples=10 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=43.7801 m, x=38.8813 m, y=20.1136 m, z=0.6203 m, yaw=124.4242 deg, dominant=yaw, samples=41 | pos=94.9337 m, x=63.3597 m, y=70.6943 m, z=0.5197 m, yaw=134.0391 deg, dominant=yaw, samples=41 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=32.4783 m, x=19.9382 m, y=25.6378 m, z=0.1121 m, yaw=146.0228 deg, dominant=yaw, samples=21 | pos=116.7269 m, x=113.9091 m, y=25.4745 m, z=0.9707 m, yaw=143.9764 deg, dominant=yaw, samples=21 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=15.6771 m, x=7.4987 m, y=13.7670 m, z=0.1018 m, yaw=70.0267 deg, dominant=yaw, samples=35 | pos=122.5834 m, x=121.8954 m, y=12.9302 m, z=0.9999 m, yaw=89.8953 deg, dominant=x, samples=35 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=1.2992 m, x=1.1396 m, y=0.6239 m, z=0.0074 m, yaw=1.4682 deg, dominant=yaw, samples=4 | pos=111.1662 m, x=109.6491 m, y=18.2840 m, z=0.8361 m, yaw=83.4181 deg, dominant=x, samples=4 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=27.5530 m, x=22.7781 m, y=15.5011 m, z=0.2114 m, yaw=34.0805 deg, dominant=yaw, samples=40 | pos=91.0696 m, x=90.6019 m, y=9.1945 m, z=0.6582 m, yaw=60.6151 deg, dominant=x, samples=40 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=7.8212 m, x=7.1173 m, y=3.2414 m, z=0.0922 m, yaw=9.1579 deg, dominant=yaw, samples=10 | pos=59.1184 m, x=57.7256 m, y=12.7530 m, z=0.3212 m, yaw=93.3764 deg, dominant=yaw, samples=10 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=31.1272 m, x=29.8893 m, y=8.6900 m, z=0.1098 m, yaw=90.6252 deg, dominant=yaw, samples=32 | pos=32.4857 m, x=30.0753 m, y=12.2787 m, z=0.1609 m, yaw=92.2281 deg, dominant=yaw, samples=32 |

**Most affected segment:** `straight_road` with relative position RMSE 73.9490 m and dominant component(s): yaw.

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
