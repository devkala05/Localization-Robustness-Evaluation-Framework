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
  "associations": 169,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.2009073211105417,
    "mean": 0.18558919843791422,
    "median": 0.18467427054115748,
    "p95": 0.29352852530113094,
    "max": 0.3679366651671281
  },
  "rpe_translation_m": {
    "rmse": 0.14945754046378432,
    "mean": 0.113078297859804,
    "count": 164,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.69984852995265,
    "mean": 0.44030143156808416,
    "count": 164,
    "delta_sec": 1.0
  }
}
```

## orbslam3

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 600,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.4400760133577448,
    "mean": 1.285689181616383,
    "median": 1.1762226854501217,
    "p95": 2.601115972382093,
    "max": 3.259534826906427
  },
  "rpe_translation_m": {
    "rmse": 0.2970740759470684,
    "mean": 0.2335282154120113,
    "count": 599,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.8736388094657134,
    "mean": 0.6372695983359019,
    "count": 599,
    "delta_sec": 1.0
  }
}
```

## lvisam

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 174,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 9.596174740016666e-15,
    "mean": 8.374333735772243e-15,
    "median": 9.162163478256516e-15,
    "p95": 1.4649896587576702e-14,
    "max": 1.5888218580782548e-14
  },
  "rpe_translation_m": {
    "rmse": 2.903875120247038e-15,
    "mean": 1.3328045586369155e-15,
    "count": 169,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.0,
    "mean": 0.0,
    "count": 169,
    "delta_sec": 1.0
  }
}
```

## fused

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1320,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 4.23807838570541,
    "mean": 3.632340260635725,
    "median": 3.0457805732865078,
    "p95": 8.269364579480156,
    "max": 11.672169491246434
  },
  "rpe_translation_m": {
    "rmse": 0.5695068141173629,
    "mean": 0.3538194336738767,
    "count": 1315,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.6466137776103107,
    "mean": 0.5941986913722842,
    "count": 1315,
    "delta_sec": 1.0
  }
}
```

## fused_continuous

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1320,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 4.23807838570541,
    "mean": 3.632340260635725,
    "median": 3.0457805732865078,
    "p95": 8.269364579480156,
    "max": 11.672169491246434
  },
  "rpe_translation_m": {
    "rmse": 0.5695068141173629,
    "mean": 0.3538194336738767,
    "count": 1315,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.6466137776103107,
    "mean": 0.5941986913722842,
    "count": 1315,
    "delta_sec": 1.0
  }
}
```

## fused_metric

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 134,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.16149980393895777,
    "mean": 0.1454844827567029,
    "median": 0.13038313948688757,
    "p95": 0.2988704325783522,
    "max": 0.34896305528529986
  },
  "rpe_translation_m": {
    "rmse": 0.16674673253465067,
    "mean": 0.13620189685853415,
    "count": 129,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7873140267278143,
    "mean": 0.5420034922043203,
    "count": 129,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.020145654678345,
    "fast_livo2": 30.728207111358643,
    "orbslam3": 269.6975049972534
  },
  "switch_count": 2,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2228599,
      "to_source": "fast_livo2",
      "wall_time": 1783261850.483639
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.2852839585937751e-14,
      "reason": "fast_livo2_unhealthy_sensor_fallback:lidar_unavailable",
      "ros_time": 1723528251.9511259,
      "to_source": "orbslam3",
      "wall_time": 1783261881.211447
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "fast_livo2_unhealthy_sensor_fallback:lidar_unavailable",
      "ros_time": 1723528251.9511259,
      "to_source": "orbslam3",
      "wall_time": 1783261881.2149553
    }
  ],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 0.0,
  "sensor_availability_fraction": {
    "lidar": 0.12443292287751134,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.12119248217757615,
    "orbslam3": 0.9980557355800389,
    "lvisam": 0.11989630589760207
  },
  "navigation_ok_fraction": 0.9481887110362258
}
```
