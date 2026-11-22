"""Unit tests for kernel.capture — the DPI and coordinate contracts.

Run: python -m pytest 01-screen-control-llm/tests -q
Verification target (NEXT_STEPS item 2): the same element box must map to the same screen point at
100% and 150% scaling once per-monitor-v2 awareness is on, and the conversions must round-trip.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel.capture import (  # noqa: E402
    Rect,
    capture_region,
    client_to_screen,
    contains_point_margin,
    crop_png,
    dpi_scale,
    enable_per_monitor_dpi_awareness,
    logical_to_physical,
    physical_to_logical,
    screen_to_client,
)


def test_rect_basics():
    r = Rect(100, 50, 200, 40)
    assert (r.right, r.bottom) == (300, 90)
    assert r.contains(150, 60)
    assert not r.contains(300, 90)  # half-open
    assert not r.is_empty()
    assert Rect(0, 0, 0, 10).is_empty()


def test_intersect_and_clamp():
    window = Rect(0, 0, 1456, 818)
    panel = Rect(1000, 600, 400, 300)  # runs past the bottom edge
    clamped = panel.clamp_to(window)
    assert clamped.as_tuple() == (1000, 600, 400, 218)
    assert panel.clamp_to(window).contains(1200, 800)


def test_logical_physical_round_trip_at_100_and_150():
    box = Rect(120, 240, 300, 60, "logical")
    for scale in (1.0, 1.25, 1.5, 2.0):
        physical = logical_to_physical(box, scale)
        back = physical_to_logical(physical, scale)
        assert abs(back.width - box.width) <= 1
        assert abs(back.height - box.height) <= 1
        assert abs(back.left - box.left) <= 1
        assert abs(back.top - box.top) <= 1


def test_same_logical_box_maps_differently_without_awareness():
    """This is the bug the module exists to prevent: a 1.5x display shifts every click."""
    box = Rect(100, 100, 50, 20, "logical")
    assert logical_to_physical(box, 1.0).as_tuple() == (100, 100, 50, 20)
    assert logical_to_physical(box, 1.5).as_tuple() == (150, 150, 75, 30)


def test_client_screen_round_trip():
    origin = (240, 130)
    client = Rect(10, 20, 300, 40, "client")
    screen = client_to_screen(client, origin)
    assert screen.as_tuple() == (250, 150, 300, 40)
    assert screen_to_client(screen, origin).as_tuple() == client.as_tuple()


def test_hit_test_margin_absorbs_rounding():
    r = Rect(10, 10, 100, 30)
    assert contains_point_margin(r, 9, 9, margin=2)      # one pixel outside, tolerated
    assert not contains_point_margin(r, 5, 5, margin=2)  # clearly outside


def test_awareness_is_idempotent_and_scalable():
    first = enable_per_monitor_dpi_awareness()
    second = enable_per_monitor_dpi_awareness()
    assert second == first or second is True  # never flips back off
    scale = dpi_scale()
    assert scale > 0


@pytest.mark.skipif(sys.platform != "win32", reason="capture is Windows-only here")
def test_window_scoped_capture_is_exact_and_croppable():
    rect = Rect(0, 0, 320, 200)
    cap = capture_region(rect)
    assert (cap.width, cap.height) == (320, 200)
    assert cap.origin == (0, 0)
    assert cap.png[:8] == b"\x89PNG\r\n\x1a\n"
    assert cap.px_per_point > 0
    cropped = crop_png(cap.png, Rect(10, 10, 100, 50))
    assert cropped[:8] == b"\x89PNG\r\n\x1a\n"
    with pytest.raises(ValueError):
        crop_png(cap.png, Rect(300, 190, 100, 100))  # exceeds the frame
    with pytest.raises(ValueError):
        capture_region(Rect(0, 0, 0, 0))  # empty refused
