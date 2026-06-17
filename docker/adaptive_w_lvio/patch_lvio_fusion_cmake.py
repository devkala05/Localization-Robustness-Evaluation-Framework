#!/usr/bin/env python3
"""Patch upstream jypjypjypjyp/lvio_fusion for ROS Noetic/focal catkin builds.

The upstream repo is usable, but its CMake files assume a looser catkin/CMake
setup than catkin_tools in a clean Docker image provides. This patch keeps the
algorithm code untouched and fixes only build-system discovery.
"""
from pathlib import Path
import re
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/root/catkin_ws/src/lvio_fusion_upstream')

find_glog = r'''# Minimal FindGlog.cmake for Ubuntu/ROS Docker images where libgoogle-glog-dev
# does not always export a usable CMake config for find_package(Glog REQUIRED).
include(FindPackageHandleStandardArgs)

find_path(GLOG_INCLUDE_DIR glog/logging.h)
find_library(GLOG_LIBRARY NAMES glog)

set(GLOG_INCLUDE_DIRS ${GLOG_INCLUDE_DIR})
set(GLOG_LIBRARIES ${GLOG_LIBRARY})

find_package_handle_standard_args(Glog DEFAULT_MSG GLOG_LIBRARY GLOG_INCLUDE_DIR)

mark_as_advanced(GLOG_INCLUDE_DIR GLOG_LIBRARY)
'''

def write_if_changed(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text() if path.exists() else None
    if old != text:
        path.write_text(text)
        print(f"[patch] wrote {path}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        print(f"[patch] WARNING: pattern not found for {label}", file=sys.stderr)
        return text
    print(f"[patch] {label}")
    return text.replace(old, new, 1)

# lvio_fusion core package -------------------------------------------------
core = root / 'src' / 'lvio_fusion' / 'CMakeLists.txt'
if core.exists():
    text = core.read_text()
    # Upstream currently calls catkin_package() but does not always call
    # find_package(catkin REQUIRED) first, which fails in clean catkin_tools builds.
    if 'find_package(catkin REQUIRED' not in text:
        text = text.replace('project(lvio_fusion)', 'project(lvio_fusion)\nfind_package(catkin REQUIRED)')
        print('[patch] added find_package(catkin REQUIRED) to lvio_fusion')
    # Sophus 1.22.x includes <fmt/format.h>, so clean focal images need
    # libfmt-dev and CMake should link fmt when the target is available.
    if 'find_package(fmt REQUIRED)' not in text:
        marker = 'find_package(catkin REQUIRED)'
        if marker in text:
            text = text.replace(marker, marker + '\nfind_package(fmt REQUIRED)')
        else:
            text = text.replace('project(lvio_fusion)', 'project(lvio_fusion)\nfind_package(fmt REQUIRED)')
        print('[patch] added find_package(fmt REQUIRED) to lvio_fusion')
    if 'catkin_INCLUDE_DIRS' not in text:
        text = text.replace(
            'include_directories(${PROJECT_SOURCE_DIR}/include)',
            'include_directories(${PROJECT_SOURCE_DIR}/include ${catkin_INCLUDE_DIRS})'
        )
        print('[patch] added ${catkin_INCLUDE_DIRS} to lvio_fusion include dirs')
    # Be tolerant of Sophus package variants. Older Sophus exports variables;
    # newer config-style Sophus often exports Sophus::Sophus target only.
    if 'if(TARGET Sophus::Sophus)' not in text:
        text = text.replace(
            'set(THIRD_PARTY_LIBS ${OpenCV_LIBRARIES} ${PCL_LIBRARIES} ${Sophus_LIBRARIES} ${CERES_LIBRARIES} ${GLOG_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT} )',
            'set(THIRD_PARTY_LIBS ${OpenCV_LIBRARIES} ${PCL_LIBRARIES} ${Sophus_LIBRARIES} ${CERES_LIBRARIES} ${GLOG_LIBRARIES} ${CMAKE_THREAD_LIBS_INIT} )\n'
            'if(TARGET Sophus::Sophus)\n'
            '  list(APPEND THIRD_PARTY_LIBS Sophus::Sophus)\n'
            'endif()'
        )
        print('[patch] added Sophus::Sophus target fallback')
    if 'if(TARGET fmt::fmt)' not in text:
        text = text.replace(
            'if(TARGET Sophus::Sophus)\n  list(APPEND THIRD_PARTY_LIBS Sophus::Sophus)\nendif()',
            'if(TARGET Sophus::Sophus)\n  list(APPEND THIRD_PARTY_LIBS Sophus::Sophus)\nendif()\n'
            'if(TARGET fmt::fmt)\n  list(APPEND THIRD_PARTY_LIBS fmt::fmt)\nendif()'
        )
        print('[patch] added fmt::fmt target fallback')
    core.write_text(text)
    write_if_changed(core.parent / 'cmake' / 'FindGlog.cmake', find_glog)

    core_src = core.parent / 'src' / 'CMakeLists.txt'
    if core_src.exists():
        src_text = core_src.read_text()
        if 'target_link_libraries(lvio_fusion ${THIRD_PARTY_LIBS} blas fmt::fmt)' not in src_text:
            src_text = src_text.replace(
                'target_link_libraries(lvio_fusion ${THIRD_PARTY_LIBS} blas)',
                'target_link_libraries(lvio_fusion ${THIRD_PARTY_LIBS} blas fmt::fmt)'
            )
            core_src.write_text(src_text)
            print('[patch] linked fmt::fmt directly into lvio_fusion target')

    frame_h = core.parent / 'include' / 'lvio_fusion' / 'frame.h'
    if frame_h.exists():
        text = frame_h.read_text()
        text = replace_once(
            text,
            '    cv::Mat image_left, image_right;\n',
            '    cv::Mat image_left, image_right;\n'
            '    cv::Mat depth_left;                         // optional CV_32F metric depth for mono-depth input\n',
            'added optional depth_left frame storage',
        )
        frame_h.write_text(text)

    estimator_h = core.parent / 'include' / 'lvio_fusion' / 'estimator.h'
    if estimator_h.exists():
        text = estimator_h.read_text()
        text = replace_once(
            text,
            '    void InputImage(double time, cv::Mat &left_image, cv::Mat &right_image, SE3d init_odom);\n',
            '    void InputImage(double time, cv::Mat &left_image, cv::Mat &right_image, SE3d init_odom);\n'
            '    void InputImageDepth(double time, cv::Mat &left_image, cv::Mat &depth_image, SE3d init_odom);\n',
            'declared Estimator::InputImageDepth',
        )
        estimator_h.write_text(text)

    estimator_cpp = core.parent / 'src' / 'estimator.cpp'
    if estimator_cpp.exists():
        text = estimator_cpp.read_text()
        text = replace_once(
            text,
            '''void Estimator::InputPointCloud(double time, Point3Cloud::Ptr point_cloud)
{
''',
            '''void Estimator::InputImageDepth(double time, cv::Mat &left_image, cv::Mat &depth_image, SE3d init_odom)
{
    Frame::Ptr new_frame = Frame::Create();
    new_frame->time = time;
    new_frame->pose = init_odom;
    cv::undistort(left_image, new_frame->image_left, Camera::Get(0)->K, Camera::Get(0)->D);
    new_frame->image_right = new_frame->image_left;
    depth_image.copyTo(new_frame->depth_left);

    auto t1 = std::chrono::steady_clock::now();
    bool success = frontend->AddFrame(new_frame);
    auto t2 = std::chrono::steady_clock::now();
    auto time_used = std::chrono::duration_cast<std::chrono::duration<double>>(t2 - t1);
}

void Estimator::InputPointCloud(double time, Point3Cloud::Ptr point_cloud)
{
''',
            'implemented Estimator::InputImageDepth',
        )
        estimator_cpp.write_text(text)

    local_map_cpp = core.parent / 'src' / 'local_map.cpp'
    if local_map_cpp.exists():
        text = local_map_cpp.read_text()
        text = replace_once(
            text,
            '''void LocalMap::Triangulate(Frame::Ptr frame, Level &features)
{
    std::vector<cv::Point2f> kps_left, kps_right;
''',
            '''void LocalMap::Triangulate(Frame::Ptr frame, Level &features)
{
    if (!frame->depth_left.empty())
    {
        const float min_depth = 0.2f;
        const float max_depth = 100.0f;
        for (int i = 0; i < features.size(); ++i)
        {
            cv::Point2f pt = features[i]->keypoint.pt;
            float sx = (float)frame->depth_left.cols / std::max(1, frame->image_left.cols);
            float sy = (float)frame->depth_left.rows / std::max(1, frame->image_left.rows);
            int x = std::min(std::max((int)std::round(pt.x * sx), 0), frame->depth_left.cols - 1);
            int y = std::min(std::max((int)std::round(pt.y * sy), 0), frame->depth_left.rows - 1);
            float depth = frame->depth_left.at<float>(y, x);
            if (!std::isfinite(depth) || depth < min_depth || depth > max_depth)
            {
                continue;
            }
            auto new_landmark = visual::Landmark::Create(1.0 / depth);
            features[i]->landmark = new_landmark;
            auto depth_feature = visual::Feature::Create(frame, cv::KeyPoint(pt, 1), new_landmark);
            depth_feature->is_on_left_image = false;
            new_landmark->AddObservation(features[i]);
            new_landmark->AddObservation(depth_feature);
            position_cache[new_landmark->id] = ToWorld(features[i]);
            landmarks[new_landmark->id] = new_landmark;
        }
        return;
    }

    std::vector<cv::Point2f> kps_left, kps_right;
''',
            'added mono-depth landmark initialization branch',
        )
        local_map_cpp.write_text(text)
else:
    print(f'[patch] WARNING: missing {core}', file=sys.stderr)

# lvio_fusion_node package -------------------------------------------------
node = root / 'src' / 'lvio_fusion_node' / 'CMakeLists.txt'
if node.exists():
    text = node.read_text()
    # message_generation generates services using geometry_msgs too, so it must
    # be listed in find_package(catkin ...) before generate_messages().
    m = re.search(r'find_package\(catkin REQUIRED COMPONENTS(.*?)\)', text, flags=re.S)
    if m and 'geometry_msgs' not in m.group(1):
        text = text.replace('sensor_msgs tf', 'sensor_msgs geometry_msgs tf')
        print('[patch] added geometry_msgs to lvio_fusion_node catkin components')
    # Sophus headers pulled in through lvio_fusion use compiled fmt symbols.
    # The node executable includes those headers too, so linking fmt only in the
    # core lvio_fusion library is not enough on Ubuntu 20.04/fmt v6.
    if 'find_package(fmt REQUIRED)' not in text:
        text = text.replace('find_package(GeographicLib REQUIRED)',
                            'find_package(GeographicLib REQUIRED)\nfind_package(fmt REQUIRED)')
        print('[patch] added find_package(fmt REQUIRED) to lvio_fusion_node')
    if 'if(TARGET fmt::fmt)' not in text:
        text = text.replace(
            'set(THIRD_PARTY_LIBS ${catkin_LIBRARIES} ${GeographicLib_LIBRARIES} )',
            'set(THIRD_PARTY_LIBS ${catkin_LIBRARIES} ${GeographicLib_LIBRARIES} )\n'
            'if(TARGET fmt::fmt)\n'
            '  list(APPEND THIRD_PARTY_LIBS fmt::fmt)\n'
            'else()\n'
            '  list(APPEND THIRD_PARTY_LIBS fmt)\n'
            'endif()'
        )
        print('[patch] added fmt link target to lvio_fusion_node')
    # Export runtime message dependency, otherwise dependent packages can fail.
    if 'CATKIN_DEPENDS' not in text:
        text = text.replace(
            'catkin_package( LIBRARIES lvio_fusion_node )',
            'catkin_package(\n'
            '  LIBRARIES lvio_fusion_node\n'
            '  CATKIN_DEPENDS roscpp std_msgs sensor_msgs geometry_msgs tf cv_bridge image_transport pcl_conversions pcl_ros lvio_fusion message_runtime\n'
            ')'
        )
        print('[patch] added CATKIN_DEPENDS to lvio_fusion_node export')
    node.write_text(text)

    node_src = node.parent / 'src' / 'CMakeLists.txt'
    if node_src.exists():
        src_text = node_src.read_text()
        if 'target_link_libraries(lvio_fusion_node ${THIRD_PARTY_LIBS} fmt::fmt)' not in src_text:
            src_text = src_text.replace(
                'target_link_libraries(lvio_fusion_node ${THIRD_PARTY_LIBS})',
                'target_link_libraries(lvio_fusion_node ${THIRD_PARTY_LIBS} fmt::fmt)'
            )
            node_src.write_text(src_text)
            print('[patch] linked fmt::fmt directly into lvio_fusion_node target')

    params_h = node.parent / 'src' / 'parameters.h'
    if params_h.exists():
        text = params_h.read_text()
        text = replace_once(
            text,
            'extern string IMAGE0_TOPIC, IMAGE1_TOPIC;\n',
            'extern string IMAGE0_TOPIC, IMAGE1_TOPIC, DEPTH_TOPIC;\n',
            'declared DEPTH_TOPIC',
        )
        text = replace_once(
            text,
            'extern int use_imu;\n',
            'extern int use_imu;\nextern int use_mono_depth;\nextern double depth_scale;\n',
            'declared mono-depth parameters',
        )
        params_h.write_text(text)

    params_cpp = node.parent / 'src' / 'parameters.cpp'
    if params_cpp.exists():
        text = params_cpp.read_text()
        text = replace_once(
            text,
            'string IMAGE0_TOPIC, IMAGE1_TOPIC;\n',
            'string IMAGE0_TOPIC, IMAGE1_TOPIC, DEPTH_TOPIC;\n',
            'defined DEPTH_TOPIC',
        )
        text = replace_once(
            text,
            'int use_imu, use_lidar, use_navsat, use_loop, use_eskf, use_adapt, train;\n',
            'int use_imu, use_lidar, use_navsat, use_loop, use_eskf, use_adapt, train;\n'
            'int use_mono_depth = 0;\n'
            'double depth_scale = 1.0;\n',
            'defined mono-depth parameters',
        )
        text = replace_once(
            text,
            '''    settings["image0_topic"] >> IMAGE0_TOPIC;
    settings["image1_topic"] >> IMAGE1_TOPIC;
''',
            '''    settings["image0_topic"] >> IMAGE0_TOPIC;
    settings["image1_topic"] >> IMAGE1_TOPIC;
    if (!settings["use_mono_depth"].empty())
    {
        settings["use_mono_depth"] >> use_mono_depth;
    }
    if (!settings["depth_topic"].empty())
    {
        settings["depth_topic"] >> DEPTH_TOPIC;
    }
    if (!settings["depth_scale"].empty())
    {
        settings["depth_scale"] >> depth_scale;
    }
''',
            'read mono-depth parameters',
        )
        params_cpp.write_text(text)

    node_cpp = node.parent / 'src' / 'lvio_fusion_node.cpp'
    if node_cpp.exists():
        text = node_cpp.read_text()
        text = replace_once(
            text,
            'ros::Subscriber sub_imu, sub_lidar, sub_navsat, sub_img0, sub_img1, sub_objects, sub_eskf;\n',
            'ros::Subscriber sub_imu, sub_lidar, sub_navsat, sub_img0, sub_img1, sub_depth, sub_objects, sub_eskf;\n',
            'added depth subscriber handle',
        )
        text = replace_once(
            text,
            '''queue<sensor_msgs::ImageConstPtr> img0_buf;
queue<sensor_msgs::ImageConstPtr> img1_buf;
''',
            '''queue<sensor_msgs::ImageConstPtr> img0_buf;
queue<sensor_msgs::ImageConstPtr> img1_buf;
queue<sensor_msgs::ImageConstPtr> depth_buf;
''',
            'added depth buffer',
        )
        text = replace_once(
            text,
            '''void img1_callback(const sensor_msgs::ImageConstPtr &img_msg)
{
    m_img_buf.lock();
    img1_buf.push(img_msg);
    m_img_buf.unlock();
}

cv::Mat get_image_from_msg(const sensor_msgs::ImageConstPtr &img_msg)
''',
            '''void img1_callback(const sensor_msgs::ImageConstPtr &img_msg)
{
    m_img_buf.lock();
    img1_buf.push(img_msg);
    m_img_buf.unlock();
}

void depth_callback(const sensor_msgs::ImageConstPtr &img_msg)
{
    m_img_buf.lock();
    depth_buf.push(img_msg);
    m_img_buf.unlock();
}

cv::Mat get_image_from_msg(const sensor_msgs::ImageConstPtr &img_msg)
''',
            'added depth callback',
        )
        text = replace_once(
            text,
            '''cv::Mat get_image_from_msg(const sensor_msgs::ImageConstPtr &img_msg)
{
''',
            '''cv::Mat get_depth_from_msg(const sensor_msgs::ImageConstPtr &img_msg)
{
    cv_bridge::CvImageConstPtr ptr = cv_bridge::toCvShare(img_msg);
    cv::Mat depth;
    if (ptr->image.type() == CV_32FC1)
    {
        ptr->image.convertTo(depth, CV_32F, depth_scale);
    }
    else if (ptr->image.type() == CV_16UC1)
    {
        ptr->image.convertTo(depth, CV_32F, depth_scale);
    }
    else
    {
        ptr->image.convertTo(depth, CV_32F, depth_scale);
    }
    return depth;
}

cv::Mat get_image_from_msg(const sensor_msgs::ImageConstPtr &img_msg)
{
''',
            'added depth image conversion',
        )
        text = replace_once(
            text,
            '''        if (!img0_buf.empty() && !img1_buf.empty())
        {
            m_img_buf.lock();
            double time0 = img0_buf.front()->header.stamp.toSec();
            double time1 = img1_buf.front()->header.stamp.toSec();
''',
            '''        if (use_mono_depth && !img0_buf.empty() && !depth_buf.empty())
        {
            m_img_buf.lock();
            double time0 = img0_buf.front()->header.stamp.toSec();
            double time1 = depth_buf.front()->header.stamp.toSec();
            if (time0 < time1 - 5 * epsilon)
            {
                img0_buf.pop();
                printf("throw img0\\n");
                m_img_buf.unlock();
            }
            else if (time0 > time1 + 5 * epsilon)
            {
                depth_buf.pop();
                printf("throw depth\\n");
                m_img_buf.unlock();
            }
            else
            {
                time = img0_buf.front()->header.stamp.toSec();
                header = img0_buf.front()->header;
                image0 = get_image_from_msg(img0_buf.front());
                cv::Mat depth = get_depth_from_msg(depth_buf.front());
                img0_buf.pop();
                depth_buf.pop();
                m_img_buf.unlock();
                estimator->InputImageDepth(time, image0, depth, get_pose_from_path(time));
                publish_car_model(estimator, time);
            }
        }
        else if (!use_mono_depth && !img0_buf.empty() && !img1_buf.empty())
        {
            m_img_buf.lock();
            double time0 = img0_buf.front()->header.stamp.toSec();
            double time1 = img1_buf.front()->header.stamp.toSec();
''',
            'added mono-depth sync path',
        )
        text = replace_once(
            text,
            '''    cout << "image1:" << IMAGE1_TOPIC << endl;
    sub_img1 = n.subscribe(IMAGE1_TOPIC, 10, img1_callback);
''',
            '''    if (use_mono_depth)
    {
        cout << "depth:" << DEPTH_TOPIC << endl;
        sub_depth = n.subscribe(DEPTH_TOPIC, 10, depth_callback);
    }
    else
    {
        cout << "image1:" << IMAGE1_TOPIC << endl;
        sub_img1 = n.subscribe(IMAGE1_TOPIC, 10, img1_callback);
    }
''',
            'switched image1 subscription to optional depth subscription',
        )
        node_cpp.write_text(text)
else:
    print(f'[patch] WARNING: missing {node}', file=sys.stderr)

print('[patch] lvio_fusion build-system patch complete')
