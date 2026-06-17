# Adaptive-W LVIO build fix

The Adaptive-W/LVIO-Fusion Docker image is based on `ros:noetic-ros-base-focal`, whose apt CMake version is 3.16.3. The latest `strasdat/Sophus` main branch now requires CMake 3.24+, so building Sophus from `main` fails during Docker build.

Fix applied:

- Pin Sophus to tag `1.22.10`.
- Disable Sophus tests/examples.
- Enable `SOPHUS_USE_BASIC_LOGGING=ON` to avoid optional fmt dependency issues.
- Keep Ubuntu 20.04 / ROS Noetic unchanged.

The Dockerfile exposes this as:

```dockerfile
ARG SOPHUS_TAG=1.22.10
```

Override only if needed:

```bash
docker build --build-arg SOPHUS_TAG=<tag> ...
```

