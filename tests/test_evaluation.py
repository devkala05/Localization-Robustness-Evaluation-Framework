#!/usr/bin/env python3
import csv
import json
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def write(path, scale=1.0):
    with path.open('w', newline='') as f:
        w=csv.writer(f); w.writerow(['timestamp_s','x_m','y_m','z_m','qx','qy','qz','qw'])
        for i in range(30):
            w.writerow([1000+i*0.1, scale*i*0.2, scale*(i*0.01)**2, 0, 0,0,0,1])

def main():
    with tempfile.TemporaryDirectory() as d:
        d=Path(d); run=d/'run'; run.mkdir(); gt=d/'gt.csv'
        write(gt)
        # Add metadata columns expected by provenance reader without changing parser behavior.
        rows=list(csv.DictReader(gt.open()))
        with gt.open('w',newline='') as f:
            fields=list(rows[0])+['source_method','notes']; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
            for row in rows: row.update(source_method='synthetic_test',notes='unit_test'); w.writerow(row)
        write(run/'fast_livo2_trajectory.csv')
        write(run/'fused_trajectory.csv')
        write(run/'lvisam_trajectory.csv')
        write(run/'orbslam3_trajectory.csv', scale=0.5)
        (run/'localization_timeline.jsonl').write_text('')
        subprocess.run(['python3',str(ROOT/'evaluation/evaluate_e2o.py'),'--run-dir',str(run),'--gt',str(gt)],check=True)
        report=json.loads((run/'evaluation/metrics.json').read_text())
        for name in ('fast_livo2','orbslam3','lvisam','fused'):
            assert report['metrics'][name]['valid']
            assert report['metrics'][name]['ate_m']['rmse'] < 1e-8
        assert (run/'evaluation/trajectory_xy.png').is_file()
    print('evaluation synthetic tests passed')
if __name__=='__main__': main()
