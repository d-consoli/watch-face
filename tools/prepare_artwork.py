"""Deterministically package painted source rasters; never redraw the artwork."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/artwork"
DEST = ROOT / "watchface/src/main/res/drawable-nodpi"


def prepare():
    DEST.mkdir(parents=True, exist_ok=True)
    for name, size in {"paper": (640, 640), "card": (160, 100),
                       "heart": (96, 96), "stroke": (384, 40)}.items():
        image = Image.open(SOURCE / f"{name}-source.png").convert("RGBA")
        if name != "paper":
            assert image.getchannel("A").getextrema()[0] == 0, f"{name} needs transparency"
            image = image.crop(image.getchannel("A").getbbox())
        image.resize(size, Image.Resampling.LANCZOS).save(DEST / f"painted_{name}.png")
    print("Packaged four painted raster assets.")


if __name__ == "__main__":
    prepare()
