# Validation record · 0.4.0

Tested on 2026-09-25 with Windows 11, Python 3.11, JDK 17, SDK platform 36 and Build Tools 36.0.0. Hardware: Pixel Watch 4 (meridian_lte), API 37, 426 × 426 display.

## Layout and data

- Two 36-degree painted arcs at 8–44 degrees (battery) and 52–88 degrees (steps), measured clockwise from the top. Radius 222 plus half the 10-unit stroke leaves at least 13 design units inside the 480-unit circular display.
- Battery and footsteps icons use the exact gauge colors. Native colored shapes are masked by the original painting's alpha. Testing exposed that image tint multiplies bitmap RGB, making dark artwork too dark; this mask approach fixes the physical rendering as well as the preview.
- Steps uses the native daily `STEP_COUNT`. The bar is `clamp(STEP_COUNT / 10000, 0, 1)`. The counter remains uncapped, with one decimal in thousands from 1,000. Cases 0, 999, 1,000, 1,213, 5,000, 10,000, 12,500 and 50,000 are checked by the preview renderer.
- WFF string literals now use double quotes. A previous single-quoted DecimalFormat pattern produced a literal leading zero on the watch. The final on-device counter correctly displays `1,2k` in the watch's locale, without that zero.
- Two unlabeled custom slots and calories form a three-column row. Heart/value are centered below it, the calendar has moved right, and the painted card has moved up. The lower-left ink area stays clear.
- The new middle custom slot is appended after the original five slots to preserve their persisted provider order. It defaults to empty. Six editable slots total.

## Completed checks

- Official Google WFF validator **1.7.0**, format 2: passes.
- SDK-only AAPT2 build, zip alignment and APK v3 signature verification: passes.
- APK inspection: no DEX; all required XML/font/painted assets present; unique slot IDs and complete branches for supported types.
- Static previews: active, ambient, missing providers, zero values and above-goal values. Generated from the actual XML, with pinned Pillow and BASIC font layout for consistent Windows/Linux pixels.
- Geometry checks: padded glyph/icon bounds stay within the round display and outside the full gauge lanes and lower-left ink area. All 1,440 clock strings fit; heart maximum animated size is included.
- Installation of the final 0.4.0 build through the connected mDNS ADB serial: **Success**.
- Unlocked hardware screenshots confirm the shorter arcs, matching colors, small edge readings, restored KCAL label, larger row readings, centered heart, shifted calendar/card, and raised battery icon.
- Existing weather, Fitbit calories/heart rate, Calendar and supermarket-card shortcut assignments were retained. The newly added middle slot appears blank as intended.
- Successive live screenshots showed changing heart-rate and calorie readings. Eight captured frames yielded seven distinct heart-region images, confirming that the heartbeat animation runs on hardware.

The heartbeat is decorative, not synchronized to individual sensor beats. Native steps and provider health readings follow their respective system/provider refresh cadence. Sample preview values are never shipped as live data.

## Remaining coverage

First-use provider permissions, changing the new custom slot, shortcut/calendar tap behavior, ambient transitions, the other round watch size and extended battery use have not been fully exercised in this revision. The static ambient fixture passes; it is not a hardware battery-life test. Personal screenshots and runtime dumps remain ignored under `captures/` and `.cache/`.

The validator checks structure rather than all expressions and runtime behavior. Local Maven downloads have timed out, so Gradle build/lint run through the repository's GitHub Actions workflow. CI also regenerates XML/images, validates WFF, builds via the SDK-only path and inspects both APKs. Previous 0.3 passed [this full run](https://github.com/d-consoli/watch-face/actions/runs/36111302646); check the latest commit's Actions status for this revision.

Artwork reproduction uses the committed source images and exact preparation code, not fresh AI generations. Debug APK bytes can differ between machines because signing keys and metadata differ. Google Play memory certification and release publishing are outside this development build.
