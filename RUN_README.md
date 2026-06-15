# Running the Benchmark

## 1. Put the E2O bag in place

```text
data/e2o/raw/one_full_loop.bag
```

## 2. Build

```bash
./build.sh all
```

A single integration can be built with, for example:

```bash
./build.sh fastlio2
```

## 3. Preflight the bag

```bash
./inspect_bag.sh --dataset e2o --strict
```

Resolve any missing `ring`/`time` field, unexpected camera dimensions, or non-overlapping GT clock before benchmarking.

## 4. Run

```bash
./run.sh --dataset e2o --algo <name> --per <0..6> --gps off
```

Automated recording and evaluation:

```bash
./run.sh --dataset e2o --algo <name> --per <0..6> --gps off --eval
```

A 60-second smoke run:

```bash
./run.sh --dataset e2o --algo fastlio2 --per 0 --gps off --eval --duration 60
```

Canonical names:

```text
fastlio2
lvisam
fastlivo2
rtabmap
adaptive_w_lvio
orbslam3
r3live
```

All seven baseline commands:

```bash
./run.sh --dataset e2o --algo fastlio2       --per 0 --gps off --eval
./run.sh --dataset e2o --algo lvisam         --per 0 --gps off --eval
./run.sh --dataset e2o --algo fastlivo2      --per 0 --gps off --eval
./run.sh --dataset e2o --algo rtabmap        --per 0 --gps off --eval
./run.sh --dataset e2o --algo adaptive_w_lvio --per 0 --gps off --eval
./run.sh --dataset e2o --algo orbslam3       --per 0 --gps off --eval
./run.sh --dataset e2o --algo r3live         --per 0 --gps off --eval
```

Use `--r3live-vio on` only when deliberately testing the experimental native visual path. ORB-SLAM3 automatically uses monocular mode on E2O.

## 5. Visualize saved trajectories

Open dataset-aware RViz comparison:

```bash
./plot.sh --dataset e2o --per 0 --algo all
```

Generate static plots instead:

```bash
./plot.sh --dataset e2o --per 0 --algo all --static
```

## 6. Results

```text
data/results/e2o/<algorithm>/per_<n>/trajectory.csv
```

Timestamped evaluation folders contain metrics, error series, analysis, and plots. The cross-algorithm ranking is written under:

```text
data/results/e2o/robustness_ranking.txt
```

## Important fairness rule

The supplied E2O reference was generated from MAVROS GPS plus IMU. Keep `--gps off` when scoring against it; GPS fusion against a GPS-derived reference is circular.
