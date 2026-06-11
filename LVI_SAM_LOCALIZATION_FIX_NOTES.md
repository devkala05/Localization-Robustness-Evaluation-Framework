# LVI-SAM localization fix notes

The LiDAR/VINS hybrid code originally subscribed imageProjection to:

`/lvi_sam/vins/odometry/imu_propagate_ros`

But the UrbanNav launch disables visual/VINS nodes because VINS repeatedly resets on this bag. That meant the LiDAR pipeline received no translational odometry initial guess; scan matching could keep the vehicle near the start while scans were still drawn in RViz.

This patch changes imageProjection to subscribe to the configured LiDAR-IMU odometry topic:

`/lvi_sam/lidar/odometry/imu`

and changes imuPreintegration to publish that namespaced topic. FAST-LIO2 files are untouched.
