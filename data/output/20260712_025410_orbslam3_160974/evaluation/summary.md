# E2O Localization Evaluation

Reference: `/home/devil/Desktop/car/localisation/Localization-Robustness-Evaluation-Framework/ss..'/data/e2o/ground_truth/ref.csv`

Source method: `unknown`

## Reference limitations

- Selected reference is not survey-grade ground truth unless externally verified.

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
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 617,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.2159283740689677,
    "mean": 1.0996714714014637,
    "median": 1.0774078960619033,
    "p95": 2.024083634230929,
    "max": 2.4826066736255905
  },
  "rpe_translation_m": {
    "rmse": 0.25583661992673434,
    "mean": 0.2131304230619967,
    "count": 616,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7812977279270876,
    "mean": 0.6150444077205046,
    "count": 616,
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

## fused_continuous

```json
{
  "valid": false,
  "reason": "fewer_than_3_associations",
  "associations": 0
}
```

## fused_metric

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
    "orbslam3": 0.9980557355800389,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": null
}
```
