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
  "associations": 659,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 2.3509666458686196,
    "mean": 2.129282465226688,
    "median": 2.165648883229644,
    "p95": 4.206624377149761,
    "max": 4.395943898787466
  },
  "rpe_translation_m": {
    "rmse": 0.3425143023555914,
    "mean": 0.2658959163621165,
    "count": 658,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 11.951332520756273,
    "mean": 8.180860871697625,
    "count": 658,
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
  "associations": 510,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.03700367847631795,
    "mean": 0.028836063796141256,
    "median": 0.020011151035265295,
    "p95": 0.0927471717596809,
    "max": 0.12692808892772395
  },
  "rpe_translation_m": {
    "rmse": 0.011515534052061434,
    "mean": 0.009056155949741452,
    "count": 507,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.11955638340811664,
    "mean": 0.061371476662795375,
    "count": 507,
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
  "associations": 494,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.061247479499032885,
    "mean": 0.039792184177474633,
    "median": 0.027042507954078233,
    "p95": 0.10649028564103717,
    "max": 0.3699691794980174
  },
  "rpe_translation_m": {
    "rmse": 0.03250140413229901,
    "mean": 0.01469217189246029,
    "count": 491,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.21783420555436225,
    "mean": 0.0955165993919137,
    "count": 491,
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
  "associations": 494,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.061247479499032885,
    "mean": 0.039792184177474633,
    "median": 0.027042507954078233,
    "p95": 0.10649028564103717,
    "max": 0.3699691794980174
  },
  "rpe_translation_m": {
    "rmse": 0.03250140413229901,
    "mean": 0.01469217189246029,
    "count": 491,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.21783420555436225,
    "mean": 0.0955165993919137,
    "count": 491,
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
  "associations": 494,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.052810936948065074,
    "mean": 0.03358972599976508,
    "median": 0.022612581292949054,
    "p95": 0.10896123026880077,
    "max": 0.48910925945455236
  },
  "rpe_translation_m": {
    "rmse": 0.04224867203341928,
    "mean": 0.015393317438147565,
    "count": 491,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.27326594197679677,
    "mean": 0.10028548640522543,
    "count": 491,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 3.4138307571411133,
    "orbslam3": 3.030484914779663,
    "lvisam": 301.9950180053711
  },
  "switch_count": 2,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528216.5973115,
      "to_source": "orbslam3",
      "wall_time": 1783160134.297862
    },
    {
      "event": "switch",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.7690777709386487e-17,
      "reason": "primary_recovered_and_consistent",
      "ros_time": 1723528219.6278403,
      "to_source": "lvisam",
      "wall_time": 1783160137.3306284
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.2133094848182044,
      "pose_jump_m": 0.034287339671726313,
      "reason": "primary_recovered_and_consistent",
      "ros_time": 1723528219.864532,
      "to_source": "lvisam",
      "wall_time": 1783160137.563095
    }
  ],
  "max_switch_pose_jump_m": 0.034287339671726313,
  "max_switch_orientation_jump_deg": 0.2133094848182044,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.0,
    "orbslam3": 0.998703823720026,
    "lvisam": 0.9974076474400518
  },
  "navigation_ok_fraction": 0.03554835224203134
}
```
