# Failure injection and expected behavior

## Start a testable run

```bash
FAULT_INJECTION=true BAG_RATE=0.5 ./run.sh fusion e2o /path/to/one_loop.bag
```

Use another ROS-configured host shell while the bag is playing. The fault injectors sit outside both native estimators. Sensor faults are applied in the E2O adapter; pose faults are applied between each wrapper and fusion.

Record status while testing:

```bash
./tests/observe_switching.sh /tmp/e2o_failure_test
```

## Commands

```bash
# Sensor availability
./tests/failure_control.sh camera_drop
./tests/failure_control.sh camera_freeze
./tests/failure_control.sh camera_delay 2.0
./tests/failure_control.sh camera_recover
./tests/failure_control.sh lidar_drop
./tests/failure_control.sh lidar_recover
./tests/failure_control.sh imu_drop
./tests/failure_control.sh imu_recover

# Estimator output corruption
./tests/failure_control.sh fast_freeze
./tests/failure_control.sh fast_nan
./tests/failure_control.sh fast_jump 100
./tests/failure_control.sh fast_delay 2.0
./tests/failure_control.sh fast_out_of_order
./tests/failure_control.sh fast_recover
./tests/failure_control.sh orb_freeze
./tests/failure_control.sh orb_nan
./tests/failure_control.sh orb_jump 100
./tests/failure_control.sh orb_delay 2.0
./tests/failure_control.sh orb_out_of_order
./tests/failure_control.sh orb_recover

# Process failure/restart
./tests/failure_control.sh kill_fast
./tests/failure_control.sh restart_fast
./tests/failure_control.sh kill_orb
./tests/failure_control.sh restart_orb
```

## Expected scenarios

### Camera unavailable

Both configured estimators require camera input, so expected active source is `none`, status is `FAILED_BOTH_UNHEALTHY`, fused pose/TF stop updating, and `/cmd_vel` is forced to zero. Recovery requires camera health plus estimator stabilization; ORB still requires a valid metric alignment.

### LiDAR unavailable

FAST-LIVO2 or the selected metric primary becomes unhealthy. If ORB is healthy and has a validated metric scale, active source becomes `orbslam3` only for the `lidar_unavailable` failure reason. The first backup pose is aligned to the last fused pose.

### IMU unavailable or FAST pose/process fault

FAST-LIVO2 becomes unhealthy, but fusion does not switch to ORB unless the active metric failure reason includes `lidar_unavailable`. The active source remains FAST-LIVO2, fused output stops while FAST is unhealthy, and navigation is stopped until FAST-LIVO2 is healthy again.

### ORB tracking lost/process stopped

FAST-LIVO2 remains active. ORB is marked unavailable and watched for recovery. No authoritative TF edge changes owner.

### FAST output frozen/process stopped

The health monitor detects repeated timestamps/staleness/process absence. These failures no longer trigger ORB fallback by themselves; recovery requires fresh valid FAST poses.

### NaN, jump, delayed, or out-of-order estimator pose

The health monitor rejects or marks the source unhealthy. Fusion also rejects non-finite and non-monotonic input. These failures do not trigger ORB fallback unless the health reason also includes `lidar_unavailable`. Inspect `reasons` in the health JSON.

### Large disagreement

When both outputs remain individually healthy but disagree beyond thresholds, the state gains `_DEGRADED_DISAGREEMENT`. The configured active source is retained because disagreement alone cannot prove which estimator is wrong. Pose covariance is inflated and the event/status log preserves the condition.

### Both estimators fail

Expected active source is `none`; no new fused pose or authoritative TF is published; `navigation_ok=false`; safety gate repeatedly publishes zero velocity.

## Recovery acceptance

For every recovery verify:

```bash
rostopic echo -n 1 /fused_localization/status
rostopic echo /fused_localization/events
rostopic hz /fused_localization/odometry
```

A recovered estimator must not switch after one sample. Confirm the event occurs only after stabilization/hysteresis, switch `pose_jump_m` remains near zero, no duplicate TF publisher appears, and navigation is re-enabled only with a healthy active source.

## Semi-automated acceptance record

`tests/failure_matrix.csv` lists expected active source, status, TF, navigation behavior, and recovery condition. Store command output, `localization_timeline.jsonl`, `fusion_events.csv`, `roswtf`, and `frames.pdf` with the run. The provided environment did not contain the E2O bag or a ROS/Docker daemon, so these runtime outcomes must be executed on the target machine before claiming completion.
