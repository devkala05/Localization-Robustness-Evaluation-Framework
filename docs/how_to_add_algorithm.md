# How To Add An Algorithm

1. Add a block under `algorithms` in `config/pipeline.yaml`.

Required keys:

- `enabled`
- `priority`
- `docker_image`
- `launch_file`
- `output_topic`
- `sensors_required`

2. Add a Dockerfile under `docker/{algorithm_id}/`.

Use `localization_eval/base:latest` as the base image, clone the algorithm source, install dependencies, and add a `/launch_algorithm.sh` wrapper that publishes or remaps odometry to `/localization/odometry`.

3. Add a service to `docker-compose.yml`.

Use the `x-ros-common` anchor, mount config/data/results, and keep the service idle by default with the `algo` profile.

4. If the algorithm needs different input topic names, add remaps to `config/topics/{dataset}_topics.yaml`.

No evaluator or report code changes should be needed if the algorithm outputs TUM-compatible poses or `nav_msgs/Odometry` mapped to `/localization/odometry`.
