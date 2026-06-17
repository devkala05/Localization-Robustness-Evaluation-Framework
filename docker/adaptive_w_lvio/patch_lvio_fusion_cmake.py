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
else:
    print(f'[patch] WARNING: missing {node}', file=sys.stderr)

print('[patch] lvio_fusion build-system patch complete')
