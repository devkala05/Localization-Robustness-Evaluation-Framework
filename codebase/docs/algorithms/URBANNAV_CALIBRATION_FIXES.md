# UrbanNav camera/extrinsic calibration fixes

This codebase uses the calibration files from `UrbanNav-HK-Medium-Urban-1`, which
correspond to the `UrbanNav-HK-TST-20210517` bag used by the benchmark.

Important convention from the uploaded UrbanNav tools:

```text
RIGHT_CAMERA_T_IMU / LEFT_CAMERA_T_IMU:  p_imu = T_imu_cam * p_cam
CENTER_LiDAR_T_IMU:                      p_imu = T_imu_lidar * p_lidar
```

Therefore:

```text
T_right_cam_lidar = inv(RIGHT_CAMERA_T_IMU) * CENTER_LiDAR_T_IMU
T_right_cam_left  = inv(RIGHT_CAMERA_T_IMU) * LEFT_CAMERA_T_IMU
```

Patched values used in the wrappers:

```yaml
T_right_cam_lidar:
  R: [0.998728714527, -0.0503671773759, 0.00202539414241,
      0.00152876377776, -0.00989676862598, -0.999949857169,
      0.0503846966803, 0.998681731791, -0.00980718749144]
  t: [-0.034160570698, -3.28115047369, -0.718453283642]

T_body_right_camera / ORB IMU.T_b_c1 / LVI-SAM VINS RIC/TIC:
  R: [0.998728714527, 0.00152876377776, 0.0503846966803,
      -0.0503671773759, -0.00989676862598, 0.998681731791,
      0.00202539414241, -0.999949857169, -0.00980718749144]
  t: [0.0753322976296, 0.68331281093, -3.00796276495]
```

Camera intrinsics are from `zed2_intrinsics.yaml` unchanged.
