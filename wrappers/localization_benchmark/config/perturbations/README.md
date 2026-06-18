Dataset-specific perturbation sets live in separate directories:

- `urbannav/per_*.yaml` uses UrbanNav-HK TST bag timestamps.
- `e2o/per_*.yaml` uses E2O one-full-loop bag timestamps.

Dataset configs must point `paths.perturbations_dir` at one of these leaf
directories. Do not place runnable `per_*.yaml` files in this parent directory;
that makes dataset-specific runs easy to mix by accident.
