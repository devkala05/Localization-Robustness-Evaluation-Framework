# E2O dataset placement

Place the bag at:

```text
data/e2o/raw/one_full_loop.bag
```

The included reference trajectory is:

```text
data/e2o/ground_truth/one_full_loop_gt.tum
```

It was derived from `/mavros/global_position/global` with orientation from
`/mavros/imu/data`; it is an approximate GNSS/IMU reference, not survey-grade RTK.
