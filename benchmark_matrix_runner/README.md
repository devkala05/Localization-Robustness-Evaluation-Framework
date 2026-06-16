# Benchmark Matrix Runner

Put this folder inside the original codebase root. It does **not** modify your codebase.

```bash
cp -r benchmark_matrix_runner /path/to/localisation_benchmark_code/
cd /path/to/localisation_benchmark_code/benchmark_matrix_runner
chmod +x run_all.sh
```

## Important behavior

- Builds **once per algorithm only**.
- Does **not rebuild** when perturbation or GPS mode changes.
- No build timeout by default.
- No run timeout by default.
- It waits for each run to finish before starting the next one.
- If the run script returns but a matching Docker container is still running, it keeps waiting.
- Logs are saved under:

```text
data/batch_runs/<timestamp>/logs/
data/batch_runs/<timestamp>/summary.tsv
```

## Run all algos, all perturbations, GPS off + on

```bash
./run_all.sh
```

Default algos:

```text
fastlio2,lvisam,fastlivo2,rtabmap,adaptive_w_lvio,orbslam3,r3live
```

## Selected algos

```bash
./run_all.sh --algos fastlio2,lvisam,rtabmap,r3live
```

## Selected perturbations

```bash
./run_all.sh --algos r3live --per 0-6
./run_all.sh --algos r3live --per 0,2,5
```

## GPS modes

```bash
./run_all.sh --gps both
./run_all.sh --gps off
./run_all.sh --gps on
```

## Skip build when already built

```bash
./run_all.sh --no-build --algos lvisam,rtabmap --per 0-6 --gps both
```

## Force no-cache build once per algo

```bash
./run_all.sh --build-no-cache --algos r3live --per 0 --gps off
```

## Time behavior

Default:

```text
min-run-min = 20
max-run-min = 0
```

`max-run-min=0` means no hard timeout. It will not kill a long build or run.

To add a hard timeout only when you really want it:

```bash
./run_all.sh --max-run-min 60
```

## Add extra args to every run

Example if your codebase supports headless runs:

```bash
./run_all.sh --extra-run-args "--headless"
```
