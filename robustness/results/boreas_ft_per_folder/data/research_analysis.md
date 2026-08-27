# Research Analysis

All statements below are generated only from valid campaign artifacts. Results are one replay per condition; a negative change is reported as a score difference, not an improvement claim.

## Overall robustness

Among systems without a configured localization failure, **FAST-LIO2** has the smallest worst-case relative 3D-RMSE change (-2.8%). **FAST-LIVO2** has the lowest clean-baseline 3D RMSE (0.521 m), but its worst perturbation increase is +9.1%.

**RTAB-Map** is excluded from the robustness ranking: the configured failure/dropout criterion was triggered in every condition, and recovery was not detected. Its RMSE values remain reported as failure evidence, not as a robustness win.

## Rain

Smallest score change among operational systems: **FAST-LIO2** (-4.0%). Largest increase: **FAST-LIVO2** (+0.6%).

## Fog

Smallest score change among operational systems: **FAST-LIO2** (-3.0%). Largest increase: **FAST-LIVO2** (+9.1%).

## Sensor Degradation

Smallest score change among operational systems: **ORB-SLAM3** (-10.7%). Largest increase: **FAST-LIVO2** (+2.9%).

## Sensor dependency and recovery

- **FAST-LIVO2** (LiDAR-camera-IMU): Rain: 0.054 s, Fog: 0.007 s, Sensor Degradation: 0.005 s.
- **FAST-LIO2** (LiDAR-IMU): Rain: 0.099 s, Fog: 0.095 s, Sensor Degradation: 0.092 s.
- **LVI-SAM** (LiDAR-IMU (visual branch disabled by campaign default)): Rain: 0.199 s, Fog: 0.196 s, Sensor Degradation: 0.193 s.
- **FLOAM** (LiDAR-only): Rain: 0.099 s, Fog: 0.095 s, Sensor Degradation: 0.092 s.
- **ORB-SLAM3** (visual RGB-D): Rain: 0.054 s, Fog: 0.017 s, Sensor Degradation: 0.106 s.
- **RTAB-Map** (LiDAR-IMU ICP/graph): Rain: not recovered, Fog: not recovered, Sensor Degradation: not recovered.

Rain and fog directly attack LiDAR returns, while fog additionally attacks image contrast/depth. The sensor-disturbance case directly attacks IMU/GNSS; the configured standalone FLOAM and visual RGB-D modes do not consume GNSS/IMU, so any change there must be interpreted alongside run-to-run determinism rather than attributed to those unused topics.
