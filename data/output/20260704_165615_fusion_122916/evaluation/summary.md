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
  "associations": 785,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3148213670109008,
    "mean": 0.2777273642940316,
    "median": 0.260150118501854,
    "p95": 0.5461391902674261,
    "max": 0.8033095334431105
  },
  "rpe_translation_m": {
    "rmse": 0.21174187180054624,
    "mean": 0.17357365688885423,
    "count": 780,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.708034212662292,
    "mean": 0.48992400716799145,
    "count": 780,
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
  "associations": 384,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 2.677740022351818,
    "mean": 2.414841757787443,
    "median": 2.5762501443120236,
    "p95": 4.29226766282202,
    "max": 4.797864464369441
  },
  "rpe_translation_m": {
    "rmse": 0.3271977265475264,
    "mean": 0.26911971953552916,
    "count": 380,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 8.890262470438817,
    "mean": 6.203928659455774,
    "count": 380,
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
  "associations": 474,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.07130589651912331,
    "mean": 0.04562876510960269,
    "median": 0.025848733884642677,
    "p95": 0.16409357546086037,
    "max": 0.31928452300903787
  },
  "rpe_translation_m": {
    "rmse": 0.019515512844889296,
    "mean": 0.011542870206078306,
    "count": 471,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.12742867691464235,
    "mean": 0.0729274621243341,
    "count": 471,
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
  "associations": 740,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.319259444689264,
    "mean": 0.2825552438835773,
    "median": 0.2675338015791741,
    "p95": 0.5502994706662242,
    "max": 0.8038929063355723
  },
  "rpe_translation_m": {
    "rmse": 0.21631112521165144,
    "mean": 0.1802322139915267,
    "count": 737,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7266009423644822,
    "mean": 0.5109829987568569,
    "count": 737,
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
  "associations": 740,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.319259444689264,
    "mean": 0.2825552438835773,
    "median": 0.2675338015791741,
    "p95": 0.5502994706662242,
    "max": 0.8038929063355723
  },
  "rpe_translation_m": {
    "rmse": 0.21631112521165144,
    "mean": 0.1802322139915267,
    "count": 737,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7266009423644822,
    "mean": 0.5109829987568569,
    "count": 737,
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
  "associations": 775,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3135677497776154,
    "mean": 0.2764962319075061,
    "median": 0.25928858580974123,
    "p95": 0.5453745687103312,
    "max": 0.8036706037345218
  },
  "rpe_translation_m": {
    "rmse": 0.21154365122338123,
    "mean": 0.1733307356235813,
    "count": 772,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7102687988378626,
    "mean": 0.4911097761713808,
    "count": 772,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.002652883529663,
    "fast_livo2": 221.95876359939575
  },
  "switch_count": 1,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.1943536,
      "to_source": "fast_livo2",
      "wall_time": 1783164402.3147523
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
    "fast_livo2": 0.9773913043478261,
    "orbslam3": 0.98,
    "lvisam": 0.9965217391304347
  },
  "navigation_ok_fraction": 0.9082939048149179
}
```
