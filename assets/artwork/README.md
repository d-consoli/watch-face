# Ink & Paper artwork

Five original raster paintings generated with Codex's built-in image generation tool on 2026-09-25. The user's ZENFORM reference was used for general material/style direction: warm paper, dry ink and muted watercolor. No commercial face artwork, font, screenshot or APK is redistributed.

- `paper-source.png`: full-resolution paper and ink background.
- `card-source.png`: ochre loyalty-card painting, with transparency.
- `heart-source.png`: vermilion brush heart, with transparency.
- `stroke-source.png`: original straight stroke, retained as the style reference for the curved revision.
- `arc-source.png`: transparent semicircular dry-brush stroke. Its exact built-in image generation prompt is in [arc-prompt.txt](arc-prompt.txt).
- [prompts.json](prompts.json): exact prompts for all four assets. The background was the style reference for the three icon calls.
- [SHA256SUMS](SHA256SUMS): source-file integrity hashes.

These source PNGs are the reproducible inputs. Repeating an AI prompt will produce different pixels. No model call or API key is required to rebuild this project.

`python tools/prepare_artwork.py` crops padding and resamples four active paintings into Android resources using Pillow's Lanczos filter. For the arc, alpha below 8/255 is ignored only when measuring padding, to avoid stray export noise; alpha inside the crop is preserved. The original source stays untouched. `python tools/render_preview.py` invokes preparation automatically. WFF tints the curved painting and uses a native arc as an invisible clipping mask to reveal two separate 72-degree progress gauges. The mask also enforces their safe outer boundary. No AI call is needed during a build.

The source assets and generated Android resources are included under the project's Apache-2.0 license, to the extent copyright applies. The font has its separate SIL OFL license.
