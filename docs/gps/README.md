# GPS / GNSS Mode

The UrbanNav-HK TST sensor bag does not include a live `sensor_msgs/NavSatFix` topic. GPS-enabled runs therefore use either a live topic supplied by the user or the normalized GNSS CSV under `data/gnss/`.

## Default CSV Mode

```bash
./run --algo fastlio2 --per 0 --gps on --eval
```

When `--gps on` is used without an explicit source, `./run` sets:

```text
GPS_SOURCE=csv
GPS_FILE=/data/gnss/urbannav_tst_gnss.csv
GPS_TOPIC=/gps/fix_raw
```

Equivalent explicit command:

```bash
./run --algo fastlio2 --per 0 --gps on --gps-source csv --gps-file data/gnss/urbannav_tst_gnss.csv --eval
```

## Live Topic Mode

```bash
./run --algo fastlio2 --per 0 --gps on --gps-source topic --gps-topic /ublox_node/fix --eval
```

Use `--gps-required` when a missing or rejected GPS stream should fail the run instead of falling back to local odometry.

## CSV Schema

```text
stamp,lat,lon,alt,cov_x,cov_y,cov_z,status,service,rtk_mode,source
```

`stamp` must be ROS/Unix time. If the source is RTKLIB GPS week/seconds-of-week, convert it first:

```bash
rosrun localization_benchmark rtklib_pos_to_csv.py input.pos output.csv
```

The repository also includes `tools/nmea_to_gnss_csv.py` for NMEA-derived CSV generation.

## Runtime Topics

```text
/gps/fix_raw
/gps/fix
/odometry/gps
/<algo>/odometry/gps_fused
/<algo>/odometry/output
/<algo>/path/output
```

CSV replay publishes `NavSatFix.header.frame_id=gnss_antenna`, matching the UrbanNav static sensor TF. If GPS is enabled but absent or rejected and `--gps-required` is not set, `output_selector.py` keeps publishing local odometry on `/<algo>/odometry/output`.
