# Benchmark Matrix Runner

This folder is standalone. Put `benchmark_matrix_runner/` inside your existing codebase root. It does **not** modify the codebase.

```bash
cd localisation_benchmark_code/benchmark_matrix_runner
chmod +x *.sh
```

Run all 7 algorithms, all perturbations 0-6, GPS off + on:

```bash
./run_all.sh
```

Run selected algorithms:

```bash
./run_all.sh --algos fastlio2,lvisam,rtabmap,r3live
```

Run selected perturbations:

```bash
./run_all.sh --algos r3live --per 0-6
./run_all.sh --algos lvisam --per 0,2,4
```

Run GPS off only or GPS on only:

```bash
./run_all.sh --gps off
./run_all.sh --gps on
```

Skip builds if images are already built:

```bash
./run_all.sh --no-build --algos fastlio2,lvisam --per 0-6 --gps both
```

One run only:

```bash
./run_one.sh r3live 0 off
./run_one.sh lvisam 3 on
```

Default behavior:

- Builds each selected algorithm once first.
- Runs every selected `algo × perturbation × gps` combination sequentially.
- Passes `--eval` by default.
- Passes `--r3live-vio true` for R3LIVE by default.
- Waits at least 20 minutes per run by default.
- Kills the run/container if it exceeds 30 minutes by default.
- Continues to the next run even if one fails.
- Logs go to:

```text
benchmark_matrix_runner/logs/<timestamp>/
```

Main summary file:

```text
benchmark_matrix_runner/logs/<timestamp>/summary.tsv
```

Useful options:

```bash
./run_all.sh --help
```
