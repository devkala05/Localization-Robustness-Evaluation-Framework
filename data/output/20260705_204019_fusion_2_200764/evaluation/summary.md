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
  "associations": 584,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 1.3359561853662694,
    "mean": 1.1980038663415773,
    "median": 1.1794690179108085,
    "p95": 2.1378421329591832,
    "max": 2.423179090074336
  },
  "rpe_translation_m": {
    "rmse": 0.2732658503936655,
    "mean": 0.22131514091102558,
    "count": 583,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.8405609587353263,
    "mean": 0.6461380919534884,
    "count": 583,
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
  "associations": 293,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 6.9253599438932785e-09,
    "mean": 9.967446148665942e-10,
    "median": 4.42748243975081e-10,
    "p95": 1.3537123919094957e-09,
    "max": 1.1788057310003309e-07
  },
  "rpe_translation_m": {
    "rmse": 9.933810933177881e-09,
    "mean": 8.860829062062937e-10,
    "count": 288,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.4229560770859896e-07,
    "mean": 1.431383274984255e-08,
    "count": 288,
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
  "associations": 1328,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 5.844533607809037,
    "mean": 5.270499121025429,
    "median": 4.742490520482915,
    "p95": 10.605974775501696,
    "max": 12.127400656288232
  },
  "rpe_translation_m": {
    "rmse": 0.5696097669334482,
    "mean": 0.3297615693375894,
    "count": 1323,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.8098559990728847,
    "mean": 0.4489115099568974,
    "count": 1323,
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
  "associations": 1328,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 5.844533607809037,
    "mean": 5.270499121025429,
    "median": 4.742490520482915,
    "p95": 10.605974775501696,
    "max": 12.127400656288232
  },
  "rpe_translation_m": {
    "rmse": 0.5696097669334482,
    "mean": 0.3297615693375894,
    "count": 1323,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 0.8098559990728847,
    "mean": 0.4489115099568974,
    "count": 1323,
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
  "associations": 256,
  "association_max_dt_sec": 0.1,
  "ate_m": {
    "rmse": 7.405862160566967e-09,
    "mean": 1.1258788945020538e-09,
    "median": 5.90769986317297e-10,
    "p95": 1.4571220401054112e-09,
    "max": 1.1778259820757432e-07
  },
  "rpe_translation_m": {
    "rmse": 1.0640791421400172e-08,
    "mean": 1.0276715762670026e-09,
    "count": 251,
    "delta_sec": 1.0
  },
  "rpe_rotation_deg": {
    "evaluated": true,
    "rmse": 1.0964934834293654e-06,
    "mean": 7.391478080811403e-07,
    "count": 251,
    "delta_sec": 1.0
  }
}
```

## Fusion timeline

```json
{
  "source_duration_sec": {
    "none": 8.005099773406982,
    "lvisam": 53.955228328704834,
    "orbslam3": 246.48909091949463
  },
  "switch_count": 2,
  "switches": [
    {
      "event": "switch",
      "from_source": "none",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "initial_healthy_source",
      "ros_time": 1723528221.207504,
      "to_source": "lvisam",
      "wall_time": 1783264245.1352978
    },
    {
      "event": "switch",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 1.464821375527116e-14,
      "reason": "lvisam_unhealthy_fallback:delayed_pose_timestamp",
      "ros_time": 1723528275.1425984,
      "to_source": "orbslam3",
      "wall_time": 1783264299.0754454
    }
  ],
  "applied_switches": [
    {
      "event": "switch_applied",
      "from_source": "lvisam",
      "orientation_jump_deg": 0.0,
      "pose_jump_m": 0.0,
      "reason": "lvisam_unhealthy_fallback:delayed_pose_timestamp",
      "ros_time": 1723528275.152668,
      "to_source": "orbslam3",
      "wall_time": 1783264299.0830564
    }
  ],
  "max_switch_pose_jump_m": 0.0,
  "max_switch_orientation_jump_deg": 0.0,
  "sensor_availability_fraction": {
    "lidar": 0.20220349967595594,
    "imu": 1.0,
    "camera": 1.0
  },
  "estimator_healthy_fraction": {
    "fast_livo2": 0.0,
    "orbslam3": 0.9980557355800389,
    "lvisam": 0.1970187945560596
  },
  "navigation_ok_fraction": 0.9481887110362258
}
```
