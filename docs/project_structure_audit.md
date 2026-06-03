# Project Structure Audit

Generated: 2026-06-03 Asia/Kolkata

Required file check:

```text
OK: config/pipeline.yaml
OK: config/perturbations/baseline.yaml
OK: config/perturbations/rain.yaml
OK: config/perturbations/fog.yaml
OK: config/perturbations/low_light.yaml
OK: config/perturbations/glare.yaml
OK: config/perturbations/tunnel_transition.yaml
OK: config/perturbations/foliage_occlusion.yaml
OK: config/perturbations/partial_failure.yaml
OK: config/perturbations/vibration.yaml
OK: config/perturbations/imu_bias_drift.yaml
OK: config/perturbations/combined_rain_low_light.yaml
OK: config/perturbations/combined_fog_vibration.yaml
OK: config/topics/kitti_topics.yaml
OK: docker-compose.yml
OK: docker/base/Dockerfile
OK: docker/fast_lio2/Dockerfile
OK: docker/fast_livo2/Dockerfile
OK: docker/lio_sam/Dockerfile
OK: docker/orb_slam3/Dockerfile
OK: docker/perturbation_injector/Dockerfile
OK: docker/evaluator/Dockerfile
OK: docker/orchestrator/Dockerfile
OK: ros2_ws/src/perturbation_injector
OK: ros2_ws/src/evaluator
OK: ros2_ws/src/orchestrator
OK: scripts/download_dataset.sh
OK: scripts/run_pipeline.sh
OK: scripts/generate_report.py
OK: .env
Total missing: 0
```

Gemini key check: `.env` contains a non-placeholder `GEMINI_API_KEY`. The value is intentionally not copied here.
