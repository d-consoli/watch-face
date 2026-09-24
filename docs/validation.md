# Validation record · 0.2.0

Environment: Windows 11, Python 3.11, JDK 17, SDK platform 36 / Build Tools 36.0.0. Hardware: connected Pixel Watch 4 (meridian_lte), API 37, 426 × 426 display.

- Official Google WFF validator **1.7.0**, format 2: passes.
- SDK-only AAPT2 build, zip alignment and APK v3 signature verification: passes.
- APK inspection: no DEX, all required XML/font/painted assets present, unique slots and complete type branches.
- Hardware install with `python tools/build_apk.py --install --serial 172.20.10.39:43389`: **Success**.
- Static previews: active, ambient and missing-provider states generated from actual XML. All 1,440 digital times fit the clock width. Pictures use checked-in source rasters, with transparency retained. Preview rendering uses pinned Pillow and explicit BASIC font layout for consistent Windows/Linux pixels.
- Fitbit default services were discovered on the connected watch. Their installed manifest supports the requested ranged-value types; Calendar supports long text. Modern and legacy Fitbit components are configured as primary/secondary defaults.
- The watch runtime loaded `io.github.dconsoli.modular 0.2.0 (2)` with all five intended slot policies. However, it remapped slots to internal IDs 11–15 and retained old steps/battery assignments in the first two positions. Changing XML IDs did not reset saved selections. The README documents adding a new instance or reassigning all five slots in Edit.
- Visual/tap verification is in progress: the watch was locked immediately after installation. A successful install and loaded runtime are not confirmation that every data provider, animation or tap action works.

The previous 0.1 prototype passed Gradle build, Android lint and both APK checks on [GitHub Actions](https://github.com/d-consoli/watch-face/actions/runs/36060023490). That result does not certify the 0.2 layout. Local Maven downloads have timed out; the SDK-only build works offline.

Still requiring device coverage: first-provider permission/setup behavior; actual calories/steps/pulse and refresh; calendar event/no-event display; card target editing/tap; heartbeat animation; ambient transitions; both round watch sizes and extended battery use. Personal on-device screenshots remain ignored under `captures/`.

The validator is structural, not a complete expression/runtime validator. AI artwork is reproduced by using committed originals, not by re-running prompts. Debug APK bytes can differ across build machines because signing keys and metadata differ. Google Play memory certification and release publishing are outside this development build.
