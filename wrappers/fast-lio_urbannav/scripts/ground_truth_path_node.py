#!/usr/bin/env python3
"""Publish UrbanNav INS text or TUM ground truth for live benchmark visualization."""
import math
import os
from bisect import bisect_left

import rospy
from geometry_msgs.msg import PoseStamped, Quaternion
from nav_msgs.msg import Odometry, Path

WGS84_A = 6378137.0
WGS84_E2 = 6.69437999014e-3


def dms_to_deg(degrees, minutes, seconds):
    sign = -1.0 if degrees < 0 else 1.0
    return sign * (abs(degrees) + minutes / 60.0 + seconds / 3600.0)


def ecef_from_lla(lat_deg, lon_deg, height):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    normal = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    return ((normal + height) * cos_lat * math.cos(lon),
            (normal + height) * cos_lat * math.sin(lon),
            (normal * (1.0 - WGS84_E2) + height) * sin_lat)


def enu_from_ecef_delta(dx, dy, dz, ref_lat_deg, ref_lon_deg):
    lat, lon = math.radians(ref_lat_deg), math.radians(ref_lon_deg)
    slat, clat, slon, clon = math.sin(lat), math.cos(lat), math.sin(lon), math.cos(lon)
    return (-slon * dx + clon * dy,
            -slat * clon * dx - slat * slon * dy + clat * dz,
            clat * clon * dx + clat * slon * dy + slat * dz)


def rotate_xy(x, y, angle):
    c, s = math.cos(angle), math.sin(angle)
    return c*x - s*y, s*x + c*y


def quaternion_yaw(qx, qy, qz, qw):
    return math.atan2(2.0*(qw*qz + qx*qy), 1.0 - 2.0*(qy*qy + qz*qz))


def yaw_quaternion(yaw):
    q = Quaternion(); q.w = math.cos(0.5*yaw); q.z = math.sin(0.5*yaw); return q


def parse_local_samples(path, yaw_offset_deg=0.0):
    raw = []
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            try:
                if len(parts) == 8:
                    vals = [float(v) for v in parts]
                    raw.append({"format":"tum", "stamp":vals[0], "x":vals[1], "y":vals[2], "z":vals[3],
                                "yaw":quaternion_yaw(vals[4], vals[5], vals[6], vals[7])})
                elif len(parts) >= 20:
                    raw.append({"format":"urbannav", "stamp":float(parts[0]),
                                "lat":dms_to_deg(float(parts[3]),float(parts[4]),float(parts[5])),
                                "lon":dms_to_deg(float(parts[6]),float(parts[7]),float(parts[8])),
                                "h":float(parts[9]), "heading":float(parts[18])})
            except ValueError:
                continue
    if not raw:
        return []
    raw.sort(key=lambda r:r["stamp"])
    offset = math.radians(yaw_offset_deg)
    if raw[0]["format"] == "tum":
        raw = [r for r in raw if r["format"] == "tum"]
        ref = raw[0]; angle = -ref["yaw"] + offset
        out=[]
        for r in raw:
            x,y=rotate_xy(r["x"]-ref["x"], r["y"]-ref["y"], angle)
            out.append({"stamp":r["stamp"], "x":x, "y":y, "z":r["z"]-ref["z"],
                        "yaw":math.atan2(math.sin(r["yaw"]-ref["yaw"]+offset), math.cos(r["yaw"]-ref["yaw"]+offset))})
        return out
    raw=[r for r in raw if r["format"] == "urbannav"]
    ref=raw[0]; ref_ecef=ecef_from_lla(ref["lat"],ref["lon"],ref["h"])
    heading=math.radians(ref["heading"]); fe,fn=math.sin(heading),math.cos(heading); re,rn=math.cos(heading),-math.sin(heading)
    out=[]
    for r in raw:
        e=ecef_from_lla(r["lat"],r["lon"],r["h"])
        east,north,up=enu_from_ecef_delta(e[0]-ref_ecef[0],e[1]-ref_ecef[1],e[2]-ref_ecef[2],ref["lat"],ref["lon"])
        x,y=rotate_xy(east*re+north*rn,east*fe+north*fn,offset)
        out.append({"stamp":r["stamp"],"x":x,"y":y,"z":up,"yaw":math.radians(r["heading"]-ref["heading"])+offset})
    return out


def build_path(samples, frame_id, z_offset):
    path=Path(); path.header.frame_id=frame_id
    for row in samples:
        ps=PoseStamped(); ps.header.frame_id=frame_id; ps.header.stamp=rospy.Time.from_sec(row["stamp"])
        ps.pose.position.x=row["x"]; ps.pose.position.y=row["y"]; ps.pose.position.z=row["z"]+z_offset
        ps.pose.orientation=yaw_quaternion(row["yaw"]); path.poses.append(ps)
    return path


def nearest_pose(path_msg, stamps, stamp):
    if not path_msg.poses: return None
    target=stamp.to_sec(); idx=bisect_left(stamps,target); candidates=[]
    if idx < len(path_msg.poses): candidates.append(path_msg.poses[idx])
    if idx > 0: candidates.append(path_msg.poses[idx-1])
    return min(candidates,key=lambda p:abs(p.header.stamp.to_sec()-target)) if candidates else path_msg.poses[-1]


def odometry_from_pose(pose, stamp, child_frame_id):
    odom=Odometry(); odom.header.frame_id=pose.header.frame_id; odom.header.stamp=stamp
    odom.child_frame_id=child_frame_id; odom.pose.pose=pose.pose; return odom


def main():
    rospy.init_node("ground_truth_path_node", anonymous=False)
    gt_path=rospy.get_param("~ground_truth_path", "/data/UrbanNav_TST_GT_raw.txt")
    topic=rospy.get_param("~topic", "/ground_truth_path")
    full_topic=rospy.get_param("~full_topic", "/ground_truth_path_full")
    odom_topic=rospy.get_param("~odom_topic", "/ground_truth_odometry")
    frame_id=rospy.get_param("~frame_id", "camera_init")
    child_frame_id=rospy.get_param("~child_frame_id", "ground_truth_car")
    publish_rate=float(rospy.get_param("~publish_rate", 10.0))
    yaw_offset_deg=float(rospy.get_param("~yaw_offset_deg", 0.0))
    z_offset=float(rospy.get_param("~z_offset", 0.0))
    publish_full=bool(rospy.get_param("~publish_full_path", True))
    if not os.path.isfile(gt_path):
        rospy.logerr("[GroundTruthPath] File not found: %s",gt_path); return
    samples=parse_local_samples(gt_path,yaw_offset_deg)
    if not samples:
        rospy.logerr("[GroundTruthPath] No valid INS/TUM samples in %s",gt_path); return
    full_path=build_path(samples,frame_id,z_offset); stamps=[p.header.stamp.to_sec() for p in full_path.poses]
    live_pub=rospy.Publisher(topic,Path,queue_size=1); full_pub=rospy.Publisher(full_topic,Path,queue_size=1,latch=True)
    odom_pub=rospy.Publisher(odom_topic,Odometry,queue_size=10)
    rospy.loginfo("[GroundTruthPath] %d poses from %s",len(full_path.poses),gt_path)
    full_path.header.stamp=rospy.Time(0); live_pub.publish(full_path)
    if publish_full: full_pub.publish(full_path)
    rate=rospy.Rate(publish_rate)
    while not rospy.is_shutdown():
        now=rospy.Time.now(); full_path.header.stamp=rospy.Time(0); live_pub.publish(full_path)
        pose=nearest_pose(full_path,stamps,now)
        if pose: odom_pub.publish(odometry_from_pose(pose,now,child_frame_id))
        rate.sleep()


if __name__ == "__main__": main()
