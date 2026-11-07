"""Laser engraving / cutting preparation.

Pipeline (LightBurn / ImagR style):
1. EXIF orientation + optional physical resize (mm + DPI)
2. Grayscale
3. Denoise → brightness → contrast → sharpen
4. Dither / threshold / grayscale finish
5. Optional invert for dark materials
"""

from __future__ import annotations

from io import BytesIO
from typing import Literal

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

PrepMode = Literal[
    "floyd",
    "jarvis",
    "stucki",
    "atkinson",
    "ordered",
    "threshold",
    "grayscale",
    "dither",  # alias for floyd (back-compat)
]

# Error-diffusion kernels: list of (dx, dy, weight). Divisor = sum(weights).
_DIFFUSION: dict[str, tuple[list[tuple[int, int, int]], int]] = {
    "floyd": (
        [(1, 0, 7), (-1, 1, 3), (0, 1, 5), (1, 1, 1)],
        16,
    ),
    "jarvis": (
        [
            (1, 0, 7),
            (2, 0, 5),
            (-2, 1, 3),
            (-1, 1, 5),
            (0, 1, 7),
            (1, 1, 5),
            (2, 1, 3),
            (-2, 2, 1),
            (-1, 2, 3),
            (0, 2, 5),
            (1, 2, 3),
            (2, 2, 1),
        ],
        48,
    ),
    "stucki": (
        [
            (1, 0, 8),
            (2, 0, 4),
            (-2, 1, 2),
            (-1, 1, 4),
            (0, 1, 8),
            (1, 1, 4),
            (2, 1, 2),
            (-2, 2, 1),
            (-1, 2, 2),
            (0, 2, 4),
            (1, 2, 2),
            (2, 2, 1),
        ],
        42,
    ),
    "atkinson": (
        [
            (1, 0, 1),
            (2, 0, 1),
            (-1, 1, 1),
            (0, 1, 1),
            (1, 1, 1),
            (0, 2, 1),
        ],
        8,
    ),
}


def _midtone_contrast(image: Image.Image, amount: float) -> Image.Image:
    """S-curve contrast around midtones."""
    amount = max(0.5, min(amount, 2.5))
    if abs(amount - 1.0) < 0.02:
        return image

    def lut(value: int) -> int:
        x = value / 255.0
        y = 0.5 + (x - 0.5) * amount
        return int(round(max(0.0, min(1.0, y)) * 255))

    return image.point(lut)


def _error_diffuse(gray: Image.Image, mode: str) -> Image.Image:
    """Apply classic error-diffusion dither to an L-mode image → L black/white."""
    key = "floyd" if mode == "dither" else mode
    kernel, divisor = _DIFFUSION[key]
    pixels = gray.load()
    width, height = gray.size
    # Work in float buffer for error accumulation
    buf = [[float(pixels[x, y]) for x in range(width)] for y in range(height)]  # type: ignore[index]
    out = Image.new("L", (width, height))
    out_px = out.load()

    for y in range(height):
        for x in range(width):
            old = buf[y][x]
            new = 255.0 if old >= 128.0 else 0.0
            out_px[x, y] = int(new)  # type: ignore[index]
            err = old - new
            for dx, dy, weight in kernel:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    buf[ny][nx] += err * weight / divisor

    return out


def _resize_for_output(
    image: Image.Image,
    *,
    width_mm: float | None,
    height_mm: float | None,
    dpi: int,
    max_edge: int,
) -> Image.Image:
    """Resize using physical size (mm @ DPI) when provided, else cap longest edge."""
    width, height = image.size
    dpi = max(72, min(dpi, 600))

    if width_mm and width_mm > 0:
        target_w = max(1, int(round(width_mm / 25.4 * dpi)))
        if height_mm and height_mm > 0:
            target_h = max(1, int(round(height_mm / 25.4 * dpi)))
        else:
            target_h = max(1, int(round(target_w * (height / width))))
        return image.resize((target_w, target_h), Image.Resampling.LANCZOS)

    if height_mm and height_mm > 0:
        target_h = max(1, int(round(height_mm / 25.4 * dpi)))
        target_w = max(1, int(round(target_h * (width / height))))
        return image.resize((target_w, target_h), Image.Resampling.LANCZOS)

    longest = max(width, height)
    if longest > max_edge:
        scale = max_edge / longest
        return image.resize(
            (max(1, round(width * scale)), max(1, round(height * scale))),
            Image.Resampling.LANCZOS,
        )
    return image


def prepare_for_laser(
    data: bytes,
    *,
    mode: PrepMode = "floyd",
    max_edge: int = 2400,
    contrast: float = 1.55,
    brightness: float = 1.05,
    sharpness: float = 1.1,
    denoise: float = 0.35,
    invert: bool = False,
    threshold: int = 128,
    width_mm: float | None = None,
    height_mm: float | None = None,
    dpi: int = 300,
) -> tuple[bytes, int, int, dict[str, float | int]]:
    """
    Prepare a photo for laser engraving / cutting raster.

    Returns PNG bytes, pixel width/height, and metrics (mm, dpi).
    """
    with Image.open(BytesIO(data)) as src:
        image = ImageOps.exif_transpose(src).convert("RGB")

    image = _resize_for_output(
        image,
        width_mm=width_mm,
        height_mm=height_mm,
        dpi=dpi,
        max_edge=max_edge,
    )

    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)

    # Denoise: light median, then optional more aggressive blur mix
    denoise = max(0.0, min(denoise, 1.0))
    if denoise > 0.05:
        radius = 1 if denoise < 0.55 else 2
        cleaned = gray.filter(ImageFilter.MedianFilter(size=3 if radius == 1 else 5))
        if denoise > 0.7:
            cleaned = cleaned.filter(ImageFilter.GaussianBlur(radius=0.6))
        # Blend original detail back
        gray = Image.blend(gray, cleaned, denoise * 0.85)

    if abs(brightness - 1.0) > 0.01:
        gray = ImageEnhance.Brightness(gray).enhance(brightness)

    gray = _midtone_contrast(gray, contrast)
    gray = ImageEnhance.Contrast(gray).enhance(1.0 + (contrast - 1.0) * 0.35)

    sharpness = max(0.0, min(sharpness, 3.0))
    if sharpness > 0.05:
        # UnsharpMask percent scales with slider (1.0 ≈ mild workshop default)
        percent = int(round(40 + sharpness * 100))
        gray = gray.filter(
            ImageFilter.UnsharpMask(radius=1.2, percent=percent, threshold=2)
        )

    resolved = "floyd" if mode == "dither" else mode
    if resolved == "grayscale":
        result = gray
    elif resolved == "threshold":
        cut = max(1, min(254, threshold))
        result = gray.point(lambda p, c=cut: 255 if p >= c else 0, mode="L")
    elif resolved == "ordered":
        bw = gray.convert("1", dither=Image.Dither.ORDERED)
        result = bw.convert("L")
    elif resolved in _DIFFUSION:
        result = _error_diffuse(gray, resolved)
    else:
        result = _error_diffuse(gray, "floyd")

    if invert:
        result = ImageOps.invert(result)

    out = BytesIO()
    # Embed DPI for CorelDRAW / LightBurn import
    result.save(out, format="PNG", optimize=True, dpi=(dpi, dpi))
    prepared_w, prepared_h = result.size
    metrics = {
        "dpi": dpi,
        "width_px": prepared_w,
        "height_px": prepared_h,
        "width_mm": round(prepared_w / dpi * 25.4, 2),
        "height_mm": round(prepared_h / dpi * 25.4, 2),
    }
    return out.getvalue(), prepared_w, prepared_h, metrics


def read_dimensions(data: bytes) -> tuple[int, int]:
    with Image.open(BytesIO(data)) as image:
        image = ImageOps.exif_transpose(image)
        return image.size
