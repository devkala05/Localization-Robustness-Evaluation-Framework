# Algorithms

Enabled production benchmark algorithms:

- `fastlio2`
- `lvisam`
- `fastlivo2`
- `rtabmap`
- `adaptive_w_lvio`
- `orbslam3`
- `r3live`

Removed / intentionally unsupported:

- `fastlivo` — removed because FAST-LIVO2 supersedes it and the previous integration was unstable.
- `lirlivo` — removed with its TensorRT/third_party dependency path.

All algorithms are launched through the unified CLI:

```bash
./run --algo <name> --per <0..6> --gps off
./run --algo <name> --per <0..6> --gps on --gps-source csv --gps-file data/gnss/urbannav_tst_gnss.csv --eval
```
