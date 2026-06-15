# Ground truth workflow

The e2o bag metadata in the request lists only front camera and LiDAR topics. A true benchmark needs a reference trajectory. This repo supports two cases.

## Case A: the bag contains a hidden/reference pose topic

Run:

```bash
./run.sh inspect --bag <bag_name>.bag
```

Look under `GROUND-TRUTH CANDIDATES`. If a good topic appears:

```bash
./run.sh gt --bag <bag_name>.bag --gt-topic /topic/name
```

Supported source message types:

- `nav_msgs/Odometry`
- `geometry_msgs/PoseStamped`
- `geometry_msgs/PoseWithCovarianceStamped`
- `nav_msgs/Path`
- `sensor_msgs/NavSatFix`
- `tf2_msgs/TFMessage` with `--tf-parent` and `--tf-child`

## Case B: the bag does not contain ground truth

Use an external reference and save it as:

```text
data/ground_truth/<bag_name>_gt.tum
```

Format:

```text
timestamp tx ty tz qx qy qz qw
```

Do not use ORB-SLAM3 output as ground truth for ORB-SLAM3 benchmarking. That would only compare the algorithm to itself.
