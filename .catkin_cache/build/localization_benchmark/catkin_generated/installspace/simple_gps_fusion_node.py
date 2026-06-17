#!/usr/bin/env python3
"""Conservative loose GPS/local odometry fusion fallback.

This is deliberately simple: it keeps local odometry orientation/twist and only
slowly corrects position toward the latest valid GPS local tangent position.
Use it when native graph GPS is unavailable. If no GPS exists, output_selector
falls back to local odometry.
"""
import math
import rospy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import NavSatFix

R_EARTH=6378137.0

def ll_to_xy(lat0,lon0,lat,lon):
    lat0r=math.radians(lat0); latr=math.radians(lat)
    x=math.radians(lon-lon0)*math.cos((lat0r+latr)*0.5)*R_EARTH
    y=math.radians(lat-lat0)*R_EARTH
    return x,y

class SimpleGPSFusion:
    def __init__(self):
        self.local_topic=rospy.get_param('~local_odom_topic')
        self.gps_topic=rospy.get_param('~gps_fix_topic','/gps/fix')
        self.output_topic=rospy.get_param('~output_topic')
        self.alpha=float(rospy.get_param('~position_alpha',0.08))
        self.use_z=bool(rospy.get_param('~use_z',False))
        self.lat0=None; self.lon0=None; self.alt0=None; self.latest_gps_xy=None; self.local_at_origin=None
        self.position_offset=[0.0,0.0,0.0]
        self.pub=rospy.Publisher(self.output_topic,Odometry,queue_size=100)
        rospy.Subscriber(self.gps_topic,NavSatFix,self.gps_cb,queue_size=50)
        rospy.Subscriber(self.local_topic,Odometry,self.odom_cb,queue_size=100)
        rospy.loginfo('[SimpleGPSFusion] local=%s gps=%s output=%s alpha=%.3f',self.local_topic,self.gps_topic,self.output_topic,self.alpha)
    def gps_cb(self,msg):
        if not math.isfinite(msg.latitude) or not math.isfinite(msg.longitude): return
        if self.lat0 is None:
            self.lat0=msg.latitude; self.lon0=msg.longitude; self.alt0=msg.altitude
        x,y=ll_to_xy(self.lat0,self.lon0,msg.latitude,msg.longitude)
        z=(msg.altitude-self.alt0) if self.use_z else None
        self.latest_gps_xy=(x,y,z,msg.header.stamp)
    def odom_cb(self,msg):
        if self.latest_gps_xy is None: return
        out=Odometry(); out.header=msg.header; out.child_frame_id=msg.child_frame_id; out.pose=msg.pose; out.twist=msg.twist
        gx,gy,gz,_=self.latest_gps_xy
        # Initialize local-to-GPS translation offset once; do not rotate frames automatically.
        if self.local_at_origin is None:
            self.local_at_origin=(msg.pose.pose.position.x,msg.pose.pose.position.y,msg.pose.pose.position.z)
            self.position_offset=[gx-self.local_at_origin[0], gy-self.local_at_origin[1], (gz or 0.0)-self.local_at_origin[2]]
        target_x=gx-self.position_offset[0]; target_y=gy-self.position_offset[1]
        out.pose.pose.position.x=(1-self.alpha)*msg.pose.pose.position.x + self.alpha*target_x
        out.pose.pose.position.y=(1-self.alpha)*msg.pose.pose.position.y + self.alpha*target_y
        if self.use_z and gz is not None:
            target_z=gz-self.position_offset[2]
            out.pose.pose.position.z=(1-self.alpha)*msg.pose.pose.position.z + self.alpha*target_z
        self.pub.publish(out)
if __name__=='__main__':
    rospy.init_node('simple_gps_fusion_node')
    SimpleGPSFusion(); rospy.spin()
