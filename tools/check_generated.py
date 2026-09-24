"""Check generated source and PNG pixels, independent of platform PNG compression."""
import io
import subprocess
from pathlib import Path
from PIL import Image, ImageChops, features
from build_apk import ROOT

print("Preview FreeType:", features.version_module("freetype2"), "(explicit BASIC layout)")
failed = False
paths = [ROOT/"watchface/src/main/res/raw/watchface.xml"]
paths += list((ROOT/"docs/images").glob("*.png"))
paths += list((ROOT/"watchface/src/main/res/drawable-nodpi").glob("*.png"))
for path in paths:
    relative = path.relative_to(ROOT).as_posix()
    committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=ROOT)
    if path.suffix == ".png":
        before = Image.open(io.BytesIO(committed)).convert("RGBA")
        after = Image.open(path).convert("RGBA")
        # Check alpha separately: RGB differences must not be masked by zero alpha diff.
        same = before.size == after.size and all(c.getbbox() is None for c in ImageChops.difference(before, after).split())
    else:
        same = committed.replace(b"\r\n", b"\n") == path.read_bytes().replace(b"\r\n", b"\n")
    if not same:
        print(f"::error file={relative}::Regenerated content differs from committed content")
        failed = True
if failed:
    raise SystemExit(1)
print("PASS: generated XML and image pixels match the committed sources.")
