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
  "associations": 1285,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.30836650194205684,
    "mean": 0.27048970335600875,
    "median": 0.24141834407090945,
    "p95": 0.554553605151885,
    "max": 0.8569894390066297
  },
  "rpe_translation_m": {
    "rmse": 0.22298920859011823,
    "mean": 0.18003769496651334,
    "count": 1280,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7749587368997299,
    "mean": 0.5090632342695407,
    "count": 1280,
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
  "associations": 628,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.850369244699828,
    "mean": 1.7281172957438742,
    "median": 1.7627366417227348,
    "p95": 2.7613936234909437,
    "max": 2.9666108369412525
  },
  "rpe_translation_m": {
    "rmse": 0.3006642815546791,
    "mean": 0.23848857903179546,
    "count": 627,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 9.949025599335638,
    "mean": 6.8515742058793005,
    "count": 627,
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
  "associations": 1252,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3110828154588702,
    "mean": 0.2733720638495225,
    "median": 0.24722154981795297,
    "p95": 0.5536870698557332,
    "max": 0.8550911350286489
  },
  "rpe_translation_m": {
    "rmse": 0.2258079571265649,
    "mean": 0.18404017919827728,
    "count": 1247,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7848527097670864,
    "mean": 0.5203412119757695,
    "count": 1247,
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
  "associations": 1252,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3110828154588702,
    "mean": 0.2733720638495225,
    "median": 0.24722154981795297,
    "p95": 0.5536870698557332,
    "max": 0.8550911350286489
  },
  "rpe_translation_m": {
    "rmse": 0.2258079571265649,
    "mean": 0.18404017919827728,
    "count": 1247,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7848527097670864,
    "mean": 0.5203412119757695,
    "count": 1247,
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
  "associations": 1282,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.30854613438686507,
    "mean": 0.27063092061859706,
    "median": 0.24193778322333237,
    "p95": 0.5544172056210926,
    "max": 0.8567465776751411
  },
  "rpe_translation_m": {
    "rmse": 0.22324567793247868,
    "mean": 0.18039601595533297,
    "count": 1277,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7758589945594785,
    "mean": 0.510101317858938,
    "count": 1277,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.01406741142273,
    "fast_livo2": 300.43901443481445
  },
  "switch_count": 1,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2066686,
      "to_source": "fast_livo2",
      "wall_time": 1783169325.2521567
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
    "orbslam3": 0.5541153596889177,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": 0.9492417860151643
}
```
