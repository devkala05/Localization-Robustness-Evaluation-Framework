# Sensor Failure and Health Monitoring

Practical guide: how to run a fault-enabled session, inject sensor and estimator
failures, and watch the fusion node respond.

All fault injection uses `robustness.sh` — the single entry point for testing.
See `FUSION.md` for the full command reference.

---

## Common test flow

**Terminal 1 — start a fault-enabled fusion run:**
```bash
./robustness.sh run /path/to/one_full_loop.bag
```

**Terminal 2 — watch live colorful status (refreshes every 1 s):**
```bash
./robustness.sh watch
```

**Terminal 3 — watch sensor gate modes (refreshes every 1 s):**
```bash
./robustness.sh gate-status
```

**Terminal 4 — inject and recover a fault:**
```bash
./robustness.sh lidar_drop
sleep 10
./robustness.sh lidar_recover
```

**Terminal 5 (optional) — record all ROS events to file:**
```bash
./robustness.sh record /tmp/e2o_fault_observation
```

---

## Sensor gate faults

No `FAULT_INJECTION=true` required. Changes take effect on the next incoming message.

```bash
# Camera
./robustness.sh camera_drop           # silence RGB + depth → ORB-SLAM3 loses tracking
./robustness.sh camera_freeze         # repeat last camera frame
./robustness.sh camera_delay 2.0      # add 2 s latency
./robustness.sh camera_recover        # restore + restart ORB and LVI-SAM containers

# LiDAR
./robustness.sh lidar_drop            # silence LiDAR → FAST-LIVO2 and LVI-SAM fail
./robustness.sh lidar_freeze
./robustness.sh lidar_delay 1.0
./robustness.sh lidar_recover         # restore + restart FAST-LIVO2 and LVI-SAM

# IMU
./robustness.sh imu_drop              # silence IMU → all estimators fail
./robustness.sh imu_freeze
./robustness.sh imu_delay 0.5
./robustness.sh imu_recover
```

---

## Estimator output faults

Requires `FAULT_INJECTION=true` at run time (`./robustness.sh run` enables it).

```bash
# FAST-LIVO2
./robustness.sh fast_freeze           # publish same pose repeatedly
./robustness.sh fast_nan              # inject NaN poses
./robustness.sh fast_jump 100         # inject a 100 m position discontinuity
./robustness.sh fast_delay 2.0        # delay output by 2 s
./robustness.sh fast_out_of_order     # send future timestamps
./robustness.sh fast_recover

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

## Process control

```bash
./robustness.sh kill_fast        ./robustness.sh restart_fast
./robustness.sh kill_lvisam      ./robustness.sh restart_lvisam
./robustness.sh kill_orb         ./robustness.sh restart_orb
```

---

## Clear all faults

```bash
./robustness.sh recover-all
```

---

## Health topics

```bash
rostopic echo /fused_localization/status       # full JSON: state, health, alignment
rostopic echo /fused_localization/active_source
rostopic echo /fused_localization/events       # JSON event log
rostopic echo /localization_health/fast_livo2
rostopic echo /localization_health/orbslam3
rostopic echo /localization_health/lvisam
rostopic echo /orbslam3/tracking_status
```

Output rates:
```bash
rostopic hz /fast_livo2/odometry
rostopic hz /orbslam3/camera_odometry
rostopic hz /lvisam/odometry
rostopic hz /fused_localization/odometry
```

One-shot diagnostics:
```bash
./scripts/diagnose_runtime.sh
```

---

## Expected behavior by scenario

| Scenario | Expected fusion behavior |
|---|---|
| Camera drop (Fusion 1) | ORB-SLAM3 loses tracking; FAST-LIVO2 reports `camera_unavailable` and fusion switches straight to LVI-SAM (`BACKUP_LVISAM`). |
| Camera drop (Fusion 2) | LVI-SAM stays healthy (camera not required) — no switch, ORB just recovers tracking in the background. |
| LiDAR drop | Metric source (FAST-LIVO2 or LVI-SAM) reports `lidar_unavailable` and fusion switches straight to ORB-SLAM3 (if scale validated). |
| IMU drop | Same as LiDAR drop — metric source reports `imu_unavailable`, fusion switches to ORB-SLAM3. In Fusion 2, if ORB also fails, fusion has no further fallback. |
| ORB tracking lost | Metric/tertiary source remains active. ORB health is tracked for recovery. |
| Metric + ORB both fail (Fusion 1) | Fusion falls back to LVI-SAM tertiary (`BACKUP_LVISAM`). |
| Metric + ORB both fail (Fusion 2) | No further fallback — `FAILED_ALL_UNHEALTHY`. |
| All estimators fail | `FAILED_ALL_UNHEALTHY`, no pose/TF published, `navigation_ok=false`. |
| Large disagreement | Active source stays but state becomes `*_DEGRADED_DISAGREEMENT`. |
| Primary recovers from backup | After `primary_recovery_sec` of stable health, fusion smoothly blends back (anchor + cross-fade, no jump). |

Show the full expected outcome matrix:
```bash
./robustness.sh matrix
```

---

## Output files per run

Each run writes to `data/output/<run_id>/`:

| File | Contents |
|---|---|
| `run_metadata.env` | Mode, bag path, `BAG_RATE`, fault injection flag |
| `localization_timeline.jsonl` | Recorded health, status, events, active source |
| `fusion_events.csv` | Source switches, failures, output gaps with timestamps |
| `fast_livo2_trajectory.csv` | FAST-LIVO2 trajectory (generic multi-topic recorder) |
| `orbslam3_trajectory.csv` | ORB-SLAM3 trajectory (generic multi-topic recorder) |
| `lvisam_trajectory.csv` | LVI-SAM trajectory (generic multi-topic recorder) |
| `fused_trajectory.csv` | Final fused/selected trajectory (generic multi-topic recorder) |
| `fastlivo2.csv` | FAST-LIVO2 raw pose, written directly by `fusion_node.py` |
| `orbslam3.csv` | ORB-SLAM3 raw pose, written directly by `fusion_node.py` |
| `lvisam.csv` | LVI-SAM raw pose, written directly by `fusion_node.py` |
| `fused.csv` | Fused pose + active source + state + blend alpha + switch count + sensor/estimator health per row |
| `evaluation/` | ATE/RTE plots and metrics (if `EVALUATE_AFTER_RUN=true`) |

Review after run:
```bash
./robustness.sh status data/output/<run_id>
```
