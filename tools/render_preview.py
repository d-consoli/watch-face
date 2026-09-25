"""Render the actual WFF geometry with deterministic fixtures (not Wear OS)."""
import math
import re
import xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont
from prepare_artwork import prepare

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "watchface/src/main/res"
SCALE = 3
FIXTURES = {
    "101": {"type": "RANGED_VALUE", "TEXT": "1,504", "fraction": .6},
    "102": {"type": "RANGED_VALUE", "TEXT": "5,275", "fraction": .53},
    "103": {"type": "RANGED_VALUE", "TEXT": "68"},
    "104": {"type": "LONG_TEXT", "TITLE": "14:30 · IN 25 MIN", "TEXT": "Design catch-up"},
    "105": {"type": "SMALL_IMAGE"},
}


class Preview:
    def __init__(self, ambient=False, empty=False, full=False):
        self.root = E.parse(RES / "raw/watchface.xml").getroot()
        self.ambient, self.empty, self.full = ambient, empty, full
        self.image = Image.new("RGBA", (480*SCALE, 480*SCALE), "black")
        self.draw = ImageDraw.Draw(self.image)

    def value(self, expr, data):
        if expr == "[DAY_OF_WEEK_S]": return "FRI"
        if expr == "[DAY]": return "25"
        if expr == "[BATTERY_PERCENT]": return "100" if self.full else "76"
        if expr.startswith("'"): return expr.strip("'")
        field = re.search(r"COMPLICATION\.(TEXT|TITLE)", expr)
        if field:
            return data.get(field[1], "—")
        raise ValueError(f"Missing fixture expression: {expr}")

    def xy(self, x, y): return round(x*SCALE), round(y*SCALE)

    def check_content_box(self, box, label):
        """Guard actual glyph/icon bounds against the display and full gauge lanes."""
        left, top, right, bottom = box
        for x in (left, right):
            for y in (top, bottom):
                assert math.hypot(x-240, y-240) < 237, f"Display edge clips {label}"
        for x in range(max(240, math.floor(left)), math.ceil(right)+1):
            for y in range(math.floor(top), math.ceil(bottom)+1):
                radius = math.hypot(x-240, y-240)
                angle = math.degrees(math.atan2(x-240, 240-y)) % 360
                assert not (213 <= radius <= 231 and
                            (11 <= angle <= 85 or 95 <= angle <= 169)), f"Gauge overlaps {label}"

    def render(self, el=None, ox=0, oy=0, data=None):
        if el is None: el = self.root.find("Scene")
        if data is None: data = {}
        tag, a = el.tag, el.attrib
        if tag in {"Variant", "Transform", "DefaultProviderPolicy", "BoundingBox", "Launch"}: return
        alpha = int(a.get("alpha", 255))
        if self.ambient:
            for v in el.findall("Variant"):
                if v.get("mode") == "AMBIENT" and v.get("target") == "alpha": alpha = int(v.get("value"))
        if alpha == 0: return
        x, y = ox+float(a.get("x", 0)), oy+float(a.get("y", 0))
        w, h = float(a.get("width", 0)), float(a.get("height", 0))
        if tag == "ComplicationSlot":
            data = {"type": "EMPTY"} if self.empty else FIXTURES[a["slotId"]]
            self.render(el.find(f"Complication[@type='{data['type']}']"), x, y, data)
        elif tag in {"Scene", "Group", "DigitalClock", "Complication", "PartDraw"}:
            masks = [child for child in el if child.get("renderMode") == "MASK"]
            if masks:
                original = self.image
                self.image = Image.new("RGBA", original.size)
                self.draw = ImageDraw.Draw(self.image)
                for child in el:
                    if child not in masks: self.render(child, x, y, data)
                source = self.image
                self.image = Image.new("RGBA", original.size)
                self.draw = ImageDraw.Draw(self.image)
                for child in masks: self.render(child, x, y, data)
                source.putalpha(ImageChops.multiply(source.getchannel("A"), self.image.getchannel("A")))
                self.image = original
                self.image.alpha_composite(source)
                self.draw = ImageDraw.Draw(self.image)
            else:
                for child in el: self.render(child, x, y, data)
        elif tag == "Arc":
            cx, cy = ox+float(a["centerX"]), oy+float(a["centerY"])
            start, end = float(a["startAngle"]), float(a["endAngle"])
            transform = el.find("Transform[@target='endAngle']")
            if transform is not None:
                fraction = 1 if self.full else (.76 if "BATTERY_PERCENT" in transform.get("value") else data.get("fraction", 0))
                end = start + (end-start)*fraction
            if end <= start: return
            stroke = el.find("Stroke")
            thickness = float(stroke.get("thickness"))
            # Pillow's stroke is inset, whereas WFF draws around the arc centerline.
            self.draw.arc((*self.xy(cx-w/2-thickness/2, cy-h/2-thickness/2),
                           *self.xy(cx+w/2+thickness/2, cy+h/2+thickness/2)),
                          start-90, end-90, fill=stroke.get("color"), width=round(thickness*SCALE))
        elif tag in {"PartText", "TimeText"}:
            f = el.find(".//Font")
            font = ImageFont.truetype(str(RES / "font/outfit_regular.ttf"), round(float(f.get("size"))*SCALE), layout_engine=ImageFont.Layout.BASIC)
            if tag == "TimeText":
                label, align = "10:09", a.get("align", "CENTER")
                widest = max((f"{hr:02}:{mn:02}" for hr in range(24) for mn in range(60)), key=font.getlength)
                assert font.getlength(widest) <= w*SCALE, f"Clock clips at {widest}"
                extent = font.getlength(widest)/SCALE
                bbox = self.draw.textbbox(self.xy(x+w/2, y+h/2), widest, font=font, anchor="mm")
                self.check_content_box((x+(w-extent)/2-3, bbox[1]/SCALE-3,
                                        x+(w+extent)/2+3, bbox[3]/SCALE+3), "widest digital time")
            else:
                t = f.find("Template")
                label = (t.text or "").strip() % tuple(self.value(p.get("expression"), data) for p in t.findall("Parameter")) if t is not None else (f.text or "")
                align = el.find("Text").get("align")
            if font.getlength(label) > w*SCALE:
                while label and font.getlength(label+"…") > w*SCALE: label = label[:-1]
                label += "…"
            px, anchor = (x+w/2, "mm") if align == "CENTER" else (x, "lm")
            bbox = self.draw.textbbox(self.xy(px, y+h/2), label, font=font, anchor=anchor)
            self.check_content_box(tuple(v/SCALE + (-3 if i < 2 else 3) for i,v in enumerate(bbox)), label)
            self.draw.text(self.xy(px, y+h/2), label, font=font, fill=f.get("color"), anchor=anchor)
        elif tag == "PartImage":
            resource = el.find("Image").get("resource")
            if resource in {"painted_card", "painted_heart"}:
                padding = 3 + (w*.14/2 if resource == "painted_heart" else 0)
                self.check_content_box((x-padding, y-padding, x+w+padding, y+h+padding), resource)
            im = Image.open(RES / f"drawable-nodpi/{resource}.png").convert("RGBA")
            transform = el.find("Transform[@target='scaleX']")
            if transform is not None and resource == "painted_stroke":
                w *= .76 if "BATTERY_PERCENT" in transform.get("value") else data.get("fraction", 0)
            if w <= 0: return
            im = im.resize(self.xy(w, h), Image.Resampling.LANCZOS)
            if "tintColor" in a:
                tinted = Image.new("RGBA", im.size, a["tintColor"])
                tinted.putalpha(im.getchannel("A"))
                im = tinted
            if alpha != 255: im.putalpha(im.getchannel("A").point(lambda v: round(v*alpha/255)))
            self.image.alpha_composite(im, self.xy(x, y))
        else:
            raise ValueError(f"Preview does not support {tag}")

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        # Round mask models the physical display and exposes edge clipping in previews.
        mask = Image.new("L", self.image.size)
        ImageDraw.Draw(mask).ellipse((0, 0, 480*SCALE-1, 480*SCALE-1), fill=255)
        image = Image.composite(self.image, Image.new("RGBA", self.image.size, "black"), mask)
        image.resize((480, 480), Image.Resampling.LANCZOS).convert("RGB").save(path)


if __name__ == "__main__":
    prepare()
    for name, options in {"ink-paper": {}, "ink-paper-ambient": {"ambient": True}, "setup": {"empty": True}, "full-gauges": {"full": True}}.items():
        preview = Preview(**options)
        preview.render()
        preview.save(ROOT / f"docs/images/{name}.png")
        if name == "ink-paper": preview.save(RES / "drawable-nodpi/preview.png")
    print("Updated painted previews with fixture data.")
