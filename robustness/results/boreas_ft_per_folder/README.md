# Presentation bundle: `boreas_ft_per_folder`

This requested folder name is preserved for the presentation handoff. The artifacts inside are from the validated ALIVE `one_full_loop.bag` campaign, not from a Boreas bag: no `boreas_ft` input was present or used in this run.

- `analysis/validation_report.md`: execution, trajectory, wiring, and interpretation audit.
- `analysis/comparison_table.md`: corrected summary; failed systems are marked `FAIL` instead of appearing as zero degradation.
- `analysis/detailed_tables.md`: X/Y/Z/XY/3D/yaw RMSE, maximum error, failure/dropout, recovery.
- `analysis/research_analysis.md`: evidence-based discussion with sensor-dependency caveats.
- `plots/`: slide-ready absolute-RMSE, relative-change, status-matrix, and perturbation-timeline figures.
- `data/`: machine-readable metrics, per-sample CSVs, and error-vs-time plots.
- `revB/`: final rerun after the perturbation-code fixes, using the stronger three-condition profile and the complete six-algorithm comparison. Use this directory for the presentation numbers.

The same original bag was replayed for every condition. Perturbations were injected live on private ROS topics; the bag and ground truth were not modified.
