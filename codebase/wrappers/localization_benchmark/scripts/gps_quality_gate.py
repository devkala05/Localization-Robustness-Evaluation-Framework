#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import NavSatFix, NavSatStatus
from std_msgs.msg import String

class GPSQualityGate:
    def __init__(self):
        self.input_topic=rospy.get_param('~input_topic','/gps/fix_raw')
        self.output_topic=rospy.get_param('~output_topic','/gps/fix')
        self.status_topic=rospy.get_param('~status_topic','/gps/status')
        self.max_cov_xy=float(rospy.get_param('~max_cov_xy',100.0))
        self.max_cov_z=float(rospy.get_param('~max_cov_z',400.0))
        self.output_frame_id=str(rospy.get_param('~output_frame_id','gnss_antenna')).strip()
        self.accept_no_fix=bool(rospy.get_param('~accept_no_fix',False))
        self.pub=rospy.Publisher(self.output_topic,NavSatFix,queue_size=50)
        self.status_pub=rospy.Publisher(self.status_topic,String,queue_size=10,latch=True)
        rospy.Subscriber(self.input_topic,NavSatFix,self.cb,queue_size=50)
        rospy.loginfo('[GPSQualityGate] %s -> %s frame=%s max_cov_xy=%.3f max_cov_z=%.3f', self.input_topic,self.output_topic,self.output_frame_id or 'preserve',self.max_cov_xy,self.max_cov_z)
    def cb(self,msg):
        if msg.status.status < NavSatStatus.STATUS_FIX and not self.accept_no_fix:
            self.status_pub.publish(String(data='rejected:no_fix')); return
        cov=msg.position_covariance
        if cov[0]>self.max_cov_xy or cov[4]>self.max_cov_xy or cov[8]>self.max_cov_z:
            self.status_pub.publish(String(data='rejected:covariance')); return
        if self.output_frame_id:
            msg.header.frame_id=self.output_frame_id
        self.pub.publish(msg); self.status_pub.publish(String(data='accepted'))
if __name__=='__main__':
    rospy.init_node('gps_quality_gate')
    GPSQualityGate(); rospy.spin()
