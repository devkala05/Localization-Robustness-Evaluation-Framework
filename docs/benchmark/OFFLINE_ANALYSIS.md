# Offline Analysis

Analysis scripts read completed benchmark results from:

```text
data/results/<result_id>/per_<N>/trajectory.csv
```

Canonical CLI names are accepted by the scripts, and result IDs with underscores are also accepted for plotting/comparison aliases.

## Algorithms

```text
fastlio2, lvisam, fastlivo2, rtabmap, adaptive_w_lvio, orbslam3, r3live
```

Result IDs:

```text
fast_lio2, lvi_sam, fast_livo2, rtab_map, adaptive_w_lvio, orb_slam3, r3live
```

## RViz Trajectory Viewer

```bash
./plot.sh --per 0 --algo all
./plot.sh --per 0 --algo fastlio2,lvisam,r3live
```

By default `plot.sh` opens RViz through Docker and publishes:

```text
/ground_truth_path
/offline/trajectory_markers
/offline/<result_id>/path
```

Use static PNG mode instead:

```bash
./plot.sh --static --per 0 --algo all
```

Use host ROS/RViz instead of Docker:

```bash
./plot.sh --no-docker --per 0 --algo all
```

## Cross-Algorithm Reports

```bash
./compare_results.sh --per 0 --algo all
./compare_results.sh --per 0 --algo fastlio2,lvisam,r3live
```

Outputs are saved under:

```text
data/analysis/per_<N>/all_algos/
```

Typical files:

```text
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

## Perturbation Comparison

```bash
./per_compare.sh --algo fastlio2 --per all
./per_compare.sh --algo fastlio2 --per 1-6
./per_compare.sh --algo all --per all
```

Outputs are saved under:

```text
data/analysis/per_compare/<result_id>/
```

Typical files:

```text
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

## Thresholds And Custom Paths

```bash
./compare_results.sh --per 0 --algo all --jump-distance 8.0 --jump-speed 50.0
```

```bash
./compare_results.sh \
  --per 0 \
  --algo all \
  --results-root data/results \
  --gt data/UrbanNav_TST_GT_raw.txt
```
