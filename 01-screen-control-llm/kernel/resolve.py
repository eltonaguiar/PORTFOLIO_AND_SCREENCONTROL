"""The five-rung resolver — generic between surfaces, not per app.

Called for *any* window: a native Win32 dialog, an Electron IDE, a browser page, a terminal, a
RustDesk viewer, a canvas app. The resolver decides which perception/actuation rung is actually
available on that window right now, records why, and caches the answer until the window changes.

Rungs, highest first (each one down costs roughly an order of magnitude in reliability):

    API    the app has a real interface (CDP for a page, CLI/process for a terminal, COM, REST)
    A11Y   an accessibility tree with usable nodes (UIA on Windows, AT-SPI on Linux, AX on macOS)
    TEXT   a text layer: UIA TextPattern, or OCR over a crop of the window
    MARKS  an element-detection model (OmniParser / ShowUI / UI-TARS) returns labelled boxes
    PIXELS raw coordinates from a screenshot; last resort, always allowed, never preferred

Measured on this machine (2026-11-22), which is why the policy is not "always use the tree":

    Chrome 1456x782, page loaded      A11Y -> 24 elements, 0 of them page content
    VS Code                           A11Y ->  3 elements (Min/Max/Close), a11y off
    RapidOCR, full 1456x818 frame     TEXT -> 106 boxes, 18.99 s
    qwen3-vl 2b/4b/8b for a coordinate GROUND -> empty string at every size

The lesson encoded here: a rung that returns *only chrome furniture* is a FAILED probe, not a
successful one. The acceptance predicate is per surface class, not `len(elements) > 0`.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


class SurfaceClass(str, Enum):
    BROWSER = "browser"          # page content lives in a renderer: CDP or pixels
    ELECTRON = "electron"        # VS Code, Slack, Discord, Obsidian: a11y behind a flag
    NATIVE = "native"            # Win32/WPF/Qt: UIA usually complete
    TERMINAL = "terminal"        # own the process, or expect text-only
    REMOTE_VIEWER = "remote"     # RustDesk/RDP window: pixels only, never a tree
    CANVAS = "canvas"            # games, design tools, video: pixels/marks only
    UNKNOWN = "unknown"


class Rung(str, Enum):
    API = "api"
    A11Y = "a11y"
    TEXT = "text"
    MARKS = "marks"
    PIXELS = "pixels"

    @property
    def rank(self) -> int:
        return {"api": 0, "a11y": 1, "text": 2, "marks": 3, "pixels": 4}[self.value]


#: The order of preference per surface class. Every list ends in PIXELS: there is always a way.
LADDER: dict[SurfaceClass, list[Rung]] = {
    SurfaceClass.BROWSER: [Rung.API, Rung.A11Y, Rung.TEXT, Rung.PIXELS],
    SurfaceClass.ELECTRON: [Rung.A11Y, Rung.API, Rung.TEXT, Rung.PIXELS],
    SurfaceClass.NATIVE: [Rung.A11Y, Rung.API, Rung.TEXT, Rung.PIXELS],
    SurfaceClass.TERMINAL: [Rung.API, Rung.A11Y, Rung.TEXT, Rung.PIXELS],
    SurfaceClass.REMOTE_VIEWER: [Rung.TEXT, Rung.PIXELS],
    SurfaceClass.CANVAS: [Rung.MARKS, Rung.TEXT, Rung.PIXELS],
    SurfaceClass.UNKNOWN: [Rung.A11Y, Rung.TEXT, Rung.PIXELS],
}

#: Hints to try BEFORE accepting a lower rung — cheaper than OCR and often unblocks A11Y entirely.
A11Y_HINTS: dict[SurfaceClass, str] = {
    SurfaceClass.ELECTRON: "launch with --force-renderer-accessibility, or set the app's own switch "
                           "(VS Code: editor.accessibilitySupport=on) and relaunch",
    SurfaceClass.BROWSER: "enable renderer accessibility, or attach CDP and use the DOM instead",
    SurfaceClass.NATIVE: "check UIA client permission / 32-vs-64-bit, or jabswitch for Java apps",
}


def classify(app_name: str, title: str = "", has_child_windows: bool = True) -> SurfaceClass:
    """Best-effort surface classification from the process name and window title.

    Wrong guesses are cheap: the probe decides, and `decide()` will walk down the ladder anyway.
    """
    a = (app_name or "").lower()
    t = (title or "").lower()

    remote = ("rustdesk", "mstsc", "teamviewer", "anydesk", "parsec", "vnc", "rdp")
    if any(k in a or k in t for k in remote):
        return SurfaceClass.REMOTE_VIEWER

    browsers = ("chrome", "msedge", "firefox", "brave", "opera", "vivaldi", "chromium")
    if any(k in a for k in browsers):
        return SurfaceClass.BROWSER

    electrons = ("code.exe", "code - insiders", "slack", "discord", "obsidian", "notion",
                 "postman", "figma", "teams", "spotify", "signal", "cursor", "windsurf")
    if any(k in a for k in electrons):
        return SurfaceClass.ELECTRON

    terminals = ("windowsterminal", "wt.exe", "conhost", "mintty", "powershell", "cmd.exe",
                 "alacritty", "wezterm", "kitty")
    if any(k in a for k in terminals):
        return SurfaceClass.TERMINAL

    canvases = ("photoshop", "illustrator", "blender", "premiere", "afterfx", "unity", "godot",
                "obs", "vlc", "steam")
    if any(k in a for k in canvases):
        return SurfaceClass.CANVAS

    if a.endswith(".exe") or a in ("explorer.exe", "notepad.exe", "winword.exe"):
        return SurfaceClass.NATIVE
    return SurfaceClass.UNKNOWN


@dataclass
class WindowProfile:
    app: str
    title: str = ""
    hwnd: Optional[int] = None
    width: int = 0
    height: int = 0
    surface: SurfaceClass = SurfaceClass.UNKNOWN

    def __post_init__(self) -> None:
        if self.surface is SurfaceClass.UNKNOWN:
            self.surface = classify(self.app, self.title)

    @property
    def signature(self) -> tuple:
        """Cache key: a resize or a title change invalidates the rung decision."""
        return (self.hwnd, self.app, self.width, self.height, self.title)


@dataclass
class Probe:
    """What a rung actually returned. `page_nodes` separates browser furniture from content."""

    rung: Rung
    elements: int = 0
    page_nodes: int = 0
    text_lines: int = 0
    latency_s: float = 0.0
    detail: str = ""

    def acceptable(self, surface: SurfaceClass) -> bool:
        """A rung is only accepted if it returned something the task could actually act on."""
        if self.elements == 0 and self.text_lines == 0:
            return False
        if self.rung is Rung.API:
            return self.page_nodes > 0 or self.elements > 0
        if self.rung is Rung.A11Y:
            if surface is SurfaceClass.BROWSER:
                # 24 elements that are all tabs/buttons while the page is blank = failed probe.
                return self.page_nodes > 0
            return self.elements >= 4
        if self.rung is Rung.TEXT:
            return self.text_lines >= 2
        if self.rung is Rung.MARKS:
            return self.elements >= 1
        return True  # pixels always work


@dataclass
class Decision:
    rung: Rung
    surface: SurfaceClass
    reason: str
    probes: list[Probe] = field(default_factory=list)
    tried: list[Rung] = field(default_factory=list)
    hint: str = ""

    @property
    def degraded(self) -> bool:
        return self.rung.rank >= Rung.TEXT.rank


# probe: (profile, rung) -> Probe.  Injected so this module stays pure and unit-testable.
ProbeFn = Callable[[WindowProfile, Rung], Probe]


def decide(profile: WindowProfile, probe: ProbeFn, *, allow_marks: bool = False) -> Decision:
    """Walk the surface's ladder and return the first rung whose probe is acceptable."""
    order = list(LADDER.get(profile.surface, LADDER[SurfaceClass.UNKNOWN]))
    if not allow_marks:
        order = [r for r in order if r is not Rung.MARKS] or [Rung.PIXELS]

    probes: list[Probe] = []
    tried: list[Rung] = []
    for rung in order:
        tried.append(rung)
        try:
            p = probe(profile, rung)
        except Exception as exc:  # a probe that throws is a failed probe, not a crash
            p = Probe(rung=rung, detail=f"probe raised {type(exc).__name__}: {exc}")
        probes.append(p)
        if p.acceptable(profile.surface):
            reason = p.detail or f"{rung.value} returned {p.elements} element(s)/{p.text_lines} line(s)"
            return Decision(rung=rung, surface=profile.surface, reason=reason, probes=probes, tried=tried)

    return Decision(
        rung=Rung.PIXELS,
        surface=profile.surface,
        reason="no rung returned actionable content; driving by coordinates",
        probes=probes,
        tried=tried,
        hint=A11Y_HINTS.get(profile.surface, ""),
    )


class ResolverCache:
    """Per-window rung memory, invalidated by the window signature (resize/title change).

    The point is not speed — it is that a task never re-derives (and never *silently changes*)
    how it perceives a window mid-run without noticing.
    """

    def __init__(self) -> None:
        self._store: dict[tuple, Decision] = {}

    def get(self, profile: WindowProfile) -> Optional[Decision]:
        return self._store.get(profile.signature)

    def put(self, profile: WindowProfile, decision: Decision) -> None:
        self._store[profile.signature] = decision

    def resolve(self, profile: WindowProfile, probe: ProbeFn, *, allow_marks: bool = False,
                max_age_s: float = 300.0) -> Decision:
        hit = self.get(profile)
        if hit is not None and (hit.probes and hit.probes[-1].latency_s < max_age_s):
            return hit
        d = decide(profile, probe, allow_marks=allow_marks)
        self.put(profile, d)
        return d

    def invalidate(self, profile: WindowProfile) -> None:
        self._store.pop(profile.signature, None)


# ---------------------------------------------------------------------------------------------
# Adapters: what "API" means for each surface class. Data, not code paths.
# ---------------------------------------------------------------------------------------------

API_ADAPTERS: dict[SurfaceClass, str] = {
    SurfaceClass.BROWSER: "CDP over --remote-debugging-port, or chrome.debugger; DOM selectors + textContent",
    SurfaceClass.TERMINAL: "own the child process: read stdout/exit code, or drive the app's tmux session",
    SurfaceClass.ELECTRON: "app IPC (VS Code: extension host / vscode.commands), or its CLI",
    SurfaceClass.NATIVE: "COM/UIA patterns directly, or the app's own CLI if it has one",
    SurfaceClass.REMOTE_VIEWER: "none — an RDP session cannot be driven through the viewer; use a service/agent on the far side",
    SurfaceClass.CANVAS: "the app's file format or plugin API; never synthesise mouse gestures into a canvas",
    SurfaceClass.UNKNOWN: "none known",
}


def wall_clock_probe(profile: WindowProfile, rung: Rung) -> Probe:
    """Placeholder used by dry runs: reports every rung as empty so the ladder bottoms out at pixels."""
    return Probe(rung=rung, latency_s=0.0, detail="dry-run probe (no transport attached)")
