# Third-party notices and provenance

## Gradle wrapper

`gradlew`, `gradlew.bat`, and `gradle/wrapper/gradle-wrapper.jar` were obtained from Google's Apache-2.0-licensed [wear-os-samples](https://github.com/android/wear-os-samples/tree/06cdb24caf15ea670256b28cd3861987e3e4790e/WatchFaceFormat/SimpleDigital) at commit `06cdb24caf15ea670256b28cd3861987e3e4790e`. Copyright and license headers are retained in the scripts. The wrapper distribution was configured for Gradle 9.3.1 with the official SHA-256 checksum. Wrapper JAR SHA-256: `76805e32c009c0cf0dd5d206bddc9fb22ea42e84db904b764f3047de095493f3`.

The Android sample code and WFF schema were consulted for API usage. This repository's watch-face layout and tooling are independently authored. The root LICENSE contains Apache License 2.0.

## Outfit font

Copyright 2021 The Outfit Project Authors (https://github.com/Outfitio/Outfit-Fonts).

The font is distributed under the SIL Open Font License, Version 1.1. Full license: [`assets/fonts/OFL-Outfit.txt`](assets/fonts/OFL-Outfit.txt).

Source: [`ofl/outfit/Outfit[wght].ttf` in google/fonts](https://github.com/google/fonts/tree/8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5/ofl/outfit), pinned commit `8b0a1d0f5983c89bc2b93f1b5fb55f9e252744b5`. The bundled `watchface/src/main/res/font/outfit_regular.ttf` is a static instance at weight 400. It is checked in, so rebuilding the face does not require downloading or processing the font.

To recreate that static instance, download the pinned variable font and run FontTools 4.63.0's `instantiateVariableFont(TTFont(path), {'wght': 400}, inplace=True).save(output_path)`. The checked-in static font SHA-256 is `ea641f9a621c734b59f08e7366ed1fc562de81d1c2051351e59093b185fd33ee`. The font's actual appearance is distinct from Google's shipping watch-face typography.

## WFF validator

`tools/validate.py` downloads the official [google/watchface validator](https://github.com/google/watchface/releases/tag/release) to the ignored `.cache/` directory. The JAR reports version 1.7.0. Its SHA-256 is pinned to `28b244289ab748bb2b07017e9f3c06bb76bdf165d6fa55652a5dc64b852c3121`; a changed download fails verification before execution. Upstream is Apache-2.0 with its dependency notices. The validator JAR is not distributed in this repository.

## Visual reference and original assets

The public [Modular image in Android Authority's gallery](https://www.androidauthority.com/google-pixel-watch-4-watch-faces-apk-teardown-3603416/) informed the arrangement. It is not included in the repository or APK. This project is not affiliated with Google. Product names identify the test target and visual reference.

The plus icon and all generated preview PNGs are original geometric renders from `tools/render_preview.py`. Demo values are fixtures, not recordings of personal health data.
