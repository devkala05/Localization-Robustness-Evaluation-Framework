# UrbanNav Localization Benchmark

ROS1/Noetic Docker benchmark for UrbanNav-HK TST localization with LiDAR, visual, and GPS-assisted pipelines under seven perturbation cases.

## Required Data

Place these files under `data/`:

```text
data/UrbanNav-HK_TST-20210517_sensors.bag
data/UrbanNav_TST_GT_raw.txt
data/gnss/urbannav_tst_gnss.csv
```

The GNSS CSV is optional for GPS-off runs, but `--gps on` defaults to that path.

## Algorithms

Canonical CLI names:

```text
fastlio2
lvisam
fastlivo2
rtabmap
adaptive_w_lvio
orbslam3
r3live
```

Result directory names:

```text
fast_lio2
lvi_sam
fast_livo2
rtab_map
adaptive_w_lvio
orb_slam3
r3live
```

## Build

Build each image once before running with the default `--skip-build` path:

```bash
./build_fastlio2.sh
./build_lvisam.sh
./build_fastlivo2.sh
./build_rtabmap.sh
./build_adaptive_w_lvio.sh
./build_orbslam3.sh
./build_r3live.sh
```

Most build scripts also accept `--no-cache`.

## Run One Case

```bash
./run --algo fastlio2 --per 0 --gps off --eval
./run --algo fastlio2 --per 0 --gps on --eval
./run --algo orbslam3 --per 0 --gps off --orb-mode stereo --eval
```

Perturbation IDs are `0..6`. `--eval` records a timestamped result folder, updates `data/results/<result_id>/per_<N>/trajectory.csv`, runs evaluation, and refreshes `robustness_ranking.txt`. Add `--duration 30` for a short run; omit it or pass `0` for the full bag.

Useful options:

```bash
./run --list
./run --algo <name> --shell
./run --algo <name> --per <0..6> --runtime-build
./run --algo <name> --per <0..6> --bag data/custom.bag --gt data/custom_gt.txt
```

## Run Full Matrix

`run_all_algos_new_terminals.sh` builds each algorithm once, then runs every selected perturbation and GPS mode sequentially in a new terminal:

```bash
./run_all_algos_new_terminals.sh
```

Default matrix:

```text
7 algorithms x 7 perturbations x 2 GPS modes = 98 evaluated runs
```

Resume or narrow the matrix:

```bash
START_ALGO=rtabmap ./run_all_algos_new_terminals.sh
START_PER=3 ./run_all_algos_new_terminals.sh
ALGO_LIST="lvisam rtabmap" ./run_all_algos_new_terminals.sh
PER_LIST="0 3 6" GPS_LIST="on" ./run_all_algos_new_terminals.sh
```

The launcher needs a supported GUI terminal: `gnome-terminal`, `kgx`, `konsole`, `xfce4-terminal`, `xterm`, or `x-terminal-emulator`.

## Standard Output Topics

Every algorithm is normalized to:

```text
/<algo>/odometry/local
/<algo>/path/local
/<algo>/odometry/output
/<algo>/path/output
/<algo>/status
```

`/<algo>/odometry/output` is local odometry for GPS-off runs and the selected GPS-fused output when GPS is enabled and accepted.

## TF Policy

The benchmark keeps one dynamic TF authority for normal output:

```text
map -> camera_init          static
camera_init -> body         dynamic, from standard_output_republisher.py
body -> gnss_antenna        static
```

Algorithm-native dynamic TF is disabled, remapped, or suppressed where needed to avoid duplicate `camera_init -> body` publishers.

## Analysis

```bash
./plot.sh --per 0 --algo all
./compare_results.sh --per 0 --algo all
./per_compare.sh --algo all --per all
```

See `docs/benchmark/OFFLINE_ANALYSIS.md` for offline plotting and report details, `docs/gps/README.md` for GNSS mode, and `docs/algorithms/README.md` for per-algorithm notes.
