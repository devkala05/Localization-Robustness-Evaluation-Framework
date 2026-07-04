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
  "associations": 1197,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 0.3096057234422964,
    "mean": 0.2753962518933424,
    "median": 0.24926016384256508,
    "p95": 0.5412347282223647,
    "max": 0.7675493008958386
  },
  "rpe_translation_m": {
    "rmse": 0.2217816185911995,
    "mean": 0.17854192863489343,
    "count": 1194,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.7825822456008884,
    "mean": 0.5087884021067332,
    "count": 1194,
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
  "associations": 814,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 21.419869117939445,
    "mean": 20.01734907870123,
    "median": 20.57986069728475,
    "p95": 32.36516774276358,
    "max": 45.432784270077946
  },
  "rpe_translation_m": {
    "rmse": 2.450813333627506,
    "mean": 1.3066835536558363,
    "count": 809,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 16.886804325512006,
    "mean": 8.007503322213628,
    "count": 809,
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
  "associations": 431,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 8.324748317390606,
    "mean": 3.20392427077938,
    "median": 1.7387255105152846,
    "p95": 1.9145538162845568,
    "max": 45.72954961531628
  },
  "rpe_translation_m": {
    "rmse": 1.6743273377823058,
    "mean": 0.22023197263440367,
    "count": 428,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.3400701666804327,
    "mean": 0.11544089365393997,
    "count": 428,
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
  "associations": 1159,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 3.616763346392329,
    "mean": 1.4961653721461685,
    "median": 0.8219240815244103,
    "p95": 1.4616064623930969,
    "max": 19.16480479361727
  },
  "rpe_translation_m": {
    "rmse": 0.5482381003176332,
    "mean": 0.2217329995073797,
    "count": 1155,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.8685894843213657,
    "mean": 0.5492953262880659,
    "count": 1155,
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
  "associations": 1159,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 3.616763346392329,
    "mean": 1.4961653721461685,
    "median": 0.8219240815244103,
    "p95": 1.4616064623930969,
    "max": 19.16480479361727
  },
  "rpe_translation_m": {
    "rmse": 0.5482381003176332,
    "mean": 0.2217329995073797,
    "count": 1155,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.8685894843213657,
    "mean": 0.5492953262880659,
    "count": 1155,
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
  "associations": 1159,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.0098060908907738,
    "mean": 0.32371123738962915,
    "median": 0.26287093290766383,
    "p95": 0.5385912982980023,
    "max": 25.928804302131624
  },
  "rpe_translation_m": {
    "rmse": 1.3520737818450463,
    "mean": 0.25962429098919587,
    "count": 1155,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.85488323216529,
    "mean": 0.5503469154072088,
    "count": 1155,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 3.408247470855713,
    "orbslam3": 3.001800775527954,
    "fast_livo2": 288.99982810020447,
    "lvisam": 11.929780006408691
  },
  "switch_count": 6,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528216.6244006,
      "to_source": "orbslam3",
      "wall_time": 1783159547.409654
    },
    {
      "event": "switch",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 4.3885418357208765e-17,
      "reason": "primary_recovered_and_consistent",
      "ros_time": 1723528219.6262014,
      "to_source": "fast_livo2",
      "wall_time": 1783159550.4120913
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.0051044705644574e-14,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528487.3626087,
      "to_source": "lvisam",
      "wall_time": 1783159818.1499412
    },
    {
      "event": "switch",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 7.94721185223203e-15,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528492.6047382,
      "to_source": "fast_livo2",
      "wall_time": 1783159823.3895936
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 7.108895957933346e-15,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528500.961617,
      "to_source": "lvisam",
      "wall_time": 1783159831.7555523
    },
    {
      "event": "switch",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528507.5951385,
      "to_source": "fast_livo2",
      "wall_time": 1783159838.3803618
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.03365897691963786,
      "pose_jump_m": 0.004488220604113352,
      "reason": "primary_recovered_and_consistent",
      "ros_time": 1723528219.7205472,
      "to_source": "fast_livo2",
      "wall_time": 1783159550.506989
    },
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.21467900062132872,
      "pose_jump_m": 0.19419361584829842,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528487.4985032,
      "to_source": "lvisam",
      "wall_time": 1783159818.2834442
    },
    {
      "event": "switch_applied",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528492.6047382,
      "to_source": "fast_livo2",
      "wall_time": 1783159823.4029741
    },
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.9512171180321943,
      "pose_jump_m": 0.19460604122842792,
      "reason": "fast_livo2_unhealthy_fallback:pose_rate_too_low",
      "ros_time": 1723528501.067446,
      "to_source": "lvisam",
      "wall_time": 1783159831.8569007
    },
    {
      "event": "switch_applied",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "primary_recovered_without_recovery_overlap",
      "ros_time": 1723528507.60524,
      "to_source": "fast_livo2",
      "wall_time": 1783159838.400566
    }
  ],
  "max_switch_pose_jump_m": 0.19460604122842792,
  "max_switch_orientation_jump_deg": 0.9512171180321943,
  "sensor_availability_fraction": {
    "lidar": 1.0,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.9882888744307091,
    "orbslam3": 0.9700715679895902,
    "lvisam": 0.9804814573845153
  },
  "navigation_ok_fraction": 0.09238126290620585
}
```
