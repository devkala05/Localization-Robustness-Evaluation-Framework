# FAST-LIVO2 Pipeline Results

This directory receives all pipeline outputs. It is created empty and populated at runtime.

## Generated Files

| File | Description |
|------|-------------|
| `trajectory_tum.txt` | Trajectory in TUM format: `timestamp tx ty tz qx qy qz qw` |
| `odometry.csv` | Full odometry CSV: pose + velocity columns |
| `trajectory.csv` | Trajectory CSV (from trajectory_exporter.py) |
| `trajectory_kitti.txt` | Trajectory in KITTI 3×4 matrix format |
| `fast_livo2_output.bag` | Rosbag with all FAST-LIVO2 output topics |
| `fast_livo2_map.pcd` | Final accumulated point-cloud map |

## Evaluation

Use the `evo` toolkit to evaluate trajectory quality:

```bash
pip install evo
evo_traj tum trajectory_tum.txt --plot
```
