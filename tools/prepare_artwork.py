"""Deterministically package painted source rasters; never redraw the artwork."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/artwork"
DEST = ROOT / "watchface/src/main/res/drawable-nodpi"


def prepare():
    DEST.mkdir(parents=True, exist_ok=True)
    for name, size in {"paper": (640, 640), "card": (160, 100),
                       "heart": (96, 96)}.items():
        image = Image.open(SOURCE / f"{name}-source.png").convert("RGBA")
        if name != "paper":
            assert image.getchannel("A").getextrema()[0] == 0, f"{name} needs transparency"
            image = image.crop(image.getchannel("A").getbbox())
        image.resize(size, Image.Resampling.LANCZOS).save(DEST / f"painted_{name}.png")
    arc = Image.open(SOURCE / "arc-source.png").convert("RGBA")
    assert arc.getchannel("A").getextrema()[0] == 0, "Arc needs transparency"
    # Ignore nearly invisible export noise when measuring padding; preserve the
    # actual alpha pixels inside that crop (the original source stays untouched).
    bounds = arc.getchannel("A").point(lambda a: 255 if a >= 8 else 0).getbbox()
    arc = arc.crop(bounds).resize((236, 464), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (480, 480))
    canvas.alpha_composite(arc, (232, 8))
    canvas.save(DEST / "painted_arc.png")
    print("Packaged four active painted raster assets.")


if __name__ == "__main__":
    prepare()
