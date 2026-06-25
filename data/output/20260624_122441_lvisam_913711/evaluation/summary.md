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
  "valid": false,
  "reason": "fewer_than_3_associations",
  "associations": 0
}
```

## lvisam

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1421,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.6121135755530667e-14,
    "mean": 1.3523040505994057e-14,
    "median": 1.2810243072846601e-14,
    "p95": 2.9299793175153404e-14,
    "max": 3.177954017774959e-14
  },
  "rpe_translation_m": {
    "rmse": 2.98299455886738e-15,
    "mean": 9.999172543428512e-16,
    "count": 1416,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 9.626033550277542e-08,
    "mean": 6.675272552002149e-09,
    "count": 1416,
    "delta_sec": 1.0
  }
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
    "orbslam3": 0.0,
    "lvisam": 0.9980557355800389
  },
  "navigation_ok_fraction": null
}
```
