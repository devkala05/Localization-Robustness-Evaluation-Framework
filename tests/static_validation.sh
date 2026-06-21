#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
find "$ROOT" -type d -name __pycache__ -prune -exec rm -rf {} +
python3 -m py_compile $(find "$ROOT" -type f -name '*.py' -print)
python3 "$ROOT/tests/test_fusion_math.py"
python3 "$ROOT/tests/test_evaluation.py"
python3 "$ROOT/tests/test_orb_launcher.py"
python3 "$ROOT/tests/test_orb_pose_axes.py"
python3 "$ROOT/tests/test_health_state.py"
python3 "$ROOT/scripts/validate_configuration.py"
python3 - <<'PY' "$ROOT"
from pathlib import Path
import sys, xml.etree.ElementTree as ET, yaml
root=Path(sys.argv[1])
for path in list(root.rglob('*.launch'))+list(root.rglob('package.xml')):
    ET.parse(path)
for path in root.rglob('*.yaml'):
    if 'orbslam3' not in str(path) and 'params_camera_e2o.yaml' not in str(path):
        yaml.safe_load(path.read_text())
print('XML/YAML parsing passed')
PY
while IFS= read -r -d '' file; do bash -n "$file"; done < <(find "$ROOT" -type f \( -name '*.sh' -o -name run -o -name build.sh \) -print0)
if grep -RIEq '(^|[/_])(urbannav|rtabmap|fast_lio([^v]|$)|coco_lic|adaptive_w_lvio)' "$ROOT" --exclude='CHANGES.md' --exclude='FINAL_REPORT.md'; then
  echo 'Unexpected removed-algorithm or UrbanNav reference remains.' >&2; exit 1
fi
find "$ROOT" -type d -name __pycache__ -prune -exec rm -rf {} +
echo 'Static repository validation passed'
