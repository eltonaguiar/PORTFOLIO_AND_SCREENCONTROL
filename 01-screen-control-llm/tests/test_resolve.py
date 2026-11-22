"""Resolver policy tests — no window needs to be open.

The cases encode the measurements in resolve.py's docstring: Chrome answered A11Y with 24 elements
and zero page nodes, VS Code with 3 elements, and OCR with text but no structure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kernel.resolve import (  # noqa: E402
    API_ADAPTERS,
    LADDER,
    Probe,
    ResolverCache,
    Rung,
    SurfaceClass,
    WindowProfile,
    classify,
    decide,
    wall_clock_probe,
)


def profile(app: str, title: str = "", w: int = 1456, h: int = 782) -> WindowProfile:
    return WindowProfile(app=app, title=title, hwnd=1, width=w, height=h)


def test_classification_covers_the_real_apps_on_this_machine():
    assert classify("chrome.exe", "Compare · ChatPlayground AI") is SurfaceClass.BROWSER
    assert classify("Code.exe", "x - Visual Studio Code") is SurfaceClass.ELECTRON
    assert classify("WindowsTerminal.exe") is SurfaceClass.TERMINAL
    assert classify("RustDesk.exe", "123 456 789 — RustDesk") is SurfaceClass.REMOTE_VIEWER
    assert classify("notepad.exe") is SurfaceClass.NATIVE


def test_every_ladder_ends_in_pixels():
    for surface, order in LADDER.items():
        assert order[-1] is Rung.PIXELS, surface


def test_browser_furniture_is_a_failed_probe_not_a_success():
    """The measured Chrome case: 24 elements, all tabs/buttons, zero page content."""
    p = Probe(rung=Rung.A11Y, elements=24, page_nodes=0)
    assert not p.acceptable(SurfaceClass.BROWSER)
    # The same counts on a native app WOULD be usable.
    assert p.acceptable(SurfaceClass.NATIVE)


def test_vscode_three_buttons_fall_through_to_text():
    chrome_furniture = Probe(rung=Rung.A11Y, elements=3, detail="Min/Max/Close only")
    ocr = Probe(rung=Rung.TEXT, text_lines=42, latency_s=0.8, detail="rapidocr crop")

    def probe(prof, rung):
        return {Rung.A11Y: chrome_furniture, Rung.API: Probe(rung=Rung.API), Rung.TEXT: ocr}.get(
            rung, Probe(rung=rung)
        )

    d = decide(profile("Code.exe"), probe)
    assert d.rung is Rung.TEXT
    assert d.degraded
    assert Rung.A11Y in d.tried


def test_cdp_wins_when_the_page_has_nodes():
    def probe(prof, rung):
        if rung is Rung.API:
            return Probe(rung=Rung.API, elements=312, page_nodes=312, latency_s=0.02, detail="CDP")
        raise AssertionError("should not fall lower once API works")

    d = decide(profile("chrome.exe"), probe)
    assert d.rung is Rung.API
    assert not d.degraded


def test_remote_viewer_never_trusts_a_tree():
    def probe(prof, rung):
        return Probe(rung=rung, elements=99 if rung is Rung.A11Y else 0,
                     text_lines=30 if rung is Rung.TEXT else 0)

    d = decide(profile("RustDesk.exe"), probe)
    assert d.rung is Rung.TEXT  # TEXT is above PIXELS for a viewer, A11Y is not in its ladder
    assert Rung.A11Y not in d.tried


def test_a_probe_that_raises_is_a_failed_probe():
    def probe(prof, rung):
        if rung is Rung.A11Y:
            raise RuntimeError("UIA client not initialised")
        return Probe(rung=rung, text_lines=5)

    d = decide(profile("notepad.exe"), probe)
    assert d.rung is Rung.TEXT
    assert "runtimeerror" in d.probes[0].detail.lower()


def test_dry_run_bottoms_out_at_pixels_with_a_hint():
    d = decide(profile("Code.exe"), wall_clock_probe)
    assert d.rung is Rung.PIXELS
    assert "accessibility" in d.hint.lower()


def test_cache_invalidates_on_resize():
    cache = ResolverCache()
    calls: list[Rung] = []

    def probe(prof, rung):
        calls.append(rung)
        return Probe(rung=rung, elements=40, text_lines=10)

    p1 = profile("notepad.exe", w=800, h=600)
    first = cache.resolve(p1, probe)
    assert cache.resolve(p1, probe) is first          # cached, no new probes
    before = len(calls)
    p2 = profile("notepad.exe", w=1000, h=600)        # resize
    cache.resolve(p2, probe)
    assert len(calls) > before                        # re-probed


def test_every_surface_has_a_documented_api_adapter():
    for surface in SurfaceClass:
        assert surface in API_ADAPTERS, surface
    assert "none" in API_ADAPTERS[SurfaceClass.REMOTE_VIEWER].lower()
