# Final Numeric Robustness Results

Values are overall 3D RMSE in metres. Parentheses show change relative to the clean baseline. Execution-quality and recovery details remain in `detailed_tables.md` and `validation_report.md`.

| Algorithm | Baseline | Rain | Fog | Sensor Degradation |
|---|---:|---:|---:|---:|
| FAST-LIVO2 | 0.521 | 0.509 (-2.4%) | 0.501 (-3.9%) | 0.542 (+4.1%) |
| FAST-LIO2 | 0.597 | 0.555 (-7.1%) | 0.581 (-2.7%) | 0.596 (-0.1%) |
| LVI-SAM | 0.547 | 0.534 (-2.4%) | 0.544 (-0.5%) | 0.547 (-0.03%) |
| FLOAM | 0.640 | 0.610 (-4.6%) | 0.630 (-1.6%) | 0.632 (-1.2%) |
| ORB-SLAM3 | 1.096 | 1.127 (+2.8%) | 1.513 (+38.0%) | 1.124 (+2.6%) |
| RTAB-Map | 26.145 | 21.849 (-16.4%) | 10.635 (-59.3%) | 27.139 (+3.8%) |
