"""Generate Ink & Paper: a resource-only WFF 2 face for Pixel Watch."""
from pathlib import Path
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
FONT = "outfit_regular"
INK, MUTED, RED, BLUE = "#292724", "#71665A", "#984832", "#3F5965"
FITBIT = "com.fitbit.FitbitMobile/"
TYPES = ("RANGED_VALUE", "GOAL_PROGRESS", "SHORT_TEXT", "EMPTY")


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


def crown(parent, name, radius, color, fraction=None, alpha=255, start=12, sweep=72):
    """Short painted perimeter gauge, revealed by an invisible native arc mask."""
    g = node(parent, "Group", name=name, x=0, y=0, width=480, height=480)
    ambient_hide(g)
    # The packaged brush has a 222-unit centerline; keep the same circular center.
    size = round(480 * radius / 222)
    inset = (480 - size) // 2
    picture(g, inset, inset, size, size, "painted_arc", tintColor=color, alpha=alpha)
    mask = node(g, "PartDraw", x=0, y=0, width=480, height=480, renderMode="MASK")
    arc = node(mask, "Arc", centerX=240, centerY=240, width=radius*2, height=radius*2,
               startAngle=start, endAngle=start+sweep)
    node(arc, "Stroke", color="#FFFFFF", thickness=10, cap="BUTT")
    if fraction is not None:
        node(arc, "Transform", target="endAngle", value=f"{start} + {sweep} * ({fraction})")
    return g


def progress(kind):
    if kind == "GOAL_PROGRESS":
        return "[COMPLICATION.GOAL_PROGRESS_TARGET_VALUE] > 0 ? clamp([COMPLICATION.GOAL_PROGRESS_VALUE] / [COMPLICATION.GOAL_PROGRESS_TARGET_VALUE], 0, 1) : 0"
    return "[COMPLICATION.RANGED_VALUE_MAX] > [COMPLICATION.RANGED_VALUE_MIN] ? clamp(([COMPLICATION.RANGED_VALUE_VALUE] - [COMPLICATION.RANGED_VALUE_MIN]) / ([COMPLICATION.RANGED_VALUE_MAX] - [COMPLICATION.RANGED_VALUE_MIN]), 0, 1) : 0"


def value(kind):
    if kind == "EMPTY":
        return "'SET UP'"
    if kind == "SHORT_TEXT":
        return "[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : '—'"
    field = "GOAL_PROGRESS_VALUE" if kind == "GOAL_PROGRESS" else "RANGED_VALUE_VALUE"
    return f"[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : numberFormat('0', [COMPLICATION.{field}])"


def slot(scene, sid, label, x, y, w, h, types, primary, primary_type,
         secondary=None, system="EMPTY", system_type="EMPTY", bounds=None):
    s = node(scene, "ComplicationSlot", slotId=sid, displayName=label,
             x=x, y=y, width=w, height=h, supportedTypes=" ".join(types))
    ambient_hide(s)
    bx, by, bw, bh = bounds or (0, 0, w, h)
    node(s, "BoundingBox", x=bx, y=by, width=bw, height=bh, outlinePadding=2)
    policy = dict(primaryProvider=primary, primaryProviderType=primary_type,
                  defaultSystemProvider=system, defaultSystemProviderType=system_type)
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
    clock = node(g, "DigitalClock", x=89, y=102, width=302, height=110)
    t = node(clock, "TimeText", x=0, y=0, width=302, height=110,
             format="hh:mm", hourFormat="SYNC_TO_DEVICE", align="CENTER")
    node(t, "Font", family=FONT, size=100, color=color)


def make_face():
    root = E.Element("WatchFace", width="480", height="480")
    node(root, "Metadata", key="CLOCK_TYPE", value="DIGITAL")
    node(root, "Metadata", key="PREVIEW_TIME", value="10:09:00")
    scene = node(root, "Scene", backgroundColor="#000000")
    p = picture(scene, 0, 0, 480, 480, "painted_paper")
    p.insert(0, E.Element("Variant", mode="AMBIENT", target="alpha", value="0"))
    # Outer edge remains at least 13 design units inside the round display.
    # Two separate 72-degree arcs (20% of a turn), clear of the left ink crescent.
    crown(scene, "battery_track", 222, BLUE, alpha=50)
    crown(scene, "calories_track", 222, RED, alpha=50, start=96)
    crown(scene, "battery_progress", 222, BLUE, "clamp([BATTERY_PERCENT] / 100, 0, 1)")
    clock_and_date(scene)
    clock_and_date(scene, ambient=True)

    g = node(scene, "Group", name="battery", x=118, y=211, width=124, height=67)
    ambient_hide(g)
    text(g, 0, 0, 124, 21, 16, "BATTERY", BLUE)
    p = text(g, 0, 20, 124, 35, 30, "[BATTERY_PERCENT]", BLUE, expression=True, pattern="%s%%")
    node(p, "Launch", target="BATTERY_STATUS")

    # Keep labels and the card painting visible even when the OS suppresses an
    # unconfigured/locked complication altogether. Live values stay in their slots.
    labels = node(scene, "Group", name="labels", x=0, y=0, width=480, height=480)
    ambient_hide(labels)
    text(labels, 272, 211, 124, 21, 16, "KCAL", RED)
    text(labels, 118, 290, 124, 21, 16, "STEPS", MUTED)
    text(labels, 272, 290, 124, 21, 16, "PULSE · BPM", MUTED)
    picture(labels, 318, 362, 50, 31, "painted_card")

    # Stable IDs for this layout. Wear OS may still retain providers by slot order
    # when upgrading the prototype; configure those slots or add a fresh instance.
    for sid, name, x, y, label, modern, legacy in [
        (101, "calories", 272, 211, "KCAL", "com.google.android.wearable.fitbit.mainapp.complications.offloadable.calories.OffloadableCaloriesComplicationDataSourceService", "com.fitbit.complications.calories.CaloriesComplicationDataSourceService"),
        (102, "steps", 118, 290, "STEPS", "com.fitbit.complications.offloadable.steps.OffloadableStepsComplicationDataSourceService", "com.fitbit.complications.steps.StepsComplicationDataSourceService"),
    ]:
        # Full drawing canvas for the calorie ring, but only its numeric tile is
        # tappable. Other complications retain their own disjoint hit targets.
        canvas = (0, 0, 480, 480) if sid == 101 else (x, y, 124, 67)
        s = slot(scene, sid, name, *canvas, TYPES, FITBIT+modern, "RANGED_VALUE", FITBIT+legacy,
                 "STEP_COUNT" if sid == 102 else "EMPTY", "SHORT_TEXT" if sid == 102 else "EMPTY",
                 bounds=(x, y, 124, 67) if sid == 101 else None)
        for kind in TYPES:
            c = node(s, "Complication", type=kind)
            tx, ty = (x, y+20) if sid == 101 else (0, 20)
            text(c, tx, ty, 124, 35, 19 if kind == "EMPTY" else 30, value(kind), RED if sid == 101 else INK, expression=True)
            if sid == 101 and kind in ("RANGED_VALUE", "GOAL_PROGRESS"):
                crown(c, f"calories_{kind.lower()}", 222, RED, progress(kind), start=96)

    s = slot(scene, 103, "pulse", 272, 290, 124, 67, ("RANGED_VALUE", "SHORT_TEXT", "EMPTY"),
             FITBIT+"com.fitbit.complications.offloadable.heartrate.OffloadableHeartRateComplicationDataSourceService",
             "RANGED_VALUE", FITBIT+"com.fitbit.complications.heartrate.HeartRateComplicationDataSourceService")
    for kind in ("RANGED_VALUE", "SHORT_TEXT", "EMPTY"):
        c = node(s, "Complication", type=kind)
        p = picture(c, 0, 28, 28, 28, "painted_heart")
        if kind != "EMPTY":
            # Decorative double beat, not a sensor-synchronized medical pulse.
            beat = "1 + 0.14 * pow(sin([SECOND_MILLISECOND] * 6.283185), 8)"
            for axis in ("scaleX", "scaleY"):
                p.insert(0, E.Element("Transform", target=axis, value=beat))
        text(c, 39, 20, 85, 39, 17 if kind == "EMPTY" else 30, value(kind), RED, expression=True)

    s = slot(scene, 104, "calendar", 130, 367, 180, 49, ("LONG_TEXT", "SHORT_TEXT", "EMPTY"),
             "com.google.android.calendar/com.google.android.apps.calendar.wear.complication.NextEventComplicationService",
             "LONG_TEXT", system="NEXT_EVENT", system_type="LONG_TEXT")
    for kind in ("LONG_TEXT", "SHORT_TEXT", "EMPTY"):
        c = node(s, "Complication", type=kind)
        if kind == "EMPTY":
            text(c, 52, 0, 128, 19, 14, "CALENDAR", MUTED)
            p = text(c, 0, 23, 180, 26, 20, "Tap to open")
            node(p, "Launch", target="CALENDAR")
        else:
            text(c, 52, 0, 128, 19, 14, "[COMPLICATION.TITLE] != null ? [COMPLICATION.TITLE] : 'NEXT EVENT'", MUTED, expression=True)
            text(c, 0, 23, 180, 26, 20, "[COMPLICATION.TEXT] != null ? [COMPLICATION.TEXT] : 'No events'", expression=True)

    s = slot(scene, 105, "shortcut", 318, 360, 50, 35,
             ("MONOCHROMATIC_IMAGE", "SMALL_IMAGE", "SHORT_TEXT", "EMPTY"),
             "com.google.android.apps.walletnfcrel/com.google.commerce.tapandpay.wear.complications.WearWalletProviderService",
             "SMALL_IMAGE", system="APP_SHORTCUT", system_type="MONOCHROMATIC_IMAGE")
    for kind in ("MONOCHROMATIC_IMAGE", "SMALL_IMAGE", "SHORT_TEXT", "EMPTY"):
        c = node(s, "Complication", type=kind)
        p = picture(c, 0, 2, 50, 31, "painted_card")
        if kind == "EMPTY":
            node(p, "Launch", target="com.google.android.apps.walletnfcrel")
    return root


if __name__ == "__main__":
    root = make_face()
    E.indent(root, space="    ")
    path = ROOT / "watchface/src/main/res/raw/watchface.xml"
    path.write_bytes(b'<?xml version="1.0" encoding="utf-8"?>\n'
                     b'<!-- Generated by tools/generate_face.py. -->\n'
                     + E.tostring(root, encoding="utf-8") + b"\n")
    print(path.relative_to(ROOT))
