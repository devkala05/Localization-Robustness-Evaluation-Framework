#!/usr/bin/env python3
import argparse, csv

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('input'); ap.add_argument('output'); args=ap.parse_args()
    with open(args.input) as f, open(args.output,'w',newline='') as out:
        reader=csv.DictReader(f)
        w=csv.writer(out); w.writerow(['stamp','lat','lon','alt','cov_x','cov_y','cov_z','status','service','rtk_mode','source'])
        for r in reader:
            stamp=r.get('stamp') or r.get('time') or r.get('timestamp')
            lat=r.get('lat') or r.get('latitude'); lon=r.get('lon') or r.get('longitude'); alt=r.get('alt') or r.get('altitude') or 0
            if not stamp or not lat or not lon: continue
            w.writerow([stamp,lat,lon,alt,r.get('cov_x',4.0),r.get('cov_y',4.0),r.get('cov_z',25.0),r.get('status',0),r.get('service',1),r.get('rtk_mode','graph'), 'graphgnss'])
if __name__=='__main__': main()
