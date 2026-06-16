# ORB-SLAM3

ORB-SLAM3 is integrated as a camera-only benchmark participant using the UrbanNav ZED2 image topics. The default mode is stereo.

## Build And Run

```bash
./build_orbslam3.sh
./run --algo orbslam3 --per 0 --gps off --eval
./run --algo orbslam3 --per 0 --gps on --eval
```

The first build is heavy because Pangolin and ORB-SLAM3 are compiled.

## Modes

```bash
./run --algo orbslam3 --per 0 --orb-mode stereo --eval
./run --algo orbslam3 --per 0 --orb-mode mono --eval
```

Stereo is the recommended benchmark mode. Monocular mode can run, but scale drift makes metric evaluation less reliable.

## Inputs

```text
/camera/left/image_raw
/camera/right/image_raw
/camera/left/camera_info
/camera/right/camera_info
```

By default the adapter uses `stereo_swap_lr:=true`, matching the current calibration path.

## Outputs

```text
/orbslam3/odometry/mapping
/orbslam3/mapping/path
/orbslam3/tracking_status
/orbslam3/odometry/local
/orbslam3/path/local
/orbslam3/odometry/output
/orbslam3/path/output
```

Results are written to `data/results/orb_slam3/`.
