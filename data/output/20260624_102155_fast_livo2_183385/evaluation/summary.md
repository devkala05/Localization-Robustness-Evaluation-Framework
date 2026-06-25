# E2O Localization Evaluation

Reference: `/home/ayush/Desktop/Localiztion/e2o_localization_fusion_framework/data/output/20260624_122441_lvisam_913711/lvisam_trajectory.csv`

Source method: `unknown`

## Reference limitations

- Neither included reference is survey-grade ground truth.

## fast_livo2

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1419,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.42393548753189164,
    "mean": 0.3910520806034229,
    "median": 0.3922053794807857,
    "p95": 0.6841694410820723,
    "max": 1.0441357156904785
  },
  "rpe_translation_m": {
    "rmse": 0.19001708213198526,
    "mean": 0.15438252881394351,
    "count": 1414,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6692518729546895,
    "mean": 0.47831541959986096,
    "count": 1414,
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
    "fast_livo2": 0.7420609202851588,
    "orbslam3": 0.0,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": null
}
```
