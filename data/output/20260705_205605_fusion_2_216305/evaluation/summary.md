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
  "associations": 57,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.43988782070773175,
    "mean": 0.3982433819618375,
    "median": 0.4070144695980157,
    "p95": 0.6277144436065425,
    "max": 0.6781126170530025
  },
  "rpe_translation_m": {
    "rmse": 0.15084260540968777,
    "mean": 0.11904098410136241,
    "count": 55,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7374869128348903,
    "mean": 0.5458430306283382,
    "count": 55,
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
  "associations": 920,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.005472972082211764,
    "mean": 0.004012032912538161,
    "median": 0.0030337141773685303,
    "p95": 0.012137164909367644,
    "max": 0.021730874960274805
  },
  "rpe_translation_m": {
    "rmse": 0.0036593310282329776,
    "mean": 0.0017155007640165631,
    "count": 915,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.02192865997026433,
    "mean": 0.009269557047691187,
    "count": 915,
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
  "associations": 883,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.005582206292553814,
    "mean": 0.004151865810783951,
    "median": 0.0032022337245376973,
    "p95": 0.012534343063808547,
    "max": 0.02167114604799669
  },
  "rpe_translation_m": {
    "rmse": 0.003735916413143894,
    "mean": 0.001786513773232556,
    "count": 878,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.022385942327171653,
    "mean": 0.009658933070434916,
    "count": 878,
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
  "associations": 883,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.005582206292553814,
    "mean": 0.004151865810783951,
    "median": 0.0032022337245376973,
    "p95": 0.012534343063808547,
    "max": 0.02167114604799669
  },
  "rpe_translation_m": {
    "rmse": 0.003735916413143894,
    "mean": 0.001786513773232556,
    "count": 878,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.022385942327171653,
    "mean": 0.009658933070434916,
    "count": 878,
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
  "associations": 883,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.005582206292553814,
    "mean": 0.004151865810783951,
    "median": 0.0032022337245376973,
    "p95": 0.012534343063808547,
    "max": 0.02167114604799669
  },
  "rpe_translation_m": {
    "rmse": 0.003735916413143894,
    "mean": 0.001786513773232556,
    "count": 878,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.022385942327171653,
    "mean": 0.009658933070434916,
    "count": 878,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.041139841079712,
    "lvisam": 300.40140867233276
  },
  "switch_count": 1,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2564373,
      "to_source": "lvisam",
      "wall_time": 1783265190.756145
    }
  ],
  "applied_switches": [],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 0.0,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 0.09397278029812055
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.0,
    "orbslam3": 0.08749189889825017,
    "lvisam": 0.9980557355800389
  },
  "navigation_ok_fraction": 0.9490365378540592
}
```
