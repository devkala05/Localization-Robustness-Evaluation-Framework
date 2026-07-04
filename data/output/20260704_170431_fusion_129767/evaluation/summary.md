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
  "associations": 853,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3766120619298882,
    "mean": 0.2615441008185332,
    "median": 0.20355478761885754,
    "p95": 0.5856904001681013,
    "max": 3.3729232506355555
  },
  "rpe_translation_m": {
    "rmse": 0.27649142065922855,
    "mean": 0.1856724224665421,
    "count": 848,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6882937079714571,
    "mean": 0.49118117715533827,
    "count": 848,
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
  "associations": 598,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 3.186887793619242,
    "mean": 2.9402218138221015,
    "median": 2.8537726319550396,
    "p95": 5.456567042808684,
    "max": 5.884783590663906
  },
  "rpe_translation_m": {
    "rmse": 0.39215564988002516,
    "mean": 0.32112495918624606,
    "count": 592,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 10.726380058520403,
    "mean": 7.6008588471990235,
    "count": 592,
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
  "associations": 436,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 23.496140883113142,
    "mean": 12.4647878859146,
    "median": 5.984752768261334,
    "p95": 49.7675423610927,
    "max": 109.5016765730838
  },
  "rpe_translation_m": {
    "rmse": 3.7677829249158283,
    "mean": 0.9149080382964188,
    "count": 433,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.0088203786353804,
    "mean": 0.30315254903661926,
    "count": 433,
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
  "associations": 762,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.2865016089045342,
    "mean": 0.24505873174162038,
    "median": 0.21321804242807557,
    "p95": 0.5565776067500962,
    "max": 0.9302242088028705
  },
  "rpe_translation_m": {
    "rmse": 0.21543194477128363,
    "mean": 0.17558049949432378,
    "count": 759,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7076812424574884,
    "mean": 0.5110548961070822,
    "count": 759,
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
  "associations": 762,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.2865016089045342,
    "mean": 0.24505873174162038,
    "median": 0.21321804242807557,
    "p95": 0.5565776067500962,
    "max": 0.9302242088028705
  },
  "rpe_translation_m": {
    "rmse": 0.21543194477128363,
    "mean": 0.17558049949432378,
    "count": 759,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7076812424574884,
    "mean": 0.5110548961070822,
    "count": 759,
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
  "associations": 792,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.284574899952537,
    "mean": 0.24335825927332033,
    "median": 0.2144841718865604,
    "p95": 0.5515088271349958,
    "max": 0.937765341587568
  },
  "rpe_translation_m": {
    "rmse": 0.2114115065795816,
    "mean": 0.16982194761030106,
    "count": 789,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.6941693653236997,
    "mean": 0.49307039303129035,
    "count": 789,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.00063705444336,
    "fast_livo2": 300.4503016471863
  },
  "switch_count": 1,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.1931822,
      "to_source": "fast_livo2",
      "wall_time": 1783164897.4054413
    }
  ],
  "applied_switches": [],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 0.0,
  "sensor_availability_fraction": {
    "lidar": 0.9906354515050168,
    "imu": 0.9986622073578595,
    "camera": 0.9879598662207358
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.8735785953177257,
    "orbslam3": 0.9652173913043478,
    "lvisam": 0.9538461538461539
  },
  "navigation_ok_fraction": 0.7567594433399603
}
```
