# Ink & Paper artwork

Seven original raster paintings generated with Codex's built-in image generation tool on 2026-09-25. The user's ZENFORM reference was used for general material/style direction: warm paper, dry ink and muted watercolor. No commercial face artwork, font, screenshot or APK is redistributed.

- `paper-source.png`: full-resolution paper and ink background.
- `card-source.png`: ochre loyalty-card painting, with transparency.
- `heart-source.png`: vermilion brush heart, with transparency.
- `stroke-source.png`: original straight stroke, retained as the style reference for the curved revision.
- `arc-source.png`: transparent semicircular dry-brush stroke. Its exact built-in image generation prompt is in [arc-prompt.txt](arc-prompt.txt).
- `battery-source.png`: refined slate-blue battery silhouette with a lightning cutout, with transparency.
- `steps-source.png`: terracotta painted footprints, with transparency.
- [prompts.json](prompts.json): exact prompts for the first four assets. The background was the style reference for the three icon calls.
- [edge-icon-prompts.json](edge-icon-prompts.json): initial battery/steps prompts; [battery-refinement-prompt.txt](battery-refinement-prompt.txt) records the follow-up battery edit.
- [SHA256SUMS](SHA256SUMS): source-file integrity hashes.

These source PNGs are the reproducible inputs. Repeating an AI prompt will produce different pixels. No model call or API key is required to rebuild this project.

`python tools/prepare_artwork.py` crops padding and resamples six active paintings into Android resources using Pillow's Lanczos filter. Alpha below 8/255 is ignored only when measuring padding, to avoid stray export noise; alpha inside the crop is preserved. Source files stay untouched. `python tools/render_preview.py` invokes preparation automatically. WFF uses the curved painting's alpha to mask two native 36-degree colored arcs. The battery and footsteps use the same alpha-mask approach so icons and gauges match exactly, without bitmap tint multiplication darkening the pigment. The native arc width enforces the safe outer boundary. No AI call is needed during a build.

The source assets and generated Android resources are included under the project's Apache-2.0 license, to the extent copyright applies. The font has its separate SIL OFL license.
