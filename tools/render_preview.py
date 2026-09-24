"""Render the actual WFF geometry with deterministic fixtures (not Wear OS)."""
import re
import xml.etree.ElementTree as E
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
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
    def __init__(self, ambient=False, empty=False):
        self.root = E.parse(RES / "raw/watchface.xml").getroot()
        self.ambient, self.empty = ambient, empty
        self.image = Image.new("RGBA", (480*SCALE, 480*SCALE), "black")
        self.draw = ImageDraw.Draw(self.image)

    def value(self, expr, data):
        if expr == "[DAY_OF_WEEK_S]": return "FRI"
        if expr == "[DAY]": return "25"
        if expr == "[BATTERY_PERCENT]": return "76"
        if expr.startswith("'"): return expr.strip("'")
        field = re.search(r"COMPLICATION\.(TEXT|TITLE)", expr)
        if field:
            return data.get(field[1], "—")
        raise ValueError(f"Missing fixture expression: {expr}")

    def xy(self, x, y): return round(x*SCALE), round(y*SCALE)

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
        elif tag in {"Scene", "Group", "DigitalClock", "Complication"}:
            for child in el: self.render(child, x, y, data)
        elif tag in {"PartText", "TimeText"}:
            f = el.find(".//Font")
            font = ImageFont.truetype(str(RES / "font/outfit_regular.ttf"), round(float(f.get("size"))*SCALE), layout_engine=ImageFont.Layout.BASIC)
            if tag == "TimeText":
                label, align = "10:09", a.get("align", "CENTER")
                widest = max((f"{hr:02}:{mn:02}" for hr in range(24) for mn in range(60)), key=font.getlength)
                assert font.getlength(widest) <= w*SCALE, f"Clock clips at {widest}"
            else:
                t = f.find("Template")
                label = (t.text or "").strip() % tuple(self.value(p.get("expression"), data) for p in t.findall("Parameter")) if t is not None else (f.text or "")
                align = el.find("Text").get("align")
            if font.getlength(label) > w*SCALE:
                while label and font.getlength(label+"…") > w*SCALE: label = label[:-1]
                label += "…"
            px, anchor = (x+w/2, "mm") if align == "CENTER" else (x, "lm")
            self.draw.text(self.xy(px, y+h/2), label, font=font, fill=f.get("color"), anchor=anchor)
        elif tag == "PartImage":
            resource = el.find("Image").get("resource")
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
    for name, options in {"ink-paper": {}, "ink-paper-ambient": {"ambient": True}, "setup": {"empty": True}}.items():
        preview = Preview(**options)
        preview.render()
        preview.save(ROOT / f"docs/images/{name}.png")
        if name == "ink-paper": preview.save(RES / "drawable-nodpi/preview.png")
    print("Updated painted previews with fixture data.")
