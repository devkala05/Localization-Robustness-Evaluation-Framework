# Manual robustness test

## 1. Verify the estimator builds

```bash
./tests/verify_v1_estimators.sh
```

To include evidence from a completed run:

```bash
./tests/verify_v1_estimators.sh data/output/<run_id>
```

## 2. Start a fault-enabled run

```bash
./robustness.sh run
```

In a second terminal:

```bash
./robustness.sh watch
```

Wait for both estimators to be healthy and `navigation-ready scale: True` before
testing FAST-LIVO2 fallback. Monocular ORB must not be used as metric fallback
before its scale is validated.

## 3. Apply and recover faults

```bash
./robustness.sh fast_freeze
./robustness.sh fast_recover

./robustness.sh orb_freeze
./robustness.sh orb_recover

./robustness.sh lidar_drop
./robustness.sh lidar_recover

./robustness.sh camera_drop
./robustness.sh camera_recover
```

Clear every fault at once:

```bash
./robustness.sh recover-all
```

See all scenarios and expected outcomes:

```bash
./robustness.sh matrix
```

## Acceptance checks

- FAST failure selects scale-valid ORB and keeps `navigation_ok=true`.
- ORB failure retains or selects healthy FAST.
- Camera failure selects `none` because both E2O estimators require it.
- Both-source failure sets `navigation_ok=false`.
- Recovery respects stabilization and dwell timers; it must not switch on one sample.
- `switch_applied` events should have near-zero position/orientation jumps.
- Large disagreement, output gaps, rejected poses, or repeated switches are test findings and must be reported.

Each run stores `fusion_events.csv`, `localization_timeline.jsonl`, and estimator
trajectories under `data/output/<run_id>/`.
