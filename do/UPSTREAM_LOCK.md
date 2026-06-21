# Upstream source lock

Docker builds use explicit refs so rebuilding does not silently change native estimator code.

| Component | Repository | Ref |
|---|---|---|
| FAST-LIVO2 | `hku-mars/FAST-LIVO2` | `0d2c0346107b75b59934975adec9a6eeeb913c64` |
| rpg_vikit | `xuankuzcr/rpg_vikit` | `6c886c8e5d83997806e00294826d528cea3581dd` |
| Sophus | `strasdat/Sophus` | `a621ff` |
| ORB-SLAM3 | `UZ-SLAMLab/ORB_SLAM3` | `0df83dde1c85c7ab91a0d47de7a29685d046f637` (V1.0 tree) |
| Pangolin | `stevenlovegrove/Pangolin` | `v0.8` |

Change a Docker build argument deliberately to update a dependency, then rerun all failure and trajectory tests.
