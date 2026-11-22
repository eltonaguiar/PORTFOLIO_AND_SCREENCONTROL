"""Window-scoped capture and DPI-safe coordinate math.

The single most common cause of "the agent clicked the wrong thing" is a coordinate that is
correct in one coordinate space and applied in another. Windows has three of them:

    physical pixels  what the framebuffer and a DPI-aware capture contain
    logical pixels   what a DPI-unaware process believes (physical / scale)
    client pixels    what a control's bounds are relative to its window's client area

This module makes the conversions explicit and never guesses. Enable per-monitor-v2 awareness
first (`enable_per_monitor_dpi_awareness`), then every number in this module is physical pixels.

Design rules enforced here:
  * capture is always window-scoped, never whole-screen, so a second monitor or a taskbar can
    never shift the origin
  * every capture returns `px_per_point` and the window origin, so downstream code can detect a
    scale mismatch instead of silently mis-clicking
  * cropping happens on bytes, so a caller can verify a small region without decoding a full frame
"""

from __future__ import annotations

import ctypes
import io
import sys
from dataclasses import dataclass
from typing import Optional


# --------------------------------------------------------------------------------------------
# DPI awareness
# --------------------------------------------------------------------------------------------

_DPI_AWARE_SET = False


def enable_per_monitor_dpi_awareness() -> bool:
    """Set PROCESS_PER_MONITOR_DPI_AWARE_V2 for this process. Idempotent; False off Windows.

    Without this, UIA bounds and screen coordinates disagree on a 125%/150% display and every
    click is offset by a few percent — enough to miss a button and hit its neighbour.
    """
    global _DPI_AWARE_SET
    if _DPI_AWARE_SET:
        return True
    if sys.platform != "win32":
        return False
    try:
        # -4 == DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (Win10 1703+)
        if ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4)):
            _DPI_AWARE_SET = True
            return True
    except Exception:
        pass
    try:  # Win8.1 fallback
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
        _DPI_AWARE_SET = True
        return True
    except Exception:
        return False


def dpi_scale(hwnd: Optional[int] = None) -> float:
    """Effective scale factor (1.0 = 96 DPI). Falls back to 1.0 when it cannot be read."""
    if sys.platform != "win32":
        return 1.0
    try:
        if hwnd:
            dpi = ctypes.windll.user32.GetDpiForWindow(ctypes.c_void_p(hwnd))
        else:
            dpi = ctypes.windll.user32.GetDpiForSystem()
        if dpi:
            return round(dpi / 96.0, 4)
    except Exception:
        pass
    return 1.0


# --------------------------------------------------------------------------------------------
# Geometry
# --------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Rect:
    """A rectangle in one named space. `space` is documentation, not enforcement."""

    left: int
    top: int
    width: int
    height: int
    space: str = "physical"  # "physical" | "logical" | "client"

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.width, self.height)

    def is_empty(self) -> bool:
        return self.width <= 0 or self.height <= 0

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x < self.right and self.top <= y < self.bottom

    def intersect(self, other: "Rect") -> "Rect":
        left = max(self.left, other.left)
        top = max(self.top, other.top)
        right = min(self.right, other.right)
        bottom = min(self.bottom, other.bottom)
        return Rect(left, top, max(0, right - left), max(0, bottom - top), self.space)

    def clamp_to(self, bounds: "Rect") -> "Rect":
        return self.intersect(bounds)


def logical_to_physical(rect: Rect, scale: float) -> Rect:
    """A DPI-unaware box -> physical pixels. Use when reading bounds from an unaware source."""
    if scale <= 0:
        raise ValueError("scale must be > 0")
    return Rect(
        int(round(rect.left * scale)),
        int(round(rect.top * scale)),
        int(round(rect.width * scale)),
        int(round(rect.height * scale)),
        "physical",
    )


def physical_to_logical(rect: Rect, scale: float) -> Rect:
    """Physical pixels -> a DPI-unaware box. Inverse of `logical_to_physical`."""
    if scale <= 0:
        raise ValueError("scale must be > 0")
    return Rect(
        int(round(rect.left / scale)),
        int(round(rect.top / scale)),
        int(round(rect.width / scale)),
        int(round(rect.height / scale)),
        "logical",
    )


def client_to_screen(rect: Rect, client_origin: tuple[int, int]) -> Rect:
    """Client-relative box -> screen coordinates (both physical)."""
    ox, oy = client_origin
    return Rect(rect.left + ox, rect.top + oy, rect.width, rect.height, "physical")


def screen_to_client(rect: Rect, client_origin: tuple[int, int]) -> Rect:
    ox, oy = client_origin
    return Rect(rect.left - ox, rect.top - oy, rect.width, rect.height, "client")


def contains_point_margin(rect: Rect, x: int, y: int, margin: int = 0) -> bool:
    """Hit-test with a tolerance, so a one-pixel rounding error does not become a miss."""
    return (
        rect.left - margin <= x < rect.right + margin
        and rect.top - margin <= y < rect.bottom + margin
    )


# --------------------------------------------------------------------------------------------
# Capture (window-scoped, DPI-annotated)
# --------------------------------------------------------------------------------------------


@dataclass
class Capture:
    png: bytes
    width: int
    height: int
    origin: tuple[int, int]  # screen-space top-left of the captured region, physical px
    px_per_point: float      # the scale in force when it was taken

    def to_physical(self, client_rect: Rect) -> Rect:
        """Map a client-relative box in this capture to absolute screen coordinates."""
        return client_to_screen(client_rect, self.origin)


def capture_region(rect: Rect, hwnd: Optional[int] = None) -> Capture:
    """Capture exactly `rect` (physical px). Window-scoped by construction: no whole-screen grab.

    Uses Pillow's ImageGrab (present in this environment). If a faster backend is available later
    (Windows Graphics Capture via cua-driver), swap it here — the return type is the contract.
    """
    if rect.is_empty():
        raise ValueError("refusing to capture an empty region")
    enable_per_monitor_dpi_awareness()
    try:
        from PIL import ImageGrab
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("Pillow is required for capture_region") from exc

    img = ImageGrab.grab(bbox=rect.as_tuple(), all_screens=True)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return Capture(
        png=buf.getvalue(),
        width=rect.width,
        height=rect.height,
        origin=(rect.left, rect.top),
        px_per_point=dpi_scale(hwnd),
    )


def crop_png(png: bytes, rect: Rect) -> bytes:
    """Crop an already-captured frame without re-grabbing the screen.

    This is what keeps OCR cheap: a full 1456x818 frame took ~19 s with RapidOCR in our
    measurements, while a 400x800 panel crop is a fraction of that.
    """
    from PIL import Image

    img = Image.open(io.BytesIO(png))
    if rect.is_empty():
        raise ValueError("refusing to crop an empty region")
    if rect.right > img.width or rect.bottom > img.height:
        raise ValueError(
            f"crop {rect.as_tuple()} exceeds frame {img.width}x{img.height}"
        )
    out = io.BytesIO()
    img.crop(rect.as_tuple()).save(out, format="PNG")
    return out.getvalue()
