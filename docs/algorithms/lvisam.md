# LVI-SAM

LVI-SAM is integrated from the upstream `TixiaoShan/LVI-SAM` code in `algorithms/lvi_sam`, with UrbanNav wrapper launch/configuration under `wrappers/lvi_sam_urbannav`.

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

The wrapper enables the UrbanNav ZED2 right-camera VINS frontend and sets `useVinsFactor: true`, so the LiDAR mapping graph accepts visual/VINS relative pose factors when the visual frontend is healthy.

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

GPS mode uses LVI-SAM's configured GPS-prior path where available, with the benchmark external fusion path as the maintained fallback surface. Runtime logs should still be checked for VINS health because LVI-SAM can down-weight or skip visual constraints when the visual frontend fails.
