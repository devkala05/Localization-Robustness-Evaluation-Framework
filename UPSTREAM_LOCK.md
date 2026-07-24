# Upstream source lock

Docker builds use explicit refs so rebuilding does not silently change native estimator code.

| Component | Repository | Ref |
|---|---|---|
| FAST-LIVO2 | `hku-mars/FAST-LIVO2` | `0d2c0346107b75b59934975adec9a6eeeb913c64` |
| rpg_vikit | `xuankuzcr/rpg_vikit` | `6c886c8e5d83997806e00294826d528cea3581dd` |
| Sophus (legacy non-template API required by FAST-LIVO2) | `obiou/Sophus` | `8032eaefcddac7f5a287b4eee3b4e737c5d0c2cd` |
| FAST-LIO2 (`FAST_LIO`) | `hku-mars/FAST_LIO` | `7cc4175de6f8ba2edf34bab02a42195b141027e9` |
| Livox ROS driver | `Livox-SDK/livox_ros_driver` | `3d240d5666129e1a3052e78ee8487a04b08fdda3` |
| Livox SDK | `Livox-SDK/Livox-SDK` | `9306596a2bf15c1343bc023b497465ed0a32909d` |
| ORB-SLAM3 | `UZ-SLAMLab/ORB_SLAM3` | `0df83dde1c85c7ab91a0d47de7a29685d046f637` (V1.0 tree) |
| Pangolin | `stevenlovegrove/Pangolin` | `v0.8` |
| LVI-SAM | `TixiaoShan/LVI-SAM` | `0d822f6dcac3378312f6703b4f45829e049f221a` |
| GTSAM | `borglab/gtsam` | `4.0.2` |
| RTAB-Map ROS packages | ROS Noetic final snapshot | `ros-noetic-rtabmap` 0.21.13, `ros-noetic-rtabmap-odom` 0.21.13 in the validated image |

The RTAB-Map packages come from the frozen ROS Noetic final snapshot rather than a
source checkout. Every benchmark run records the resulting Docker image ID, so a
package-snapshot change cannot be mistaken for the validated image.

Build-time compatibility patches are versioned in this repository. The
ORB-SLAM3 patch exposes native mono-inertial poses/keyframes without changing
tracking. The LVI-SAM patch supplies Noetic/OpenCV compatibility, avoids an
empty GPS subscription, and adds an opt-in calibrated VINS-to-LiDAR conversion
for public datasets. That conversion replaces the upstream hard-coded
camera/LiDAR axis quaternion with the dataset matrices for the mapper's initial
guess and depth-registration TF; the E2O configs leave it disabled.

Change a Docker build argument deliberately to update a dependency, then rerun all failure and trajectory tests.
