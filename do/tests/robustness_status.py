#!/usr/bin/env python3
"""Print a concise status summary from a fusion run directory."""
import argparse
import json
from pathlib import Path


def last_topic(path: Path, topic: str):
    with path.open("rb") as stream:
        stream.seek(0, 2)
        position = stream.tell()
        remainder = b""
        while position > 0:
            size = min(65536, position)
            position -= size
            stream.seek(position)
            block = stream.read(size) + remainder
            lines = block.splitlines()
            remainder = lines[0] if position else b""
            for line in reversed(lines[1:] if position else lines):
                try:
                    item = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if item.get("topic") == topic:
                    return item
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    timeline = args.run_dir / "localization_timeline.jsonl"
    if not timeline.is_file():
        raise SystemExit(f"No timeline found in {args.run_dir}")
    item = last_topic(timeline, "/fused_localization/status")
    if item is None:
        raise SystemExit("No fused status has been recorded yet")
    data = item.get("data", {})
    health = data.get("health", {})
    alignment = data.get("alignment_quality", {})
    disagreement = data.get("disagreement", {})
    print(f"run: {args.run_dir}")
    print(f"state: {data.get('state')}  active: {data.get('active_source')}  valid: {data.get('valid')}")
    print(f"navigation-ready scale: {data.get('orb_metric_scale_ready')} ({data.get('orb_metric_scale')})")
    print("alignment: position_rmse={position_rmse_m}m orientation_rmse={orientation_rmse_deg}deg".format(**alignment))
    print("disagreement: position={position_m}m orientation={orientation_deg}deg consistent={consistent}".format(**disagreement))
    for source in ("fast_livo2", "orbslam3"):
        source_health = health.get(source, {})
        reasons = ",".join(source_health.get("reasons", [])) or "none"
        print(f"{source}: healthy={source_health.get('healthy')} rate={source_health.get('pose_rate_hz')}Hz reasons={reasons}")
    events = args.run_dir / "fusion_events.csv"
    if events.is_file():
        lines = events.read_text().splitlines()
        print("recent events:")
        for line in lines[-5:]:
            print(f"  {line}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
