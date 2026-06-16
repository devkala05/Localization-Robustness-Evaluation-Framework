# LVI-SAM

LVI-SAM is integrated from `algorithms/lvi_sam` with UrbanNav-specific wrapper launch/configuration under `wrappers/lvi_sam_urbannav`.

## Build And Run

```bash
./build_lvisam.sh
./run --algo lvisam --per 0 --gps off --eval
./run --algo lvisam --per 0 --gps on --eval
```

## Inputs

```text
/cloud_registered_raw
/livox/imu
/camera/right/image_raw
/camera/right/camera_info
```

The wrapper enables UrbanNav ZED2 right-camera intrinsics/extrinsics for visual feature/depth aiding and diagnostics.

## Outputs

```text
/lvi_sam/lidar/mapping/odometry
/lvi_sam/lidar/mapping/path
/lvisam/odometry/local
/lvisam/path/local
/lvisam/odometry/output
/lvisam/path/output
/lvisam/status
```

Results are written to `data/results/lvi_sam/`.

## Notes

GPS mode uses LVI-SAM's configured GPS-prior path where available, with the benchmark external fusion path as the maintained fallback surface.
