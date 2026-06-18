#!/usr/bin/env python3
"""
Convert UrbanNav / receiver NMEA logs to the benchmark GNSS CSV format.

Output CSV columns:
  stamp,lat,lon,alt,cov_x,cov_y,cov_z,status,service,rtk_mode,source

Typical usage:
  python3 nmea_to_gnss_csv.py \
    --input data/gnss/raw/UrbanNav-HK-Medium-Urban-1.ublox.f9p.nmea \
    --output data/gnss/urbannav_tst_gnss.csv \
    --date 2021-05-17 \
    --source ublox_f9p

Notes:
- NMEA time is normally UTC, so default --time-offset-sec is 0.
- If your NMEA has RMC sentences with date, that date is used automatically.
- If your NMEA only has GGA sentences, pass --date YYYY-MM-DD.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple


# ROS sensor_msgs/NavSatStatus constants
STATUS_NO_FIX = -1
STATUS_FIX = 0
STATUS_SBAS_FIX = 1
STATUS_GBAS_FIX = 2

# ROS sensor_msgs/NavSatStatus service bitmask
SERVICE_GPS = 1
SERVICE_GLONASS = 2
SERVICE_COMPASS = 4  # BeiDou in ROS constant naming
SERVICE_GALILEO = 8


@dataclass
class FixRecord:
    stamp: float
    lat: float
    lon: float
    alt: float
    cov_x: float
    cov_y: float
    cov_z: float
    status: int
    service: int
    rtk_mode: str
    source: str


def strip_checksum(sentence: str) -> str:
    sentence = sentence.strip()
    if not sentence:
        return ""
    if sentence.startswith("$"):
        sentence = sentence[1:]
    if "*" in sentence:
        sentence = sentence.split("*", 1)[0]
    return sentence


def checksum_ok(sentence: str) -> bool:
    s = sentence.strip()
    if not s.startswith("$") or "*" not in s:
        return True  # accept lines without checksum
    body, given = s[1:].split("*", 1)
    given = given[:2]
    calc = 0
    for ch in body:
        calc ^= ord(ch)
    try:
        return calc == int(given, 16)
    except ValueError:
        return False


def parse_nmea_latlon(value: str, hemi: str) -> Optional[float]:
    if not value or not hemi:
        return None
    try:
        raw = float(value)
    except ValueError:
        return None
    deg = int(raw // 100)
    minutes = raw - deg * 100
    decimal = deg + minutes / 60.0
    if hemi.upper() in ("S", "W"):
        decimal *= -1.0
    return decimal


def parse_time_utc(hhmmss: str) -> Optional[Tuple[int, int, int, int]]:
    if not hhmmss:
        return None
    try:
        if "." in hhmmss:
            main, frac = hhmmss.split(".", 1)
            micro = int(float("0." + frac) * 1_000_000)
        else:
            main = hhmmss
            micro = 0
        main = main.zfill(6)
        hour = int(main[0:2])
        minute = int(main[2:4])
        second = int(main[4:6])
        return hour, minute, second, micro
    except Exception:
        return None


def parse_rmc_date(ddmmyy: str) -> Optional[dt.date]:
    if not ddmmyy or len(ddmmyy) < 6:
        return None
    try:
        day = int(ddmmyy[0:2])
        month = int(ddmmyy[2:4])
        yy = int(ddmmyy[4:6])
        year = 2000 + yy if yy < 80 else 1900 + yy
        return dt.date(year, month, day)
    except Exception:
        return None


def make_stamp(date_obj: dt.date, hhmmss: str, offset_sec: float = 0.0) -> Optional[float]:
    t = parse_time_utc(hhmmss)
    if t is None:
        return None
    hour, minute, second, micro = t
    try:
        dtime = dt.datetime(
            date_obj.year,
            date_obj.month,
            date_obj.day,
            hour,
            minute,
            second,
            micro,
            tzinfo=dt.timezone.utc,
        )
    except ValueError:
        return None
    return dtime.timestamp() + offset_sec


def quality_to_status_and_mode(quality: int) -> Tuple[int, str, float, float]:
    """Return ROS status, mode string, horizontal sigma base, vertical sigma base."""
    # NMEA GGA quality:
    # 0 invalid, 1 GPS/SPS, 2 DGPS, 4 RTK fixed, 5 RTK float, 6 estimated/dead reckoning
    if quality == 0:
        return STATUS_NO_FIX, "no_fix", 100.0, 150.0
    if quality == 4:
        return STATUS_GBAS_FIX, "rtk_fixed", 0.05, 0.10
    if quality == 5:
        return STATUS_GBAS_FIX, "rtk_float", 0.50, 1.00
    if quality == 2:
        return STATUS_SBAS_FIX, "dgps", 1.00, 2.00
    if quality == 6:
        return STATUS_FIX, "estimated", 10.0, 15.0
    return STATUS_FIX, "single", 5.00, 8.00


def talker_to_service(talker: str) -> int:
    # GP=GPS, GL=GLONASS, GB/BD=BeiDou, GA=Galileo, GN=mixed multi-GNSS
    talker = talker.upper()
    if talker == "GP":
        return SERVICE_GPS
    if talker == "GL":
        return SERVICE_GLONASS
    if talker in ("GB", "BD"):
        return SERVICE_COMPASS
    if talker == "GA":
        return SERVICE_GALILEO
    if talker == "GN":
        return SERVICE_GPS | SERVICE_GLONASS | SERVICE_COMPASS | SERVICE_GALILEO
    return SERVICE_GPS


def parse_default_date(date_str: Optional[str]) -> Optional[dt.date]:
    if not date_str:
        return None
    try:
        return dt.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise SystemExit(f"Bad --date '{date_str}', expected YYYY-MM-DD")


def iter_nmea_lines(path: str) -> Iterable[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line:
                yield line


def convert_nmea(
    input_path: str,
    output_path: str,
    default_date: Optional[dt.date],
    source: str,
    time_offset_sec: float = 0.0,
    check_checksum: bool = False,
    min_quality: int = 1,
    max_hdop: float = 99.0,
) -> List[FixRecord]:
    current_date = default_date
    records: List[FixRecord] = []
    skipped_no_date = 0
    skipped_bad = 0
    skipped_quality = 0
    last_stamp: Optional[float] = None

    for line in iter_nmea_lines(input_path):
        if check_checksum and not checksum_ok(line):
            skipped_bad += 1
            continue

        clean = strip_checksum(line)
        if not clean:
            continue
        fields = clean.split(",")
        sentence = fields[0].upper()
        talker = sentence[:2]
        msg_type = sentence[2:]

        if msg_type == "RMC":
            # $GNRMC,time,status,lat,N,lon,E,sog,cog,date,...
            if len(fields) > 9:
                parsed_date = parse_rmc_date(fields[9])
                if parsed_date is not None:
                    current_date = parsed_date
            continue

        if msg_type != "GGA":
            continue

        # $GNGGA,time,lat,N,lon,E,quality,num_sats,hdop,alt,M,geoid,M,...
        if len(fields) < 10:
            skipped_bad += 1
            continue
        if current_date is None:
            skipped_no_date += 1
            continue

        time_str = fields[1]
        lat = parse_nmea_latlon(fields[2], fields[3])
        lon = parse_nmea_latlon(fields[4], fields[5])
        try:
            quality = int(fields[6]) if fields[6] else 0
        except ValueError:
            quality = 0
        try:
            hdop = float(fields[8]) if fields[8] else 99.0
        except ValueError:
            hdop = 99.0
        try:
            alt = float(fields[9]) if fields[9] else float("nan")
        except ValueError:
            alt = float("nan")

        if lat is None or lon is None or not math.isfinite(alt):
            skipped_bad += 1
            continue
        if quality < min_quality or hdop > max_hdop:
            skipped_quality += 1
            continue

        stamp = make_stamp(current_date, time_str, offset_sec=time_offset_sec)
        if stamp is None:
            skipped_bad += 1
            continue

        # Deduplicate identical or non-increasing timestamps, common with mixed talker logs.
        if last_stamp is not None and stamp <= last_stamp:
            # Keep strictly increasing output for the replay node.
            if abs(stamp - last_stamp) < 1e-6:
                continue
        last_stamp = stamp

        status, mode, sigma_xy_base, sigma_z_base = quality_to_status_and_mode(quality)
        # HDOP scales horizontal accuracy. Clamp so RTK fixed does not become zero.
        sigma_xy = max(sigma_xy_base * max(hdop, 0.5), sigma_xy_base)
        sigma_z = max(sigma_z_base * max(hdop, 0.5), sigma_z_base)

        records.append(
            FixRecord(
                stamp=stamp,
                lat=lat,
                lon=lon,
                alt=alt,
                cov_x=sigma_xy * sigma_xy,
                cov_y=sigma_xy * sigma_xy,
                cov_z=sigma_z * sigma_z,
                status=status,
                service=talker_to_service(talker),
                rtk_mode=mode,
                source=source,
            )
        )

    records.sort(key=lambda r: r.stamp)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["stamp", "lat", "lon", "alt", "cov_x", "cov_y", "cov_z", "status", "service", "rtk_mode", "source"])
        for r in records:
            writer.writerow([
                f"{r.stamp:.6f}",
                f"{r.lat:.10f}",
                f"{r.lon:.10f}",
                f"{r.alt:.4f}",
                f"{r.cov_x:.6f}",
                f"{r.cov_y:.6f}",
                f"{r.cov_z:.6f}",
                r.status,
                r.service,
                r.rtk_mode,
                r.source,
            ])

    print(f"Wrote {len(records)} fixes: {output_path}")
    if skipped_no_date:
        print(f"Skipped {skipped_no_date} GGA lines before date was known. Pass --date if needed.")
    if skipped_bad:
        print(f"Skipped {skipped_bad} malformed/checksum-bad lines.")
    if skipped_quality:
        print(f"Skipped {skipped_quality} low-quality/high-HDOP fixes.")
    if records:
        t0 = dt.datetime.fromtimestamp(records[0].stamp, tz=dt.timezone.utc).isoformat()
        t1 = dt.datetime.fromtimestamp(records[-1].stamp, tz=dt.timezone.utc).isoformat()
        modes: Dict[str, int] = {}
        for r in records:
            modes[r.rtk_mode] = modes.get(r.rtk_mode, 0) + 1
        print(f"Time range UTC: {t0}  ->  {t1}")
        print("Modes:", ", ".join(f"{k}={v}" for k, v in sorted(modes.items())))
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert NMEA GGA/RMC logs to UrbanNav benchmark GNSS CSV.")
    ap.add_argument("--input", "-i", required=True, help="Input .nmea file")
    ap.add_argument("--output", "-o", required=True, help="Output benchmark CSV path")
    ap.add_argument(
        "--date",
        default="2021-05-17",
        help="Fallback date for GGA-only logs, YYYY-MM-DD. Default: 2021-05-17 for UrbanNav HK TST.",
    )
    ap.add_argument("--source", default=None, help="Source label stored in CSV, default=input basename")
    ap.add_argument(
        "--time-offset-sec",
        type=float,
        default=0.0,
        help="Add this offset to output timestamps. NMEA is UTC, so default 0 is normally correct.",
    )
    ap.add_argument("--check-checksum", action="store_true", help="Drop NMEA sentences with bad checksums")
    ap.add_argument("--min-quality", type=int, default=1, help="Minimum GGA quality to keep. 1 keeps normal fixes; 4 keeps only RTK fixed.")
    ap.add_argument("--max-hdop", type=float, default=99.0, help="Drop fixes with HDOP larger than this")
    args = ap.parse_args()

    default_date = parse_default_date(args.date)
    source = args.source or os.path.splitext(os.path.basename(args.input))[0]

    if not os.path.exists(args.input):
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 2

    records = convert_nmea(
        input_path=args.input,
        output_path=args.output,
        default_date=default_date,
        source=source,
        time_offset_sec=args.time_offset_sec,
        check_checksum=args.check_checksum,
        min_quality=args.min_quality,
        max_hdop=args.max_hdop,
    )
    return 0 if records else 1


if __name__ == "__main__":
    raise SystemExit(main())
