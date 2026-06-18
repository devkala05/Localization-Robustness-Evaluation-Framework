# Localization Run Analysis

**Algorithm note:** FAST-LIO2 has no native GPS input in this wrapper; --gps on uses shared external loose/global fusion.

## Run summary

- GPS mode: `on`
- GPS source: `topic`
- RTK mode: `auto`
- Samples compared: **3056**
- Robustness score, lower is better: **80.5693**
- Overall position RMSE: **65.5063 m**
- Overall max position error: **141.6148 m**
- Overall dominant component(s): **yaw**

## Time ranges

- Run CSV: `1723528213.518148` → `1723528521.604704`
- Ground truth: `1723528213.816268` → `1723528521.641233`

> Segment metrics below use **segment-local relative error**: the error at the first matched sample of the segment is subtracted, so the values describe drift or degradation inside that marked scene only, not the whole-run starting bias.

## Segment-wise analysis

| # | Segment | Type | Time window | Relative RMSE summary | Absolute RMSE summary |
|---:|---|---|---|---|---|
| 1 | straight_road | temporal_phase | 1723528213.157124 → 1723528321.185588 | pos=0.7591 m, x=0.3195 m, y=0.5022 m, z=0.4710 m, yaw=0.5833 deg, dominant=yaw, samples=1068 | pos=0.7583 m, x=0.3208 m, y=0.5001 m, z=0.4712 m, yaw=0.5901 deg, dominant=yaw, samples=1068 |
| 2 | left_turn | temporal_phase | 1723528321.185588 → 1723528237.046052 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 | pos=n/a, x=n/a, y=n/a, z=n/a, yaw=n/a, dominant=n/a, samples=0 |
| 3 | straight_road | temporal_phase | 1723528237.046052 → 1723528244.525495 | pos=0.1618 m, x=0.0866 m, y=0.0944 m, z=0.0987 m, yaw=0.1927 deg, dominant=yaw, samples=74 | pos=0.3580 m, x=0.1950 m, y=0.1151 m, z=0.2772 m, yaw=0.3167 deg, dominant=yaw, samples=74 |
| 4 | left_turn | temporal_phase | 1723528244.525495 → 1723528250.465728 | pos=0.1681 m, x=0.0545 m, y=0.1188 m, z=0.1058 m, yaw=0.8298 deg, dominant=yaw, samples=59 | pos=0.6071 m, x=0.3229 m, y=0.1902 m, z=0.4776 m, yaw=1.0808 deg, dominant=yaw, samples=59 |
| 5 | straight_road | temporal_phase | 1723528250.465728 → 1723528263.265728 | pos=0.7503 m, x=0.7155 m, y=0.1713 m, z=0.1468 m, yaw=0.4678 deg, dominant=x, samples=127 | pos=0.5598 m, x=0.3878 m, y=0.2426 m, z=0.3228 m, yaw=0.3535 deg, dominant=x, yaw, samples=127 |
| 6 | trees_occlusion | temporal_phase | 1723528263.265728 → 1723528273.585834 | pos=0.2830 m, x=0.1071 m, y=0.1040 m, z=0.2405 m, yaw=0.1489 deg, dominant=z, samples=102 | pos=0.4223 m, x=0.2331 m, y=0.3302 m, z=0.1221 m, yaw=0.4725 deg, dominant=yaw, samples=102 |
| 7 | straight_road | temporal_phase | 1723528273.585834 → 1723528280.882174 | pos=0.2317 m, x=0.2008 m, y=0.0806 m, z=0.0829 m, yaw=0.2704 deg, dominant=yaw, samples=73 | pos=0.5441 m, x=0.1923 m, y=0.5028 m, z=0.0790 m, yaw=0.4936 deg, dominant=y, yaw, samples=73 |
| 8 | left_turn | temporal_phase | 1723528280.882174 → 1723528285.674305 | pos=0.3552 m, x=0.3170 m, y=0.1594 m, z=0.0177 m, yaw=0.5414 deg, dominant=yaw, samples=47 | pos=0.6464 m, x=0.1743 m, y=0.6045 m, z=0.1483 m, yaw=0.4862 deg, dominant=y, samples=47 |
| 9 | straight_road | temporal_phase | 1723528285.674305 → 1723528306.693810 | pos=0.7073 m, x=0.3309 m, y=0.1216 m, z=0.6132 m, yaw=0.1503 deg, dominant=z, samples=209 | pos=0.9643 m, x=0.2016 m, y=0.7858 m, z=0.5212 m, yaw=0.7835 deg, dominant=y, yaw, samples=209 |
| 10 | trees+building_occlusion | temporal_phase | 1723528306.693810 → 1723528317.083501 | pos=0.3522 m, x=0.2463 m, y=0.2240 m, z=0.1151 m, yaw=0.1690 deg, dominant=x, y, samples=103 | pos=1.4159 m, x=0.6169 m, y=0.8226 m, z=0.9734 m, yaw=0.8333 deg, dominant=z, samples=103 |
| 11 | u-turn | temporal_phase | 1723528317.083501 → 1723528334.696008 | pos=0.6730 m, x=0.5427 m, y=0.3855 m, z=0.0996 m, yaw=4.2692 deg, dominant=yaw, samples=174 | pos=1.5437 m, x=0.7542 m, y=0.8988 m, z=1.0032 m, yaw=3.9043 deg, dominant=yaw, samples=174 |
| 12 | speed_breaker | temporal_phase | 1723528334.696008 → 1723528336.569798 | pos=0.2682 m, x=0.2536 m, y=0.0860 m, z=0.0145 m, yaw=1.0281 deg, dominant=yaw, samples=19 | pos=1.8656 m, x=0.3088 m, y=1.6418 m, z=0.8305 m, yaw=7.7807 deg, dominant=yaw, samples=19 |
| 13 | straight_road | temporal_phase | 1723528336.569798 → 1723528356.963645 | pos=4.5109 m, x=2.0526 m, y=4.0106 m, z=0.2248 m, yaw=9.0227 deg, dominant=yaw, samples=202 | pos=5.8314 m, x=1.7799 m, y=5.5138 m, z=0.6596 m, yaw=3.9356 deg, dominant=y, samples=202 |
| 14 | right_turn | temporal_phase | 1723528356.963645 → 1723528362.235453 | pos=2.9045 m, x=2.7904 m, y=0.8003 m, z=0.0979 m, yaw=20.6319 deg, dominant=yaw, samples=52 | pos=10.1317 m, x=6.5158 m, y=7.7521 m, z=0.3189 m, yaw=28.1093 deg, dominant=yaw, samples=52 |
| 15 | straight_road | temporal_phase | 1723528362.235453 → 1723528378.383415 | pos=7.2230 m, x=6.2823 m, y=3.5625 m, z=0.1131 m, yaw=23.9357 deg, dominant=yaw, samples=160 | pos=15.4515 m, x=15.1017 m, y=3.2655 m, z=0.1588 m, yaw=16.9041 deg, dominant=yaw, samples=160 |

**Most affected segment:** `straight_road` with relative position RMSE 7.2230 m and dominant component(s): yaw.

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
