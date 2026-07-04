# E2O Localization Evaluation

Reference: `/home/devil/Desktop/car/localisation/Localization-Robustness-Evaluation-Framework/ss..'/data/e2o/ground_truth/ref.csv`

Source method: `unknown`

## Reference limitations

- Selected reference is not survey-grade ground truth unless externally verified.

## fast_livo2

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1408,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3779065873094104,
    "mean": 0.33567257208655565,
    "median": 0.32693247745600584,
    "p95": 0.639932360020888,
    "max": 0.8639768229724981
  },
  "rpe_translation_m": {
    "rmse": 0.17736479730503207,
    "mean": 0.1452677636948104,
    "count": 1403,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6501435500684594,
    "mean": 0.4638145256968026,
    "count": 1403,
    "delta_sec": 1.0
  }
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
    "fast_livo2": 0.9967595593000648,
    "orbslam3": 0.0,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": null
}
```
