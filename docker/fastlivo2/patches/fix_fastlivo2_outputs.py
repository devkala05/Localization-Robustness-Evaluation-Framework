#!/usr/bin/env python3
"""Fix measurement timestamps, configurable PCD output, and unbounded sensor
buffering in pinned FAST-LIVO2.

The buffer-bounding change addresses real-time playback (bag rate 1) falling
behind: initializeSubscribersAndPublishers() subscribes with queue_size=200000
and run()'s sync_packages() drains lid_raw_data_buffer/img_buffer/imu_buffer
strictly oldest-first. When stateEstimationAndMapping() cannot keep up with
live sensor input, these deques grow without bound and the pipeline forever
processes older and older backlog instead of catching up — published pose
timestamps fall progressively further behind wall/bag time. The fix bounds
each buffer at the ROS delivery layer, dropping the oldest queued entries
(pop_front) once a cap is exceeded, mirroring the drop-stale-backlog pattern
already used for ORB-SLAM3's frame delivery. Only sensor buffering in the
callbacks is touched; stateEstimationAndMapping/the EKF/mapping/VIO internals
are untouched.
"""
import os
from pathlib import Path


root = Path(os.environ.get("FAST_LIVO2_ROOT", "/root/catkin_ws/src/FAST-LIVO2"))
path = root / "src/LIVMapper.cpp"
text = path.read_text()

old_stamp = "odomAftMapped.header.stamp = ros::Time::now(); //.ros::Time()fromSec(last_timestamp_lidar);"
new_stamp = (
    "odomAftMapped.header.stamp = "
    "ros::Time().fromSec(LidarMeasures.measures.back().lio_time);"
)
if old_stamp in text:
    text = text.replace(old_stamp, new_stamp, 1)
elif new_stamp not in text:
    raise RuntimeError("FAST-LIVO2 odometry timestamp pattern not found")

old_paths = '''    std::string raw_points_dir = std::string(ROOT_DIR) + "Log/pcd/all_raw_points.pcd";
    std::string downsampled_points_dir = std::string(ROOT_DIR) + "Log/pcd/all_downsampled_points.pcd";'''
new_paths = '''    std::string configured_pcd_path;
    ros::param::param<std::string>("pcd_save/pcd_path", configured_pcd_path, "");
    std::string raw_points_dir = configured_pcd_path.empty()
        ? std::string(ROOT_DIR) + "Log/pcd/all_raw_points.pcd"
        : configured_pcd_path + ".raw.pcd";
    std::string downsampled_points_dir = configured_pcd_path.empty()
        ? std::string(ROOT_DIR) + "Log/pcd/all_downsampled_points.pcd"
        : configured_pcd_path;'''
if old_paths in text:
    text = text.replace(old_paths, new_paths, 1)
elif new_paths not in text:
    raise RuntimeError("FAST-LIVO2 PCD output path pattern not found")

# Bound sensor delivery buffers (see module docstring). Insert the trim
# helpers immediately before standard_pcl_cbk and call them at the end of
# each of the four buffer-filling callbacks, dropping oldest entries in
# lockstep across paired buffers once a cap is exceeded.
trim_helpers = '''static const size_t kMaxBufferedLidarScans = 10;
static const size_t kMaxBufferedImageFrames = 16;
static const size_t kMaxBufferedImuMsgs = 300;

template <typename PrimaryBuf, typename SecondaryBuf>
static void trimBufferPairFront(PrimaryBuf &primary, SecondaryBuf &secondary, size_t max_size)
{
  while (primary.size() > max_size)
  {
    primary.pop_front();
    secondary.pop_front();
  }
}

template <typename Buf>
static void trimBufferFront(Buf &buffer, size_t max_size)
{
  while (buffer.size() > max_size) buffer.pop_front();
}

void LIVMapper::standard_pcl_cbk(const sensor_msgs::PointCloud2::ConstPtr &msg)'''
marker_old = "void LIVMapper::standard_pcl_cbk(const sensor_msgs::PointCloud2::ConstPtr &msg)"
if "trimBufferPairFront" not in text:
    if marker_old not in text:
        raise RuntimeError("FAST-LIVO2 standard_pcl_cbk signature not found")
    text = text.replace(marker_old, trim_helpers, 1)

old_standard_end = '''  lid_raw_data_buffer.push_back(ptr);
  lid_header_time_buffer.push_back(cur_head_time);
  last_timestamp_lidar = cur_head_time;

  mtx_buffer.unlock();
  sig_buffer.notify_all();
}

void LIVMapper::livox_pcl_cbk(const livox_ros_driver::CustomMsg::ConstPtr &msg_in)'''
new_standard_end = '''  lid_raw_data_buffer.push_back(ptr);
  lid_header_time_buffer.push_back(cur_head_time);
  last_timestamp_lidar = cur_head_time;
  trimBufferPairFront(lid_raw_data_buffer, lid_header_time_buffer, kMaxBufferedLidarScans);

  mtx_buffer.unlock();
  sig_buffer.notify_all();
}

void LIVMapper::livox_pcl_cbk(const livox_ros_driver::CustomMsg::ConstPtr &msg_in)'''
if old_standard_end in text:
    text = text.replace(old_standard_end, new_standard_end, 1)
elif "trimBufferPairFront(lid_raw_data_buffer, lid_header_time_buffer" not in text:
    raise RuntimeError("FAST-LIVO2 standard_pcl_cbk buffer tail pattern not found")

old_livox_end = '''  lid_raw_data_buffer.push_back(ptr);
  lid_header_time_buffer.push_back(cur_head_time);
  last_timestamp_lidar = cur_head_time;

  mtx_buffer.unlock();
  sig_buffer.notify_all();
}

void LIVMapper::imu_cbk(const sensor_msgs::Imu::ConstPtr &msg_in)'''
new_livox_end = '''  lid_raw_data_buffer.push_back(ptr);
  lid_header_time_buffer.push_back(cur_head_time);
  last_timestamp_lidar = cur_head_time;
  trimBufferPairFront(lid_raw_data_buffer, lid_header_time_buffer, kMaxBufferedLidarScans);

  mtx_buffer.unlock();
  sig_buffer.notify_all();
}

void LIVMapper::imu_cbk(const sensor_msgs::Imu::ConstPtr &msg_in)'''
if old_livox_end in text:
    text = text.replace(old_livox_end, new_livox_end, 1)
elif "trimBufferPairFront(lid_raw_data_buffer, lid_header_time_buffer, kMaxBufferedLidarScans);\n\n  mtx_buffer.unlock();\n  sig_buffer.notify_all();\n}\n\nvoid LIVMapper::imu_cbk" not in text:
    raise RuntimeError("FAST-LIVO2 livox_pcl_cbk buffer tail pattern not found")

old_imu_end = '''  imu_buffer.push_back(msg);
  // cout<<"got imu: "<<timestamp<<" imu size "<<imu_buffer.size()<<endl;
  mtx_buffer.unlock();'''
new_imu_end = '''  imu_buffer.push_back(msg);
  trimBufferFront(imu_buffer, kMaxBufferedImuMsgs);
  // cout<<"got imu: "<<timestamp<<" imu size "<<imu_buffer.size()<<endl;
  mtx_buffer.unlock();'''
if old_imu_end in text:
    text = text.replace(old_imu_end, new_imu_end, 1)
elif "trimBufferFront(imu_buffer, kMaxBufferedImuMsgs);" not in text:
    raise RuntimeError("FAST-LIVO2 imu_cbk buffer tail pattern not found")

old_img_end = '''  img_buffer.push_back(img_cur);
  img_time_buffer.push_back(img_time_correct);

  // ROS_INFO("Correct Image time: %.6f", img_time_correct);

  last_timestamp_img = img_time_correct;'''
new_img_end = '''  img_buffer.push_back(img_cur);
  img_time_buffer.push_back(img_time_correct);
  trimBufferPairFront(img_buffer, img_time_buffer, kMaxBufferedImageFrames);

  // ROS_INFO("Correct Image time: %.6f", img_time_correct);

  last_timestamp_img = img_time_correct;'''
if old_img_end in text:
    text = text.replace(old_img_end, new_img_end, 1)
elif "trimBufferPairFront(img_buffer, img_time_buffer, kMaxBufferedImageFrames);" not in text:
    raise RuntimeError("FAST-LIVO2 img_cbk buffer tail pattern not found")

path.write_text(text)
