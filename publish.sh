#!/bin/bash
# Rebuild the Americar vehicle feed locally and push it to GitHub Pages.
# Used as a manual fallback when GitHub Actions cannot run.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# When this script lives in the merchant-feed working copy, the clone is
# alongside it. When it lives in the repo itself, $HERE is the clone.
if [ -f "$HERE/scrape.py" ] && [ -f "$HERE/docs/vehicle_feed.xml" ]; then
  BUILD_DIR="$HERE"
  REPO_DIR="${REPO_DIR:-$HERE}"
else
  BUILD_DIR="$HERE"
  REPO_DIR="${REPO_DIR:-/workspace/americar/vehicle-feed-repo}"
fi

cd "$BUILD_DIR"
mkdir -p data out
python3 run.py

python3 - <<'PY'
import sys, xml.etree.ElementTree as ET
from pathlib import Path
xml_path = Path("out/vehicle_feed.xml")
tsv_path = Path("out/vehicle_feed.tsv")
if not xml_path.is_file() or not tsv_path.is_file():
    sys.exit("Build did not write out/vehicle_feed.xml and out/vehicle_feed.tsv")
try:
    root = ET.parse(xml_path).getroot()
except ET.ParseError as exc:
    sys.exit(f"vehicle_feed.xml is not valid XML: {exc}")
n = len(root.findall(".//item"))
print(f"parsed_items={n}")
if n < 5:
    sys.exit(f"Refusing to publish: only {n} vehicles (need >= 5)")
ns = "http://base.google.com/ns/1.0"
missing_lt = []
for item in root.findall(".//item"):
    lt = item.findtext(f"{{{ns}}}link_template") or ""
    if "{store_code}" not in lt or not lt.startswith("http"):
        missing_lt.append(item.findtext(f"{{{ns}}}id") or "?")
if missing_lt:
    sys.exit(f"Missing or invalid link_template on {len(missing_lt)} items: {', '.join(missing_lt[:5])}")
open("/tmp/americar-feed-item-count", "w").write(str(n))
PY

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "Repo clone not found at $REPO_DIR" >&2
  exit 1
fi

mkdir -p "$REPO_DIR/docs"
cp -f out/vehicle_feed.xml out/vehicle_feed.tsv "$REPO_DIR/docs/"
: > "$REPO_DIR/docs/.nojekyll"

cd "$REPO_DIR"
git pull --ff-only
git add docs/vehicle_feed.xml docs/vehicle_feed.tsv docs/.nojekyll
if git diff --staged --quiet; then
  echo "No feed changes to push ($(cat /tmp/americar-feed-item-count) vehicles)"
  exit 0
fi
git commit -m "Refresh vehicle feed ($(date '+%Y-%m-%d %I:%M %p %Z'))"
git push
echo "Published $(cat /tmp/americar-feed-item-count) vehicles to origin"
