# Algorithm Integrations

All production algorithms are launched through the root `./run` CLI and configured in `wrappers/localization_benchmark/config/algorithms.yaml`.

## Canonical Names

| CLI name | Display name | Result ID | Build script |
| --- | --- | --- | --- |
| `fastlio2` | FAST-LIO2 | `fast_lio2` | `./build_fastlio2.sh` |
| `lvisam` | LVI-SAM | `lvi_sam` | `./build_lvisam.sh` |
| `fastlivo2` | FAST-LIVO2 | `fast_livo2` | `./build_fastlivo2.sh` |
| `rtabmap` | RTAB-Map ICP | `rtab_map` | `./build_rtabmap.sh` |
| `adaptive_w_lvio` | Adaptive-W LVIO | `adaptive_w_lvio` | `./build_adaptive_w_lvio.sh` |
| `orbslam3` | ORB-SLAM3 | `orb_slam3` | `./build_orbslam3.sh` |
| `r3live` | R3LIVE | `r3live` | `./build_r3live.sh` |

## Common Commands

```bash
./run --list
./run --algo <name> --per <0..6> --gps off --eval
./run --algo <name> --per <0..6> --gps on --eval
```

The default runtime path uses the image built by the matching build script. Use `--runtime-build` only when you intentionally want package compilation during the run container startup.

## Common Outputs

Every integration publishes the same benchmark surface:

```text
/<algo>/odometry/local
/<algo>/path/local
/<algo>/odometry/output
/<algo>/path/output
/<algo>/status
```

Recorded trajectories are stored under:

```text
data/results/<dataset>/<result_id>/<with_gps|without_gps>/per_<N>/<YYYY-MM-DD_HH-MM-SS>/trajectory.csv
data/results/<dataset>/<result_id>/<with_gps|without_gps>/per_<N>/<YYYY-MM-DD_HH-MM-SS>/metrics.json
data/results/<dataset>/<result_id>/<with_gps|without_gps>/per_<N>/<YYYY-MM-DD_HH-MM-SS>/analysis.txt
```

## Removed Algorithms

`fastlivo` and `lirlivo` are intentionally not part of the maintained benchmark. FAST-LIVO2 supersedes FAST-LIVO, and LIR-LIVO was removed with its extra TensorRT/third-party dependency path.
