#!/usr/bin/env bash
set -euo pipefail

# Sequential full benchmark launcher.
# It opens ONE new terminal per command, waits until that terminal finishes,
# then opens the next terminal. Each algorithm is built once first, then all
# per/gps runs are executed with --eval and full bag duration.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT_DIR}"

ALGOS=(
  fastlio2
  lvisam
  fastlivo2
  rtabmap
  adaptive_w_lvio
  orbslam3
  r3live
)

# Run order: for each algo -> build once -> dataset -> per 0 gps off/on -> ... -> per 6 gps off/on
DATASETS=(urbannav e2o)
PERS=(0 1 2 3 4 5 6)
GPS_MODES=(off on)

# Optional overrides:
#   START_ALGO=rtabmap ./run_all_algos_new_terminals.sh   # skip algos before rtabmap
#   START_PER=3 ./run_all_algos_new_terminals.sh          # for every algo, start from per 3
#   GPS_LIST="on" ./run_all_algos_new_terminals.sh        # run only GPS on
#   DATASET_LIST="e2o" ./run_all_algos_new_terminals.sh   # run only one dataset
#   ALGO_LIST="lvisam rtabmap" ./run_all_algos_new_terminals.sh
if [ -n "${ALGO_LIST:-}" ]; then
  # shellcheck disable=SC2206
  ALGOS=(${ALGO_LIST})
fi
if [ -n "${DATASET_LIST:-}" ]; then
  # shellcheck disable=SC2206
  DATASETS=(${DATASET_LIST})
fi
if [ -n "${PER_LIST:-}" ]; then
  # shellcheck disable=SC2206
  PERS=(${PER_LIST})
elif [ -n "${START_PER:-}" ]; then
  if ! [[ "${START_PER}" =~ ^[0-6]$ ]]; then
    echo "ERROR: START_PER must be 0..6, got '${START_PER}'" >&2
    exit 2
  fi
  PERS=()
  for p in 0 1 2 3 4 5 6; do
    [ "${p}" -ge "${START_PER}" ] && PERS+=("${p}")
  done
fi
if [ -n "${GPS_LIST:-}" ]; then
  # shellcheck disable=SC2206
  GPS_MODES=(${GPS_LIST})
fi

validate_algo_name() {
  case "$1" in
    fastlio2|lvisam|fastlivo2|rtabmap|adaptive_w_lvio|orbslam3|r3live) ;;
    *) echo "ERROR: unknown algorithm '$1'" >&2; return 2 ;;
  esac
}

for algo in "${ALGOS[@]}"; do
  validate_algo_name "${algo}"
done

if [ -n "${START_ALGO:-}" ]; then
  validate_algo_name "${START_ALGO}"
fi

for dataset in "${DATASETS[@]}"; do
  case "${dataset}" in
    urbannav|e2o) ;;
    *) echo "ERROR: dataset must be urbannav/e2o, got '${dataset}'" >&2; exit 2 ;;
  esac
done

for per in "${PERS[@]}"; do
  if ! [[ "${per}" =~ ^[0-6]$ ]]; then
    echo "ERROR: per must be 0..6, got '${per}'" >&2
    exit 2
  fi
done

for gps in "${GPS_MODES[@]}"; do
  case "${gps}" in
    off|on) ;;
    *) echo "ERROR: gps mode must be off/on, got '${gps}'" >&2; exit 2 ;;
  esac
done

if [ "${#ALGOS[@]}" -eq 0 ]; then
  echo "ERROR: algorithm list is empty" >&2
  exit 2
fi

if [ "${#PERS[@]}" -eq 0 ]; then
  echo "ERROR: perturbation list is empty" >&2
  exit 2
fi

if [ "${#GPS_MODES[@]}" -eq 0 ]; then
  echo "ERROR: GPS mode list is empty" >&2
  exit 2
fi

build_script_for_algo() {
  case "$1" in
    fastlio2) echo "./build_fastlio2.sh" ;;
    lvisam) echo "./build_lvisam.sh" ;;
    fastlivo2) echo "./build_fastlivo2.sh" ;;
    rtabmap) echo "./build_rtabmap.sh" ;;
    adaptive_w_lvio) echo "./build_adaptive_w_lvio.sh" ;;
    orbslam3) echo "./build_orbslam3.sh" ;;
    r3live) echo "./build_r3live.sh" ;;
    *) echo "ERROR: unknown algorithm '$1'" >&2; return 2 ;;
  esac
}

terminal_cmd_available() {
  command -v "$1" >/dev/null 2>&1
}

open_terminal_wait() {
  local title="$1"
  local cmd="$2"
  local tmp_dir status_file wrapper
  tmp_dir="$(mktemp -d /tmp/urbannav_benchmark_XXXXXX)"
  status_file="${tmp_dir}/status"
  wrapper="${tmp_dir}/command.sh"

  cat > "${wrapper}" <<EOF_WRAPPER
#!/usr/bin/env bash
set -o pipefail
cd "${ROOT_DIR}"
unset TMUX
clear || true
echo "============================================================"
echo "${title}"
echo "============================================================"
echo "Working directory: ${ROOT_DIR}"
echo "Command: ${cmd}"
echo
bash -lc '${cmd}'
status=\$?
echo "\${status}" > '${status_file}'
echo
if [ "\${status}" -eq 0 ]; then
  echo "DONE: ${title}"
  sleep 1
  exit 0
else
  echo "FAILED with exit code \${status}: ${title}"
  echo "Terminal kept open so you can read the error. Press Enter to continue/close."
  read -r _
  exit "\${status}"
fi
EOF_WRAPPER
  chmod +x "${wrapper}"

  echo "[launcher] opening terminal: ${title}"

  if terminal_cmd_available gnome-terminal; then
    gnome-terminal --wait --title="${title}" -- bash -lc "'${wrapper}'"
  elif terminal_cmd_available kgx; then
    kgx --wait --title="${title}" -- bash -lc "'${wrapper}'"
  elif terminal_cmd_available konsole; then
    konsole --nofork --new-tab --workdir "${ROOT_DIR}" -p tabtitle="${title}" -e bash -lc "'${wrapper}'"
  elif terminal_cmd_available xfce4-terminal; then
    xfce4-terminal --disable-server --title="${title}" --command="bash -lc '${wrapper}'" &
    # xfce4-terminal may return before the command finishes on some systems; wait for status file.
    while [ ! -f "${status_file}" ]; do sleep 2; done
  elif terminal_cmd_available xterm; then
    xterm -T "${title}" -e bash -lc "'${wrapper}'"
  elif terminal_cmd_available x-terminal-emulator; then
    x-terminal-emulator -T "${title}" -e bash -lc "'${wrapper}'" &
    while [ ! -f "${status_file}" ]; do sleep 2; done
  else
    echo "ERROR: no supported terminal found. Install gnome-terminal, kgx, konsole, xfce4-terminal, xterm, or x-terminal-emulator." >&2
    rm -rf "${tmp_dir}"
    return 127
  fi

  if [ ! -f "${status_file}" ]; then
    echo "ERROR: terminal closed before status was written: ${title}" >&2
    rm -rf "${tmp_dir}"
    return 1
  fi

  local status
  status="$(cat "${status_file}" 2>/dev/null || echo 1)"
  rm -rf "${tmp_dir}"

  if [ "${status}" != "0" ]; then
    echo "ERROR: command failed: ${title}" >&2
    return "${status}"
  fi
  echo "[launcher] finished: ${title}"
}

STARTED="false"

for algo in "${ALGOS[@]}"; do
  if [ -n "${START_ALGO:-}" ] && [ "${STARTED}" = "false" ]; then
    if [ "${algo}" != "${START_ALGO}" ]; then
      echo "[launcher] skipping algo before START_ALGO: ${algo}"
      continue
    fi
  fi
  STARTED="true"

  echo
  echo "============================================================"
  echo "starting algo ${algo}"
  echo "============================================================"

  build_script="$(build_script_for_algo "${algo}")"
  if [ ! -x "${build_script}" ]; then
    chmod +x "${build_script}"
  fi
  open_terminal_wait "BUILD ${algo}" "${build_script}"

  for dataset in "${DATASETS[@]}"; do
    for per in "${PERS[@]}"; do
      for gps in "${GPS_MODES[@]}"; do
        title="RUN ${dataset} ${algo} per_${per} gps_${gps} eval_full"
        cmd="./run --dataset ${dataset} --algo ${algo} --per ${per} --gps ${gps} --eval"
        open_terminal_wait "${title}" "${cmd}"
      done
    done
  done

  echo "[launcher] completed algo ${algo}"
done

echo
echo "============================================================"
echo "ALL REQUESTED ALGORITHMS / PERTURBATIONS / GPS MODES DONE"
echo "============================================================"
