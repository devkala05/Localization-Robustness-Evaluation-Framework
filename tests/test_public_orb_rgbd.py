from pathlib import Path
import re

import numpy as np
import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_sensor_config(name):
    path = ROOT / "wrappers" / "localization_benchmark" / "config" / name
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def transform(values):
    matrix = np.asarray(values, dtype=float).reshape(4, 4)
    assert np.all(np.isfinite(matrix))
    assert np.allclose(matrix[3], [0.0, 0.0, 0.0, 1.0])
    assert np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=2e-6)
    assert np.isclose(np.linalg.det(matrix[:3, :3]), 1.0, atol=2e-6)
    return matrix


def static_transform(config, child):
    entry = next(item for item in config["static_transforms"] if item["child"] == child)
    matrix = np.eye(4)
    matrix[:3, :3] = np.asarray(entry["rotation"]).reshape(3, 3)
    matrix[:3, 3] = entry["translation"]
    return matrix


def test_public_orb_uses_metric_rgbd_without_reference_input():
    for name in (
        "boreas_2024_12_04_14_44.yaml",
        "urbanloco_ca_20190828184706.yaml",
    ):
        config = load_sensor_config(name)
        adapter = config["adapter"]
        rgbd = adapter["orb_rgbd"]
        assert adapter["orb_mode"] == "rgbd"
        assert rgbd["project_lidar_depth"] is True
        assert not adapter["topics"]["depth"]
        assert "ground_truth" not in str(rgbd).lower()


def test_lidar_depth_projection_matches_published_static_calibration():
    cases = (
        ("boreas_2024_12_04_14_44.yaml", "lidar", "camera"),
        ("urbanloco_ca_20190828184706.yaml", "rslidar", "camera0"),
    )
    for name, lidar_frame, camera_frame in cases:
        config = load_sensor_config(name)
        configured = transform(config["adapter"]["orb_rgbd"]["lidar_to_camera"])
        base_lidar = static_transform(config, lidar_frame)
        base_camera = static_transform(config, camera_frame)
        expected = np.linalg.inv(base_camera) @ base_lidar
        assert np.allclose(configured, expected, atol=2e-6)


def test_boreas_orb_intrinsics_match_isolated_resized_feed():
    sensor = load_sensor_config("boreas_2024_12_04_14_44.yaml")["adapter"]
    orb = sensor["orb_rgbd"]
    camera = sensor["camera"]
    settings_path = (
        ROOT / "wrappers" / "orbslam3_e2o" / "config"
        / "boreas_2024_12_04_14_44.yaml"
    )
    settings_text = settings_path.read_text(encoding="utf-8")

    def setting(name):
        match = re.search(rf"^{re.escape(name)}:\s*([-+0-9.eE]+)\s*$",
                          settings_text, re.MULTILINE)
        assert match, name
        return float(match.group(1))

    scale_x = orb["width"] / camera["width"]
    scale_y = orb["height"] / camera["height"]
    assert setting("Camera.width") == orb["width"]
    assert setting("Camera.height") == orb["height"]
    assert np.isclose(setting("Camera.fx"), camera["K"][0] * scale_x)
    assert np.isclose(setting("Camera.fy"), camera["K"][4] * scale_y)
    assert np.isclose(setting("Camera.cx"), camera["K"][2] * scale_x)
    assert np.isclose(setting("Camera.cy"), camera["K"][5] * scale_y)


def test_boreas_orb_preserves_native_rectified_camera_intensity():
    rgbd = load_sensor_config(
        "boreas_2024_12_04_14_44.yaml"
    )["adapter"]["orb_rgbd"]
    assert rgbd["max_rate_hz"] == 10.5
    assert "intensity_target_mean" not in rgbd
    assert "intensity_target_std" not in rgbd
    assert "clahe_clip_limit" not in rgbd


def test_boreas_depth_merges_complete_camera_visible_lidar_sweep():
    rgbd = load_sensor_config(
        "boreas_2024_12_04_14_44.yaml"
    )["adapter"]["orb_rgbd"]
    assert rgbd["depth_time_slice_sec"] == 0.0
    assert rgbd["depth_merge_window_sec"] == 0.0
    assert rgbd["depth_pairing_wait_sec"] == 0.06
    assert rgbd["depth_deskew_pose_topic"] == "/orb_slam3/camera_pose"
    assert rgbd["depth_deskew_bin_sec"] == 0.005
    assert rgbd["depth_deskew_max_pose_age_sec"] == 0.3
    assert rgbd["depth_sweep_count"] == 1
    assert rgbd["depth_splat_px"] == 8
    adapter = (
        ROOT / "wrappers" / "localization_benchmark" / "scripts"
        / "e2o_sensor_adapter.py"
    ).read_text(encoding="utf-8")
    assert "np.median(point_offsets[selected])" in adapter
    assert "camera_stamp + self.orb_depth_pairing_wait_sec" in adapter
    assert "abs(item_stamp - camera_stamp)" in adapter
    assert "depth = np.minimum.reduce(contributors)" in adapter
    assert "camera_stamp - acquisition_stamps" in adapter
    assert "self.orb_latest_motion" in adapter
    assert "nearest_items" in adapter
    assert "self.orb_depth_sweep_count" in adapter
    assert "ground_truth" not in adapter


def test_benchmark_uses_native_boreas_camera_imu_modality():
    script = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    assert "ORB_MODE=rgbd" in script
    assert "ORB_EXECUTABLE=RGBD_Inertial" in script
    assert "ORB_EXECUTABLE=RGBD" in script
    assert 'ALIGNMENT=sim3' in script  # retained only for explicit mono ablations


def test_rgbd_inertial_frontend_does_not_drop_synchronized_frames():
    for name in ("add_rgbd_inertial.py", "add_orbslam3_pose_publishers.py"):
        patch = (
            ROOT / "docker" / "orbslam3" / "patches" / name
        ).read_text(encoding="utf-8")
        assert "mFrameBuf.push({msgRGB, msgD});" in patch
        assert "while (!mFrameBuf.empty()) mFrameBuf.pop()" not in patch


def test_plain_rgbd_transport_queues_do_not_drop_frames_before_sync():
    patch = (
        ROOT / "docker" / "orbslam3" / "patches"
        / "add_orbslam3_pose_publishers.py"
    ).read_text(encoding="utf-8")
    assert 'rgb_sub(nh, "/camera/rgb/image_raw", 100)' in patch
    assert (
        'depth_sub(nh, "camera/depth_registered/image_raw", 100)' in patch
    )
    assert "sync(sync_pol(100), rgb_sub,depth_sub)" in patch


def test_sparse_plain_rgbd_uses_validated_local_map_gate():
    patch = (
        ROOT / "docker" / "orbslam3" / "patches"
        / "add_orbslam3_pose_publishers.py"
    ).read_text(encoding="utf-8")
    assert "(mSensor == System::RGBD) ? 15 : 30" in patch
    assert "mnMatchesInliers<minInliers" in patch
    assert "bNeedToInsertClose = (mSensor != System::RGBD)" in patch
    assert "sparseRGBDPeriodic" in patch
    assert "(mSensor == System::RGBD) && c1a && bLocalMappingIdle" in patch
    assert "mlFrameTimes.push_back(mCurrentFrame.mTimeStamp)" in patch
    assert "mlbLost.push_back(true)" in patch
    assert "ORB RGB-D frame %.6f not published" in patch
    assert 'nh.param<double>("mask_top_fraction"' in patch
    assert 'nh.param<double>("mask_bottom_fraction"' in patch
    assert "rgb.rowRange(0, top).setTo" in patch
    assert "depth.rowRange(depth.rows - bottom, depth.rows).setTo" in patch
    assert '<< mnMatchesInliers << " state=" << mState' in patch


def test_native_tracking_patch_is_applied_before_core_build():
    dockerfile = (ROOT / "docker" / "orbslam3" / "Dockerfile").read_text(
        encoding="utf-8"
    )
    patch_at = dockerfile.index("RUN python3 /tmp/add_pose_publishers.py")
    core_build_at = dockerfile.index(
        "cd ${ORB_SLAM3_ROOT} && tar -xf Vocabulary/ORBvoc.txt.tar.gz"
    )
    assert patch_at < core_build_at


def test_rgbd_inertial_waits_for_imu_to_reach_each_image():
    patch = (
        ROOT / "docker" / "orbslam3" / "patches" / "add_rgbd_inertial.py"
    ).read_text(encoding="utf-8")
    assert "WaitAndDrainUpTo" in patch
    assert "imuBuf.back()->header.stamp.toSec() >= tImg" in patch
    assert "if (!mpImuGb->WaitAndDrainUpTo(tImg, vImuMeas))" in patch
    assert "imugb.Stop();" in patch


def test_sparse_imu_rgbd_retains_native_local_map_criterion():
    patch = (
        ROOT / "docker" / "orbslam3" / "patches" / "add_rgbd_inertial.py"
    ).read_text(encoding="utf-8")
    assert "minInliers" not in patch
    assert "Tracking.cc" not in patch


def test_boreas_orb_uses_sensor_measured_imu_noise():
    config = (
        ROOT / "wrappers" / "orbslam3_e2o" / "config"
        / "boreas_2024_12_04_14_44.yaml"
    ).read_text(encoding="utf-8")
    assert "ORBextractor.nFeatures: 15000" in config
    assert "IMU.NoiseGyro: 0.0002" in config
    assert "IMU.NoiseAcc: 0.02" in config
    assert "IMU.GyroWalk: 0.00001" in config
    assert "IMU.AccWalk: 0.001" in config


def test_orb_default_playback_keeps_lossless_frontend_bounded():
    script = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    assert 'orbslam3) RATE="0.07"' in script


def test_boreas_routes_declare_continuous_orb_initialization_preroll():
    expected = {
        "boreas_2025_07_18_15_30_farm": (1752867150.0, 40.0),
        "boreas_2025_07_18_11_53_forest": (1752854430.0, 40.0),
        "boreas_2025_08_06_06_33_urban": (1754476978.0, 40.0),
    }
    for sequence, values in expected.items():
        manifest = yaml.safe_load(
            (
                ROOT / "configs" / "datasets" / "boreas_rt" / sequence
                / "sequence.yaml"
            ).read_text(encoding="utf-8")
        )
        source = manifest["source"]
        assert source["orb_pre_roll_start_timestamp_s"] == values[0]
        assert source["orb_pre_roll_seconds"] == values[1]
        evaluation_time = (
            source["window_start_timestamp_s"]
            + source["evaluation_start_offset_s"]
        )
        assert evaluation_time - values[0] == values[1]


def test_farm_fastlivo_declares_low_speed_native_initialization():
    manifest = yaml.safe_load(
        (
            ROOT / "configs" / "datasets" / "boreas_rt"
            / "boreas_2025_07_18_15_30_farm" / "sequence.yaml"
        ).read_text(encoding="utf-8")
    )
    source = manifest["source"]
    assert source["fastlivo_pre_roll_start_timestamp_s"] == 1752867070.0
    assert source["fastlivo_pre_roll_seconds"] == 120.0
    assert (
        source["window_start_timestamp_s"]
        + source["evaluation_start_offset_s"]
        - source["fastlivo_pre_roll_start_timestamp_s"]
        == source["fastlivo_pre_roll_seconds"]
    )
    benchmark = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    matrix = (ROOT / "scripts/run_boreas_route_matrix.sh").read_text(
        encoding="utf-8"
    )
    assert "FASTLIVO_IMG_EN=0" in benchmark
    assert 'img_en:="$FASTLIVO_IMG_EN"' in benchmark
    assert 'fastlivo_img_en=%s' in benchmark
    assert 'source["fastlivo_pre_roll_seconds"]' in matrix


def test_benchmark_preroll_does_not_move_evaluation_origin():
    script = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    assert '--pre-roll' in script
    assert '"$START_OFFSET" "$PRE_ROLL"' in script
    assert '"$PRE_ROLL" "$DURATION"' in script
    assert 'evaluation_start_offset=%s' in script


def test_boreas_final_outputs_bypass_unverified_rtab_graph():
    script = (ROOT / "run_benchmark.sh").read_text(encoding="utf-8")
    launch = (
        ROOT / "wrappers" / "rtabmap_benchmark" / "launch" / "algorithm.launch"
    ).read_text(encoding="utf-8")
    assert 'RTAB_ODOM_MODE=icp' in script
    assert 'USE_RTAB_GRAPH=false' in script
    assert 'use_graph:="$USE_RTAB_GRAPH"' in script
    assert 'if="$(arg use_graph)" pkg="rtabmap_slam"' in launch


def test_recorder_rejects_invalid_native_pose_sentinels():
    recorder = (
        ROOT / "wrappers" / "e2o_localization_fusion" / "scripts"
        / "multi_trajectory_recorder.py"
    ).read_text(encoding="utf-8")
    assert "0.9 <= norm <= 1.1" in recorder
    assert "stamp <= self.last_stamps.get" in recorder
