"""Run Google's official WFF validator with checksum verification and fail-fast status."""
import hashlib
from pathlib import Path
import subprocess
import urllib.request
from build_apk import ROOT, java_tool

URL = "https://github.com/google/watchface/releases/download/release/wff-validator.jar"
SHA256 = "28b244289ab748bb2b07017e9f3c06bb76bdf165d6fa55652a5dc64b852c3121"

if __name__ == "__main__":
    jar = ROOT/".cache/wff-validator.jar"
    jar.parent.mkdir(parents=True, exist_ok=True)
    if not jar.exists():
        with urllib.request.urlopen(URL, timeout=60) as response:
            payload = response.read()
        if hashlib.sha256(payload).hexdigest() != SHA256:
            raise SystemExit("Validator release changed. Review the upstream release before updating the pinned hash.")
        jar.write_bytes(payload)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != SHA256:
        raise SystemExit("Validator checksum mismatch; refusing to execute.")
    subprocess.run([java_tool("java"), "-jar", str(jar), "2", "--stop-on-fail",
                    str(ROOT/"watchface/src/main/res/raw/watchface.xml")], check=True)
