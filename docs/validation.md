# Validation record · 0.3.0

The perimeter revision replaces the three straight tracks with two painted 72-degree arcs on the right: battery at 12–84 degrees and calories at 96–168 degrees. Steps retains its numeric count. Both arc centerlines use radius 222 on the 480px design canvas, with a 10-unit stroke mask, leaving at least 13 units inside the display edge. No gauge enters the left artwork region.

The preview renderer now implements WFF group clipping masks, includes a full-gauges fixture, and checks padded text/icon bounds against the complete gauge lanes and the round display. The widest of all 1,440 clock strings and the heart's maximum animated size are included. These checks pass for active, ambient, empty and full-gauge previews. The clock, calendar and card were repositioned to preserve clear space.

This revision passes official WFF 2 validation and the SDK-only APK build/inspection locally. The watch disconnected from ADB during this revision, so 0.3 has not yet been installed or checked on hardware. The 0.2 runtime/provider issues below remain pending a connected, unlocked watch.

Commit `655ea14` also passed the full [GitHub Actions run](https://github.com/d-consoli/watch-face/actions/runs/36111302646): cross-platform generated-file checks, WFF validation, Gradle build and lint, SDK-only build, and inspection of both APKs.

## Previous hardware evidence · 0.2.0

Environment: Windows 11, Python 3.11, JDK 17, SDK platform 36 / Build Tools 36.0.0. Hardware: connected Pixel Watch 4 (meridian_lte), API 37, 426 × 426 display.

- Official Google WFF validator **1.7.0**, format 2: passes.
- SDK-only AAPT2 build, zip alignment and APK v3 signature verification: passes.
- APK inspection: no DEX, all required XML/font/painted assets present, unique slots and complete type branches.
- Hardware install with `python tools/build_apk.py --install --serial 172.20.10.39:43389`: **Success**.
- Static previews: active, ambient and missing-provider states generated from actual XML. All 1,440 digital times fit the clock width. Pictures use checked-in source rasters, with transparency retained. Preview rendering uses pinned Pillow and explicit BASIC font layout for consistent Windows/Linux pixels.
- Fitbit default services were discovered on the connected watch. Their installed manifest supports the requested ranged-value types; Calendar supports long text. Modern and legacy Fitbit components are configured as primary/secondary defaults.
- The watch runtime loaded `io.github.dconsoli.modular 0.2.0 (2)` with all five intended slot policies. However, it remapped slots to internal IDs 11–15 and retained old steps/battery assignments in the first two positions. Changing XML IDs did not reset saved selections. The README documents adding a new instance or reassigning all five slots in Edit.
- A locked-face screenshot confirmed the painted background, large clock and inset battery/progress geometry on the 426px display. It exposed a WFF expression issue with concatenated weekday/percent text; those have been replaced with multi-parameter/literal-suffix Templates. Labels and card art also now remain visible independently of unavailable complication data.
- Unlocking is still needed to reconfigure old provider assignments and verify live health/calendar readings, animation and taps. A successful install and loaded runtime are not confirmation of those behaviors.

The final 0.2 implementation and text fixes at commit `36b786a` passed generated XML/image comparisons, official validation, Gradle build, Android lint and both APK checks on [GitHub Actions](https://github.com/d-consoli/watch-face/actions/runs/36068107640). That same source is installed on the watch. Local Maven downloads have timed out; the SDK-only build works offline.

Still requiring device coverage: first-provider permission/setup behavior; actual calories/steps/pulse and refresh; calendar event/no-event display; card target editing/tap; heartbeat animation; ambient transitions; both round watch sizes and extended battery use. Personal on-device screenshots remain ignored under `captures/`.

The validator is structural, not a complete expression/runtime validator. AI artwork is reproduced by using committed originals, not by re-running prompts. Debug APK bytes can differ across build machines because signing keys and metadata differ. Google Play memory certification and release publishing are outside this development build.
