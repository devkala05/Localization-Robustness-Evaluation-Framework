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
  "associations": 997,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3060268440415096,
    "mean": 0.27671205724694603,
    "median": 0.24889841423099085,
    "p95": 0.5263447761070034,
    "max": 0.8585286034878941
  },
  "rpe_translation_m": {
    "rmse": 0.2097808238699828,
    "mean": 0.16834728366304347,
    "count": 992,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6401095373572834,
    "mean": 0.47132777114391655,
    "count": 992,
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
  "associations": 522,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.8453629687976736,
    "mean": 1.7402520388200984,
    "median": 1.7930247754378423,
    "p95": 2.8225803232376987,
    "max": 3.242053312963841
  },
  "rpe_translation_m": {
    "rmse": 0.2999664902028208,
    "mean": 0.24581695525188665,
    "count": 520,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 13.580513750891667,
    "mean": 7.558342207957381,
    "count": 520,
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
  "associations": 348,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 26.992001152452215,
    "mean": 15.895680046203879,
    "median": 7.2766097131208305,
    "p95": 75.13927545002606,
    "max": 102.48904238155285
  },
  "rpe_translation_m": {
    "rmse": 3.117667706684987,
    "mean": 1.1063495181694447,
    "count": 346,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.9033466035082213,
    "mean": 0.34636581838697,
    "count": 346,
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
  "associations": 915,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 37.675007648556125,
    "mean": 31.333246927346483,
    "median": 21.448252939282664,
    "p95": 73.95912460764511,
    "max": 76.81333044609327
  },
  "rpe_translation_m": {
    "rmse": 1.3929755082988138,
    "mean": 0.5928133430187501,
    "count": 911,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7050686140611339,
    "mean": 0.5156959907563213,
    "count": 911,
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
  "associations": 915,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 37.675007648556125,
    "mean": 31.333246927346483,
    "median": 21.448252939282664,
    "p95": 73.95912460764511,
    "max": 76.81333044609327
  },
  "rpe_translation_m": {
    "rmse": 1.3929755082988138,
    "mean": 0.5928133430187501,
    "count": 911,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7050686140611339,
    "mean": 0.5156959907563213,
    "count": 911,
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
  "associations": 915,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 7.520573951722757,
    "mean": 1.7338097831358759,
    "median": 0.923074276786848,
    "p95": 1.4653935554601263,
    "max": 95.6713722575509
  },
  "rpe_translation_m": {
    "rmse": 6.231483014108661,
    "mean": 0.7811222836723414,
    "count": 911,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.8036051768088075,
    "mean": 0.6523906430086707,
    "count": 911,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.014703750610352,
    "fast_livo2": 261.0416967868805,
    "lvisam": 39.386783838272095
  },
  "switch_count": 5,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2174482,
      "to_source": "fast_livo2",
      "wall_time": 1783161440.5484033
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 3.552713678800501e-15,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528406.7067256,
      "to_source": "lvisam",
      "wall_time": 1783161626.0456731
    },
    {
      "event": "switch",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 7.951088352073423e-15,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528439.9855578,
      "to_source": "fast_livo2",
      "wall_time": 1783161659.3156176
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 3.554447978966673e-15,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528447.7126331,
      "to_source": "lvisam",
      "wall_time": 1783161667.045587
    },
    {
      "event": "switch",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.9621758982171556e-14,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528453.8007379,
      "to_source": "fast_livo2",
      "wall_time": 1783161673.138128
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528406.716808,
      "to_source": "lvisam",
      "wall_time": 1783161626.052236
    },
    {
      "event": "switch_applied",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528439.9855578,
      "to_source": "fast_livo2",
      "wall_time": 1783161659.3228421
    },
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 1.9645700014567047,
      "pose_jump_m": 0.6036908502702363,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528448.7516568,
      "to_source": "lvisam",
      "wall_time": 1783161668.0824144
    },
    {
      "event": "switch_applied",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528453.8109345,
      "to_source": "fast_livo2",
      "wall_time": 1783161673.144116
    }
  ],
  "max_switch_pose_jump_m": 0.6036908502702363,
  "max_switch_orientation_jump_deg": 1.9645700014567047,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.9063719115734721,
    "orbslam3": 0.9752925877763329,
    "lvisam": 0.9863459037711313
  },
  "navigation_ok_fraction": 0.1907281964436918
}
```
