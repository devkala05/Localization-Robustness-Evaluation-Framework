# ALIVE controlled perturbation evaluation

This directory implements the robustness campaign for the original ALIVE
`one_full_loop.bag`. The bag is never rewritten or copied. During a live run,
the player publishes its original messages, a deterministic bridge perturbs
only the configured sensor payloads/time window, and the unmodified estimator
receives those bridge outputs. The frozen reference trajectory is never an
input to the bridge or an estimator.

## Experimental design

The frozen configuration is
[`config/alive_perturbations.yaml`](config/alive_perturbations.yaml). Times are
seconds from the first rosbag record. The default windows are disjoint:

| Scenario | Interval | Modified raw topics |
|---|---:|---|
| Rain | 70–110 s | `/lidar103/velodyne_points` |
| Fog | 140–180 s | LiDAR, RGB image, depth image |
| Sensor degradation | 210–250 s | NavSatFix and IMU; GNSS outage is 228–240 s |

Rain applies stochastic return loss, radial ranging uncertainty, intensity
attenuation and a small population of low-intensity near-field false returns.
Fog applies range-dependent optical extinction to LiDAR and a veiling-light,
contrast and blur model to RGB, plus configurable loss of distant depth.
Sensor degradation applies a persistent multipath displacement, a true GNSS
message outage, IMU bias, bias random walk and measurement noise. A fixed seed
makes all samples reproducible.

The live bridge preserves original topic names at bag read time, ROS message
types, record/header timestamps, frames and TF. It republishes under private
bridge topics only; the existing input adapter subscribes there. A GNSS outage
intentionally omits only live NavSatFix publications in its outage subinterval.

## Run the six-by-four matrix

Build the six estimator images first, then run the complete matrix. Playback
rate changes wall-clock compute load only; sensor timestamps are unchanged.

```bash
./build.sh all
RVIZ=false ./robustness/run_alive_matrix.sh
```

The same runner, configs, recorder, reference CSV and SE(3) evaluator are used
for clean and live-perturbed streams. Individual/restartable examples:

```bash
./robustness/run_alive_matrix.sh --algorithm fastlivo2 --scenario rain
./robustness/run_alive_matrix.sh --algorithm fastlio2  --scenario fog
./robustness/run_alive_matrix.sh --algorithm lvisam    --scenario sensor_degradation
./robustness/run_alive_matrix.sh --algorithm floam     --scenario rain
./robustness/run_alive_matrix.sh --algorithm orbslam3  --scenario fog
./robustness/run_alive_matrix.sh --algorithm rtabmap   --scenario baseline
./robustness/run_alive_matrix.sh --skip-existing
```

Each pair is stored under
`results/alive/one_full_loop/<algorithm>/<campaign>_<scenario>_<algorithm>/`.
The campaign TSV is stored under `robustness/results/`. A rejected or failed
run is retained and explicitly reported; it is not silently converted into a
numeric success.

## Aggregate metrics and plots

```bash
./robustness/evaluate.sh
```

This produces:

- `robustness_metrics.json`: complete machine-readable metrics/provenance;
- `detailed_metrics.csv`: X/Y/Z/XY/3D/yaw RMSE, maximum error, failure and recovery;
- `detailed_tables.md`: paper-ready table for each clean/adverse condition;
- `comparison_table.md`: requested baseline/rain/fog/sensor comparison;
- one `*_per_sample_errors.csv` per valid run;
- one `*_error_vs_time.png` per algorithm, with the affected interval shaded;
- `research_analysis.md`, generated only if all 24 pairs have valid trajectories.

Recovery is the first post-perturbation time at which 3D error remains below
the configured threshold for the configured hold duration. A localization
failure is recorded for early trajectory termination, an output gap exceeding
the threshold, or a sustained high-error episode. These operational definitions
are frozen in YAML and should be reported with paper results.

## Interpretation constraint

GNSS is present in the bag but not consumed by every estimator configuration.
The report therefore attributes a response only to sensors actually consumed
by that mode. In particular, LiDAR-only FLOAM and RGB-D ORB-SLAM3 should not be
claimed to respond to GNSS/IMU corruption. The evaluator refuses to write a
winner/loser analysis until every required run contains an evaluable trajectory.
