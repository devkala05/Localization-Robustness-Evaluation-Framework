#!/usr/bin/env python3
"""Static cross-checks for E2O calibration duplicated by native config formats."""
from pathlib import Path
import math
import re
import sys
import yaml
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
central = yaml.safe_load((ROOT / "wrappers/localization_benchmark/config/e2o.yaml").read_text())
fast = yaml.safe_load((ROOT / "wrappers/fast_livo2_e2o/config/fast_livo2_e2o.yaml").read_text())
orb_text = (ROOT / "wrappers/orbslam3_e2o/config/e2o_front_mono_orbslam3.yaml").read_text()
fusion = yaml.safe_load((ROOT / "wrappers/e2o_localization_fusion/config/fusion.yaml").read_text())
fusion_2 = yaml.safe_load((ROOT / "wrappers/e2o_localization_fusion/config/fusion_2.yaml").read_text())
lvisam_lidar = yaml.safe_load((ROOT / "wrappers/lvisam_e2o/config/params_lidar_e2o.yaml").read_text())
lvisam_camera_text = (ROOT / "wrappers/lvisam_e2o/config/params_camera_e2o.yaml").read_text()

def orb_value(key):
    match = re.search(rf"^{re.escape(key)}:\s*([^#\n]+)", orb_text, flags=re.MULTILINE)
    if not match:
        raise AssertionError(f"missing ORB key {key}")
    return float(match.group(1).strip().strip('"'))

def opencv_value(text, key):
    match = re.search(rf"^\s*{re.escape(key)}:\s*([^#\n]+)", text, flags=re.MULTILINE)
    if not match:
        raise AssertionError(f"missing OpenCV YAML key {key}")
    return float(match.group(1).strip().strip('"'))

def opencv_matrix(text, key):
    match = re.search(
        rf"^\s*{re.escape(key)}:\s*!!opencv-matrix\s*"
        r"rows:\s*(\d+)\s*cols:\s*(\d+)\s*dt:\s*\w+\s*data:\s*\[([^\]]+)\]",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        raise AssertionError(f"missing OpenCV matrix {key}")
    rows, cols = int(match.group(1)), int(match.group(2))
    data = [float(value) for value in re.split(r"[\s,]+", match.group(3).strip()) if value]
    return np.asarray(data, dtype=float).reshape(rows, cols)

def qmat(q):
    x,y,z,w=np.asarray(q,dtype=float)/np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                     [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                     [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def transform(item):
    T=np.eye(4); T[:3,3]=np.asarray(item.get('translation',[0,0,0]),float)
    T[:3,:3]=(np.asarray(item['rotation'],float).reshape(3,3)
              if 'rotation' in item else qmat(item['quaternion']))
    return T

camera = central["adapter"]["camera"]
if camera.get("timestamp_mode") != "rebase" or "restamp" in camera:
    raise AssertionError("camera timestamps must be epoch-rebased, not callback-restamped")
checks = {
    "fx": (camera["K"][0], fast["camera"]["fx"], orb_value("Camera.fx")),
    "fy": (camera["K"][4], fast["camera"]["fy"], orb_value("Camera.fy")),
    "cx": (camera["K"][2], fast["camera"]["cx"], orb_value("Camera.cx")),
    "cy": (camera["K"][5], fast["camera"]["cy"], orb_value("Camera.cy")),
    "width": (camera["width"], fast["camera"]["image_width"], orb_value("Camera.width")),
    "height": (camera["height"], fast["camera"]["image_height"], orb_value("Camera.height")),
}
for name, values in checks.items():
    if max(values) - min(values) > 1.0e-8:
        raise AssertionError(f"camera {name} mismatch: {values}")
for index,key in enumerate(("Camera.k1","Camera.k2","Camera.p1","Camera.p2")):
    values=(camera['D'][index], fast['camera']['distortion_coeffs'][index], orb_value(key))
    if max(values)-min(values)>1e-8:
        raise AssertionError(f"camera distortion mismatch {key}: {values}")
for name, key in {
    "fx": "fx",
    "fy": "fy",
    "cx": "cx",
    "cy": "cy",
}.items():
    values = (camera["K"][{"fx": 0, "fy": 4, "cx": 2, "cy": 5}[name]],
              opencv_value(lvisam_camera_text, key))
    if max(values)-min(values)>1e-8:
        raise AssertionError(f"LVI-SAM camera {name} mismatch: {values}")
for index,key in enumerate(("k1","k2","p1","p2")):
    values=(camera['D'][index], opencv_value(lvisam_camera_text, key))
    if max(values)-min(values)>1e-8:
        raise AssertionError(f"LVI-SAM camera distortion mismatch {key}: {values}")

items={item['child']:item for item in central['static_transforms']}
T_base_camera=transform(items['camera_right']) @ transform(items['camera_color_optical_frame'])
T_camera_base=np.linalg.inv(T_base_camera)
T_fusion=np.eye(4)
T_fusion[:3,:3]=np.asarray(fusion['fusion']['orb_camera_to_base']['rotation'],float).reshape(3,3)
T_fusion[:3,3]=fusion['fusion']['orb_camera_to_base']['translation']
T_fusion_2=np.eye(4)
T_fusion_2[:3,:3]=np.asarray(fusion_2['fusion']['orb_camera_to_base']['rotation'],float).reshape(3,3)
T_fusion_2[:3,3]=fusion_2['fusion']['orb_camera_to_base']['translation']
T_fast=np.eye(4)
T_fast[:3,:3]=np.asarray(fast['extrin_calib']['Rcl'],float).reshape(3,3)
T_fast[:3,3]=fast['extrin_calib']['Pcl']
if not np.allclose(T_fast,T_camera_base,atol=1e-7):
    raise AssertionError("FAST-LIVO2 camera-to-base calibration disagrees with static TF")
lvi = lvisam_lidar["lvi_sam"]
if lvi["pointCloudTopic"] != "/lvisam/points_raw" or lvi["imuTopic"] != "/lvisam/imu_raw":
    raise AssertionError("LVI-SAM must use dedicated E2O input topics")
if lvi["N_SCAN"] != 16 or lvi["timeField"] != "time":
    raise AssertionError("LVI-SAM must preserve E2O VLP-16 ring/time layout")
if lvi.get("gpsTopic", None) != "":
    raise AssertionError("LVI-SAM GPS subscription must remain disabled for E2O")
if float(lvi.get("z_tollerance", 0.0)) > 20.0:
    raise AssertionError("LVI-SAM z_tollerance is too loose for road-driving E2O runs")
if float(lvi.get("rotation_tollerance", 0.0)) > 2.0:
    raise AssertionError("LVI-SAM rotation_tollerance is too loose for road-driving E2O runs")
if not bool(lvi.get("loopClosureEnableFlag", False)):
    raise AssertionError("LVI-SAM native loop closure must stay enabled for the closed E2O loop")
if float(lvi.get("imuAccNoise", 1.0)) > 0.05 or float(lvi.get("imuGyrNoise", 1.0)) > 0.05:
    raise AssertionError("LVI-SAM IMU noise is too loose; vertical drift will pass too easily")
if not np.allclose(np.asarray(lvi["extrinsicTrans"], float), [0.0, 0.0, 0.0], atol=1e-12):
    raise AssertionError("LVI-SAM IMU/LiDAR assumption unexpectedly changed")
if not np.allclose(np.asarray(lvi["extrinsicRot"], float).reshape(3, 3), np.eye(3), atol=1e-12):
    raise AssertionError("LVI-SAM IMU/LiDAR rotation assumption unexpectedly changed")
if not np.allclose(np.asarray(lvi["extrinsicRPY"], float).reshape(3, 3), np.eye(3), atol=1e-12):
    raise AssertionError("LVI-SAM IMU/LiDAR RPY assumption unexpectedly changed")
for key, expected in {
    "lidar_to_cam_tx": T_camera_base[0, 3],
    "lidar_to_cam_ty": T_camera_base[1, 3],
    "lidar_to_cam_tz": T_camera_base[2, 3],
}.items():
    actual = opencv_value(lvisam_camera_text, key)
    if abs(actual - expected) > 1e-7:
        raise AssertionError(f"LVI-SAM {key} disagrees with static TF: {actual} vs {expected}")
if not np.allclose(opencv_matrix(lvisam_camera_text, "extrinsicRotation"), T_base_camera[:3, :3], atol=1e-7):
    raise AssertionError("LVI-SAM camera-to-body rotation disagrees with static TF")
if not np.allclose(opencv_matrix(lvisam_camera_text, "extrinsicTranslation").reshape(3), T_base_camera[:3, 3], atol=1e-7):
    raise AssertionError("LVI-SAM camera-to-body translation disagrees with static TF")
if int(opencv_value(lvisam_camera_text, "estimate_td")) != 1:
    raise AssertionError("LVI-SAM visual frontend must estimate camera/IMU time offset when enabled")
# The ORB E2O wrapper ports v1's optical-camera/body basis conversion before
# publishing odometry. Fusion must therefore receive an identity transform.
if not np.allclose(T_fusion,np.eye(4),atol=1e-7):
    raise AssertionError("fusion must not apply camera-to-base twice to ORB body poses")
if not np.allclose(T_fusion_2,np.eye(4),atol=1e-7):
    raise AssertionError("fusion_2 must not apply camera-to-base twice to ORB body poses")
if not np.allclose(T_fusion[:3,:3].T@T_fusion[:3,:3],np.eye(3),atol=1e-5) or np.linalg.det(T_fusion[:3,:3])<0.999:
    raise AssertionError("camera-to-base rotation is not proper")
if fusion_2["fusion"].get("primary_source") != "lvisam" or fusion_2["fusion"].get("metric_source") != "lvisam":
    raise AssertionError("fusion_2 must use LVI-SAM as the metric primary source")
if fusion_2["fusion"]["topics"].get("lvisam_odom") != "/lvisam/odometry":
    raise AssertionError("fusion_2 must consume standardized LVI-SAM odometry")
for name, cfg in (("fusion", fusion["fusion"]), ("fusion_2", fusion_2["fusion"])):
    if not bool(cfg.get("require_recovery_consistency", False)):
        raise AssertionError(f"{name} must require recovery consistency")
    if int(cfg.get("min_alignment_pairs", 0)) < 30 or int(cfg.get("alignment_window", 0)) < 100:
        raise AssertionError(f"{name} ORB alignment window is too small for robust monocular scale")
    if float(cfg.get("orb_scale_ratio_min", 0.0)) < 8.0 or float(cfg.get("orb_scale_ratio_max", 99.0)) > 15.0:
        raise AssertionError(f"{name} ORB scale gate is too permissive")
    if float(cfg.get("max_alignment_rmse_m", 99.0)) > 0.5:
        raise AssertionError(f"{name} ORB alignment RMSE gate is too permissive")
    if "metric_odom" not in cfg.get("topics", {}):
        raise AssertionError(f"{name} must publish a metric odometry stream")
if fast["extrin_calib"]["extrinsic_T"] != [0.0, 0.0, 0.0]:
    raise AssertionError("IMU/LiDAR assumption unexpectedly changed")
if "mapping" in fast:
    raise AssertionError("legacy FAST-LIVO2 mapping parameters are ignored upstream")
required_publish = {"dense_map_en", "pub_effect_point_en", "pub_plane_en", "pub_scan_num", "blind_rgb_points"}
if not required_publish.issubset(fast.get("publish", {})):
    raise AssertionError("FAST-LIVO2 publish parameters do not match pinned upstream names")
print("configuration cross-checks passed")
sys.exit(0)
