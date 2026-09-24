# Validation record

Checked locally on Windows 11 with JDK 17, Python 3.11, Android platform 36 and Build Tools 36.0.0.

- **Google WFF validator 1.7.0:** the final XML passes format version 2 with `--stop-on-fail`. The validator also rejected invalid element ordering and invalid slot nesting during development; both were corrected.
- **APK build:** the SDK-only pipeline compiled and linked Android resources, aligned the APK, signed it with the local Android debug key and passed `apksigner verify`.
- **Packaging:** `tools/check_apk.py` checks for no DEX code, required XML/font/image assets, unique complication IDs, complete supported-type rendering and compatible default providers.
- **Assets:** images were generated from the checked-in XML and bundled font, then visually reviewed. The first-install preview has empty health slots. The ambient preview contains time and date only. These are approximate layout renders, not Android screenshots.
- **Clock width:** all 1,440 HH:mm combinations are measured with the bundled font during preview generation. The initial font size clipped at midnight; it was reduced so even the widest time fits inside the clock's bounds.
- **Reproducibility:** Gradle/AGP/SDK versions, Gradle distribution checksum, validator checksum, font source revision and Python image dependency are recorded. The source XML and images are committed and regenerated in CI to detect drift. Preview text explicitly uses Pillow's BASIC layout engine on Windows and Linux. CI compares image pixels rather than compressed PNG bytes, because PNG compression libraries vary across platforms. Debug APKs are not promised to be byte-for-byte identical across different machines: signing keys and build metadata differ.

Local Gradle dependency resolution could not complete because `dl.google.com` timed out. GitHub Actions provides the separate Gradle build and lint check; consult its actual run status before assuming it passed. The SDK-only APK build does not require those Maven downloads.

No physical watch was connected and no Wear OS emulator was installed in this workspace, so device behavior has **not** been verified. Before treating this as a daily-use face, follow the README to check:

1. Installation, face selection and the built-in editor.
2. All seven tap targets, provider selection and live updates.
3. A short-text provider, a ranged-value provider and a goal-progress provider.
4. Long/empty values, missing provider images and unconfigured slots.
5. 12/24-hour time, your locale and both round watch sizes.
6. Always-on entry/exit, text clipping and battery use on the actual watch.

The official XSD validator checks structure, not every runtime expression, provider capability or visual detail. Expressions also follow the official complication sample data-source names and arithmetic-expression reference. The project has not undergone Google Play memory-footprint certification or release publishing checks.
