# Ink & Paper artwork

Four original raster paintings generated with Codex's built-in image generation tool on 2026-09-25. The user's ZENFORM reference was used for general material/style direction: warm paper, dry ink and muted watercolor. No commercial face artwork, font, screenshot or APK is redistributed.

- `paper-source.png`: full-resolution paper and ink background.
- `card-source.png`: ochre loyalty-card painting, with transparency.
- `heart-source.png`: vermilion brush heart, with transparency.
- `stroke-source.png`: dry charcoal progress stroke, with transparency.
- [prompts.json](prompts.json): exact prompts for all four assets. The background was the style reference for the three icon calls.
- [SHA256SUMS](SHA256SUMS): source-file integrity hashes.

These source PNGs are the reproducible inputs. Repeating an AI prompt will produce different pixels. No model call or API key is required to rebuild this project.

`python tools/prepare_artwork.py` crops transparent padding from the three foreground assets and resamples all four into bounded Android resources using Pillow's Lanczos filter. It retains alpha and does no creative redrawing. `python tools/render_preview.py` invokes this preparation automatically. The watch tints/scales the real brush bitmap to show progress.

The source assets and generated Android resources are included under the project's Apache-2.0 license, to the extent copyright applies. The font has its separate SIL OFL license.
