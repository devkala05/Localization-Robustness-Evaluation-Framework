# Adaptive-W LVIO build fix 3

The Docker build reached the upstream `lvio_fusion` package but failed with:

```text
fatal error: fmt/format.h: No such file or directory
```

Root cause: pinned Sophus 1.22.10 includes `<fmt/format.h>`, but the ROS Noetic focal image did not install fmt headers.

Fixes in this version:

- Install `libfmt-dev` in `docker/adaptive_w_lvio/Dockerfile`.
- Patch upstream `lvio_fusion` CMake to call `find_package(fmt REQUIRED)`.
- Append `fmt::fmt` to `THIRD_PARTY_LIBS` when the target exists.

This keeps the upstream LVIO-Fusion algorithm code unchanged; only Docker dependencies and CMake discovery/linking are adjusted.
