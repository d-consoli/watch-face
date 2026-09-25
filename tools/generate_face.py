"""Generate Ink & Paper: a resource-only WFF 2 face for Pixel Watch."""
from pathlib import Path
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
FONT = "outfit_regular"
INK, MUTED, RED, BLUE = "#292724", "#71665A", "#984832", "#3F5965"
FITBIT = "com.fitbit.FitbitMobile/"
TYPES = ("RANGED_VALUE", "GOAL_PROGRESS", "SHORT_TEXT", "EMPTY")
STEP_GOAL = 10000
STEP_NUMBER = '[STEP_COUNT] >= 1000 ? numberFormat("0.0", [STEP_COUNT] / 1000) : numberFormat("0", [STEP_COUNT])'
STEP_UNIT = '[STEP_COUNT] >= 1000 ? "k" : ""'
BATTERY_START, STEPS_START, GAUGE_SWEEP = 8, 52, 36


def node(parent, tag, **attrs):
    return E.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def ambient_hide(parent):
    node(parent, "Variant", mode="AMBIENT", target="alpha", value=0)


def text(parent, x, y, w, h, size, value, color=INK, expression=False, align="START", pattern="%s"):
    p = node(parent, "PartText", x=x, y=y, width=w, height=h)
    t = node(p, "Text", align=align, ellipsis="TRUE", maxLines=1)
    f = node(t, "Font", family=FONT, size=size, color=color)
    if expression:
        template = node(f, "Template")
        template.text = pattern
        for field in value if isinstance(value, tuple) else (value,):
            node(template, "Parameter", expression=field)
    else:
        f.text = value
    return p


def picture(parent, x, y, w, h, resource, **attrs):
    p = node(parent, "PartImage", x=x, y=y, width=w, height=h, **attrs)
    node(p, "Image", resource=resource)
    return p


def ink_picture(parent, x, y, w, h, resource, color, name):
    """Color a painting through its alpha, without multiplying its dark RGB."""
    g = node(parent, "Group", name=name, x=x, y=y, width=w, height=h)
    draw = node(g, "PartDraw", x=0, y=0, width=w, height=h)
    rect = node(draw, "Rectangle", x=0, y=0, width=w, height=h)
    node(rect, "Fill", color=color)
    picture(g, 0, 0, w, h, resource, renderMode="MASK")
    return g


def crown(parent, name, radius, color, fraction=None, alpha=255, start=BATTERY_START, sweep=GAUGE_SWEEP):
    """Native colored arc clipped by the original painting's alpha texture."""
    g = node(parent, "Group", name=name, x=0, y=0, width=480, height=480)
    ambient_hide(g)
    # The packaged brush has a 222-unit centerline; keep the same circular center.
    size = round(480 * radius / 222)
    inset = (480 - size) // 2
    picture(g, inset, inset, size, size, "painted_arc", renderMode="MASK", alpha=alpha)
    draw = node(g, "PartDraw", x=0, y=0, width=480, height=480)
    arc = node(draw, "Arc", centerX=240, centerY=240, width=radius*2, height=radius*2,
               startAngle=start, endAngle=start+sweep)
    node(arc, "Stroke", color=color, thickness=10, cap="BUTT")
    if fraction is not None:
        node(arc, "Transform", target="endAngle", value=f"{start} + {sweep} * ({fraction})")
    return g


def step_progress():
    # Only the visual fill is capped; the displayed daily count remains unbounded.
    return f"clamp([STEP_COUNT] / {STEP_GOAL}, 0, 1)"


def value(kind):
    if kind == "EMPTY":
        return '"SET UP"'
    if kind == "SHORT_TEXT":
        return '[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : "—"'
    field = "GOAL_PROGRESS_VALUE" if kind == "GOAL_PROGRESS" else "RANGED_VALUE_VALUE"
    return f'[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : numberFormat("0", [COMPLICATION.{field}])'


def slot(scene, sid, label, x, y, w, h, types, primary, primary_type,
         secondary=None, system="EMPTY", system_type="EMPTY", bounds=None):
    s = node(scene, "ComplicationSlot", slotId=sid, displayName=label,
             x=x, y=y, width=w, height=h, supportedTypes=" ".join(types))
    ambient_hide(s)
    bx, by, bw, bh = bounds or (0, 0, w, h)
    node(s, "BoundingBox", x=bx, y=by, width=bw, height=bh, outlinePadding=2)
    policy = dict(defaultSystemProvider=system, defaultSystemProviderType=system_type)
    if primary:
        policy.update(primaryProvider=primary, primaryProviderType=primary_type)
    if secondary:
        policy.update(secondaryProvider=secondary, secondaryProviderType=primary_type)
    node(s, "DefaultProviderPolicy", **policy)
    return s


def clock_and_date(scene, ambient=False):
    g = node(scene, "Group", name="ambient_clock" if ambient else "active_clock", x=0, y=0, width=480, height=480, alpha=0 if ambient else 255)
    node(g, "Variant", mode="AMBIENT", target="alpha", value=255 if ambient else 0)
    color = "#BAB6AE" if ambient else INK
    p = text(g, 120, 59, 240, 34, 24,
             ("[DAY_OF_WEEK_S]", "[DAY]"), color, expression=True, align="CENTER", pattern="%s  %s")
    node(p, "Launch", target="CALENDAR")
    clock = node(g, "DigitalClock", x=91, y=102, width=286, height=110)
    t = node(clock, "TimeText", x=0, y=0, width=286, height=110,
             format="hh:mm", hourFormat="SYNC_TO_DEVICE", align="CENTER")
    node(t, "Font", family=FONT, size=94, color=color)


def custom_slot(scene, sid, name, x, width, primary=None, legacy=None, calories=False):
    kinds = TYPES + ("LONG_TEXT", "MONOCHROMATIC_IMAGE", "SMALL_IMAGE")
    s = slot(scene, sid, name, x, 211 if calories else 228, width,
             72 if calories else 55, kinds, primary, "RANGED_VALUE", legacy)
    for kind in kinds:
        c = node(s, "Complication", type=kind)
        if calories:
            text(c, 0, 0, width, 17, 13, "KCAL", MUTED)
        offset = 17 if calories else 0
        if kind == "MONOCHROMATIC_IMAGE":
            ink_picture(c, 0, offset+6, 36, 36, f"[COMPLICATION.{kind}]", INK, f"custom_icon_{sid}")
        elif kind == "SMALL_IMAGE":
            picture(c, 0, offset+6, 36, 36, f"[COMPLICATION.{kind}]")
        elif kind == "EMPTY":
            text(c, 0, offset, width, 55, 34, "")
        else:
            expression = value(kind) if kind != "LONG_TEXT" else "[COMPLICATION.TEXT]"
            text(c, 0, offset, width, 55, 26 if kind == "LONG_TEXT" else 34, expression, expression=True)
    return s


def make_face():
    root = E.Element("WatchFace", width="480", height="480")
    node(root, "Metadata", key="CLOCK_TYPE", value="DIGITAL")
    node(root, "Metadata", key="PREVIEW_TIME", value="10:09:00")
    scene = node(root, "Scene", backgroundColor="#000000")
    p = picture(scene, 0, 0, 480, 480, "painted_paper")
    p.insert(0, E.Element("Variant", mode="AMBIENT", target="alpha", value="0"))
    # Outer edge remains at least 13 design units inside the round display.
    # Two 36-degree arcs, both in the upper-right quarter, clear of the ink.
    crown(scene, "battery_track", 222, BLUE, alpha=50)
    crown(scene, "steps_track", 222, RED, alpha=50, start=STEPS_START)
    crown(scene, "battery_progress", 222, BLUE, "clamp([BATTERY_PERCENT] / 100, 0, 1)")
    crown(scene, "steps_progress", 222, RED, step_progress(), start=STEPS_START)
    clock_and_date(scene)
    clock_and_date(scene, ambient=True)

    g = node(scene, "Group", name="edge_values", x=0, y=0, width=480, height=480)
    ambient_hide(g)
    p = ink_picture(g, 231, 22, 25, 15, "painted_battery", BLUE, "battery_icon")
    node(p, "Launch", target="BATTERY_STATUS")
    p = text(g, 281, 41, 51, 22, 16, "[BATTERY_PERCENT]", BLUE, expression=True, pattern="%s%%")
    node(p, "Launch", target="BATTERY_STATUS")
    p = ink_picture(g, 400, 139, 22, 24, "painted_steps", RED, "steps_icon")
    node(p, "Launch", target="com.fitbit.FitbitMobile")
    p = text(g, 379, 167, 67, 24, 16, (STEP_NUMBER, STEP_UNIT), RED, expression=True, align="CENTER", pattern="%s%s")
    node(p, "Launch", target="com.fitbit.FitbitMobile")

    # Card moves 24 units up from its original position. The lower-left ink stays
    # clear; the heart/value pair is centered in the open paper below the data row.
    labels = node(scene, "Group", name="labels", x=0, y=0, width=480, height=480)
    ambient_hide(labels)
    picture(labels, 335, 354, 58, 36, "painted_card")

    # Preserve the original five slots' order so saved provider assignments survive.
    custom_slot(scene, 101, "calories", 334, 110,
                FITBIT+"com.google.android.wearable.fitbit.mainapp.complications.offloadable.calories.OffloadableCaloriesComplicationDataSourceService",
                FITBIT+"com.fitbit.complications.calories.CaloriesComplicationDataSourceService", calories=True)
    custom_slot(scene, 102, "custom_left", 118, 100)

    s = slot(scene, 103, "pulse", 202, 299, 126, 63, ("RANGED_VALUE", "SHORT_TEXT", "EMPTY"),
             FITBIT+"com.fitbit.complications.offloadable.heartrate.OffloadableHeartRateComplicationDataSourceService",
             "RANGED_VALUE", FITBIT+"com.fitbit.complications.heartrate.HeartRateComplicationDataSourceService")
    for kind in ("RANGED_VALUE", "SHORT_TEXT", "EMPTY"):
        c = node(s, "Complication", type=kind)
        p = picture(c, 0, 21, 28, 28, "painted_heart")
        if kind != "EMPTY":
            # Decorative double beat, not a sensor-synchronized medical pulse.
            beat = "1 + 0.14 * pow(sin([SECOND_MILLISECOND] * 6.283185), 8)"
            for axis in ("scaleX", "scaleY"):
                p.insert(0, E.Element("Transform", target=axis, value=beat))
        text(c, 38, 9, 88, 45, 17 if kind == "EMPTY" else 36, value(kind), RED, expression=True)

    s = slot(scene, 104, "calendar", 146, 392, 201, 47, ("LONG_TEXT", "SHORT_TEXT", "EMPTY"),
             "com.google.android.calendar/com.google.android.apps.calendar.wear.complication.NextEventComplicationService",
             "LONG_TEXT", system="NEXT_EVENT", system_type="LONG_TEXT")
    for kind in ("LONG_TEXT", "SHORT_TEXT", "EMPTY"):
        c = node(s, "Complication", type=kind)
        if kind == "EMPTY":
            text(c, 0, 0, 201, 19, 15, "CALENDAR", MUTED)
            p = text(c, 0, 19, 201, 27, 21, "Tap to open")
            node(p, "Launch", target="CALENDAR")
        else:
            text(c, 0, 0, 201, 19, 15, '[COMPLICATION.TITLE] != null ? [COMPLICATION.TITLE] : "NEXT EVENT"', MUTED, expression=True)
            text(c, 0, 19, 201, 27, 21, '[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : "No events"', expression=True)

    s = slot(scene, 105, "shortcut", 335, 348, 58, 49,
             ("MONOCHROMATIC_IMAGE", "SMALL_IMAGE", "SHORT_TEXT", "EMPTY"),
             "com.google.android.apps.walletnfcrel/com.google.commerce.tapandpay.wear.complications.WearWalletProviderService",
             "SMALL_IMAGE", system="APP_SHORTCUT", system_type="MONOCHROMATIC_IMAGE")
    for kind in ("MONOCHROMATIC_IMAGE", "SMALL_IMAGE", "SHORT_TEXT", "EMPTY"):
        c = node(s, "Complication", type=kind)
        p = picture(c, 0, 6, 58, 36, "painted_card")
        if kind == "EMPTY":
            node(p, "Launch", target="com.google.android.apps.walletnfcrel")
    # Append instead of inserting: Wear OS persists provider choices by slot order.
    custom_slot(scene, 106, "custom_middle", 226, 100)
    return root


if __name__ == "__main__":
    root = make_face()
    E.indent(root, space="    ")
    path = ROOT / "watchface/src/main/res/raw/watchface.xml"
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n'
                     b'<!-- Generated by tools/generate_face.py. -->\n'
                     + E.tostring(root, encoding="utf-8") + b"\n")
    print(path.relative_to(ROOT))
