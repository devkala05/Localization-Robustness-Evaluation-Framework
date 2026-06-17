# Permanent dataset segment files

Edit these files once to mark timestamp windows such as straight, left turn,
right turn, under bridge, stop, GPS outage, etc.  Every `./run ... --eval`
loads the dataset's segment file and writes segment-wise relative-error reports
inside that run's timestamped result folder.

Files used by default:

- `urban_segments.yaml` for UrbanNav
- `e2o_segments.yaml` for E2O

Schema:

```yaml
segments:
  - name: right_turn_1
    type: turn_right
    start: 1723528230.123456   # bag/ROS timestamp seconds
    end: 1723528238.654321
    description: optional human note
```
