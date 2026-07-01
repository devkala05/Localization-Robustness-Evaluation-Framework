#!/usr/bin/env bash
# Build a fresh ROS1 Noetic + RViz Docker image (when needed), then compare
# two CSV trajectories in RViz.
#
# Run this FROM the folder containing:
#   compare_csv_trajectories.py
#   lvisam.csv
#   fastlio2.csv
#
# Example:
#   chmod +x run_csv_compare_docker.sh
#   ./run_csv_compare_docker.sh \
#     --csv-a lvisam.csv --csv-b fastlio2.csv \
#     --name-a LVISAM --name-b FASTLIO2 \
#     --align se2 --frame map
#
# Add --rebuild once to force Docker to rebuild the image.

set -Eeuo pipefail

IMAGE_NAME="csv-rviz-noetic:latest"
WORK_DIR="$(pwd)"
BUILD_DIR="${WORK_DIR}/.csv_rviz_docker_build"
PYTHON_SCRIPT="${WORK_DIR}/compare_csv_trajectories.py"
REBUILD=0
TRAJ_ARGS=()

usage() {
  cat <<'EOF'
Usage:
  ./run_csv_compare_docker.sh [--rebuild] \
    --csv-a lvisam.csv --csv-b fastlio2.csv \
    --name-a LVISAM --name-b FASTLIO2 \
    --align se2 --frame map

This must be run from the folder containing compare_csv_trajectories.py.
Use relative CSV paths from that same folder.
EOF
}

# Keep --rebuild for this shell script; pass every other option unchanged
# to compare_csv_trajectories.py inside the container.
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rebuild)
      REBUILD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      TRAJ_ARGS+=("$1")
      shift
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is not installed or is not on PATH." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: Docker daemon is not available." >&2
  echo "Try: sudo systemctl start docker" >&2
  echo "If you get a permission error, run: sudo usermod -aG docker \$USER" >&2
  echo "Then log out and log in once." >&2
  exit 1
fi

if [[ ${#TRAJ_ARGS[@]} -eq 0 ]]; then
  echo "ERROR: Provide CSV arguments. Example:" >&2
  echo "  ./run_csv_compare_docker.sh --csv-a lvisam.csv --csv-b fastlio2.csv --name-a LVISAM --name-b FASTLIO2 --align se2 --frame map" >&2
  exit 1
fi

if [[ ! -f "$PYTHON_SCRIPT" ]]; then
  echo "ERROR: Missing ${PYTHON_SCRIPT}" >&2
  echo "Put compare_csv_trajectories.py in the current comparisons folder first." >&2
  exit 1
fi

if [[ ! -n "${DISPLAY:-}" ]]; then
  echo "ERROR: DISPLAY is empty. Run this from your graphical desktop terminal." >&2
  exit 1
fi

if ! command -v xauth >/dev/null 2>&1; then
  echo "ERROR: xauth is required on the HOST for secure RViz X11 access." >&2
  echo "Install it once on the host:" >&2
  echo "  sudo apt update && sudo apt install -y xauth" >&2
  exit 1
fi

mkdir -p "$BUILD_DIR"

cat > "${BUILD_DIR}/Dockerfile" <<'DOCKERFILE'
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

# ROS1 Noetic targets Ubuntu 20.04 (Focal).
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      gnupg \
      locales \
      python3 \
      libgl1 \
      libgl1-mesa-dri \
      libgl1-mesa-glx \
      mesa-utils \
      xauth \
    && sed -i 's/^# *\(en_US.UTF-8 UTF-8\)/\1/' /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# Official ROS package repository signing key and Focal repository.
RUN curl -fsSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros/ubuntu focal main" \
      > /etc/apt/sources.list.d/ros1.list

# Only install the ROS pieces required by the publisher and RViz.
RUN apt-get update && apt-get install -y --no-install-recommends \
      ros-noetic-ros-base \
      ros-noetic-rospy \
      ros-noetic-rviz \
      ros-noetic-geometry-msgs \
      ros-noetic-nav-msgs \
      ros-noetic-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /opt/csv_compare/entrypoint.sh
COPY csv_compare.rviz /opt/csv_compare/csv_compare.rviz
RUN chmod +x /opt/csv_compare/entrypoint.sh

ENTRYPOINT ["/opt/csv_compare/entrypoint.sh"]
DOCKERFILE

cat > "${BUILD_DIR}/entrypoint.sh" <<'ENTRYPOINT'
#!/usr/bin/env bash
set -Eeuo pipefail

# ROS Noetic setup scripts reference unset variables internally, so do not
# keep bash nounset (-u) enabled while sourcing them.
set +u
source /opt/ros/noetic/setup.bash
set -u

cleanup() {
  [[ -n "${PUBLISHER_PID:-}" ]] && kill "${PUBLISHER_PID}" 2>/dev/null || true
  [[ -n "${ROSCORE_PID:-}" ]] && kill "${ROSCORE_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

roscore >/tmp/roscore.log 2>&1 &
ROSCORE_PID=$!

# Wait until roscore really accepts requests.
for _ in $(seq 1 30); do
  if rosparam list >/dev/null 2>&1; then
    break
  fi
  sleep 0.2
done

if ! rosparam list >/dev/null 2>&1; then
  echo "ERROR: roscore did not start. Log:" >&2
  cat /tmp/roscore.log >&2 || true
  exit 1
fi

python3 /work/compare_csv_trajectories.py "$@" &
PUBLISHER_PID=$!

# Do not open an empty RViz window if CSV parsing/publishing failed.
sleep 1
if ! kill -0 "$PUBLISHER_PID" 2>/dev/null; then
  echo "ERROR: CSV trajectory publisher exited before RViz started." >&2
  wait "$PUBLISHER_PID" || true
  exit 1
fi

rviz -d /opt/csv_compare/csv_compare.rviz
RVIZ_STATUS=$?
exit "$RVIZ_STATUS"
ENTRYPOINT

cat > "${BUILD_DIR}/csv_compare.rviz" <<'RVIZCFG'
Panels:
  - Class: rviz/Displays
    Help Height: 78
    Name: Displays
    Property Tree Widget:
      Expanded:
        - /Global Options1
        - /CSV trajectories1
      Splitter Ratio: 0.5
    Tree Height: 400
  - Class: rviz/Selection
    Name: Selection
  - Class: rviz/Tool Properties
    Expanded:
      - /2D Pose Estimate1
      - /2D Nav Goal1
    Name: Tool Properties
    Splitter Ratio: 0.588
  - Class: rviz/Views
    Expanded:
      - /Current View1
    Name: Views
    Splitter Ratio: 0.5
Preferences:
  PromptSaveOnExit: false
Toolbars:
  toolButtonStyle: 2
Visualization Manager:
  Class: ""
  Displays:
    - Class: rviz/MarkerArray
      Enabled: true
      Marker Topic: /csv_compare/markers
      Name: CSV trajectories
      Namespaces:
        csv_trajectory: true
        csv_trajectory_labels: true
      Queue Size: 100
    - Alpha: 1
      Buffer Length: 1
      Class: rviz/Path
      Color: 0; 255; 255
      Enabled: true
      Line Style: Lines
      Line Width: 0.03
      Name: Path A (cyan)
      Offset:
        X: 0
        Y: 0
        Z: 0
      Pose Color: 255; 255; 255
      Pose Style: None
      Topic: /csv_compare/path_a
      Unreliable: false
    - Alpha: 1
      Buffer Length: 1
      Class: rviz/Path
      Color: 255; 110; 0
      Enabled: true
      Line Style: Lines
      Line Width: 0.03
      Name: Path B (orange)
      Offset:
        X: 0
        Y: 0
        Z: 0
      Pose Color: 255; 255; 255
      Pose Style: None
      Topic: /csv_compare/path_b
      Unreliable: false
  Enabled: true
  Global Options:
    Background Color: 48; 48; 48
    Fixed Frame: map
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz/Interact
      Hide Inactive Objects: true
    - Class: rviz/MoveCamera
    - Class: rviz/Select
    - Class: rviz/FocusCamera
    - Class: rviz/Measure
    - Class: rviz/SetInitialPose
      Topic: /initialpose
    - Class: rviz/SetGoal
      Topic: /move_base_simple/goal
  Views:
    Current:
      Class: rviz/Orbit
      Distance: 30
      Focal Point:
        X: 0
        Y: 0
        Z: 0
      Name: Current View
      Pitch: 0.785
      Yaw: 0.785
Window Geometry:
  Height: 900
  Width: 1400
  X: 50
  Y: 50
RVIZCFG

if [[ "$REBUILD" -eq 1 ]] || ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
  echo "Building Docker image: ${IMAGE_NAME}"
  docker build --pull -t "$IMAGE_NAME" "$BUILD_DIR"
fi

# Make an Xauthority file containing only this display's cookie.
XAUTH_FILE="${BUILD_DIR}/.docker.xauth"
rm -f "$XAUTH_FILE"
touch "$XAUTH_FILE"
xauth nlist "$DISPLAY" | sed -e 's/^..../ffff/' | xauth -f "$XAUTH_FILE" nmerge - || true
chmod 644 "$XAUTH_FILE"

if [[ ! -s "$XAUTH_FILE" ]]; then
  echo "ERROR: Could not create an X11 authentication cookie for DISPLAY=${DISPLAY}." >&2
  echo "Open a terminal from the same desktop session and run this script there." >&2
  exit 1
fi

DOCKER_RUN_ARGS=(
  --rm
  -it
  --name "csv-rviz-compare-$RANDOM"
  --user "$(id -u):$(id -g)"
  --env "DISPLAY=${DISPLAY}"
  --env "XAUTHORITY=/tmp/.docker.xauth"
  --env "HOME=/tmp"
  --env "QT_X11_NO_MITSHM=1"
  --volume "${WORK_DIR}:/work:rw"
  --volume "/tmp/.X11-unix:/tmp/.X11-unix:rw"
  --volume "${XAUTH_FILE}:/tmp/.docker.xauth:ro"
  --workdir /work
)

# Enable hardware OpenGL through DRM when available; it is safe to omit when absent.
if [[ -d /dev/dri ]]; then
  DOCKER_RUN_ARGS+=(--device /dev/dri)
  for drm_dev in /dev/dri/*; do
    [[ -e "$drm_dev" ]] || continue
    drm_gid="$(stat -c '%g' "$drm_dev")"
    DOCKER_RUN_ARGS+=(--group-add "$drm_gid")
  done
fi

echo "Starting a new temporary container from ${IMAGE_NAME}..."
echo "Close RViz to stop the publisher and remove this container."

docker run "${DOCKER_RUN_ARGS[@]}" "$IMAGE_NAME" "${TRAJ_ARGS[@]}"
