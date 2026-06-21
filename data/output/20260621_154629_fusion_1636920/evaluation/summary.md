# E2O Localization Evaluation

Reference: `/home/ayush/Desktop/Localiztion/e2o_localization_fusion_framework/data/e2o/ground_truth/one_loop_gps_enu.csv`

Source method: `gps_enu_rolling_mean`

## Reference limitations

- GPS-ENU reference has meter-level uncertainty and does not provide trustworthy orientation/yaw.
- Neither included reference is survey-grade ground truth.

## fast_livo2

```json
{
  "valid": true,
  "alignment": "se3",
  "alignment_scale": 1.0,
  "associations": 1701,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 17.955442967753246,
    "mean": 16.99511810864472,
    "median": 18.364705605378127,
    "p95": 25.31612132117969,
    "max": 30.168303230654168
  },
  "rpe_translation_m": {
    "rmse": 4.1867686073279105,
    "mean": 1.275952033985736,
    "count": 1692,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": false,
    "rmse": null,
    "mean": null,
    "count": 0,
    "delta_sec": 1.0
  }
}
```

## orbslam3

```json
{
  "valid": true,
  "alignment": "sim3",
  "alignment_scale": 5.610772286769744,
  "associations": 3106,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 24.0007522099544,
    "mean": 20.309077793023942,
    "median": 18.445222446405346,
    "p95": 47.83508090066623,
    "max": 54.12449628383375
  },
  "rpe_translation_m": {
    "rmse": 2.3483380504761233,
    "mean": 1.5060705602329691,
    "count": 3096,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": false,
    "rmse": null,
    "mean": null,
    "count": 0,
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
  "associations": 1883,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 56.71346253488434,
    "mean": 47.187166902537605,
    "median": 43.00539362106449,
    "p95": 105.0954752243632,
    "max": 117.89352300859046
  },
  "rpe_translation_m": {
    "rmse": 4.4603046801159785,
    "mean": 2.5821320563245016,
    "count": 1877,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": false,
    "rmse": null,
    "mean": null,
    "count": 0,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 69.35089063644409,
    "fast_livo2": 56.56163167953491,
    "orbslam3": 182.52925181388855
  },
  "switch_count": 5,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528217.1734388,
      "to_source": "fast_livo2",
      "wall_time": 1782037011.710387
    },
    {
      "event": "switch",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 2.7755575615628914e-17,
      "reason": "active_unhealthy:duplicate_timestamp",
      "ros_time": 1723528273.7350705,
      "to_source": "orbslam3",
      "wall_time": 1782037068.2725244
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 2.0116800053149086e-14,
      "reason": "initial_healthy_source",
      "ros_time": 1723528344.8030562,
      "to_source": "orbslam3",
      "wall_time": 1782037139.3401546
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.5943977756741603e-14,
      "reason": "initial_healthy_source",
      "ros_time": 1723528412.2040377,
      "to_source": "orbslam3",
      "wall_time": 1782037206.7410872
    },
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.5987211554602254e-14,
      "reason": "initial_healthy_source",
      "ros_time": 1723528461.8087215,
      "to_source": "orbslam3",
      "wall_time": 1782037256.3457515
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "fast_livo2",
      "orientation_jump_deg": 1.2074182697257333e-06,
      "pose_jump_m": 0.0,
      "reason": "active_unhealthy:duplicate_timestamp",
      "ros_time": 1723528273.7350705,
      "to_source": "orbslam3",
      "wall_time": 1782037068.2752666
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528344.8030562,
      "to_source": "orbslam3",
      "wall_time": 1782037139.3442059
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528412.2040377,
      "to_source": "orbslam3",
      "wall_time": 1782037206.7498076
    },
    {
      "event": "switch_applied",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528461.8087215,
      "to_source": "orbslam3",
      "wall_time": 1782037256.3513138
    }
  ],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 1.2074182697257333e-06,
  "sensor_availability_fraction": {
    "lidar": 0.9176928062216462,
    "imu": 1.0,
    "camera": 0.9844458846403111
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.32534024627349317,
    "orbslam3": 0.7744653272845107
  },
  "navigation_ok_fraction": 0.7690645927846187
}
```
