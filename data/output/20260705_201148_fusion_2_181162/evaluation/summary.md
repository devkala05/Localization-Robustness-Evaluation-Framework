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
  "associations": 566,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.2491911929202864,
    "mean": 1.1154793799654947,
    "median": 1.0011773848264711,
    "p95": 2.194666274507194,
    "max": 2.604767139326395
  },
  "rpe_translation_m": {
    "rmse": 0.24414661855388778,
    "mean": 0.2041872401387424,
    "count": 565,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7739469667585404,
    "mean": 0.5999133524233922,
    "count": 565,
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
  "associations": 964,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.0059579555903548406,
    "mean": 0.004040910750882253,
    "median": 0.0030076713414878154,
    "p95": 0.013883780172918194,
    "max": 0.029423517380648776
  },
  "rpe_translation_m": {
    "rmse": 0.004267118872271156,
    "mean": 0.0021777360112590675,
    "count": 960,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.024718084745226052,
    "mean": 0.01144849547321227,
    "count": 960,
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
  "associations": 927,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.006072809529759359,
    "mean": 0.004177148374510495,
    "median": 0.0031069439016744404,
    "p95": 0.014258885619130662,
    "max": 0.029412638947673393
  },
  "rpe_translation_m": {
    "rmse": 0.004352011129151373,
    "mean": 0.002264320245662407,
    "count": 923,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.02520864956755763,
    "mean": 0.011906272740200919,
    "count": 923,
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
  "associations": 927,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.006072809529759359,
    "mean": 0.004177148374510495,
    "median": 0.0031069439016744404,
    "p95": 0.014258885619130662,
    "max": 0.029412638947673393
  },
  "rpe_translation_m": {
    "rmse": 0.004352011129151373,
    "mean": 0.002264320245662407,
    "count": 923,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.02520864956755763,
    "mean": 0.011906272740200919,
    "count": 923,
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
  "associations": 927,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.006072809529759359,
    "mean": 0.004177148374510495,
    "median": 0.0031069439016744404,
    "p95": 0.014258885619130662,
    "max": 0.029412638947673393
  },
  "rpe_translation_m": {
    "rmse": 0.004352011129151373,
    "mean": 0.002264320245662407,
    "count": 923,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.02520864956755763,
    "mean": 0.011906272740200919,
    "count": 923,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.011366128921509,
    "lvisam": 300.426198720932
  },
  "switch_count": 1,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2141426,
      "to_source": "lvisam",
      "wall_time": 1783262533.3985465
    }
  ],
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
    "lvisam": 0.9980557355800389
  },
  "navigation_ok_fraction": 0.9492417860151643
}
```
