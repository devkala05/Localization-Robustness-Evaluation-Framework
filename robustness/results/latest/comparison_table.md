# ALIVE Robustness Comparison

Values are 3D RMSE in metres; parentheses give change relative to the clean baseline.

| Algorithm | Baseline | Rain | Fog | Sensor Degradation | Worst % degradation |
|---|---:|---:|---:|---:|---:|
| FAST-LIVO2 | 0.521 | 0.524 (+0.6%) | 0.569 (+9.1%) | 0.536 (+2.9%) | +9.1% |
| FAST-LIO2 | 0.597 | 0.573 (-4.0%) | 0.579 (-3.0%) | 0.580 (-2.8%) | -2.8% |
| LVI-SAM | 0.547 | 0.540 (-1.3%) | 0.545 (-0.5%) | 0.549 (+0.3%) | +0.3% |
| FLOAM | 0.640 | 0.621 (-2.9%) | 0.635 (-0.7%) | 0.640 (+0.0%) | +0.0% |
| ORB-SLAM3 | 1.096 | 1.080 (-1.5%) | 1.164 (+6.2%) | 0.979 (-10.7%) | +6.2% |
| RTAB-Map | 26.145 | 21.767 (-16.7%) | 10.917 (-58.2%) | 26.145 (+0.0%) | +0.0% |
