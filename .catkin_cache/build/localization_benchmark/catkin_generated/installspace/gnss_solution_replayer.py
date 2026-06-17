#!/usr/bin/env python3
"""Replay a normalized GNSS CSV as sensor_msgs/NavSatFix under /clock.

CSV contract:
  stamp,lat,lon,alt,cov_x,cov_y,cov_z,status,service,rtk_mode,source
Only stamp/lat/lon/alt are required. stamp must be ROS/Unix time seconds.
"""
import csv
import math
import bisect
import rospy
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import NavSatFix, NavSatStatus

class GnssSolutionReplayer:
    def __init__(self):
        self.csv_path = rospy.get_param('~csv_path', '')
        self.output_topic = rospy.get_param('~output_topic', '/gps/fix')
        self.frame_id = rospy.get_param('~frame_id', 'gnss_antenna')
        self.publish_all_before_clock = bool(rospy.get_param('~publish_all_before_clock', False))
        self.required = bool(rospy.get_param('~required', False))
        self.rows=[]; self.stamps=[]; self.index=0
        if self.csv_path:
            self.load_csv(self.csv_path)
        elif self.required:
            raise RuntimeError('GNSS CSV required but ~csv_path is empty')
        self.pub = rospy.Publisher(self.output_topic, NavSatFix, queue_size=50)
        rospy.Subscriber('/clock', Clock, self.clock_cb, queue_size=50)
        rospy.loginfo('[GNSSReplayer] file=%s rows=%d output=%s', self.csv_path or 'none', len(self.rows), self.output_topic)

    def load_csv(self,path):
        with open(path,'r',encoding='utf-8') as f:
            reader=csv.DictReader(f)
            for r in reader:
                try:
                    stamp=float(r.get('stamp') or r.get('time') or r.get('timestamp'))
                    lat=float(r.get('lat') or r.get('latitude'))
                    lon=float(r.get('lon') or r.get('longitude'))
                    alt=float(r.get('alt') or r.get('altitude') or 0.0)
                except Exception:
                    continue
                covx=float(r.get('cov_x') or r.get('cov_e') or r.get('std_e', 5.0))
                covy=float(r.get('cov_y') or r.get('cov_n') or r.get('std_n', 5.0))
                covz=float(r.get('cov_z') or r.get('cov_u') or r.get('std_u', 20.0))
                # Treat std values as covariance if user already named cov; if named std, square them.
                if 'std_e' in r or 'std_n' in r or 'std_u' in r:
                    covx, covy, covz = covx*covx, covy*covy, covz*covz
                status=int(float(r.get('status') or 0))
                service=int(float(r.get('service') or NavSatStatus.SERVICE_GPS))
                self.rows.append((stamp,lat,lon,alt,covx,covy,covz,status,service))
        self.rows.sort(key=lambda x:x[0]); self.stamps=[r[0] for r in self.rows]

    def row_to_msg(self,row):
        stamp,lat,lon,alt,cx,cy,cz,status,service=row
        msg=NavSatFix(); msg.header.stamp=rospy.Time.from_sec(stamp); msg.header.frame_id=self.frame_id
        msg.status.status=status; msg.status.service=service
        msg.latitude=lat; msg.longitude=lon; msg.altitude=alt
        msg.position_covariance=[cx,0,0,0,cy,0,0,0,cz]
        msg.position_covariance_type=NavSatFix.COVARIANCE_TYPE_DIAGONAL_KNOWN
        return msg

    def clock_cb(self,clock):
        if not self.rows: return
        t=clock.clock.to_sec()
        if self.publish_all_before_clock:
            end=bisect.bisect_right(self.stamps,t)
            while self.index<end:
                self.pub.publish(self.row_to_msg(self.rows[self.index])); self.index+=1
        else:
            idx=bisect.bisect_right(self.stamps,t)-1
            if idx>=0 and idx!=self.index:
                self.index=idx
                self.pub.publish(self.row_to_msg(self.rows[idx]))

if __name__=='__main__':
    rospy.init_node('gnss_solution_replayer')
    GnssSolutionReplayer()
    rospy.spin()
