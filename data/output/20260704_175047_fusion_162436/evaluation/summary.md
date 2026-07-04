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
  "associations": 1124,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.29158330168280394,
    "mean": 0.25359525490521106,
    "median": 0.21363327987586084,
    "p95": 0.5480908604819725,
    "max": 0.8822376525976207
  },
  "rpe_translation_m": {
    "rmse": 0.21435228621514849,
    "mean": 0.17322467872974862,
    "count": 1119,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6751674213208569,
    "mean": 0.4798090216387198,
    "count": 1119,
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
  "associations": 553,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 2.8630463054154895,
    "mean": 2.2191959264727417,
    "median": 1.9285019336012286,
    "p95": 4.968369289263632,
    "max": 12.580326460069882
  },
  "rpe_translation_m": {
    "rmse": 0.44129956648377844,
    "mean": 0.29453138291980097,
    "count": 548,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 10.226462699328314,
    "mean": 6.95184174240996,
    "count": 548,
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
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1088,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.2948371481507006,
    "mean": 0.25717162257172993,
    "median": 0.22222488863831513,
    "p95": 0.5469303409307082,
    "max": 0.877529809988608
  },
  "rpe_translation_m": {
    "rmse": 0.21784990248685276,
    "mean": 0.17831272295162381,
    "count": 1083,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6861342644032659,
    "mean": 0.49370313849209435,
    "count": 1083,
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
  "associations": 1088,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.2948371481507006,
    "mean": 0.25717162257172993,
    "median": 0.22222488863831513,
    "p95": 0.5469303409307082,
    "max": 0.877529809988608
  },
  "rpe_translation_m": {
    "rmse": 0.21784990248685276,
    "mean": 0.17831272295162381,
    "count": 1083,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6861342644032659,
    "mean": 0.49370313849209435,
    "count": 1083,
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
  "associations": 1121,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.2918250120658832,
    "mean": 0.2538417739461208,
    "median": 0.21422354988300402,
    "p95": 0.5478996359393251,
    "max": 0.8818840025248578
  },
  "rpe_translation_m": {
    "rmse": 0.2146385475745331,
    "mean": 0.17365463158811437,
    "count": 1116,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.676065108308423,
    "mean": 0.4809382357604898,
    "count": 1116,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.012854814529419,
    "fast_livo2": 300.4529016017914
  },
  "switch_count": 1,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.194711,
      "to_source": "fast_livo2",
      "wall_time": 1783167673.2896857
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
    "fast_livo2": 0.9967595593000648,
    "orbslam3": 0.9760207388204796,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": 0.9492310933220982
}
```
