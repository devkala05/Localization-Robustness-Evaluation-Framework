#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
./run_all.sh --dry-run --algos fastlio2,lvisam --per 0,1 --gps both
