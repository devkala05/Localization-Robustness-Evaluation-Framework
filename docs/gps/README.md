# GPS / GNSS benchmark mode

The UrbanNav-HK_TST-20210517 sensor bag does not contain a live `sensor_msgs/NavSatFix` topic. For `--gps on`, provide either:

1. a live/topic `NavSatFix` stream:
   ```bash
   ./run --algo fastlio2 --per 0 --gps on --gps-source topic --gps-topic /ublox_node/fix
   ```

2. a normalized GNSS CSV replayed by the benchmark:
   ```bash
   ./run --algo fastlio2 --per 0 --gps on --gps-source csv --gps-file data/gnss/urbannav_tst_gnss.csv
   ```

CSV schema:

```text
stamp,lat,lon,alt,cov_x,cov_y,cov_z,status,service,rtk_mode,source
```

`stamp` must be ROS/Unix time. If your source is RTKLIB GPS week/seconds-of-week, convert it first with:

```bash
rosrun localization_benchmark rtklib_pos_to_csv.py input.pos output.csv
```

Runtime topics:

- `/gps/fix_raw` — raw replayed GPS when CSV mode is used
- `/gps/fix` — quality-gated GPS
- `/odometry/gps` — robot_localization `navsat_transform_node` GPS odometry
- `/<algo>/odometry/gps_fused` — GPS/global EKF output
- `/<algo>/odometry/output` — selected benchmark output; local when GPS is off, GPS-fused when GPS is available

CSV replay publishes `NavSatFix.header.frame_id=gnss_antenna` by default, matching the UrbanNav static TF `body -> gnss_antenna`.

If GPS is enabled but absent or rejected, `output_selector.py` falls back to local odometry so runs do not fail silently.
