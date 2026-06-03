# Dataset Choice

Default selection: **KITTI Raw Dataset**.

KITTI is the better default for this pipeline because all required modalities are available in the raw data: Velodyne LiDAR, camera, IMU, and GPS/OXTS. It is also the cleaner choice for unattended evaluation across the requested algorithm set because KITTI has broad ROS bag wrapper support and is commonly used for LIO, VIO, and LVIO benchmarking.

UrbanNavDataset is a strong alternative for urban canyon and tunnel-like degradation realism, but the mixed ROS1 bag status and sequence packaging make it less predictable for a one-command Docker pipeline. The config keeps an UrbanNav topic map so it can be added later without changing the evaluator or orchestrator.

The default sequence slots are:

- `urban_01`: KITTI `2011_09_26_drive_0005_sync`, a longer residential/urban drive. This slot is intentionally mapped to the longer downloaded sequence because FAST-LIO2 begins publishing after initialization and the shorter drive does not produce more than 100 real odometry poses.
- `highway_01`: KITTI `2011_09_26_drive_0001_sync`, a shorter secondary drive used for contrast.

Calibration files should be placed in `config/calibration/kitti/` after dataset download.
