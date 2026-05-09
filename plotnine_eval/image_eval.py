from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageStat


@dataclass
class ImageEval:
    exists: bool
    passed: bool
    detail: str
    width: int = 0
    height: int = 0
    file_size: int = 0
    color_extrema: tuple | None = None


def evaluate_image(path: str | Path) -> ImageEval:
    image_path = Path(path)
    if not image_path.exists():
        return ImageEval(False, False, "output.png was not created")

    file_size = image_path.stat().st_size
    if file_size == 0:
        return ImageEval(True, False, "output.png is empty", file_size=file_size)

    try:
        with Image.open(image_path) as img:
            width, height = img.size
            rgb = img.convert("RGB")
            stat = ImageStat.Stat(rgb)
            extrema = rgb.getextrema()
            channel_ranges = [high - low for low, high in extrema]
            mean_range = max(stat.mean) - min(stat.mean)
    except Exception as exc:
        return ImageEval(True, False, f"could not read output.png: {exc}", file_size=file_size)

    if width < 200 or height < 150:
        return ImageEval(True, False, f"image too small: {width}x{height}", width, height, file_size, extrema)

    if max(channel_ranges) < 10 and mean_range < 5:
        return ImageEval(True, False, "image appears blank or nearly uniform", width, height, file_size, extrema)

    return ImageEval(True, True, f"image exists and is nonblank ({width}x{height}, {file_size} bytes)", width, height, file_size, extrema)

