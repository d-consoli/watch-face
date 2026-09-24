"""Save an actual watch/emulator screenshot without PowerShell corrupting binary output."""
import argparse
from datetime import datetime
import subprocess
from build_apk import ROOT, find_sdk, select_watch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--serial")
args = parser.parse_args()
prefix = select_watch(find_sdk(), args.serial)
data = subprocess.check_output(prefix+["exec-out", "screencap", "-p"])
if not data.startswith(b"\x89PNG\r\n\x1a\n"):
    raise SystemExit("ADB did not return a PNG screenshot.")
path = ROOT/"captures"/f"watch-{datetime.now():%Y%m%d-%H%M%S}.png"
path.parent.mkdir(exist_ok=True)
path.write_bytes(data)
print(path)
