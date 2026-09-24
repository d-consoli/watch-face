"""Generate the repetitive WFF layout. Standard library only; no Android SDK needed."""
from pathlib import Path
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
COLOR = "[CONFIGURATION.palette.0]"
ACCENT = "[CONFIGURATION.palette.1]"
TRACK = "[CONFIGURATION.palette.2]"
SURFACE = "[CONFIGURATION.palette.3]"
FONT = "outfit_regular"


def node(parent, tag, **attrs):
    return E.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def ambient_hide(parent):
    node(parent, "Variant", mode="AMBIENT", target="alpha", value=0)


def text(parent, x, y, w, h, size, value, color=COLOR, expression=False):
    p = node(parent, "PartText", x=x, y=y, width=w, height=h)
    t = node(p, "Text", align="CENTER", ellipsis="TRUE")
    f = node(t, "Font", family=FONT, size=size, color=color)
    if expression:
        node(node(f, "Template"), "Parameter", expression=value)
        f.find("Template").text = "%s"
    else:
        f.text = value
    return p


def arc(parent, cx, cy, diameter, start, end, color, thickness, progress=None):
    p = node(parent, "PartDraw", x=0, y=0, width=480 if cx == 240 else 106,
             height=480 if cy == 240 else 110)
    a = node(p, "Arc", centerX=cx, centerY=cy, width=diameter, height=diameter,
             startAngle=start, endAngle=end)
    node(a, "Stroke", color=color, thickness=thickness, cap="ROUND")
    if progress:
        node(a, "Transform", target="endAngle", value=f"{start} + ({progress}) * {end-start}")
    return p


def circular_text(parent, start, end, direction, value, expression=True):
    p = node(parent, "PartText", x=0, y=0, width=480, height=480)
    t = node(p, "TextCircular", centerX=240, centerY=240, width=438, height=438,
             startAngle=start, endAngle=end, direction=direction, align="CENTER", ellipsis="TRUE")
    f = node(t, "Font", family=FONT, size=22, color=COLOR)
    if expression:
        template = node(f, "Template")
        template.text = "%s"
        node(template, "Parameter", expression=value)
    else:
        f.text = value


def optional_icon(parent, x, y, size):
    c = node(parent, "Condition")
    node(node(c, "Expressions"), "Expression", name="has_icon").text = "[COMPLICATION.MONOCHROMATIC_IMAGE] != null"
    p = node(node(c, "Compare", expression="has_icon"), "PartImage", x=x, y=y,
             width=size, height=size, tintColor=ACCENT)
    node(p, "Image", resource="[COMPLICATION.MONOCHROMATIC_IMAGE]")


def complication_value(parent, draw_text, ranged=False, goal=False):
    if not (ranged or goal):
        draw_text(parent, "[COMPLICATION.TEXT]")
        return
    c = node(parent, "Condition")
    node(node(c, "Expressions"), "Expression", name="has_text").text = "[COMPLICATION.TEXT] != null"
    draw_text(node(c, "Compare", expression="has_text"), "[COMPLICATION.TEXT]")
    field = "GOAL_PROGRESS_VALUE" if goal else "RANGED_VALUE_VALUE"
    draw_text(node(c, "Default"), f"numberFormat('0', [COMPLICATION.{field}])")


def progress(kind):
    # Guard zero-length provider ranges, then clamp bad provider data to [0, 1].
    if kind == "GOAL_PROGRESS":
        return "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE] > 0 ? clamp([COMPLICATION.GOAL_PROGRESS_VALUE] / [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE], 0, 1) : 0"
    return "[COMPLICATION.RANGED_VALUE_MAX] > [COMPLICATION.RANGED_VALUE_MIN] ? clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1) : 0"


def make_face():
    root = E.Element("WatchFace", width="480", height="480")
    node(root, "Metadata", key="CLOCK_TYPE", value="DIGITAL")
    node(root, "Metadata", key="PREVIEW_TIME", value="10:09:00")
    configs = node(root, "UserConfigurations")
    palette = node(configs, "ColorConfiguration", id="palette", displayName="colors_label", defaultValue="lavender")
    for name, colors in [
        ("lavender", "#DFDFFD #B7A5F3 #52576D #22212D"),
        ("lime", "#E3F4CA #C2EC85 #4B5940 #20271D"),
        ("ice", "#DBEEFA #9DDCF3 #435B69 #1B252D"),
    ]:
        node(palette, "ColorOption", id=name, displayName=name, colors=colors)
    scene = node(root, "Scene", backgroundColor="#000000")

    # Date remains legible in ambient. Background is interactive only.
    p = node(scene, "PartDraw", x=247, y=56, width=52, height=40)
    ambient_hide(p)
    r = node(p, "RoundRectangle", x=0, y=0, width=52, height=40, cornerRadiusX=10, cornerRadiusY=10)
    node(r, "Fill", color=TRACK)
    text(scene, 171, 55, 72, 42, 28, "[DAY_OF_WEEK_S]", expression=True)
    text(scene, 247, 55, 52, 42, 28, "[DAY]", expression=True)
    clock = node(scene, "DigitalClock", x=51, y=113, width=378, height=134)
    time = node(clock, "TimeText", x=0, y=0, width=378, height=134,
                format="hh:mm", hourFormat="SYNC_TO_DEVICE", align="CENTER")
    node(time, "Variant", mode="AMBIENT", target="alpha", value=160)
    node(time, "Font", family=FONT, size=142, color=COLOR)

    # WFF 2 requires ComplicationSlot to be a direct child of Scene.
    interactive = scene

    # Four disjoint annular hit targets: they do not intercept the inner widgets.
    edges = [
        (1, "edge_top_left", 282, 348, 312, 346, 283, 310, "CLOCKWISE", "STEP_COUNT", "SHORT_TEXT", "STEPS"),
        (2, "edge_top_right", 12, 78, 31, 76, 12, 29, "CLOCKWISE", "WATCH_BATTERY", "RANGED_VALUE", "FLOORS"),
        (3, "edge_bottom_left", 192, 258, 224, 256, 222, 194, "COUNTER_CLOCKWISE", "EMPTY", "EMPTY", "KCAL"),
        (4, "edge_bottom_right", 102, 168, 144, 166, 140, 104, "COUNTER_CLOCKWISE", "EMPTY", "EMPTY", "DIST"),
    ]
    for sid, name, start, end, a1, a2, t1, t2, direction, provider, provider_type, hint in edges:
        slot = node(interactive, "ComplicationSlot", slotId=sid, displayName=name,
                    x=0, y=0, width=480, height=480,
                    supportedTypes="SHORT_TEXT RANGED_VALUE GOAL_PROGRESS EMPTY")
        ambient_hide(slot)
        node(slot, "BoundingArc", centerX=240, centerY=240, width=444, height=444,
             thickness=38, startAngle=start, endAngle=end, isRoundEdge="TRUE")
        node(slot, "DefaultProviderPolicy", defaultSystemProvider=provider, defaultSystemProviderType=provider_type)
        for kind in ("SHORT_TEXT", "RANGED_VALUE", "GOAL_PROGRESS", "EMPTY"):
            c = node(slot, "Complication", type=kind)
            arc(c, 240, 240, 444, a1, a2, TRACK, 10)
            if kind in ("RANGED_VALUE", "GOAL_PROGRESS"):
                arc(c, 240, 240, 444, a1, a2, ACCENT, 10, progress(kind))
            if kind == "EMPTY":
                circular_text(c, t1, t2, direction, hint, expression=False)
            else:
                complication_value(c, lambda p, v: circular_text(p, t1, t2, direction, v),
                                   kind == "RANGED_VALUE", kind == "GOAL_PROGRESS")

    for sid, name, x, hint in [(5, "circle_left", 66, "WEATHER"), (6, "circle_right", 308, "PULSE")]:
        slot = node(interactive, "ComplicationSlot", slotId=sid, displayName=name,
                    x=x, y=257, width=106, height=110,
                    supportedTypes="SHORT_TEXT RANGED_VALUE GOAL_PROGRESS MONOCHROMATIC_IMAGE EMPTY")
        ambient_hide(slot)
        node(slot, "BoundingOval", x=0, y=0, width=106, height=110, outlinePadding=4)
        node(slot, "DefaultProviderPolicy", defaultSystemProvider="EMPTY", defaultSystemProviderType="EMPTY")
        for kind in ("SHORT_TEXT", "RANGED_VALUE", "GOAL_PROGRESS", "MONOCHROMATIC_IMAGE", "EMPTY"):
            c = node(slot, "Complication", type=kind)
            # Arc helper uses a full local canvas; drawing coordinates remain within the slot.
            arc(c, 53, 53, 94, -145, 145, TRACK, 10)
            if kind in ("RANGED_VALUE", "GOAL_PROGRESS"):
                arc(c, 53, 53, 94, -145, 145, ACCENT, 10, progress(kind))
            if kind == "EMPTY":
                text(c, 9, 26, 88, 40, 32, "—")
                text(c, 7, 70, 92, 24, 13, hint, ACCENT)
            elif kind == "MONOCHROMATIC_IMAGE":
                p = node(c, "PartImage", x=31, y=29, width=44, height=44, tintColor=ACCENT)
                node(p, "Image", resource="[COMPLICATION.MONOCHROMATIC_IMAGE]")
            else:
                complication_value(c, lambda p, v: text(p, 12, 26, 82, 44, 32, v, expression=True),
                                   kind == "RANGED_VALUE", kind == "GOAL_PROGRESS")
                optional_icon(c, 43, 83, 20)

    slot = node(interactive, "ComplicationSlot", slotId=7, displayName="shortcut",
                x=194, y=325, width=92, height=92,
                supportedTypes="MONOCHROMATIC_IMAGE SMALL_IMAGE SHORT_TEXT EMPTY")
    ambient_hide(slot)
    node(slot, "BoundingOval", x=0, y=0, width=92, height=92, outlinePadding=3)
    node(slot, "DefaultProviderPolicy", defaultSystemProvider="EMPTY", defaultSystemProviderType="EMPTY")
    for kind in ("MONOCHROMATIC_IMAGE", "SMALL_IMAGE", "SHORT_TEXT", "EMPTY"):
        c = node(slot, "Complication", type=kind)
        p = node(c, "PartDraw", x=0, y=0, width=92, height=92)
        node(node(p, "Ellipse", x=0, y=0, width=92, height=92), "Fill", color=SURFACE)
        if kind == "SHORT_TEXT":
            text(c, 6, 26, 80, 40, 24, "[COMPLICATION.TEXT]", expression=True)
        else:
            p = node(c, "PartImage", x=24, y=24, width=44, height=44, tintColor=ACCENT)
            node(p, "Image", resource="add" if kind == "EMPTY" else f"[COMPLICATION.{kind}]")
    return root


if __name__ == "__main__":
    root = make_face()
    E.indent(root, space="    ")
    path = ROOT / "watchface/src/main/res/raw/watchface.xml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n'
                     b'<!-- Generated by tools/generate_face.py. Edit the generator, then regenerate. -->\n'
                     + E.tostring(root, encoding="utf-8") + b"\n")
    print(path.relative_to(ROOT))
