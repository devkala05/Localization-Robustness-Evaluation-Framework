#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-all}"
NO_CACHE=""
if [[ "${2:-}" == "--no-cache" || "${1:-}" == "--no-cache" ]]; then
  NO_CACHE="--no-cache"
  [[ "${1:-}" == "--no-cache" ]] && TARGET="all"
fi
build_image() {
  local name="$1" dockerfile="$2" tag="$3"
  echo "[build] ${name} -> ${tag}"
  docker build ${NO_CACHE} --network host -f "${ROOT}/${dockerfile}" -t "${tag}" "${ROOT}"
}
case "${TARGET}" in
  all)
    build_image fusion docker/fusion/Dockerfile e2o-localization-fusion:latest
    build_image fast_livo2 docker/fastlivo2/Dockerfile fastlivo2-e2o:latest
    build_image orbslam3 docker/orbslam3/Dockerfile orbslam3-e2o:latest
    ;;
  fusion) build_image fusion docker/fusion/Dockerfile e2o-localization-fusion:latest ;;
  fast_livo2) build_image fast_livo2 docker/fastlivo2/Dockerfile fastlivo2-e2o:latest ;;
  orbslam3) build_image orbslam3 docker/orbslam3/Dockerfile orbslam3-e2o:latest ;;
  *) echo "Usage: ./build.sh [all|fusion|fast_livo2|orbslam3] [--no-cache]" >&2; exit 2 ;;
esac
