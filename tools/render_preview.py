"""Render our WFF subset with fixture data, for fast layout checks (not Wear OS).

Reads the actual generated XML: geometry, palette, font and ambient visibility.
Unknown drawing elements fail loudly so preview support cannot silently drift.
"""
import argparse
import math
import re
import xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "watchface/src/main/res"
SCALE = 3
FONT = RES / "font/outfit_regular.ttf"
FIXTURES = {
    "1": {"type": "SHORT_TEXT", "TEXT": "5,275"},
    "2": {"type": "RANGED_VALUE", "TEXT": "76%", "RANGED_VALUE_VALUE": 76,
          "RANGED_VALUE_MIN": 0, "RANGED_VALUE_MAX": 100},
    "3": {"type": "GOAL_PROGRESS", "TEXT": "1,500", "GOAL_PROGRESS_VALUE": 1500, "GOAL_PROGRESS_TARGET_VALUE": 2000},
    "4": {"type": "SHORT_TEXT", "TEXT": "0.85"},
    "5": {"type": "SHORT_TEXT", "TEXT": "19°"},
    "6": {"type": "RANGED_VALUE", "TEXT": "68", "RANGED_VALUE_VALUE": 68,
          "RANGED_VALUE_MIN": 40, "RANGED_VALUE_MAX": 180},
    "7": {"type": "EMPTY"},
}


def make_add():
    """Original neutral add icon, built from geometry, with a transparent background."""
    im = Image.new("RGBA", (132, 132))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((60, 21, 72, 111), radius=6, fill="white")
    d.rounded_rectangle((21, 60, 111, 72), radius=6, fill="white")
    target = RES / "drawable-nodpi/add.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    im.resize((44, 44), Image.Resampling.LANCZOS).save(target)


class Preview:
    def __init__(self, palette="lavender", ambient=False, empty=False):
        self.root = E.parse(RES / "raw/watchface.xml").getroot()
        self.colors = self.root.find(f".//ColorOption[@id='{palette}']").get("colors").split()
        self.ambient, self.empty = ambient, empty
        self.image = Image.new("RGBA", (480*SCALE, 480*SCALE), "black")
        self.draw = ImageDraw.Draw(self.image)

    def color(self, value):
        match = re.fullmatch(r"\[CONFIGURATION.palette.(\d)\]", value)
        return self.colors[int(match[1])] if match else value

    def value(self, expr, data):
        if expr == "[DAY_OF_WEEK_S]": return "THU"
        if expr == "[DAY]": return "24"
        if expr.startswith("numberFormat"):
            key = re.search(r"COMPLICATION.(\w+)", expr)[1]
            return str(round(data.get(key, 0)))
        return str(data.get(expr.removeprefix("[COMPLICATION.").removesuffix("]"), ""))

    def font(self, el):
        return ImageFont.truetype(str(FONT), round(float(el.get("size"))*SCALE))

    def label(self, el, data):
        t = el.find("Template")
        return self.value(t.find("Parameter").get("expression"), data) if t is not None else (el.text or "")

    def xy(self, x, y): return (round(x*SCALE), round(y*SCALE))

    def render(self, el=None, ox=0, oy=0, data=None):
        if el is None: el = self.root.find("Scene")
        if data is None: data = {}
        tag, a = el.tag, el.attrib
        if tag in {"Metadata", "Variant", "DefaultProviderPolicy", "BoundingArc", "BoundingOval", "Expressions"}:
            return
        alpha = int(a.get("alpha", 255))
        if self.ambient:
            for v in el.findall("Variant"):
                if v.get("mode") == "AMBIENT" and v.get("target") == "alpha": alpha = int(v.get("value"))
        if alpha == 0: return
        x, y = ox + float(a.get("x", 0)), oy + float(a.get("y", 0))
        w, h = float(a.get("width", 0)), float(a.get("height", 0))
        if tag == "ComplicationSlot":
            data = {} if self.empty else FIXTURES.get(a["slotId"], {})
            if not data:
                default = el.find("DefaultProviderPolicy").get("defaultSystemProviderType")
                data = FIXTURES.get(a["slotId"], {}) if default != "EMPTY" else {"type": "EMPTY"}
            child = el.find(f"Complication[@type='{data['type']}']")
            self.render(child, x, y, data)
        elif tag == "Condition":
            name = "has_text" if "has_text" in E.tostring(el, encoding="unicode") else "has_icon"
            has_value = data.get("TEXT" if name == "has_text" else "MONOCHROMATIC_IMAGE") is not None
            child = el.find("Compare" if has_value else "Default")
            if child is not None: self.render(child, x, y, data)
        elif tag in {"Scene", "Group", "DigitalClock", "Complication", "Compare", "Default", "PartDraw"}:
            for child in el: self.render(child, x, y, data)
        elif tag in {"PartText", "TimeText"}:
            circular = el.find("TextCircular")
            f = el.find(".//Font")
            value = "10:09" if tag == "TimeText" else self.label(f, data)
            color = self.color(f.get("color", "#FFFFFF"))
            if alpha != 255:
                color = tuple(round(int(color[i:i+2], 16)*alpha/255) for i in (1, 3, 5))
            font = self.font(f)
            if tag == "TimeText":
                times = (f"{hour:02}:{minute:02}" for hour in range(24) for minute in range(60))
                widest = max(times, key=font.getlength)
                if font.getlength(widest) > w*SCALE:
                    raise ValueError(f"Clock clips at {widest}; reduce font size or widen TimeText.")
            if circular is None:
                self.draw.text(self.xy(x+w/2, y+h/2), value, font=font, fill=color, anchor="mm")
            else:
                self.curved(circular, x, y, value, font, color)
        elif tag in {"RoundRectangle", "Ellipse"}:
            color = self.color(el.find("Fill").get("color"))
            box = (*self.xy(x, y), *self.xy(x+w, y+h))
            if tag == "Ellipse": self.draw.ellipse(box, fill=color)
            else: self.draw.rounded_rectangle(box, radius=float(a["cornerRadiusX"])*SCALE, fill=color)
        elif tag == "Arc":
            cx, cy = ox+float(a["centerX"]), oy+float(a["centerY"])
            start, end = float(a["startAngle"]), float(a["endAngle"])
            if el.find("Transform") is not None:
                if data["type"] == "GOAL_PROGRESS":
                    fraction = data["GOAL_PROGRESS_VALUE"]/max(1, data["GOAL_PROGRESS_TARGET_VALUE"])
                else:
                    fraction = (data["RANGED_VALUE_VALUE"]-data["RANGED_VALUE_MIN"])/max(.001, data["RANGED_VALUE_MAX"]-data["RANGED_VALUE_MIN"])
                end = start+max(0, min(1, fraction))*(end-start)
            stroke = el.find("Stroke")
            color, thickness = self.color(stroke.get("color")), float(stroke.get("thickness"))
            self.draw.arc((*self.xy(cx-w/2, cy-h/2), *self.xy(cx+w/2, cy+h/2)), start-90, end-90,
                          fill=color, width=round(thickness*SCALE))
            # Pillow draws strokes inward; cap centers match that inset.
            radius = (w-thickness)/2
            for angle in (start, end):
                r = math.radians(angle)
                px, py = cx+radius*math.sin(r), cy-radius*math.cos(r)
                self.draw.ellipse((*self.xy(px-thickness/2, py-thickness/2), *self.xy(px+thickness/2, py+thickness/2)), fill=color)
        elif tag == "PartImage":
            resource = el.find("Image").get("resource")
            if resource != "add": return # Provider images are deliberately absent from fixtures.
            im = Image.open(RES / "drawable-nodpi/add.png").convert("RGBA").resize(self.xy(w, h))
            tinted = Image.new("RGBA", im.size, self.color(a["tintColor"]))
            tinted.putalpha(im.getchannel("A"))
            self.image.alpha_composite(tinted, self.xy(x, y))
        else:
            raise ValueError(f"Preview does not support {tag}")

    def curved(self, el, ox, oy, label, font, color):
        a = el.attrib
        cx, cy = ox+float(a["centerX"]), oy+float(a["centerY"])
        radius = float(a["width"])/2 - 7
        clockwise = a["direction"] == "CLOCKWISE"
        direction = 1 if clockwise else -1
        widths = [font.getlength(c)/SCALE for c in label]
        total = sum(widths)
        mid = (float(a["startAngle"])+float(a["endAngle"]))/2
        offset = -total/2
        for char, width in zip(label, widths):
            angle = mid + direction*math.degrees((offset+width/2)/radius)
            glyph = Image.new("RGBA", (150, 150))
            ImageDraw.Draw(glyph).text((75,75), char, font=font, fill=color, anchor="mm")
            glyph = glyph.rotate(-angle if clockwise else 180-angle, Image.Resampling.BICUBIC)
            rad = math.radians(angle)
            px, py = self.xy(cx+radius*math.sin(rad), cy-radius*math.cos(rad))
            self.image.alpha_composite(glyph, (px-75, py-75))
            offset += width

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image.resize((480,480), Image.Resampling.LANCZOS).convert("RGB").save(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    make_add()
    for palette in ("lavender", "lime", "ice"):
        for ambient in (False, True):
            preview = Preview(palette, ambient)
            preview.render()
            preview.save(ROOT / f"docs/images/{palette}{'-ambient' if ambient else ''}.png")
            if palette == "lavender" and not ambient:
                preview.save(RES / "drawable-nodpi/preview.png")
    preview = Preview(empty=True)
    preview.render()
    preview.save(ROOT / "docs/images/first-install.png")
    print("Updated drawable assets and docs/images previews (fixture data, not emulator captures).")
