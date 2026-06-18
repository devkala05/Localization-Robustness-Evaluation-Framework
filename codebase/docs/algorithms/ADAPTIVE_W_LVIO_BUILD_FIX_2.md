# Adaptive-W LVIO build fix 2

The failed Docker build reached the catkin workspace and then failed only at the upstream `lvio_fusion` package. The visible Docker output did not include the actual compiler/CMake error; it only showed `Failed <<< lvio_fusion`, followed by abandoned dependent packages.

This patch fixes the common clean-Docker build issues in `jypjypjypjyp/lvio_fusion` without modifying algorithm logic:

- Adds a Docker-time patch script: `docker/adaptive_w_lvio/patch_lvio_fusion_cmake.py`.
- Keeps Sophus pinned to `1.22.10` for ROS Noetic/focal CMake compatibility.
- Adds `libgflags-dev` and `libunwind-dev` for glog/Ceres-related linking.
- Adds a minimal `FindGlog.cmake` into the upstream package after clone.
- Ensures the core `lvio_fusion` CMake calls `find_package(catkin REQUIRED)` before `catkin_package()`.
- Adds `${catkin_INCLUDE_DIRS}` to the core package include paths.
- Adds a `Sophus::Sophus` target fallback for Sophus config variants.
- Adds missing `geometry_msgs` in the node package's catkin components when needed.
- Builds `lvio_fusion` separately and dumps its catkin log if it still fails.

Rebuild command:

```bash
./build_adaptive_w_lvio.sh --no-cache
```

If it still fails, the Docker output should now show the exact `lvio_fusion` CMake/compiler error instead of only the package summary.
