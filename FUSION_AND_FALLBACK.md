# Fusion and fallback design

## Selected method

The implementation uses **health-gated primary-source selection with external trajectory alignment and consistency checking**. This is simpler and more maintainable than an EKF that would require trustworthy covariances and observability assumptions not available from both wrappers. It is still genuine loose coupling: both estimators run independently; the supervisor uses their complete pose estimates and never forwards the newest message blindly.

FAST-LIVO2 is the default primary. ORB-SLAM3 is an independent visual backup and consistency monitor.

## ORB-SLAM3 metric alignment

The E2O ORB pipeline runs RGB-D, with RGB resized to the depth image dimensions before ORB-SLAM3. During synchronized periods where both health monitors report healthy, the fusion node collects `(FAST base pose, ORB camera pose)` pairs. It estimates:

1. quaternion-safe world-orientation alignment;
2. a positive scalar consistency scale from trajectory motion;
3. world translation;
4. camera-to-base compensation using the configured metric lever arm after scale.

The result is accepted only when sample count, scale bounds, position RMSE, and orientation RMSE pass configuration thresholds. ORB cannot become fallback by default until this metric alignment is validated.

## Health criteria

Each estimator is unhealthy when any required criterion fails:

- no pose, stale pose, low output rate, repeated/frozen stamp, timestamp regression, delayed/future stamp;
- non-finite pose;
- position/orientation discontinuity;
- unrealistic velocity, angular velocity, or acceleration;
- required sensor unavailable, frozen, delayed, or timestamp-invalid;
- expected process absent;
- ORB tracking state not healthy or stale.

FAST-LIVO2 requires LiDAR, IMU, and camera by default. This deliberately avoids assuming that a native LIO-only or VIO-only fallback is safe. Change `required_sensors` only after runtime verification of the pinned implementation and configuration.

## Switching

### FAST-LIVO2 failure

After `failure_hold_sec`, a stable and scale-valid ORB source is selected. The current ORB metric pose is rigidly aligned to the last fused pose:

```text
T_output_from_orb = T_last_fused × inverse(T_current_metric_orb)
```

Therefore the first backup pose equals the previous fused pose. Following samples transition over `blend_duration_sec`. The event includes source, reason, and measured switch jump.

### ORB-SLAM3 failure

FAST-LIVO2 continues. ORB health remains visible and is monitored for recovery; the active output is not interrupted.

### Both unhealthy

The node stops publishing new fused pose/TF, publishes `FAILED_BOTH_UNHEALTHY`, sets `navigation_ok=false`, and the velocity gate emits zero commands. Stale pose is never labeled valid.

### Recovery

A recovering source must remain healthy for the configured stabilization interval. Returning to the primary additionally requires minimum source dwell, stricter disagreement thresholds, and `primary_recovery_sec`. The same continuity transform and blend are used for the return switch.

## Important limitation

A continuity transform prevents a discontinuity at the switching instant; it does not make an already drifted backup trajectory globally correct. The online disagreement monitor detects large divergence but does not solve a full multi-session map-merging problem.
