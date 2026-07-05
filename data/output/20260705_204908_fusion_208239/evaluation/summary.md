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
  "associations": 87,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.16984679869643532,
    "mean": 0.15363228761872919,
    "median": 0.17286743779619537,
    "p95": 0.27143149748647244,
    "max": 0.34939949541529547
  },
  "rpe_translation_m": {
    "rmse": 0.09956030198956957,
    "mean": 0.06914776763266271,
    "count": 82,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.17668232306131615,
    "mean": 0.1400613500264204,
    "count": 82,
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
  "associations": 32,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3181173158842395,
    "mean": 0.2664701628323849,
    "median": 0.264378067533591,
    "p95": 0.5950136509808335,
    "max": 0.6231967730476514
  },
  "rpe_translation_m": {
    "rmse": 0.13490931488111668,
    "mean": 0.10820629709440562,
    "count": 30,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.27005610158969573,
    "mean": 0.2490311785539463,
    "count": 30,
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
  "associations": 1074,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.005077399036069643,
    "mean": 0.0038066737294567775,
    "median": 0.003104672035365682,
    "p95": 0.011085873376702282,
    "max": 0.023792614109288308
  },
  "rpe_translation_m": {
    "rmse": 0.004024608853405977,
    "mean": 0.002107170382790366,
    "count": 1069,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.02746763569127032,
    "mean": 0.012518258616383955,
    "count": 1069,
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
  "associations": 1022,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.4298417667928613,
    "mean": 0.6152069862732082,
    "median": 0.34249761168408366,
    "p95": 0.9208744517408757,
    "max": 7.283615693402746
  },
  "rpe_translation_m": {
    "rmse": 0.42561966771192405,
    "mean": 0.06147903051519047,
    "count": 1017,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.2808751638239821,
    "mean": 0.12527989119613286,
    "count": 1017,
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
  "associations": 1022,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.4298417667928613,
    "mean": 0.6152069862732082,
    "median": 0.34249761168408366,
    "p95": 0.9208744517408757,
    "max": 7.283615693402746
  },
  "rpe_translation_m": {
    "rmse": 0.42561966771192405,
    "mean": 0.06147903051519047,
    "count": 1017,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.2808751638239821,
    "mean": 0.12527989119613286,
    "count": 1017,
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
  "associations": 51,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.13039627233632292,
    "mean": 0.11413711902138551,
    "median": 0.10433063652787627,
    "p95": 0.22531022383521315,
    "max": 0.2422171298133602
  },
  "rpe_translation_m": {
    "rmse": 0.12736943349267735,
    "mean": 0.10089743427088951,
    "count": 46,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.21577399627991845,
    "mean": 0.19627213925727413,
    "count": 46,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.0054292678833,
    "fast_livo2": 13.385457515716553,
    "lvisam": 287.0516936779022
  },
  "switch_count": 2,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2176344,
      "to_source": "fast_livo2",
      "wall_time": 1783264773.2725697
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 3.356589068483857e-16,
      "reason": "fast_livo2_unhealthy_camera_fallback:camera_unavailable",
      "ros_time": 1723528234.593028,
      "to_source": "lvisam",
      "wall_time": 1783264786.647992
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "fast_livo2_unhealthy_camera_fallback:camera_unavailable",
      "ros_time": 1723528234.593028,
      "to_source": "lvisam",
      "wall_time": 1783264786.6569667
    }
  ],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 0.0,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 0.06934543097861309
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.06286454957874271,
    "orbslam3": 0.06221646143875567,
    "lvisam": 0.9980557355800389
  },
  "navigation_ok_fraction": 0.9441933788754598
}
```
