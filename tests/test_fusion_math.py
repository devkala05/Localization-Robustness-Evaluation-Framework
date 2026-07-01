#!/usr/bin/env python3
import importlib.util
import math
import sys
import types
from pathlib import Path
import numpy as np

class V:
    def __init__(self): self.x=self.y=self.z=0.0
class Q:
    def __init__(self): self.x=self.y=self.z=0.0; self.w=1.0
class Pose:
    def __init__(self): self.position=V(); self.orientation=Q()
geometry=types.ModuleType("geometry_msgs")
msg=types.ModuleType("geometry_msgs.msg")
msg.Pose=Pose
msg.Quaternion=Q
geometry.msg=msg
sys.modules["geometry_msgs"]=geometry
sys.modules["geometry_msgs.msg"]=msg
path=Path(__file__).resolve().parents[1]/"wrappers/e2o_localization_fusion/scripts/fusion_math.py"
spec=importlib.util.spec_from_file_location("fusion_math", path)
fm=importlib.util.module_from_spec(spec); spec.loader.exec_module(fm)

def rz(angle):
    c,s=math.cos(angle),math.sin(angle)
    R=np.array([[c,-s,0],[s,c,0],[0,0,1]],float)
    T=np.eye(4); T[:3,:3]=R; return T

def main():
    q=np.array([0.1,-0.2,0.3,0.9]); q=q/np.linalg.norm(q)
    assert np.allclose(fm.matrix_to_quaternion(fm.quaternion_to_matrix(q)), q) or np.allclose(fm.matrix_to_quaternion(fm.quaternion_to_matrix(q)), -q)
    camera_to_base=np.eye(4); camera_to_base[:3,3]=[0.3,-0.1,0.2]; camera_to_base[:3,:3]=rz(0.2)[:3,:3]
    alignment=rz(0.7); alignment[:3,3]=[5,-3,1]
    scale=1.0
    pairs=[]
    for i in range(20):
        camera=rz(0.03*i); camera[:3,3]=[0.4*i, math.sin(i*0.2), 0.1*i]
        base=fm.apply_camera_to_base_similarity(alignment, scale, camera_to_base, camera)
        pairs.append((base,camera))
    estimated,s,pr,rr=fm.estimate_camera_to_base_similarity(pairs,camera_to_base)
    assert abs(s-scale)<1e-8, (s,scale)
    assert pr<1e-8, pr
    assert rr<1e-8, rr
    for base,camera in pairs:
        assert np.allclose(fm.apply_camera_to_base_similarity(estimated,s,camera_to_base,camera),base,atol=1e-8)
    T0=np.eye(4); T1=rz(math.pi/2); T1[:3,3]=[2,0,0]
    mid=fm.interpolate_transform(T0,T1,0.5)
    assert np.allclose(mid[:3,3],[1,0,0])
    print("fusion_math synthetic tests passed")
if __name__ == "__main__": main()
