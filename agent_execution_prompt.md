# Agent Task: End-to-End Execution & Verification of Localization Robustness Pipeline

## Context

A localization robustness evaluation pipeline has been scaffolded at:
```
/home/devil/Desktop/car/localisation/
```

The scaffold was verified for syntax and structure only. The previous agent used **deterministic synthetic trajectory simulation** instead of real SLAM algorithms running on real data. 

Your job is to make everything work for **real** — real Docker builds, real dataset download, real algorithm execution, real sensor data flowing through the perturbation injector, real trajectory output, real evaluation against ground truth. Do not stop until every item in the **Success Checklist** at the bottom of this prompt is confirmed green with real evidence (actual file contents, actual metric values from real data, not synthetic placeholders).

---

## Ground Rules

1. **Never simulate or stub.** If a step fails, fix the actual failure. Do not patch around it by generating fake output files. If an algorithm won't build, debug and fix the build. If a topic doesn't publish, debug the remapping.

2. **Fix forward, not around.** If Docker build fails for `fast_livo2`, fix the Dockerfile. Do not skip `fast_livo2` and mark it done.

3. **Document every fix.** For every non-trivial fix you make (patching a Dockerfile, changing a topic name, adjusting a launch arg), append one line to `/home/devil/Desktop/car/localisation/docs/fixes_log.md` in format: `[YYYY-MM-DD] <component>: <what was broken> → <what you changed>`.

4. **Confirm output is real.** After every step that produces a file, `cat` or `head` the file and confirm it contains real data (real timestamps, real coordinate values, real metric numbers — not zeros, not hardcoded test values, not "None").

5. **One algorithm first, then scale.** Get the full pipeline working end-to-end for **FAST-LIO2 on baseline + rain scenarios on one sequence** before touching the other four algorithms. Once FAST-LIO2 works fully, apply the same fixes to the rest.

6. **Do not exceed disk or RAM.** Check `df -h` before downloading datasets. If disk is under 30 GB free, tell the user and stop — do not proceed with download. Check `free -h` before starting multi-container builds.

---

## Phase 0: Environment Audit

Before doing anything else, run and record the output of each command:

```bash
# GPU
nvidia-smi

# Docker
docker --version
docker compose version
docker info | grep -i runtime   # must show nvidia runtime

# NVIDIA Container Toolkit
dpkg -l | grep nvidia-container

# Disk space
df -h /home/devil/Desktop/car/

# RAM
free -h

# ROS2
source /opt/ros/humble/setup.bash 2>/dev/null && echo "ROS2 Humble OK" || echo "ROS2 NOT FOUND"

# Python
python3 --version
pip3 show rosbags 2>/dev/null || echo "rosbags not installed"
pip3 show google-generativeai 2>/dev/null || echo "google-generativeai not installed"
```

If NVIDIA Container Toolkit is missing, install it:
```bash
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list \
  | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

If `rosbags` is missing: `pip3 install rosbags`
If `google-generativeai` is missing: `pip3 install google-generativeai`

After Phase 0, record all output in `docs/environment_audit.md`.

---

## Phase 1: Project Structure Audit

```bash
cd /home/devil/Desktop/car/localisation

# Print the full tree (2 levels)
find . -maxdepth 3 -not -path '*/\.*' | sort

# Confirm required files exist
required_files=(
  "config/pipeline.yaml"
  "config/perturbations/baseline.yaml"
  "config/perturbations/rain.yaml"
  "config/perturbations/fog.yaml"
  "config/perturbations/low_light.yaml"
  "config/perturbations/glare.yaml"
  "config/perturbations/tunnel_transition.yaml"
  "config/perturbations/foliage_occlusion.yaml"
  "config/perturbations/partial_failure.yaml"
  "config/perturbations/vibration.yaml"
  "config/perturbations/imu_bias_drift.yaml"
  "config/perturbations/combined_rain_low_light.yaml"
  "config/perturbations/combined_fog_vibration.yaml"
  "config/topics/kitti_topics.yaml"
  "docker-compose.yml"
  "docker/base/Dockerfile"
  "docker/fast_lio2/Dockerfile"
  "docker/fast_livo2/Dockerfile"
  "docker/lio_sam/Dockerfile"
  "docker/orb_slam3/Dockerfile"
  "docker/perturbation_injector/Dockerfile"
  "docker/evaluator/Dockerfile"
  "docker/orchestrator/Dockerfile"
  "ros2_ws/src/perturbation_injector"
  "ros2_ws/src/evaluator"
  "ros2_ws/src/orchestrator"
  "scripts/download_dataset.sh"
  "scripts/run_pipeline.sh"
  "scripts/generate_report.py"
  ".env"
)

missing=0
for f in "${required_files[@]}"; do
  if [ ! -e "$f" ]; then
    echo "MISSING: $f"
    missing=$((missing+1))
  else
    echo "OK: $f"
  fi
done
echo "Total missing: $missing"
```

For every missing file: create it correctly. Do not proceed past Phase 1 until `missing=0`.

Also verify `.env` contains a real (non-placeholder) `GEMINI_API_KEY`:
```bash
grep GEMINI_API_KEY .env
```
If it shows `your_key_here` or is empty, stop and ask the user to provide their Gemini API key before continuing.

---

## Phase 2: Dataset Download

### 2a. Choose and Download

The pipeline targets KITTI. Download the **KITTI Raw Data** sequences that provide all four sensors (LiDAR + stereo camera + IMU/GPS oxts). Use sequences from the `2011_09_26` date which has the most complete sensor coverage.

Download exactly **two sequences**:
- `2011_09_26_drive_0001` — short urban sequence (~2 min, ~1.5 GB)
- `2011_09_26_drive_0005` — longer residential sequence (~5 min, ~4 GB)

```bash
cd /home/devil/Desktop/car/localisation

# Check disk first — need at least 15 GB free
FREE_GB=$(df -BG /home/devil/Desktop/car/ | awk 'NR==2 {print $4}' | tr -d 'G')
echo "Free disk: ${FREE_GB} GB"
if [ "$FREE_GB" -lt 15 ]; then
  echo "ERROR: Insufficient disk space. Need 15 GB, have ${FREE_GB} GB. Stopping."
  exit 1
fi

mkdir -p data/raw/kitti
cd data/raw/kitti

# Download sequences (synced data = LiDAR + camera + GPS/IMU together)
BASE_URL="https://s3.eu-central-1.amazonaws.com/avg-kitti/raw_data"

# Sequence 0001 (synced + tracklets)
wget -c "${BASE_URL}/2011_09_26_drive_0001/2011_09_26_drive_0001_sync.zip"
unzip 2011_09_26_drive_0001_sync.zip

# Sequence 0005
wget -c "${BASE_URL}/2011_09_26_drive_0005/2011_09_26_drive_0005_sync.zip"
unzip 2011_09_26_drive_0005_sync.zip

# Also download calibration (needed for all sequences from this date)
wget -c "${BASE_URL}/2011_09_26_calib.zip"
unzip 2011_09_26_calib.zip
```

After download, verify structure:
```bash
ls 2011_09_26/2011_09_26_drive_0001_sync/
# Must show: image_00/ image_01/ image_02/ image_03/ oxts/ velodyne_points/
```

### 2b. Convert to ROS2 Bags

KITTI raw data is not a ROS bag — it is folders of binary files. Convert using `kitti2rosbag` or the `kitti_to_rosbag` approach with `rosbags`.

Install the conversion tool:
```bash
pip3 install kitti2bag 2>/dev/null || true
# If kitti2bag fails (Python 3 issues are common), use the rosbags-based converter below
```

Primary approach — use the community `kitti_to_rosbag` script that supports ROS2:
```bash
cd /home/devil/Desktop/car/localisation

# Clone kitti2rosbag2 (ROS2-native converter)
git clone https://github.com/tomas789/kitti2bag.git /tmp/kitti2bag || true

# Alternative: use raw2rosbag2 approach via rosbags Python API
# Write a conversion script if no suitable tool found
```

**IMPORTANT:** If no existing converter handles KITTI→ROS2 bag cleanly, write the conversion yourself using the `rosbags` Python library. The converter must produce a ROS2 bag containing:

| Topic | Message Type | Source |
|-------|-------------|--------|
| `/kitti/velo/pointcloud` | `sensor_msgs/msg/PointCloud2` | `velodyne_points/data/*.bin` |
| `/kitti/camera/color/left/image_raw` | `sensor_msgs/msg/Image` | `image_02/data/*.png` |
| `/kitti/camera/color/right/image_raw` | `sensor_msgs/msg/Image` | `image_03/data/*.png` |
| `/kitti/oxts/imu` | `sensor_msgs/msg/Imu` | `oxts/data/*.txt` columns |
| `/kitti/oxts/gps/fix` | `sensor_msgs/msg/NavSatFix` | `oxts/data/*.txt` columns |
| `/tf_static` | `tf2_msgs/msg/TFMessage` | calibration files |

KITTI oxts format reference: each `.txt` file has 30 columns. Columns 0-1 = lat/lon, 2 = alt, 3-5 = roll/pitch/yaw, 6-8 = vn/ve/vf (velocity), 9-11 = vl/vu/ax, 12-17 = ay/az/af/al/au/wx, 18-23 = wy/wz/wf/wl/wu/posacc, 24-25 = velacc/navstat, 26-29 = numsats/posmode/velmode/orimode.

Timestamps come from `oxts/timestamps.txt` (one ISO timestamp per line).

The conversion script goes in `scripts/kitti_to_ros2bag.py`. Run it:
```bash
python3 scripts/kitti_to_ros2bag.py \
  --kitti_root data/raw/kitti/2011_09_26 \
  --sequence 2011_09_26_drive_0001_sync \
  --output data/sequences/urban_01/ \
  --calib data/raw/kitti/2011_09_26

python3 scripts/kitti_to_ros2bag.py \
  --kitti_root data/raw/kitti/2011_09_26 \
  --sequence 2011_09_26_drive_0005_sync \
  --output data/sequences/highway_01/ \
  --calib data/raw/kitti/2011_09_26
```

Verify the bags:
```bash
ros2 bag info data/sequences/urban_01/
# Must show all 5 topics with non-zero message counts
# LiDAR: expect ~200 messages for drive_0001
# Camera: expect ~200 messages  
# IMU: expect ~2000+ messages
# GPS: expect ~200 messages

ros2 bag play data/sequences/urban_01/ --topics /kitti/velo/pointcloud &
sleep 5
ros2 topic echo /kitti/velo/pointcloud --once --field header
# Must show a real timestamp and frame_id
kill %1
```

Save calibration files to `config/calibration/kitti/`:
```bash
mkdir -p config/calibration/kitti
cp data/raw/kitti/2011_09_26/calib_cam_to_cam.txt config/calibration/kitti/
cp data/raw/kitti/2011_09_26/calib_imu_to_velo.txt config/calibration/kitti/
cp data/raw/kitti/2011_09_26/calib_velo_to_cam.txt config/calibration/kitti/
```

---

## Phase 3: Build Base Docker Image

Build the base image first. Everything else depends on it.

```bash
cd /home/devil/Desktop/car/localisation
docker build -t localization_eval/base:latest docker/base/ 2>&1 | tee /tmp/build_base.log
echo "Exit code: $?"
```

The base Dockerfile must install:
- `ros-humble-desktop` (or `ros-humble-ros-base` minimum)
- `ros-humble-pcl-ros ros-humble-cv-bridge ros-humble-tf2-ros`
- `python3-pip python3-colcon-common-extensions`
- `libpcl-dev libeigen3-dev libopencv-dev`
- `cuda-toolkit-12-x` (or the CUDA base from `nvidia/cuda:12.x-devel-ubuntu22.04`)

**If the base build fails:** Read the full log, fix the Dockerfile line by line. Common issues:
- CUDA apt key expired → update to current CUDA keyring
- ROS2 apt key issue → use `sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg`
- Package name changed → search `apt-cache search ros-humble` for correct names

Do not proceed until `docker build` exits 0.

---

## Phase 4: Build Algorithm Containers

Build in this order (simplest → most complex):

### 4a. FAST-LIO2 (LiDAR + IMU only — simplest)

```bash
docker build -t localization_eval/fast_lio2:latest docker/fast_lio2/ 2>&1 | tee /tmp/build_fast_lio2.log
echo "Exit code: $?"
```

The `docker/fast_lio2/Dockerfile` must:
```dockerfile
FROM localization_eval/base:latest

# Pin to a specific commit for reproducibility
RUN mkdir -p /ros2_ws/src && cd /ros2_ws/src && \
    git clone https://github.com/hku-mars/FAST_LIO.git && \
    cd FAST_LIO && git checkout <latest stable commit hash>

# Install dependencies
RUN cd /ros2_ws && \
    rosdep init || true && \
    rosdep update && \
    rosdep install --from-paths src --ignore-src -r -y

# Build
RUN cd /ros2_ws && \
    . /opt/ros/humble/setup.sh && \
    colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release \
    2>&1 | tail -20

# Verify build
RUN ls /ros2_ws/install/fast_lio/

# Launch wrapper
COPY launch/fast_lio2.launch.py /ros2_ws/src/fast_lio2_launch/
COPY config/fast_lio2_kitti.yaml /ros2_ws/src/fast_lio2_launch/config/

CMD ["/bin/bash", "-c", "source /ros2_ws/install/setup.bash && ros2 launch fast_lio2_launch fast_lio2.launch.py"]
```

The launch file must:
- Load `config/fast_lio2_kitti.yaml` with KITTI VLP-16 parameters
- Subscribe to `/kitti/velo/pointcloud` → remapped to FAST-LIO2's expected topic
- Subscribe to `/kitti/oxts/imu` → remapped
- Publish to `/localization/odometry`

After build, do a smoke test:
```bash
# Start the container, replay 10 seconds of bag, check topic publishes
docker run --rm --network host \
  -v $(pwd)/data:/data:ro \
  localization_eval/fast_lio2:latest &
ALGO_PID=$!

sleep 5
ros2 bag play data/sequences/urban_01/ --duration 10 &

sleep 12
ros2 topic echo /localization/odometry --once
# Must print a nav_msgs/Odometry message with real numbers

kill $ALGO_PID
wait $ALGO_PID 2>/dev/null
```

If no message appears: check topic names, check TF frames, check IMU rate (FAST-LIO2 needs ≥100 Hz).

### 4b. LIO-SAM

```bash
docker build -t localization_eval/lio_sam:latest docker/lio_sam/ 2>&1 | tee /tmp/build_lio_sam.log
```

LIO-SAM Dockerfile must clone the `ros2` branch:
```bash
git clone https://github.com/TixiaoShan/LIO-SAM.git && \
cd LIO-SAM && git checkout ros2
```

LIO-SAM requires a **9-axis IMU** (with magnetometer / orientation estimate). KITTI oxts provides full orientation. Ensure the IMU message populates `orientation` field from the oxts yaw/pitch/roll columns. If not, set `imuType: 0` in LIO-SAM config (6-axis mode, which uses GPS heading initialisation instead).

Also add GPS factor support: LIO-SAM subscribes to `sensor_msgs/NavSatFix`. Map `/kitti/oxts/gps/fix` → LIO-SAM's GPS topic in the launch file.

### 4c. FAST-LIVO2

```bash
docker build -t localization_eval/fast_livo2:latest docker/fast_livo2/ 2>&1 | tee /tmp/build_fast_livo2.log
```

FAST-LIVO2 Dockerfile uses the ROS2 port:
```bash
git clone https://github.com/VIS4ROB-lab/FAST-LIVO2-ROS2.git
```

Dependencies beyond base:
- `libsophus-dev` or build Sophus from source
- `vikit_common` (from the rpg_vikit package — build from source)

These are the most likely build failures. If `Sophus` is missing:
```bash
git clone https://github.com/strasdat/Sophus.git -b 1.22.10 /tmp/Sophus && \
  cd /tmp/Sophus && mkdir build && cd build && cmake .. && make -j4 && make install
```

### 4d. ORB-SLAM3

```bash
docker build -t localization_eval/orb_slam3:latest docker/orb_slam3/ 2>&1 | tee /tmp/build_orb_slam3.log
```

ORB-SLAM3 is the most complex build. Use this repo for the ROS2 wrapper:
```bash
git clone https://github.com/zang09/ORB-SLAM3-ROS2-wrapper.git
```

ORB-SLAM3 requires vocabulary files:
```bash
# Inside the container or Dockerfile
wget https://github.com/UZ-SLAMLab/ORB_SLAM3/raw/master/Vocabulary/ORBvoc.txt.tar.gz
tar -xf ORBvoc.txt.tar.gz
```

ORB-SLAM3 needs a KITTI camera calibration YAML. Generate `config/calibration/kitti/orb_slam3_kitti_stereo.yaml` from the KITTI calib files:
```yaml
Camera.type: KannalaBrandt8   # or PinHole for KITTI
Camera.fx: <from calib_cam_to_cam.txt P_rect_02 col 0>
Camera.fy: <from P_rect_02 col 5>
Camera.cx: <from P_rect_02 col 2>
Camera.cy: <from P_rect_02 col 6>
Camera.k1: 0.0
Camera.k2: 0.0
Camera.p1: 0.0
Camera.p2: 0.0
Camera.width: 1242
Camera.height: 375
Camera.fps: 10.0
Camera.RGB: 1
ORBextractor.nFeatures: 1200
ORBextractor.scaleFactor: 1.2
ORBextractor.nLevels: 8
ORBextractor.iniThFAST: 20
ORBextractor.minThFAST: 7
```

### 4e. GLIM

GLIM has a pre-built Docker image. Pull and verify:
```bash
docker pull koide3/glim_ros2:latest
# Verify it starts
docker run --rm --network host --runtime nvidia \
  koide3/glim_ros2:latest \
  ros2 pkg list | grep glim
```

If the pre-built image has topic name mismatches, create a wrapper:
```dockerfile
# docker/glim/Dockerfile
FROM koide3/glim_ros2:latest
COPY launch/glim_kitti.launch.py /glim_launch/
CMD ["ros2", "launch", "/glim_launch/glim_kitti.launch.py"]
```

---

## Phase 5: Build Infrastructure Containers

```bash
# Build perturbation injector
docker build -t localization_eval/perturbation_injector:latest \
  docker/perturbation_injector/ 2>&1 | tee /tmp/build_injector.log

# Build evaluator
docker build -t localization_eval/evaluator:latest \
  docker/evaluator/ 2>&1 | tee /tmp/build_evaluator.log

# Build orchestrator
docker build -t localization_eval/orchestrator:latest \
  docker/orchestrator/ 2>&1 | tee /tmp/build_orchestrator.log

echo "All infrastructure builds done"
docker images | grep localization_eval
```

---

## Phase 6: Perturbation Injector Verification

This is the most critical component. Verify each perturbation class actually modifies data.

```bash
# Start injector with rain config, replay bag, check output
docker run --rm --network host \
  -v $(pwd)/config:/config:ro \
  -v $(pwd)/data:/data:ro \
  localization_eval/perturbation_injector:latest \
  ros2 run perturbation_injector sensor_perturbation_node \
    --ros-args \
    -p perturbation_yaml_path:=/config/perturbations/rain.yaml \
    -p bag_path:=/data/sequences/urban_01/ \
    -p playback_rate:=1.0 &

INJECTOR_PID=$!
sleep 5

# Sample original vs perturbed pointcloud
echo "=== Checking LiDAR point count modification ==="
ros2 topic echo /localization/lidar/pointcloud --once | grep -E "width|height"
# Should show reduced point count vs original due to rain dropout

# Sample camera brightness
echo "=== Checking camera perturbation ==="
ros2 topic echo /localization/camera/image_raw --once | grep encoding
# At minimum, topic must be publishing

kill $INJECTOR_PID
wait $INJECTOR_PID 2>/dev/null
```

Write a standalone test script `scripts/test_perturbations.py` that:
1. Loads one pointcloud message from the bag
2. Applies each LiDAR perturbation class with test params
3. Asserts that point count changed (for dropout), that intensity values changed (for scale), etc.
4. Prints PASS/FAIL for each perturbation class

Run it and confirm all pass:
```bash
python3 scripts/test_perturbations.py
# Expected output:
# LidarPointDropout      [PASS] 1000 → 800 points (dropout=0.2)
# LidarGaussianNoise     [PASS] mean position change: 0.021m (std=0.02)
# LidarIntensityScale    [PASS] mean intensity: 100.0 → 80.1 (scale=0.8)
# ...etc
```

---

## Phase 7: Evaluator Verification

The evaluator must compare two real trajectories and produce real error numbers. Test it with a known case:

```bash
# Create two test TUM trajectories where the answer is known
python3 - <<'EOF'
import numpy as np

# Golden: straight line along X, 1 m/s
# Test: same but with 0.5m constant lateral offset
timestamps = np.linspace(0, 10, 100)
with open('/tmp/golden.tum', 'w') as f:
    for t in timestamps:
        # timestamp tx ty tz qx qy qz qw
        f.write(f"{t:.6f} {t:.4f} 0.0000 0.0000 0 0 0 1\n")

with open('/tmp/test_offset.tum', 'w') as f:
    for t in timestamps:
        f.write(f"{t:.6f} {t:.4f} 0.5000 0.0000 0 0 0 1\n")

print("Test TUM files written")
EOF

# Run evaluator on them — lateral error should be exactly 0.5m
docker run --rm \
  -v /tmp:/tmp \
  -v $(pwd)/results:/results \
  localization_eval/evaluator:latest \
  python3 /app/evaluate_trajectory.py \
    --golden /tmp/golden.tum \
    --test   /tmp/test_offset.tum \
    --output /tmp/eval_test/ \
    --scenario test_known_offset

cat /tmp/eval_test/metrics.json | python3 -m json.tool
# MUST show lateral RMSE ≈ 0.500 m (within 0.001 m tolerance)
# If it shows 0.0 or any other value, the evaluator has a bug — fix it.
```

---

## Phase 8: End-to-End Pipeline Run — FAST-LIO2 Only

Now run the complete pipeline for one algorithm to confirm every stage connects.

### Step 8a: Golden run (baseline, no perturbations)

```bash
cd /home/devil/Desktop/car/localisation

# Start the full compose stack
docker compose up -d perturbation_injector evaluator

# Run FAST-LIO2 with baseline scenario
./scripts/run_pipeline.sh \
  --algo fast_lio2 \
  --scenario baseline \
  --sequence urban_01 \
  2>&1 | tee /tmp/run_baseline.log
```

After completion, verify:
```bash
# 1. TUM trajectory file must exist and have real coordinates
echo "=== Trajectory file ==="
wc -l results/golden/fast_lio2/urban_01/trajectory.tum
head -5 results/golden/fast_lio2/urban_01/trajectory.tum
# Must show: timestamp tx ty tz qx qy qz qw with non-zero tx/ty values
# If all positions are 0.0 0.0 0.0 → the algorithm isn't publishing, fix topic remapping

# 2. Metrics file
echo "=== Metrics ==="
cat results/golden/fast_lio2/urban_01/baseline/metrics.json | python3 -m json.tool
# Must show: status: "SUCCESS", num_poses > 100, rmse values are small (< 0.5 m for baseline)

# 3. Plots exist and are non-empty
echo "=== Plots ==="
ls -lh results/golden/fast_lio2/urban_01/baseline/plots/
file results/golden/fast_lio2/urban_01/baseline/plots/trajectory_comparison.png
# Must say: PNG image data, <size> x <size>

# 4. Deviation report
echo "=== Deviation report ==="
cat results/golden/fast_lio2/urban_01/baseline/deviation_report.txt
# Must show real metric numbers, not "None" or "N/A"
```

**If trajectory is all zeros:** The algorithm node is running but not receiving sensor data. Debug:
```bash
# While the algorithm container is running, check what it sees
docker exec -it <fast_lio2_container> bash -c \
  "source /ros2_ws/install/setup.bash && ros2 topic list"

# If /localization/lidar/pointcloud is absent → topic bridge isn't running
# If topic exists but no messages → perturbation injector isn't publishing
# Check injector:
docker logs perturbation_injector --tail=50
```

**If algorithm crashes:** Check logs:
```bash
docker logs fast_lio2 --tail=100
# Common: "IMU frequency too low" → check IMU topic rate with: ros2 topic hz /localization/imu/data
# Common: "Calibration file not found" → mount config/calibration/kitti/ into container
```

### Step 8b: Rain scenario run

```bash
./scripts/run_pipeline.sh \
  --algo fast_lio2 \
  --scenario rain \
  --sequence urban_01 \
  2>&1 | tee /tmp/run_rain.log
```

Verify degradation is real:
```bash
python3 - <<'EOF'
import json

with open('results/golden/fast_lio2/urban_01/baseline/metrics.json') as f:
    baseline = json.load(f)
with open('results/scenarios/fast_lio2/urban_01/rain/metrics.json') as f:
    rain = json.load(f)

b_rmse = baseline['rmse']['position_3d_m']
r_rmse = rain['rmse']['position_3d_m']
factor = r_rmse / b_rmse

print(f"Baseline RMSE: {b_rmse:.4f} m")
print(f"Rain RMSE:     {r_rmse:.4f} m")
print(f"Degradation:   {factor:.2f}x")

# Rain should degrade localization — expect factor > 1.2
if factor < 1.0:
    print("FAIL: Rain scenario shows BETTER accuracy than baseline — perturbation not working")
elif 1.0 <= factor < 1.2:
    print("WARN: Rain shows only marginal degradation — perturbation effect may be too subtle")
else:
    print(f"PASS: Rain degrades localization by {factor:.2f}x as expected")
EOF
```

If degradation factor < 1.2, the perturbation is not reaching the algorithm. Debug the injector to confirm it's actually publishing modified point clouds (check point count before and after dropout).

---

## Phase 9: Gemini API Verification

```bash
# Confirm API key is set
source .env
echo "Key starts with: ${GEMINI_API_KEY:0:6}..."

# Test Gemini connectivity
python3 - <<'EOF'
import os, google.generativeai as genai
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# List available models and find the best free Flash model
for m in genai.list_models():
    if "flash" in m.name.lower() and "generateContent" in m.supported_generation_methods:
        print(f"Available: {m.name}")

# Quick test call
model_name = "models/gemini-2.0-flash-exp"  # update to whatever list shows
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say 'Gemini API OK' and nothing else.")
    print(f"API test: {response.text.strip()}")
except Exception as e:
    print(f"FAIL: {e}")
EOF
```

If API fails: check key, check quota, try `gemini-1.5-flash` as fallback model. Update `config/pipeline.yaml` `gemini.model` with the working model name.

Run the report generator on the real metrics from Phase 8:
```bash
python3 scripts/generate_report.py \
  --mode scenario \
  --metrics results/scenarios/fast_lio2/urban_01/rain/metrics.json \
  --baseline results/golden/fast_lio2/urban_01/baseline/metrics.json \
  --output results/scenarios/fast_lio2/urban_01/rain/gemini_summary.txt

cat results/scenarios/fast_lio2/urban_01/rain/gemini_summary.txt
# Must contain: 3+ paragraphs, mention specific numbers from metrics.json,
# mention "FAST-LIO2" or "fast_lio2", mention "rain" or the scenario name.
# Must NOT be: empty, "None", an error message, or generic boilerplate.
```

---

## Phase 10: Full Pipeline — All Algorithms, All Scenarios

Once Phase 8 and 9 are confirmed working for FAST-LIO2, run the complete pipeline:

```bash
cd /home/devil/Desktop/car/localisation

# Start infrastructure services
docker compose up -d perturbation_injector evaluator

# Run orchestrator (this drives everything)
docker compose up orchestrator 2>&1 | tee /tmp/full_pipeline.log
```

The orchestrator must iterate:
- 5 algorithms × 2 sequences × 12 scenarios = **120 runs total**
- Each run: golden already done for FAST-LIO2; repeat for remaining 4 algorithms
- Print live progress

Monitor:
```bash
# In another terminal, watch results accumulate
watch -n 10 'find results/ -name "metrics.json" | wc -l'
# Should increment from 0 toward 120 (5 algos × 2 seqs × 12 scenarios)

# Watch for errors
grep -i "error\|failed\|exception" /tmp/full_pipeline.log | tail -20
```

**If an algorithm consistently fails** (e.g. ORB-SLAM3 can't initialise in short sequences):
- Check if the sequence is long enough for ORB-SLAM3 to initialise (needs textured features)
- If genuinely unsupported: write `metrics.json` with `"status": "FAILED_TO_INIT"` and continue
- Do NOT remove the algorithm from the pipeline — document the failure in `docs/fixes_log.md`

---

## Phase 11: Final Report Generation

```bash
python3 scripts/generate_report.py \
  --mode final \
  --results_dir results/ \
  --output results/final_report/

# Verify all final outputs
ls -lh results/final_report/
# Must contain:
# - final_gemini_report.md (non-empty, structured markdown)
# - cross_algo_comparison.png (bar chart, all 5 algos shown)
# - scenario_sensitivity_matrix.png (5x12 heatmap grid)

# Verify the heatmap
python3 - <<'EOF'
from PIL import Image
import numpy as np

img = Image.open("results/final_report/scenario_sensitivity_matrix.png")
arr = np.array(img)
print(f"Image size: {img.size}")
print(f"Non-uniform (not a blank image): {arr.std() > 10}")
# std > 10 means it has actual colour variation = real data plotted
EOF

# Verify the report has content
wc -l results/final_report/final_gemini_report.md
# Should be > 50 lines

grep -c "##" results/final_report/final_gemini_report.md
# Should be >= 5 (has multiple sections)
```

---

## Phase 12: Portability Verification

Confirm the pipeline respects `config/pipeline.yaml` hardware settings:

```bash
# Change cpu_threads to 4 (simulating a weaker machine) and verify pipeline reads it
sed -i 's/cpu_threads: 6/cpu_threads: 4/' config/pipeline.yaml

# Run a quick single scenario and confirm it uses 4 threads
docker compose run --rm orchestrator python3 -c \
  "import yaml; c=yaml.safe_load(open('/config/pipeline.yaml')); print('Threads:', c['hardware']['cpu_threads'])"
# Must print: Threads: 4

# Restore
sed -i 's/cpu_threads: 4/cpu_threads: 6/' config/pipeline.yaml
```

---

## Success Checklist

Do not mark the task complete until every item below can be confirmed with actual command output or file contents, pasted into your response:

**Environment:**
- [ ] `nvidia-smi` shows the RTX 4060
- [ ] `docker info` shows `nvidia` as a runtime
- [ ] All Python dependencies installed

**Dataset:**
- [ ] `ros2 bag info data/sequences/urban_01/` shows 5 topics with real message counts
- [ ] `ros2 bag info data/sequences/highway_01/` shows 5 topics with real message counts
- [ ] `head -3 data/sequences/urban_01/*.db3` is not needed — just `ros2 bag info` output

**Docker Builds:**
- [ ] `docker images | grep localization_eval` shows all 8 images built
- [ ] GLIM image pulled: `docker images | grep glim`

**Perturbation Injector:**
- [ ] `python3 scripts/test_perturbations.py` shows PASS for all perturbation classes

**Evaluator:**
- [ ] Known-offset test from Phase 7 shows lateral RMSE = 0.500 ± 0.001 m

**FAST-LIO2 Baseline:**
- [ ] `results/golden/fast_lio2/urban_01/trajectory.tum` has > 100 lines with non-zero XYZ
- [ ] `metrics.json` shows `status: SUCCESS`, `num_poses > 100`, `position_3d_m < 0.5`
- [ ] All 4 plots exist as valid PNG files > 10 KB each

**FAST-LIO2 Rain:**
- [ ] Rain degradation factor > 1.2× vs baseline
- [ ] `gemini_summary.txt` has ≥ 3 paragraphs citing real metric numbers

**Full Pipeline:**
- [ ] `find results/ -name "metrics.json" | wc -l` shows 120 (or N where N = completed runs)
- [ ] `results/final_report/scenario_sensitivity_matrix.png` is a valid non-blank PNG
- [ ] `results/final_report/final_gemini_report.md` has ≥ 5 markdown sections

**Portability:**
- [ ] Changing `cpu_threads` in `pipeline.yaml` is reflected in orchestrator output

---

## What to Do When Stuck

In order:

1. **Read the full error**, not just the last line. Run with verbose flags.
2. **Isolate the component**. Test the failing piece standalone (e.g. run the algorithm container alone with `docker run --rm -it` and replay a bag manually).
3. **Check ROS2 topic graph.** `ros2 topic list`, `ros2 topic hz <topic>`, `ros2 topic echo <topic> --once`. Topic mismatches are the #1 cause of silent failures.
4. **Check TF frames.** SLAM algorithms are extremely sensitive to TF frame IDs. Run `ros2 run tf2_tools view_frames` and verify the frame tree is consistent.
5. **Check timestamp alignment.** If IMU timestamps don't align with LiDAR timestamps (within 50 ms), algorithms may not initialise. Check with `ros2 topic echo /localization/imu/data --field header.stamp`.
6. **Search GitHub issues** for the specific algorithm + error message before attempting a workaround.
7. **Document and move on** only if an algorithm is genuinely incompatible with this hardware setup — write the reason in `docs/fixes_log.md` and ensure the pipeline handles the failure gracefully.

---

*End of agent task. Do not stop until the Success Checklist is fully confirmed with real evidence.*
