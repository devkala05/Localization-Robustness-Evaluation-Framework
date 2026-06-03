from __future__ import annotations

import argparse
from pathlib import Path

import yaml


def main() -> None:
    parser = argparse.ArgumentParser(description="Print configured dataset topic remappings.")
    parser.add_argument("--topics", default="/config/topics/kitti_topics.yaml")
    args = parser.parse_args()
    data = yaml.safe_load(Path(args.topics).read_text())
    for name, remap in data.get("remappings", {}).items():
        print(f"{name}: {remap['from']} -> {remap['to']}")


if __name__ == "__main__":
    main()
