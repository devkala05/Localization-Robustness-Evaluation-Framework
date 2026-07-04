#!/usr/bin/env python3
"""Colorful health/fusion status summary from a fusion run directory.

Called by:
  ./robustness.sh status [run_dir]
  ./robustness.sh watch  [run_dir]   (loops with clear + 1 s sleep)
"""
import argparse
import json
import math
import sys
from pathlib import Path

# ── ANSI colors ───────────────────────────────────────────────────────────────
RED   = "\033[0;31m"
GRN   = "\033[0;32m"
YEL   = "\033[0;33m"
CYN   = "\033[0;36m"
BOLD  = "\033[1m"
DIM   = "\033[2m"
RST   = "\033[0m"

NO_COLOR = not sys.stdout.isatty()

def c(color: str, text: str) -> str:
    return text if NO_COLOR else f"{color}{text}{RST}"

def ok(text: str) -> str:   return c(GRN, text)
def bad(text: str) -> str:  return c(RED, text)
def warn(text: str) -> str: return c(YEL, text)
def dim(text: str) -> str:  return c(DIM, text)
def bold(text: str) -> str: return c(BOLD, text)

def health_str(healthy) -> str:
    return ok("healthy") if healthy else bad("UNHEALTHY")

def state_color(state: str) -> str:
    if state is None:
        return dim("unknown")
    if "PRIMARY" in state and "UNHEALTHY" not in state and "DEGRADED" not in state:
        return ok(state)
    if "BACKUP" in state or "TERTIARY" in state:
        return warn(state)
    if "FAILED" in state or "UNHEALTHY" in state:
        return bad(state)
    if "DEGRADED" in state:
        return warn(state)
    return dim(state)

def fmt_float(value, digits: int = 3, unit: str = "") -> str:
    if value is None:
        return dim("n/a")
    return f"{value:.{digits}f}{unit}"

# ── reader ─────────────────────────────────────────────────────────────────────
def last_topic(path: Path, topic: str):
    with path.open("rb") as f:
        f.seek(0, 2)
        pos = f.tell()
        remainder = b""
        while pos > 0:
            size = min(65536, pos)
            pos -= size
            f.seek(pos)
            block = f.read(size) + remainder
            lines = block.splitlines()
            remainder = lines[0] if pos else b""
            for line in reversed(lines[1:] if pos else lines):
                try:
                    item = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue
                if item.get("topic") == topic:
                    return item
    return None

# ── main ───────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    timeline = args.run_dir / "localization_timeline.jsonl"
    if not timeline.is_file():
        print(bad(f"No timeline found in {args.run_dir}"))
        return 1
    item = last_topic(timeline, "/fused_localization/status")
    if item is None:
        print(warn("No fused status recorded yet — bag may still be starting."))
        return 1

    data   = item.get("data", {})
    health = data.get("health", {})
    alq    = data.get("alignment_quality", {})
    dis    = data.get("disagreement", {})
    rec_alq = data.get("recovery_alignment_quality", {})

    # ── header ────────────────────────────────────────────────────────────────
    print(bold("━━  Fusion status  ") + dim(f"run: {args.run_dir.name}"))
    print()

    state = data.get("state")
    valid = data.get("valid", False)
    active = data.get("active_source") or "none"
    tertiary = data.get("tertiary_source")
    switches = data.get("switch_count", 0)
    tf_mode = data.get("tf_mode", "?")

    print(f"  {'State':<24} {state_color(state)}")
    valid_str = ok("valid") if valid else bad("INVALID")
    print(f"  {'Active source':<24} {warn(active) if active not in ('fast_livo2', 'none') else (bad(active) if active == 'none' else ok(active))}  {valid_str}")
    print(f"  {'Primary':<24} {data.get('primary_source', '?')}")
    print(f"  {'Metric':<24} {data.get('metric_source', '?')}")
    if tertiary:
        print(f"  {'Tertiary':<24} {tertiary}")
    print(f"  {'Switches':<24} {switches}")
    print(f"  {'TF mode':<24} {tf_mode}")

    # ── estimator health ──────────────────────────────────────────────────────
    print()
    print(bold("  Estimator health"))
    sources = ["fast_livo2", "orbslam3", "lvisam"]
    for src in sources:
        sh = health.get(src, {})
        h = sh.get("healthy", False)
        rate = sh.get("pose_rate_hz")
        reasons = ", ".join(sh.get("reasons", [])) or dim("none")
        rate_str = f"{rate:.1f} Hz" if rate is not None else dim("n/a")
        marker = ok("●") if h else bad("●")
        print(f"  {marker} {src:<20} {health_str(h):<28} {rate_str}  {dim(reasons) if h else bad(reasons)}")

    # ── ORB alignment ─────────────────────────────────────────────────────────
    scale_ready = data.get("orb_metric_scale_ready", False)
    scale = data.get("orb_metric_scale")
    print()
    print(bold("  ORB metric alignment"))
    scale_s = (ok if scale_ready else bad)(f"{'ready' if scale_ready else 'NOT READY'}")
    print(f"  {'Scale ready':<24} {scale_s}  ({fmt_float(scale, 4)})")
    print(f"  {'Position RMSE':<24} {fmt_float(alq.get('position_rmse_m'), 3, ' m')}")
    orient_rmse = alq.get("orientation_rmse_deg")
    print(f"  {'Orientation RMSE':<24} {fmt_float(orient_rmse, 1, ' °')}")

    # ── cross-estimator disagreement ──────────────────────────────────────────
    print()
    print(bold("  Cross-estimator disagreement"))
    consistent = dis.get("consistent", False)
    pos_m = dis.get("position_m")
    ori_deg = dis.get("orientation_deg")
    dis_str = (ok if consistent else warn)("consistent" if consistent else "INCONSISTENT")
    print(f"  {'Agreement':<24} {dis_str}")
    print(f"  {'Position delta':<24} {fmt_float(pos_m, 2, ' m')}")
    print(f"  {'Orientation delta':<24} {fmt_float(ori_deg, 1, ' °')}")

    # ── recent events ─────────────────────────────────────────────────────────
    events = args.run_dir / "fusion_events.csv"
    if events.is_file():
        lines = [l for l in events.read_text().splitlines() if l.strip()]
        if len(lines) > 1:
            print()
            print(bold("  Recent events (last 5)"))
            for line in lines[-5:]:
                print(f"  {dim(line)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
