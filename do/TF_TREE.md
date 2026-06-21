# TF ownership

There must be one authoritative navigation chain. Native estimator TF output is remapped to `/native/fast_livo2/*` and `/native/orbslam3/*` and is not consumed by navigation.

## Direct mode (default)

```text
map --static identity, fusion--> odom --dynamic, fusion--> base_link
                                                ├─static, E2O adapter--> velodyne103
                                                └─static, E2O adapter--> camera_right
                                                                          └─static--> camera_color_optical_frame
```

The fused pose is numerically represented in `map`; because `map -> odom` is identity, fusion publishes the same transform as `odom -> base_link`. Use this mode when there is no separate wheel-odometry chain.

## Map-to-odom mode

```text
map --dynamic, fusion--> odom --dynamic, external odometry--> base_link
```

Fusion looks up the existing `odom -> base_link` and computes `map -> odom` such that the composed transform matches the fused map pose. Do not use this mode unless the external transform is present and continuous.

## Topics-only mode

`TF_MODE=none` publishes fused topics but no world TF.

## Ownership table

| Transform | Publisher | Notes |
|---|---|---|
| `map -> odom` | fusion | static identity in direct mode; dynamic in map-to-odom mode |
| `odom -> base_link` | fusion in direct mode, external odometry in map-to-odom mode | never both |
| `base_link -> velodyne103` | E2O static TF publisher | currently identity assumption |
| `base_link -> camera_right` | E2O static TF publisher | supplied LiDAR-camera calibration transformed to base convention |
| `camera_right -> camera_color_optical_frame` | E2O static TF publisher | ROS optical-frame convention |

## Checks

```bash
roswtf
rosrun tf2_tools view_frames.py
rosrun rqt_graph rqt_graph
rostopic echo -n 1 /tf
rostopic echo -n 1 /tf_static
```

Inspect the generated frame graph for duplicate parents, loops, old estimator world frames, and more than one publisher of an authoritative edge.
