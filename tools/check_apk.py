"""Catch packaging mistakes that WFF raw-XML validation cannot detect."""
import argparse
import re
import sys
import traceback
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("apk", type=Path)
args = parser.parse_args()
# Make failures visible in GitHub's public check annotations as well as raw logs.
def report_exception(kind, value, tb):
    print(f"::error file={args.apk.as_posix()}::{kind.__name__}: {value}", flush=True)
    traceback.print_exception(kind, value, tb)
sys.excepthook = report_exception
with zipfile.ZipFile(args.apk) as z:
    names = set(z.namelist())
    assert not any(re.fullmatch(r"classes\d*\.dex", n) for n in names), "WFF must have no runtime bytecode"
    for resource in ("res/raw/watchface.xml", "res/xml/watch_face_info.xml", "res/font/outfit_regular.ttf"):
        assert resource in names, f"Missing {resource}"
    for image in ("preview.png", "painted_paper.png", "painted_card.png", "painted_heart.png", "painted_arc.png"):
        assert any(n.startswith("res/drawable") and n.endswith("/"+image) for n in names), f"Missing {image}"
    face = E.fromstring(z.read("res/raw/watchface.xml"))
    slots = face.findall("Scene/ComplicationSlot")
    assert 1 <= len(slots) <= 8, f"Invalid slot count: {len(slots)}"
    assert len({s.get("slotId") for s in slots}) == len(slots), "Duplicate slot IDs"
    for slot in slots:
        supported = set(slot.get("supportedTypes").split())
        rendered = {c.get("type") for c in slot.findall("Complication")}
        assert supported == rendered, f"Slot {slot.get('slotId')} has an unrendered type"
        provider = slot.find("DefaultProviderPolicy")
        assert provider.get("defaultSystemProviderType") in supported, "Default type is unsupported"
    assert face.find(".//TimeText").get("hourFormat") == "SYNC_TO_DEVICE", "Clock ignores device hour format"
print(f"PASS: {args.apk} is resource-only, with required assets and consistent complication slots.")
