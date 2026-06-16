# compare_rviz

`compare_rviz` opens saved benchmark trajectories in RViz without replaying the bag or running an algorithm.

## Examples

```bash
./compare_rviz --algo rtabmap
./compare_rviz --algo rtabmap --per 0
./compare_rviz --algo rtabmap --per 0 --gps on
./compare_rviz --algo all --per 0
./compare_rviz --algo all --per 0 --results-root data/results/e2o --gt e20_GT_scripts/gt_one_full_loop_fastlivo2_lidar103.csv
```

`--algo rtabmap` shows the latest RTAB-Map trajectory for every available perturbation/GPS mode. Adding `--per 0` narrows that to the GPS comparison for `per_0`.

## Filters

```bash
./compare_rviz --algo fastlio2,lvisam --per 0,3,6
./compare_rviz --algo fastlio2 --per 0 --gps off
./compare_rviz --algo fastlio2 --per 0 --all-runs
./compare_rviz --algo fastlio2 --per 0 --list
```

By default the tool shows the latest run for each algorithm/per/GPS combination. Use `--all-runs` to include every timestamped rerun.

## RViz Topics

```text
/compare_rviz/markers
/compare_rviz/ground_truth/path
/compare_rviz/<run>/path
```

The marker layer contains the colored trajectories, start/end points, numeric labels, and a legend box with algorithm, perturbation, GPS mode, GPS source, RMSE when available, and timestamp.
