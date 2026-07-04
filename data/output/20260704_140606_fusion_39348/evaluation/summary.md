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
  "associations": 937,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 11569.178845362117,
    "mean": 9478.307985910582,
    "median": 7465.57326007388,
    "p95": 28516.143135620016,
    "max": 36275.07127754782
  },
  "rpe_translation_m": {
    "rmse": 348.24003013952426,
    "mean": 221.58075751854318,
    "count": 936,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 9.478330161147785,
    "mean": 4.665899122223006,
    "count": 936,
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
  "associations": 405,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 2.6896762221871273,
    "mean": 2.4212984931598087,
    "median": 2.396862335219984,
    "p95": 3.809602177560104,
    "max": 8.84218469094436
  },
  "rpe_translation_m": {
    "rmse": 1.6429415966095438,
    "mean": 0.6405721323658733,
    "count": 404,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 27.15829014784043,
    "mean": 10.163963719690766,
    "count": 404,
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
  "associations": 292,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 23.31343582950168,
    "mean": 13.087317741666226,
    "median": 3.254214108597142,
    "p95": 58.825243097743076,
    "max": 72.79023577936307
  },
  "rpe_translation_m": {
    "rmse": 4.462905761807576,
    "mean": 1.7460160909841742,
    "count": 291,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.9539522555442937,
    "mean": 0.4376030893214796,
    "count": 291,
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
  "associations": 399,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 9.592987317847637,
    "mean": 3.1012095900278402,
    "median": 1.4485726423516594,
    "p95": 3.0737963067628726,
    "max": 96.3245004556321
  },
  "rpe_translation_m": {
    "rmse": 5.20519241402042,
    "mean": 0.977039079107228,
    "count": 398,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 5.219457885538778,
    "mean": 1.1866616305349278,
    "count": 398,
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
  "associations": 399,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 9.592987317847637,
    "mean": 3.1012095900278402,
    "median": 1.4485726423516594,
    "p95": 3.0737963067628726,
    "max": 96.3245004556321
  },
  "rpe_translation_m": {
    "rmse": 5.20519241402042,
    "mean": 0.977039079107228,
    "count": 398,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 5.219457885538778,
    "mean": 1.1866616305349278,
    "count": 398,
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
  "associations": 399,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 9.184170980465746,
    "mean": 3.176571327229861,
    "median": 1.5583684687944337,
    "p95": 2.255163648733875,
    "max": 56.79623575230215
  },
  "rpe_translation_m": {
    "rmse": 4.600270562253264,
    "mean": 0.9075209968298507,
    "count": 398,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 3.723741760688188,
    "mean": 0.9491548641042541,
    "count": 398,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 25.59048342704773,
    "orbslam3": 3.0185742378234863,
    "fast_livo2": 215.54402804374695,
    "lvisam": 57.763635873794556
  },
  "switch_count": 6,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528216.8043368,
      "to_source": "orbslam3",
      "wall_time": 1783154190.248742
    },
    {
      "event": "switch",
      "from_source": "orbslam3",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 6.206335383118183e-17,
      "reason": "primary_recovered_and_consistent",
      "ros_time": 1723528219.8332126,
      "to_source": "fast_livo2",
      "wall_time": 1783154193.2754948
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "active_unhealthy_tertiary_fallback:position_discontinuity,unrealistic_velocity",
      "ros_time": 1723528435.3180516,
      "to_source": "lvisam",
      "wall_time": 1783154408.7761855
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528464.0784981,
      "to_source": "lvisam",
      "wall_time": 1783154437.5179105
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.4210854715202004e-14,
      "reason": "initial_healthy_source",
      "ros_time": 1723528486.0052178,
      "to_source": "lvisam",
      "wall_time": 1783154459.446718
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528513.363969,
      "to_source": "lvisam",
      "wall_time": 1783154486.8033383
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "orbslam3",
      "orientation_jump_deg": 1.5841267126319483,
      "pose_jump_m": 0.2159086342996802,
      "reason": "primary_recovered_and_consistent",
      "ros_time": 1723528220.6837156,
      "to_source": "fast_livo2",
      "wall_time": 1783154194.1244185
    },
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "active_unhealthy_tertiary_fallback:position_discontinuity,unrealistic_velocity",
      "ros_time": 1723528435.3671687,
      "to_source": "lvisam",
      "wall_time": 1783154408.810715
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528464.0885718,
      "to_source": "lvisam",
      "wall_time": 1783154437.5330598
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528486.0160992,
      "to_source": "lvisam",
      "wall_time": 1783154459.4600282
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528513.3740396,
      "to_source": "lvisam",
      "wall_time": 1783154486.8203535
    }
  ],
  "max_switch_pose_jump_m": 0.2159086342996802,
  "max_switch_orientation_jump_deg": 1.5841267126319483,
  "sensor_availability_fraction": {
    "lidar": 0.9408602150537635,
    "imu": 0.989247311827957,
    "camera": 0.931899641577061
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.40860215053763443,
    "orbslam3": 0.8485663082437276,
    "lvisam": 0.6747311827956989
  },
  "navigation_ok_fraction": 0.1393348623853211
}
```
