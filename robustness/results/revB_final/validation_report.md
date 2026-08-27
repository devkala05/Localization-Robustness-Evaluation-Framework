# Campaign validation

Source: original ALIVE `one_full_loop.bag`; no bag was rewritten. Ground truth was the frozen reference trajectory.

- Expected pairs: 24
- Completed execution with poses: 24/24
- Trajectories passing finite/monotonic validation: 24/24
- Non-baseline runs with perturbation bridge and private adapter wiring recorded: 18/18

## Pair audit

| Algorithm | Scenario | Execution | Poses | Trajectory validation |
|---|---|---|---:|---|
| FAST-LIVO2 | baseline | completed | 2511 | True |
| FAST-LIVO2 | rain | completed | 2498 | True |
| FAST-LIVO2 | fog | completed | 2506 | True |
| FAST-LIVO2 | sensor_degradation | completed | 2487 | True |
| FAST-LIO2 | baseline | completed | 3056 | True |
| FAST-LIO2 | rain | completed | 3056 | True |
| FAST-LIO2 | fog | completed | 3056 | True |
| FAST-LIO2 | sensor_degradation | completed | 3056 | True |
| LVI-SAM | baseline | completed | 1528 | True |
| LVI-SAM | rain | completed | 1528 | True |
| LVI-SAM | fog | completed | 1528 | True |
| LVI-SAM | sensor_degradation | completed | 1528 | True |
| FLOAM | baseline | completed | 3059 | True |
| FLOAM | rain | completed | 3059 | True |
| FLOAM | fog | completed | 3059 | True |
| FLOAM | sensor_degradation | completed | 3059 | True |
| ORB-SLAM3 | baseline | completed | 2073 | True |
| ORB-SLAM3 | rain | completed | 2073 | True |
| ORB-SLAM3 | fog | completed | 2073 | True |
| ORB-SLAM3 | sensor_degradation | completed | 2073 | True |
| RTAB-Map | baseline | completed | 2977 | True |
| RTAB-Map | rain | completed | 1575 | True |
| RTAB-Map | fog | completed | 1642 | True |
| RTAB-Map | sensor_degradation | completed | 2973 | True |

## Interpretation of zero or negative changes

FLOAM is evaluated in its LiDAR-only mode; GPS/IMU disturbance is not an input to that estimator, so zero sensor-degradation change is physically expected and is not evidence that the perturbation failed.
RTAB-Map's previous 0% worst-change summary was misleading: its run metrics are marked localization failure/dropout and it did not recover. The revised comparison table reports `FAIL` instead of ranking that value as robustness.
Negative percentage changes are retained as measured replay differences. They are not described as improvements because one run per condition cannot separate estimator robustness from scan selection/timing variability.
