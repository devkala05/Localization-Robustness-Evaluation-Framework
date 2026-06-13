# Offline trajectory plotting and comparison

These scripts work after runs have produced result CSVs like:

```text
data/results/<algo_result_id>/per_<N>/trajectory.csv
```

The expected final algorithms are:

```text
fastlio2, lvisam, fastlivo2, rtabmap, adaptive_w_lvio, orbslam3, r3live
```

## 1. Open a 3D comparison plot

Compare GT with all algorithms for one perturbation case:

```bash
./plot.sh --per 0 --algo all
```

Compare only specific algorithms:

```bash
./plot.sh --per 0 --algo fastlio2,lvisam,r3live
```

It also saves static plots under:

```text
data/analysis/per_<N>/plot3d/
```

## 2. Save cross-algorithm comparison plots and reports

```bash
./compare_results.sh --per 0 --algo all
```

Outputs:

```text
data/analysis/per_<N>/all_algos/
  summary.csv
  segment_comparison.csv
  segment_type_comparison.csv
  perturbation_window_comparison.csv
  jump_events.csv
  comparison_report.txt
  comparison_report.json
  trajectory_xy_gt_algos.png
  trajectory_3d_gt_algos.png
  position_error_over_time.png
  position_rmse_bar.png
  position_max_error_bar.png
  sudden_change_count_bar.png
```

The report highlights:

- overall RMSE and max error
- sudden pose jumps
- worst algorithm at turns, under bridges, stops, straights, etc.
- worst algorithm inside perturbation windows

## 3. Compare different perturbation runs of the same algorithm

```bash
./per_compare.sh --algo fastlio2 --per all
```

or only stress cases:

```bash
./per_compare.sh --algo fastlio2 --per 1-6
```

For all algorithms:

```bash
./per_compare.sh --algo all --per all
```

Outputs are saved under:

```text
data/analysis/per_compare/<algo>/
  per_summary.csv
  per_delta_vs_per0.csv
  perturbation_effects_vs_per0.csv
  jump_events.csv
  per_compare_report.txt
  per_xy_paths.png
  rmse_by_per.png
  max_error_by_per.png
  jump_count_by_per.png
  delta_vs_per0_by_per.png
```

`per_delta_vs_per0.csv` tells how much each perturbation run changed from the clean `per_0` trajectory.

## Useful thresholds

Sudden-change detection defaults:

```bash
--jump-distance 5.0
--jump-speed 35.0
```

If the detector is too strict or loose:

```bash
./compare_results.sh --per 0 --algo all --jump-distance 8.0 --jump-speed 50.0
```

## Custom GT/results paths

```bash
./compare_results.sh \
  --per 0 \
  --algo all \
  --results-root data/results \
  --gt data/UrbanNav_TST_GT_raw.txt
```

## RViz trajectory viewer

`plot.sh` now opens RViz by default instead of trying to open an interactive Matplotlib window.

Examples:

```bash
./plot.sh --per 0 --algo all
./plot.sh --per 0 --algo fast_lio2,lvisam,r3live
```

It reads saved trajectories from:

```text
data/results/<algo>/per_<N>/trajectory.csv
```

and publishes them into RViz as:

```text
/ground_truth_path
/offline/trajectory_markers
/offline/<algo>/path
```

The colored `MarkerArray` display is the easiest one to compare visually. The individual `Path` topics are also available in the RViz display list.

To keep the old PNG-only behavior:

```bash
./plot.sh --static --per 0 --algo all
```

If you want to run RViz without Docker and you already have ROS Noetic sourced on the host:

```bash
./plot.sh --no-docker --per 0 --algo all
```
