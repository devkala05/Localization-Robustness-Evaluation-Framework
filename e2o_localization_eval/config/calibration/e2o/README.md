# e2o calibration files

This directory contains the usable calibration generated from the attached files:

- `front_camera_orb_slam3.yaml` — ORB-SLAM3 monocular camera config for `/camera/color/image_raw`.
- `front_camera_info.yaml` — ROS `CameraInfo` values published beside the image stream.
- `e2o_sensor_calibration.yaml` — parsed front/back camera intrinsics and LiDAR-camera/LiDAR-LiDAR extrinsics.
- `static_transforms.yaml` — TF tree used by the launch files and RViz.
- `raw/` — original calibration files from the request.

The uploaded calibration did not provide image dimensions. The default is `1280x720`; run `./run.sh inspect` after dropping the bag into `data/` and update width/height if needed.
