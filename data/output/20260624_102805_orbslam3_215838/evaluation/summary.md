# E2O Localization Evaluation

Reference: `/home/ayush/Desktop/Localiztion/e2o_localization_fusion_framework/data/output/20260624_122441_lvisam_913711/lvisam_trajectory.csv`

Source method: `unknown`

## Reference limitations

- Neither included reference is survey-grade ground truth.

## fast_livo2

```json
{
  "valid": false,
  "reason": "fewer_than_3_associations",
  "associations": 0
}
```

## orbslam3

```json
{
  "valid": true,
  "alignment": "sim3",
  "alignment_scale": 7.20911279872222,
  "associations": 1391,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 3.010041668609969,
    "mean": 2.5753772432798527,
    "median": 2.233530285428791,
    "p95": 5.758708679154768,
    "max": 6.689668462040547
  },
  "rpe_translation_m": {
    "rmse": 0.36726798172997616,
    "mean": 0.28297878482817174,
    "count": 1386,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.0579246453895463,
    "mean": 0.7819763113897444,
    "count": 1386,
    "delta_sec": 1.0
  }
}
```

## lvisam

```json
{
  "valid": false,
  "reason": "fewer_than_3_associations",
  "associations": 0
}
```

## fused

```json
{
  "valid": false,
  "reason": "fewer_than_3_associations",
  "associations": 0
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {},
  "switch_count": 0,
  "switches": [],
  "applied_switches": [],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 0.0,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.0,
    "orbslam3": 0.9176928062216462,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": null
}
```
