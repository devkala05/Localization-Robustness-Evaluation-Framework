# Public-dataset validation report

This is a record of real executions, not a compatibility prediction. A
`process complete` result means that playback ended normally and the exported
trajectory passed finite, quaternion, and strictly-monotonic timestamp checks.
It does not by itself mean that localization accuracy is acceptable.

Accuracy acceptance is now automatic. A run must complete, have at least 20
matched poses, cover at least 80% of the scored reference duration, and have
ATE RMSE no greater than 2% of the reference distance covered by its matched
poses (with a 1 m floor for short windows), and maximum ATE no greater than
15 m. Metric modes use SE(3). Sim(3) is
allowed only for explicitly declared pure-monocular mode, where scale is
genuinely unobservable.
Evaluation writes `quality_status.json` plus exactly one of
`VALIDATION_ACCEPTED` or `VALIDATION_REJECTED`; `run_benchmark.sh` exits
non-zero for a rejected run.

## Full-sequence results

These are the longest real runs after applying that gate. `Operational` means
the player and estimator process completed and a valid trajectory was
evaluated. It is intentionally separate from `Accepted`.

| Dataset | Algorithm / mode | Operational | Duration (s) | Matched | Reference distance (m) | ATE RMSE (m) | Max ATE (m) | Accepted |
|---|---|---|---:|---:|---:|---:|---:|---|
| Boreas-RT | FAST-LIO2, SE(3) | yes | 168.81 | 1,623 | 1,853.23 | 2.1735 | 4.2144 | yes |
| Boreas-RT | FAST-LIVO2, SE(3) | yes | 168.90 | 1,518 | 1,853.21 | 3.3570 | 6.0717 | yes |
| Boreas-RT | ORB-SLAM3 mono, Sim(3) | yes | 163.70 | 1,558 | 1,852.06 | 551.9646 | 1,070.1757 | no |
| Boreas-RT | RTAB-Map graph SLAM, SE(3) | yes | 169.02 | 511 | 1,853.10 | 18.3755 | 31.9317 | no |
| Boreas-RT | LVI-SAM visual-LIO, SE(3) | yes | 168.91 | 501 | 1,853.11 | 549.4547 | 838.5802 | no |
| UrbanLoco | FAST-LIO2, SE(3) | yes | 248.27 | 2,407 | 1,360.92 | 4.9585 | 11.2606 | yes |
| UrbanLoco | FAST-LIVO2, SE(3) | yes | 248.00 | 1,610 | 1,360.36 | 6.4072 | 13.2957 | yes |
| UrbanLoco | ORB-SLAM3 mono, Sim(3) | yes | 248.20 | 1,958 | 1,360.68 | 160.4074 | 343.1235 | no |
| UrbanLoco | RTAB-Map graph SLAM, SE(3) | yes | 248.27 | 2,202 | 1,360.87 | 29.0027 | 54.5093 | no |
| UrbanLoco | LVI-SAM lidar-inertial, SE(3) | yes | 248.27 | 1,180 | 1,360.88 | 56.9434 | 99.3513 | no |

UrbanLoco FAST-LIVO2 originally diverged after about 140 seconds: its visual
map grew to 2.6 million points, LiDAR correspondences fell to zero, and the
full ATE RMSE was 641.1261 m. The retained configuration uses the upstream
documented 100 visual outlier threshold, subsamples each organized scan by
four instead of two, and enables the upstream local-map sliding path. The full
rerun covered 1,349.73 estimated metres, ended with a 55,307-point sparse map,
and had no zero-correspondence, NaN-residual, or voxel-overflow log signals.

The corrected RTAB-Map integration runs graph SLAM rather than mislabeling bare
ICP as RTAB-Map. Its full Urban result is still 29.0027 m RMSE and 54.5093 m
maximum ATE; Boreas is 18.3755 m RMSE and 31.9317 m maximum. Both preserve most
travelled distance and have small local RPE, but accumulated ICP drift violates
the 15 m ceiling. No GT anchor was added.

Urban visual LVI-SAM still logged repeated native VINS reboots after calibrated
LiDAR-to-VINS initialization and reached 96.8428 m RMSE. The camera-disabled
native LVI LIO backend completed without those reboots but still produced
56.9434 m RMSE and 99.3513 m maximum ATE, so it is the reported full Urban
result. Full Boreas visual LVI likewise diverged after an accurate first 15
seconds. Accepted short/local slices are not substituted for these results.

## Leak-free chronological retuning

The retuning pass uses the windows in `docs/TUNING_PROTOCOL.md`. Validation
and holdout replay sensors from sequence start for estimator warm-up, then
crop metrics to the requested interval. Boreas evaluation uses the measured
first raw-sensor timestamp, `1733341473.191912`; its ground-truth file starts
36.42 seconds earlier and is not the playback origin.

| Dataset / phase | Algorithm / mode | Alignment | Coverage | ATE RMSE | ATE / distance | Transl. RPE RMSE | Result |
|---|---|---|---:|---:|---:|---:|---|
| Urban tuning, 0--60 s | ORB-SLAM3 pure mono | Sim(3) | 98.5% | 0.7534 m | 0.536% | 0.3565 m | accepted |
| Urban validation, 60--120 s | ORB-SLAM3 pure mono | Sim(3) | 99.9% | 1.7716 m | 0.530% | 0.5420 m | accepted |
| Urban holdout, 180--248 s | ORB-SLAM3 pure mono | Sim(3) | 99.9% | 58.3285 m | 13.249% | 11.1873 m | rejected |
| Urban tuning, 0--60 s | LVI-SAM lidar-inertial | SE(3) | 99.3% | 1.8588 m | 1.315% | 0.4511 m | accepted |
| Urban validation, 60--120 s | LVI-SAM lidar-inertial | SE(3) | 99.3% | 1.3791 m | 0.416% | 0.5677 m | accepted |
| Urban holdout, 180--248 s | LVI-SAM lidar-inertial | SE(3) | 99.4% | 5.2475 m | 1.191% | 1.3627 m | accepted |
| Boreas tuning, 0--45 s | ORB-SLAM3 pure mono | Sim(3) | 87.6% | 13.3735 m | 3.006% | 3.0679 m | rejected |
| Boreas tuning, 0--45 s | ORB-SLAM3 mono-inertial | SE(3) | 85.3% | 84.2254 m | 19.044% | 12.4478 m | rejected |
| Boreas tuning, 0--45 s | LVI-SAM lidar-inertial | SE(3) | 99.3% | 92.8601 m | 21.018% | 11.2319 m | rejected |

Urban ORB-SLAM3 is therefore not complete despite excellent development and
validation metrics: the frozen configuration failed the untouched holdout and
the full exact-timestamp rerun created a second atlas map. Urban LVI-SAM's
locally aligned holdout passes the position gate but its full native trajectory
does not, so it is not complete. Boreas ORB-SLAM3 and LVI-SAM remain rejected.

Urban RTAB-Map's built-in Kalman odometry filter reduced tuning ATE from
1.8724 m to 1.8190 m and its first validation attempt from 7.0553 m to
6.9620 m, but it remained above the 2% gate and was not promoted to holdout.

## Boreas-RT short validation

Sequence: `boreas-2024-12-04-14-44`. The tested window is the first 30 seconds
of the official streams. Every run used the independent DMU41 input and the
post-processed Applanix solution only as evaluation reference. Every topic
graph captured before playback showed subscribers for the mode's required
sensors. Alignment is SE(3), with a 0.05 s association tolerance and no scale
optimization.

| Algorithm | Actual mode | Process | Poses | ATE RMSE (m) | ATE MAE (m) | Transl. RPE RMSE (m) | Rot. RPE RMSE (deg) | Observed localization status |
|---|---|---|---:|---:|---:|---:|---:|---|
| FAST-LIO2 | Alpha Prime LiDAR + DMU41 | complete | 285 | 0.0373 | 0.0350 | 0.0279 | 0.0201 | short validation passed |
| FAST-LIVO2 | Alpha Prime LiDAR + rectified camera + DMU41 | complete | 287 | 0.0513 | 0.0480 | 0.0204 | 0.0219 | short validation passed |
| RTAB-Map | LiDAR ICP odometry + IMU initialization | complete | 83 | 3.2177 | 2.9267 | 0.4906 | 0.2938 | operational, but substantial accumulated drift |
| ORB-SLAM3 | mono-inertial | complete | 243 | 26.0588 | 23.8058 | 4.3339 | 17.2453 | failed accuracy validation; metric trajectory is badly inconsistent with reference |
| LVI-SAM | LiDAR + rectified camera + DMU41 | complete | 128 | 1.1649 | 1.0160 | 0.2969 | 0.0851 | short validation passed after calibrated VINS/LiDAR conversion |

The RTAB-Map configuration raises `Icp/MaxTranslation` from its 0.2 m indoor
default to 1.5 m because the measured vehicle motion between 10 Hz scans is
larger than 0.2 m. This is an input-motion acceptance gate, not trajectory
alignment. The original setting rejected most scans; that failed run is not
presented as a successful result.

The ORB-SLAM3 public runner disables the E2O continuity re-anchor policy. The
reported path is the native metric mono-inertial result transformed only by the
official camera-to-DMU calibration, so estimator resets or jumps are measured
rather than rewritten. Sim(3) was not used because inertial scale is observable.

The first LVI-SAM attempt consumed all three streams but covered only about half
the reference motion (44.4100 m ATE RMSE) and its visual depth-cloud process
reported voxel-index overflow after VINS diverged. Source inspection found that
upstream LVI-SAM uses one hard-coded 180-degree camera/LiDAR quaternion for both
the mapper's VINS initial guess and depth-registration TF. The compatibility
patch now has an opt-in public-dataset path: mapping receives the supplied
IMU-to-LiDAR transform, while depth registration receives the supplied
IMU-to-camera transform. E2O retains the legacy default. With that calibrated
path, the 30-second rerun covered 265.4 m, produced no voxel-overflow warnings,
and achieved the measured result in the table. No sensor was disabled and no
alignment setting was changed.

These numbers are short-window integration evidence only. The full-sequence
table above is authoritative for final acceptance.

The Boreas reference/map overlay was also launched in RViz during a real
FAST-LIO2 playback. The saved profile displayed the official reference path,
reference vehicle pose/TF, live estimator path, and the explicitly labelled
unofficial accumulated LiDAR cloud without applying a visual pose offset.

## UrbanLoco status

The selected 14,079,033,456-byte bag, calibration, documentation, and checksum
manifest are complete. Actual bag inspection found 2,439 organized 32-row LiDAR
clouds, 24,865 IMU messages, 2,487 camera-0 images, and 4,648 SPAN messages; all
selected streams are timestamp-monotonic. Ground-truth conversion retained 4,592
`INS_SOLUTION_GOOD` poses.

The first FAST-LIO2 attempt is a recorded failure, not a result: the actual
RS-LiDAR messages contain only `x,y,z,intensity`, whereas the native Velodyne
parser requires `ring,time`. The adapter now has an UrbanLoco-only organized
cloud conversion that derives channel from the 32 cloud rows and relative scan
time from column acquisition order and the documented 10 Hz period. The full
rerun is the accepted FAST-LIO2 result in the table above.

All UrbanLoco algorithms show much larger 3D rotational RPE than yaw error,
including the two translationally accepted estimators. The official calibration
expresses the Xsens and SPAN frames with non-ROS vehicle-axis conventions. That
remaining orientation-convention discrepancy is reported, not silently
corrected with a fitted transform, and rotational RPE is not part of the ATE
acceptance gate.

## Excluded diagnostic runs

A diagnostic experiment mistakenly applied `camera0_intrinsics.yaml`
undistortion to the Boreas PNGs. The official data reference states that the
distributed images are already rectified and that `P_camera.txt` should be used
directly. Those double-rectified runs were invalidated, the adapter change was
reverted, and none of their metrics are used above.
