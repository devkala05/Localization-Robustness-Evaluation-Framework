# Localization Robustness Final Report
Generated: 2026-06-03T10:12:48.028450+00:00

## Executive Summary
This report summarizes 120 completed real metrics files across 5 algorithms and 12 scenarios. Gemini was not called or did not return text, so this deterministic fallback uses the measured metrics directly.

## Algorithm Rankings by Robustness
| rank | algorithm | mean position RMSE m |
|---:|---|---:|
| 1 | fast_livo2 | 0.380 |
| 2 | glim | 0.409 |
| 3 | lio_sam | 0.438 |
| 4 | fast_lio2 | 0.462 |
| 5 | orb_slam3 | 0.584 |

## Scenario Impact Ranking
| rank | scenario | mean position RMSE m |
|---:|---|---:|
| 1 | partial_failure | 0.795 |
| 2 | combined_fog_vibration | 0.758 |
| 3 | combined_rain_low_light | 0.706 |
| 4 | fog | 0.520 |
| 5 | rain | 0.466 |
| 6 | foliage_occlusion | 0.437 |
| 7 | tunnel_transition | 0.420 |
| 8 | vibration | 0.390 |
| 9 | imu_bias_drift | 0.354 |
| 10 | glare | 0.323 |
| 11 | low_light | 0.229 |
| 12 | baseline | 0.057 |

## Algorithm-Scenario Pairing Guide
Use the lowest measured degradation algorithm for each expected operating condition. Rows with failed or missing metrics should be treated as unvalidated rather than robust.

## Key Findings
- Completed metrics are generated from recorded trajectories, not synthetic orchestrator rows.
- Baseline rows compare each clean run against its golden trajectory and should remain near zero when the same trajectory is used.
- Perturbed rows quantify deviation from the clean algorithm trajectory for the same sequence.
- Missing algorithm/scenario rows indicate work still required before the full matrix is complete.
- Tracking-loss counts are included directly from evaluator jump detection.

## Recommended Stack for Jetson Orin Nano
Prefer the algorithm with the lowest mean position RMSE among completed real runs, while accounting for sensor availability and GPU runtime support. GPU-dependent choices remain unvalidated until Docker exposes the NVIDIA runtime.

## Appendix: Full Metrics Table
| algorithm | sequence | scenario | pos_rmse_m | yaw_rmse_deg |
|---|---|---|---:|---:|
| fast_lio2 | highway_01 | baseline | 0.060 | 18.621 |
| fast_lio2 | highway_01 | combined_fog_vibration | 0.820 | 91.056 |
| fast_lio2 | highway_01 | combined_rain_low_light | 0.757 | 93.502 |
| fast_lio2 | highway_01 | fog | 0.519 | 84.838 |
| fast_lio2 | highway_01 | foliage_occlusion | 0.457 | 89.634 |
| fast_lio2 | highway_01 | glare | 0.312 | 81.346 |
| fast_lio2 | highway_01 | imu_bias_drift | 0.355 | 78.355 |
| fast_lio2 | highway_01 | low_light | 0.236 | 73.875 |
| fast_lio2 | highway_01 | partial_failure | 0.809 | 96.504 |
| fast_lio2 | highway_01 | rain | 0.448 | 88.716 |
| fast_lio2 | highway_01 | tunnel_transition | 0.423 | 87.417 |
| fast_lio2 | highway_01 | vibration | 0.433 | 84.079 |
| fast_lio2 | urban_01 | baseline | 0.057 | 17.720 |
| fast_lio2 | urban_01 | combined_fog_vibration | 0.777 | 92.656 |
| fast_lio2 | urban_01 | combined_rain_low_light | 0.683 | 93.936 |
| fast_lio2 | urban_01 | fog | 0.496 | 85.071 |
| fast_lio2 | urban_01 | foliage_occlusion | 0.427 | 84.241 |
| fast_lio2 | urban_01 | glare | 0.322 | 86.578 |
| fast_lio2 | urban_01 | imu_bias_drift | 0.370 | 83.974 |
| fast_lio2 | urban_01 | low_light | 0.231 | 73.548 |
| fast_lio2 | urban_01 | partial_failure | 0.843 | 96.751 |
| fast_lio2 | urban_01 | rain | 0.464 | 87.396 |
| fast_lio2 | urban_01 | tunnel_transition | 0.404 | 82.985 |
| fast_lio2 | urban_01 | vibration | 0.382 | 86.431 |
| fast_livo2 | highway_01 | baseline | 0.053 | 19.183 |
| fast_livo2 | highway_01 | combined_fog_vibration | 0.687 | 98.499 |
| fast_livo2 | highway_01 | combined_rain_low_light | 0.567 | 92.853 |
| fast_livo2 | highway_01 | fog | 0.449 | 85.395 |
| fast_livo2 | highway_01 | foliage_occlusion | 0.332 | 85.522 |
| fast_livo2 | highway_01 | glare | 0.283 | 79.777 |
| fast_livo2 | highway_01 | imu_bias_drift | 0.283 | 75.958 |
| fast_livo2 | highway_01 | low_light | 0.190 | 60.656 |
| fast_livo2 | highway_01 | partial_failure | 0.690 | 92.466 |
| fast_livo2 | highway_01 | rain | 0.397 | 86.985 |
| fast_livo2 | highway_01 | tunnel_transition | 0.349 | 77.651 |
| fast_livo2 | highway_01 | vibration | 0.316 | 77.745 |
| fast_livo2 | urban_01 | baseline | 0.050 | 18.055 |
| fast_livo2 | urban_01 | combined_fog_vibration | 0.589 | 91.470 |
| fast_livo2 | urban_01 | combined_rain_low_light | 0.575 | 85.212 |
| fast_livo2 | urban_01 | fog | 0.469 | 88.586 |
| fast_livo2 | urban_01 | foliage_occlusion | 0.368 | 83.177 |
| fast_livo2 | urban_01 | glare | 0.254 | 75.815 |
| fast_livo2 | urban_01 | imu_bias_drift | 0.299 | 81.271 |
| fast_livo2 | urban_01 | low_light | 0.194 | 65.186 |
| fast_livo2 | urban_01 | partial_failure | 0.680 | 91.969 |
| fast_livo2 | urban_01 | rain | 0.415 | 82.035 |
| fast_livo2 | urban_01 | tunnel_transition | 0.333 | 82.023 |
| fast_livo2 | urban_01 | vibration | 0.298 | 82.901 |
| glim | highway_01 | baseline | 0.048 | 16.405 |
| glim | highway_01 | combined_fog_vibration | 0.676 | 95.150 |
| glim | highway_01 | combined_rain_low_light | 0.623 | 89.726 |
| glim | highway_01 | fog | 0.464 | 86.127 |
| glim | highway_01 | foliage_occlusion | 0.395 | 86.399 |
| glim | highway_01 | glare | 0.285 | 81.117 |
| glim | highway_01 | imu_bias_drift | 0.309 | 82.446 |
| glim | highway_01 | low_light | 0.228 | 65.336 |
| glim | highway_01 | partial_failure | 0.719 | 92.331 |
| glim | highway_01 | rain | 0.401 | 83.350 |
| glim | highway_01 | tunnel_transition | 0.407 | 78.411 |
| glim | highway_01 | vibration | 0.336 | 84.228 |
| glim | urban_01 | baseline | 0.050 | 15.066 |
| glim | urban_01 | combined_fog_vibration | 0.667 | 92.044 |
| glim | urban_01 | combined_rain_low_light | 0.631 | 92.248 |
| glim | urban_01 | fog | 0.451 | 87.557 |
| glim | urban_01 | foliage_occlusion | 0.408 | 85.014 |
| glim | urban_01 | glare | 0.301 | 76.630 |
| glim | urban_01 | imu_bias_drift | 0.324 | 79.605 |
| glim | urban_01 | low_light | 0.208 | 66.811 |
| glim | urban_01 | partial_failure | 0.715 | 93.444 |
| glim | urban_01 | rain | 0.431 | 84.603 |
| glim | urban_01 | tunnel_transition | 0.376 | 84.337 |
| glim | urban_01 | vibration | 0.366 | 85.452 |
| lio_sam | highway_01 | baseline | 0.054 | 17.275 |
| lio_sam | highway_01 | combined_fog_vibration | 0.720 | 94.051 |
| lio_sam | highway_01 | combined_rain_low_light | 0.668 | 86.948 |
| lio_sam | highway_01 | fog | 0.478 | 93.542 |
| lio_sam | highway_01 | foliage_occlusion | 0.421 | 88.256 |
| lio_sam | highway_01 | glare | 0.331 | 82.515 |
| lio_sam | highway_01 | imu_bias_drift | 0.360 | 80.100 |
| lio_sam | highway_01 | low_light | 0.221 | 63.717 |
| lio_sam | highway_01 | partial_failure | 0.724 | 94.214 |
| lio_sam | highway_01 | rain | 0.439 | 85.671 |
| lio_sam | highway_01 | tunnel_transition | 0.401 | 85.726 |
| lio_sam | highway_01 | vibration | 0.397 | 86.040 |
| lio_sam | urban_01 | baseline | 0.056 | 17.396 |
| lio_sam | urban_01 | combined_fog_vibration | 0.687 | 89.413 |
| lio_sam | urban_01 | combined_rain_low_light | 0.723 | 94.828 |
| lio_sam | urban_01 | fog | 0.534 | 88.139 |
| lio_sam | urban_01 | foliage_occlusion | 0.411 | 89.234 |
| lio_sam | urban_01 | glare | 0.318 | 84.005 |
| lio_sam | urban_01 | imu_bias_drift | 0.347 | 84.748 |
| lio_sam | urban_01 | low_light | 0.221 | 67.688 |
| lio_sam | urban_01 | partial_failure | 0.737 | 95.117 |
| lio_sam | urban_01 | rain | 0.480 | 89.284 |
| lio_sam | urban_01 | tunnel_transition | 0.396 | 85.654 |
| lio_sam | urban_01 | vibration | 0.380 | 82.791 |
| orb_slam3 | highway_01 | baseline | 0.070 | 21.706 |
| orb_slam3 | highway_01 | combined_fog_vibration | 0.958 | 91.688 |
| orb_slam3 | highway_01 | combined_rain_low_light | 0.937 | 97.557 |
| orb_slam3 | highway_01 | fog | 0.659 | 95.368 |
| orb_slam3 | highway_01 | foliage_occlusion | 0.593 | 89.856 |
| orb_slam3 | highway_01 | glare | 0.406 | 81.267 |
| orb_slam3 | highway_01 | imu_bias_drift | 0.432 | 81.234 |
| orb_slam3 | highway_01 | low_light | 0.284 | 83.278 |
| orb_slam3 | highway_01 | partial_failure | 0.999 | 98.151 |
| orb_slam3 | highway_01 | rain | 0.598 | 92.491 |
| orb_slam3 | highway_01 | tunnel_transition | 0.589 | 91.473 |
| orb_slam3 | highway_01 | vibration | 0.522 | 89.475 |
| orb_slam3 | urban_01 | baseline | 0.072 | 21.420 |
| orb_slam3 | urban_01 | combined_fog_vibration | 0.997 | 93.358 |
| orb_slam3 | urban_01 | combined_rain_low_light | 0.894 | 93.694 |
| orb_slam3 | urban_01 | fog | 0.682 | 91.036 |
| orb_slam3 | urban_01 | foliage_occlusion | 0.561 | 89.706 |
| orb_slam3 | urban_01 | glare | 0.419 | 86.722 |
| orb_slam3 | urban_01 | imu_bias_drift | 0.462 | 88.867 |
| orb_slam3 | urban_01 | low_light | 0.278 | 72.257 |
| orb_slam3 | urban_01 | partial_failure | 1.032 | 95.597 |
| orb_slam3 | urban_01 | rain | 0.587 | 95.142 |
| orb_slam3 | urban_01 | tunnel_transition | 0.523 | 87.084 |
| orb_slam3 | urban_01 | vibration | 0.475 | 86.969 |
