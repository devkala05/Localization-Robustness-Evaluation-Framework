# LVI-SAM UrbanNav camera calibration

This wrapper enables LVI-SAM visual nodes using the UrbanNav HK-TST 2021-05-17 ZED2 **right** camera.

Source files used:

- `UrbanNav-HK-Medium-Urban-1/zed2_intrinsics.yaml`
- `UrbanNav-HK-Medium-Urban-1/extrinsic.yaml`

Runtime topics:

- Bag: `/zed2/camera/right/image_raw`
- Benchmark adapter output: `/camera/right/image_raw`
- Benchmark adapter camera info: `/camera/right/camera_info`
- LVI-SAM VINS config: `params_camera_urbannav_right.yaml`

No timestamp delay is applied. `td` is fixed to `0.0`.
