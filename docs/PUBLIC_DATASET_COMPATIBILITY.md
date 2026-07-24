# Public dataset compatibility

This report records the sequence choice before algorithm integration. Values come from the official dataset documentation, the UrbanLoco ROS bag index, and the Boreas-RT S3 object/calibration metadata. It does not claim any estimator run is successful.

## Storage decision

| Dataset | Selected content | Bytes | GiB | Extraction |
|---|---|---:|---:|---|
| UrbanLoco | `CA-20190828184706_blur_align-002.bag` plus calibration | 14,079,033,456 + 4.78 KB | 13.11 | None; ROS 1 bag |
| Boreas-RT | `boreas-2024-12-04-14-44`: lidar, camera, independent DMU, Applanix, calibration | 13,179,516,822 | 12.27 | None; native files are streamed |
| Combined | Required sensor/GT/calibration content | 27,258,550,278 | 25.39 | No generated bag is required |

The machine had 68 GB free before download. Boreas is played directly from native files to avoid another approximately 13 GB generated bag.

## Sequence facts

| Property | UrbanLoco CA-20190828184706 | Boreas-RT 2024-12-04-14-44 |
|---|---|---|
| Duration | 248.743 s | about 169.35 s for lidar/camera/DMU overlap |
| LiDAR | RoboSense RS-LiDAR-32, 32 beams, organized 32xN ROS `PointCloud2`, 2,439 scans, 9.80 Hz. Actual fields are only float32 `x,y,z,intensity`; the adapter derives `ring` from the organized row and relative time from column acquisition order plus the documented 10 Hz scan rate. | Velodyne Alpha Prime, 128 beams; float32 binary `[x,y,z,intensity,ring,time]`, 1,627 scans, about 10 Hz |
| Camera | Six 2048x1536 camera streams, JPEG `CompressedImage`, about 10 Hz; camera 0 selected | Rectified 2448x2048 FLIR Blackfly S PNG, 1,694 frames, about 10 Hz |
| IMU | Xsens MTi-10 `/imu_raw`, 24,865 messages, about 100 Hz | Independent Silicon Sensing DMU41, `dmu_imu_infilled.csv`, 200 Hz; the Applanix IMU is deliberately not used. The official fixed DMU mounting plus raw gyro integration supplies LVI-SAM's mandatory nonzero attitude field; no GT/GNSS pose is used. |
| GNSS / GT | u-blox plus NovAtel SPAN-CPT; `/novatel_data/inspvax` is the RTK GNSS/INS reference | POSPac post-processed Applanix GNSS/INS/wheel solution at 200 Hz, normally 2-4 cm RMS according to the dataset guide |
| Calibration | `calibration_CA.txt`: six camera intrinsics/extrinsics, IMU-LiDAR, GNSS and SPAN-LiDAR | Per-sequence camera intrinsics and `T_applanix_lidar`, `T_applanix_dmu`, `T_camera_lidar` matrices |
| Original format | ROS 1 bag | Timestamped binary lidar, PNG camera, CSV IMU/GT |
| Time convention | Unix ROS stamps and bag ordering retained. LiDAR/IMU carry header stamps; compressed camera headers are zero, so the adapter uses the original bag record time exposed by `/clock`. | Sensor files use UTC microseconds; DMU CSV uses UTC nanoseconds; lidar stamp is scan midpoint |
| Reference frame | Local ENU constructed from SPAN latitude/longitude/height; first valid pose is the numerical origin | Official global ENU translated to the first evaluation pose; axes remain East, North, Up |
| Official map | None in selected download | None in selected download |

The smaller `HK-Data20190117` was rejected after inspecting its actual ROS 2 metadata: it has LiDAR, IMU and GNSS/INS but no camera topic. Remote inspection of the adjacent `test2.bag` and `test3.bag` indexes showed the same limitation. The California sequence is the smallest currently accessible UrbanLoco bag that actually contains LiDAR, camera, IMU, and legitimate SPAN ground truth.

## Intended modes (pre-run)

| Algorithm | UrbanLoco mode | Boreas-RT mode | Pre-run compatibility |
|---|---|---|---|
| FAST-LIO2 | RS-LiDAR-32 + Xsens IMU | Alpha Prime lidar + independent DMU41 | Sensor/calibration compatible; execution pending |
| FAST-LIVO2 | RS-LiDAR-32 + camera 0 + Xsens IMU | Alpha Prime lidar + rectified monocular camera + independent DMU41 | Sensor/calibration compatible; execution pending |
| ORB-SLAM3 | pure monocular camera 0 | pure rectified monocular camera | Native mono-inertial mode was also tested but rejected; pure mono is explicitly Sim(3)-scored |
| RTAB-Map | LiDAR point-to-plane ICP odometry + graph SLAM + IMU initialization | LiDAR point-to-plane ICP odometry + graph SLAM + IMU initialization | Native `map->odom` graph correction is composed with ICP odometry; no RGB-D mode is claimed |
| LVI-SAM | RS-LiDAR-32 + Xsens IMU (visual branch opt-in) | Alpha Prime lidar + independent DMU41 (visual branch opt-in) | LIO is the default because full-route visual runs trigger native VINS reboots |

LiDAR/inertial modes use SE(3). Pure monocular ORB-SLAM3 uses one global Sim(3)
because metric scale is unobservable; a reset into a differently scaled atlas
map is not repaired or aligned separately.

The public files provide extrinsic/intrinsic calibration but not a complete Allan-variance noise model for either independent IMU. Noise parameters in the initial estimator configurations are therefore explicitly pre-validation values, not claimed dataset calibration. A pair cannot be marked working until the real short run passes the message, TF, trajectory, timestamp, visualization, and evaluation checks.

Real short-window outcomes are recorded separately in
[`VALIDATION_REPORT.md`](VALIDATION_REPORT.md). They do not turn this pre-run
compatibility table into a full-sequence success claim.
