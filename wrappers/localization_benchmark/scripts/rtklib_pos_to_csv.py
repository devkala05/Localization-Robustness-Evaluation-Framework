#!/usr/bin/env python3
import argparse, csv, datetime, re
GPS_UTC_OFFSET_2021=18.0

def parse_time(date_s,time_s):
    dt=datetime.datetime.strptime(date_s+' '+time_s,'%Y/%m/%d %H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc)
    return dt.timestamp() - GPS_UTC_OFFSET_2021

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); args=ap.parse_args()
    with open(args.input) as f, open(args.output,'w',newline='') as out:
        w=csv.writer(out); w.writerow(['stamp','lat','lon','alt','cov_x','cov_y','cov_z','status','service','rtk_mode','source'])
        for line in f:
            if not line.strip() or line.startswith('%'): continue
            parts=line.split()
            if len(parts)<5: continue
            try:
                stamp=parse_time(parts[0],parts[1]); lat=float(parts[2]); lon=float(parts[3]); alt=float(parts[4])
            except Exception: continue
            q=parts[5] if len(parts)>5 else '0'
            status=2 if q in ('1','2') else 0
            w.writerow([f'{stamp:.3f}',lat,lon,alt,4.0,4.0,25.0,status,1,q,'rtklib_pos'])
if __name__=='__main__': main()
