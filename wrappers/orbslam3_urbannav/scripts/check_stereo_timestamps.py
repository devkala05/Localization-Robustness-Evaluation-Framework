#!/usr/bin/env python3
import statistics

import rosbag


BAG = "/data/UrbanNav-HK_TST-20210517_sensors.bag"
LEFT = "/zed2/camera/left/image_raw"
RIGHT = "/zed2/camera/right/image_raw"


def main():
    left = []
    right = []
    with rosbag.Bag(BAG) as bag:
        for topic, msg, _ in bag.read_messages(topics=[LEFT, RIGHT]):
            if topic == LEFT:
                left.append(msg.header.stamp.to_sec())
            else:
                right.append(msg.header.stamp.to_sec())
            if len(left) >= 300 and len(right) >= 300:
                break

    n = min(len(left), len(right))
    diffs = [abs(left[i] - right[i]) for i in range(n)]
    print(f"left={len(left)} right={len(right)} pairs={n}")
    print(f"first_left={left[:3]}")
    print(f"first_right={right[:3]}")
    print(
        "diff_sec "
        f"min={min(diffs):.9f} "
        f"mean={statistics.mean(diffs):.9f} "
        f"max={max(diffs):.9f}"
    )


if __name__ == "__main__":
    main()
