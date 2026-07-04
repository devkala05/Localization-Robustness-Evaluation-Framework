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
  "associations": 1044,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3588425946807249,
    "mean": 0.31981868150566095,
    "median": 0.29811045545215187,
    "p95": 0.6006645519534133,
    "max": 0.9013470872447834
  },
  "rpe_translation_m": {
    "rmse": 0.2118590256341945,
    "mean": 0.1670595857831203,
    "count": 1038,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.0441677417488235,
    "mean": 0.5469046349340515,
    "count": 1038,
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
  "associations": 701,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 5.52497322708135,
    "mean": 4.567659904229332,
    "median": 4.0195767240539935,
    "p95": 10.42024679840424,
    "max": 20.438644270061864
  },
  "rpe_translation_m": {
    "rmse": 2.2179648957521794,
    "mean": 0.7147651899532126,
    "count": 700,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 10.199141188530414,
    "mean": 7.153605384238936,
    "count": 700,
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
  "associations": 1045,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 8.458745034588755,
    "mean": 4.80050082545206,
    "median": 2.9980220917007063,
    "p95": 20.94973688917916,
    "max": 52.946909047925004
  },
  "rpe_translation_m": {
    "rmse": 3.7500795343447355,
    "mean": 0.9845185872501458,
    "count": 1040,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 6.589536348388332,
    "mean": 1.7058165785618027,
    "count": 1040,
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
  "associations": 1045,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 8.458745034588755,
    "mean": 4.80050082545206,
    "median": 2.9980220917007063,
    "p95": 20.94973688917916,
    "max": 52.946909047925004
  },
  "rpe_translation_m": {
    "rmse": 3.7500795343447355,
    "mean": 0.9845185872501458,
    "count": 1040,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 6.589536348388332,
    "mean": 1.7058165785618027,
    "count": 1040,
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
  "associations": 1045,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 17.512661020169755,
    "mean": 9.39827814017541,
    "median": 4.872252785522167,
    "p95": 52.08052912157627,
    "max": 75.15526746396704
  },
  "rpe_translation_m": {
    "rmse": 6.260088141520039,
    "mean": 1.3796251143246112,
    "count": 1040,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 10.150060471101291,
    "mean": 2.0058640778224683,
    "count": 1040,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.857699632644653,
    "fast_livo2": 264.7123897075653,
    "orbslam3": 34.868778467178345
  },
  "switch_count": 7,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.2158027,
      "to_source": "fast_livo2",
      "wall_time": 1783163418.6576953
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.0630965195904451e-14,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528421.0257225,
      "to_source": "orbslam3",
      "wall_time": 1783163618.4763823
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 56.786655448507524,
      "reason": "initial_healthy_source",
      "ros_time": 1723528434.8019295,
      "to_source": "fast_livo2",
      "wall_time": 1783163632.2448888
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.4988010832439613e-15,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528443.7735348,
      "to_source": "orbslam3",
      "wall_time": 1783163641.222928
    },
    {
      "event": "switch",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 42.84252847990551,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528454.0055594,
      "to_source": "fast_livo2",
      "wall_time": 1783163651.4477062
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.4283958749745402e-14,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528459.172967,
      "to_source": "orbslam3",
      "wall_time": 1783163656.6227522
    },
    {
      "event": "switch",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 36.966429274322934,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528471.0168366,
      "to_source": "fast_livo2",
      "wall_time": 1783163668.4618719
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528421.0357687,
      "to_source": "orbslam3",
      "wall_time": 1783163618.4872625
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528434.8120117,
      "to_source": "fast_livo2",
      "wall_time": 1783163632.2557392
    },
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528443.8255167,
      "to_source": "orbslam3",
      "wall_time": 1783163641.2698073
    },
    {
      "event": "switch_applied",
      "from_source": "orbslam3",
      "orientation_jump_deg": 6.183529560385795,
      "pose_jump_m": 18.99481290748504,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528454.4331832,
      "to_source": "fast_livo2",
      "wall_time": 1783163651.8758233
    },
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528459.1938062,
      "to_source": "orbslam3",
      "wall_time": 1783163656.6433043
    },
    {
      "event": "switch_applied",
      "from_source": "orbslam3",
      "orientation_jump_deg": 65.6452766748334,
      "pose_jump_m": 28.044466986735245,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528471.7535634,
      "to_source": "fast_livo2",
      "wall_time": 1783163669.196447
    }
  ],
  "max_switch_pose_jump_m": 28.044466986735245,
  "max_switch_orientation_jump_deg": 65.6452766748334,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.9397278029812054,
    "orbslam3": 0.9747245625405055,
    "lvisam": 0.0
  },
  "navigation_ok_fraction": 0.8786888701517707
}
```
