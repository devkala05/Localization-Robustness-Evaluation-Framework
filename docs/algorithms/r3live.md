# R3LIVE

R3LIVE is integrated through `wrappers/r3live_urbannav` and runs native `r3live_mapping` in the maintained benchmark path.

## Build And Run

```bash
./build_r3live.sh
./run --algo r3live --per 0 --gps off --eval
./run --algo r3live --per 0 --gps on --eval
```

The first build is heavy because upstream R3LIVE, vikit, and the Livox driver are compiled.

## Inputs

```text
/livox/lidar
/livox/imu
/camera/right/image_raw
/camera/image_raw
```

The adapter adds fields expected by the R3LIVE path, including normal/curvature handling where configured.

## Outputs

```text
/r3live/odometry/mapping
/r3live/mapping/path
/r3live/odometry/local
/r3live/path/local
/r3live/odometry/output
/r3live/path/output
/r3live/status
```

Results are written to `data/results/r3live/`.

## Notes

The maintained configuration disables the FAST-LIO2 fallback. If native R3LIVE does not compile or publish odometry, the run should fail or report that clearly instead of recording a FAST-LIO2 trajectory as R3LIVE.
