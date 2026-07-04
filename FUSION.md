# Fusion Modes

The fusion node runs two or three estimators in parallel, monitors their health independently,
and selects the best available source with continuity-preserving switching.
Fused output: `/fused_localization/odometry`, `/fused_localization/pose`, `/fused_localization/path`

---

## Modes at a glance

| Mode | Estimators | Primary | Backup | Tertiary |
|---|---|---|---|---|
| `fusion` | FAST-LIVO2 + ORB-SLAM3 + LVI-SAM | FAST-LIVO2 | ORB-SLAM3 | LVI-SAM |
| `lvisam_fusion` / `fusion_2` | LVI-SAM + ORB-SLAM3 | LVI-SAM | ORB-SLAM3 | — |
| `fusion_navigation` | FAST-LIVO2 + ORB-SLAM3 + LVI-SAM + nav gate | FAST-LIVO2 | ORB-SLAM3 | LVI-SAM |

---

## Build

```bash
./build.sh all
```

---

## Run

```bash
./run.sh fusion            e2o /path/to/one_full_loop.bag
./run.sh lvisam_fusion     e2o /path/to/one_full_loop.bag
./run.sh fusion_2          e2o /path/to/one_full_loop.bag   # alias for lvisam_fusion
./run.sh fusion_navigation e2o /path/to/one_full_loop.bag
```

With RViz:
```bash
RVIZ=true ./run.sh fusion e2o /path/to/one_full_loop.bag
```

Run only the first N seconds of the bag:
```bash
BAG_DURATION=60 ./run.sh fusion e2o /path/to/one_full_loop.bag
BAG_DURATION=60 ./run.sh fusion_2 e2o /path/to/one_full_loop.bag
```

With navigation launch file:
```bash
TF_MODE=direct \
NAVIGATION_LAUNCH_FILE=/workspace/navigation/my_navigation.launch \
./run.sh fusion_navigation e2o /path/to/one_full_loop.bag
```

Custom fusion config:
```bash
FUSION_CONFIG=/path/to/fusion.yaml ./run.sh fusion e2o /path/to/one_full_loop.bag
```

---

## robustness.sh — all fault testing in one script

`robustness.sh` is the single entry point for starting fault-enabled runs,
monitoring status, injecting sensor/pose faults, and recording events.

### Start a fault-enabled run

```bash
./robustness.sh run
./robustness.sh run /path/to/one_full_loop.bag
```

Equivalent to `FAULT_INJECTION=true RVIZ=true ./run.sh fusion e2o <bag>`.

---

### Live status monitoring

Print the current health summary once (reads from the latest run directory):
```bash
./robustness.sh status
./robustness.sh status data/output/<run_id>
```

Live colorful status, refreshes every 1 s:
```bash
./robustness.sh watch
./robustness.sh watch data/output/<run_id>
```

Live sensor gate mode display, refreshes every 1 s:
```bash
./robustness.sh gate-status
```

Shows the current mode of each stream gate (color-coded: **green**=pass, **red**=drop, **yellow**=freeze/delay).

Record live ROS topics to files while a run is active:
```bash
./robustness.sh record
./robustness.sh record /tmp/my_session
```

---

### Sensor stream faults  *(no `FAULT_INJECTION=true` required)*

These set the `StreamFaultGate` in the sensor adapter. Changes take effect on the next incoming message — no node restart needed.

```bash
# Camera
./robustness.sh camera_drop               # silence RGB + depth → ORB-SLAM3 loses tracking
./robustness.sh camera_freeze             # repeat last frame
./robustness.sh camera_delay 2.0          # insert 2 s latency
./robustness.sh camera_recover            # restore + restart ORB and LVI-SAM containers

# LiDAR
./robustness.sh lidar_drop                # silence LiDAR → FAST-LIVO2 and LVI-SAM fail
./robustness.sh lidar_freeze
./robustness.sh lidar_delay 1.0
./robustness.sh lidar_recover             # restore + restart FAST-LIVO2 and LVI-SAM

# IMU
./robustness.sh imu_drop                  # silence IMU → all estimators fail
./robustness.sh imu_freeze
./robustness.sh imu_delay 0.5
./robustness.sh imu_recover               # restore + restart FAST-LIVO2 and LVI-SAM
```

---

### Estimator pose faults  *(requires `FAULT_INJECTION=true` at run time)*

Corrupt or disrupt the odometry published by a specific estimator, without touching sensors.

```bash
# FAST-LIVO2
./robustness.sh fast_freeze               # publish same pose repeatedly
./robustness.sh fast_nan                  # publish NaN poses
./robustness.sh fast_jump 100             # inject a 100 m position jump
./robustness.sh fast_delay 2.0            # delay output by 2 s
./robustness.sh fast_out_of_order         # send future timestamps
./robustness.sh fast_recover              # restore normal output

# LVI-SAM
./robustness.sh lvisam_freeze
./robustness.sh lvisam_nan
./robustness.sh lvisam_jump 50
./robustness.sh lvisam_delay 1.0
./robustness.sh lvisam_out_of_order
./robustness.sh lvisam_recover

# ORB-SLAM3
./robustness.sh orb_freeze
./robustness.sh orb_nan
./robustness.sh orb_jump 100
./robustness.sh orb_delay 1.0
./robustness.sh orb_out_of_order
./robustness.sh orb_recover
```

---

### Process control

```bash
./robustness.sh kill_fast       # stop the FAST-LIVO2 container
./robustness.sh restart_fast
./robustness.sh kill_lvisam
./robustness.sh restart_lvisam
./robustness.sh kill_orb
./robustness.sh restart_orb
```

---

### Clear all faults

```bash
./robustness.sh recover-all
```

Resets every sensor gate to `pass` and every pose fault to `pass`.

---

### Expected failure outcome table

```bash
./robustness.sh matrix
```

---

## Expected fault behavior

Fusion 1 (`fusion` / `fusion_navigation` mode, primary = FAST-LIVO2): FAST-LIVO2 runs
while LiDAR + camera + IMU are all healthy. A LiDAR/IMU-specific failure switches
straight to ORB-SLAM3; a camera-only failure switches straight to LVI-SAM. Any other
FAST-LIVO2 degradation (jitter, discontinuity, stale output) prefers LVI-SAM over
ORB-SLAM3, since LVI-SAM is still metric-grade. When FAST-LIVO2 recovers and stays
stable for `primary_recovery_sec`, fusion smoothly returns to it.

Fusion 2 (`lvisam_fusion` / `fusion_2` mode, primary = LVI-SAM): LVI-SAM runs while
LiDAR + IMU are healthy. Any LVI-SAM failure switches to ORB-SLAM3 — there is no
tertiary. If ORB-SLAM3 also fails, fusion has no further fallback and declares failure.

### LiDAR fails
FAST-LIVO2/LVI-SAM report `lidar_unavailable`. After `failure_hold_sec`, fusion
switches directly to ORB-SLAM3 (Fusion 1: metric → ORB; Fusion 2: LVI-SAM → ORB).

### Camera fails (Fusion 1 only)
ORB-SLAM3 loses tracking, but FAST-LIVO2 reports `camera_unavailable`. Fusion
switches directly to LVI-SAM (the LiDAR+IMU tertiary), independent of any
FAST-LIVO2 health-score degradation.

### Camera fails (Fusion 2)
LVI-SAM continues unchanged (camera not required). ORB-SLAM3 loses tracking and
recovers in the background. No source switch — LVI-SAM stays primary.

### Metric source and ORB both fail (Fusion 1)
Fusion falls back to LVI-SAM tertiary (`BACKUP_LVISAM` state). When the metric
source or ORB-SLAM3 recovers and stabilizes, fusion switches back automatically.

### All estimators fail
Fusion publishes `FAILED_ALL_UNHEALTHY`, stops publishing pose/TF, sets
`navigation_ok=false`, and the velocity gate zeroes all `cmd_vel` commands.

### Every switch is a smooth blend, not a jump
On every switch the last fused pose is kept as an anchor; the incoming source's
pose is aligned to that anchor and cross-faded in over `blend_duration_sec`
(position lerp + orientation slerp) so there is no position or yaw jump. Switching
to ORB-SLAM3 aligns its corrected (non-raw) current pose to the anchor; switching
back from ORB-SLAM3 aligns the recovered source's own output to the anchor and
fades ORB's weight down to zero as the recovered source's weight fades up.

---

## Monitoring topics

```
/fused_localization/status          JSON health + state + switch count
/fused_localization/active_source   current active source name
/fused_localization/events          JSON event log (switches, gaps, faults)
/fused_localization/navigation_ok   Bool — safe to move
/localization_health/fast_livo2     JSON per-estimator health
/localization_health/orbslam3
/localization_health/lvisam
```

Watch live:
```bash
rostopic echo /fused_localization/status
rostopic echo /fused_localization/active_source
```

---

## State machine states

| State | Meaning |
|---|---|
| `WAITING_FOR_LOCALIZATION` | No healthy source yet |
| `PRIMARY_FAST_LIVO2` | Normal — FAST-LIVO2 active (Fusion 1) |
| `PRIMARY_LVISAM` | Normal — LVI-SAM active (Fusion 1 tertiary or Fusion 2 primary) |
| `BACKUP_LVISAM` | Fusion 1: metric source down, LVI-SAM tertiary active |
| `BACKUP_ORB_SLAM3` | Metric/tertiary source down, ORB-SLAM3 active |
| `*_DEGRADED_DISAGREEMENT` | Active source healthy but diverging from ORB |
| `PRIMARY_*_UNHEALTHY_NO_FALLBACK` | Fusion 1: metric source failed, no fallback usable yet |
| `BACKUP_LVISAM_UNHEALTHY_NO_FALLBACK` | Fusion 1: LVI-SAM tertiary failed, ORB not usable yet |
| `PRIMARY_LVISAM_UNHEALTHY_NO_ORB_FALLBACK` | Fusion 2: LVI-SAM failed, ORB not yet scale-validated |
| `FAILED_ALL_UNHEALTHY` | No valid source (ORB fails with no further fallback) |

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `BAG_RATE` | `1.0` | Rosbag playback speed |
| `BAG_DURATION` | — | Stop rosbag playback after this many seconds |
| `RVIZ` | `false` | Launch RViz |
| `TF_MODE` | `direct` | `direct`, `map_to_odom`, or `none` |
| `PRIMARY_SOURCE` | `fast_livo2` / `lvisam` | Override active primary |
| `FAULT_INJECTION` | `false` | Enable pose fault injectors |
| `FUSION_CONFIG` | mode-specific yaml | Override fusion config path |
| `NAVIGATION_LAUNCH_FILE` | — | Launch file for `fusion_navigation` mode |
| `EVALUATE_AFTER_RUN` | `true` | Run evaluator when bag finishes |
| `EVAL_GT` | `data/e2o/ground_truth/ref.csv` | Ground truth CSV |
| `FAST_SAVE_PCD` | `false` | Save FAST-LIVO2 point cloud map |
| `LIDAR_TOPIC` | `/lidar103/velodyne_points` | Raw LiDAR topic |
| `IMU_TOPIC` | `/mavros/imu/data` | Raw IMU topic |
| `CAMERA_TOPIC` | `/camera/color/image_raw` | Raw RGB topic |
| `DEPTH_TOPIC` | `/camera/depth/image_rect_raw` | Raw depth topic |
