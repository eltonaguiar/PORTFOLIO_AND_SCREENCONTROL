"""Offline tests for screen_control.vscode_panels.

These do not need VS Code or a CDP listener. They pin the invariants that were expensive to
discover: NBSP normalisation, visibility-filtered button evidence, identification by extension
globals, and the rule that `send()` must not report success when the text never reached the
transcript.
"""

import json

import pytest

from screen_control import vscode_panels as vp


# ---------- pure helpers ----------

def test_norm_replaces_monaco_nbsp():
    # Monaco renders spaces as U+00A0; a raw `in` test fails against visibly-correct text.
    assert "git log --oneline -3" not in "git\u00a0log\u00a0--oneline\u00a0-3"
    assert "git log --oneline -3" in vp.norm(["git\u00a0log\u00a0--oneline\u00a0-3"])


def test_norm_joins_nodes_with_newlines():
    assert vp.norm(["a", "b"]) == "a\nb"


def test_visible_button_js_requires_nonzero_box():
    # The single most costly bug: a hidden zero-width Cancel made an idle agent look busy.
    assert "offsetParent" in vp._JS_VISIBLE_BUTTONS
    assert "r.width > 0" in vp._JS_VISIBLE_BUTTONS
    assert "r.height > 0" in vp._JS_VISIBLE_BUTTONS


def test_text_walker_excludes_script_text():
    # Kilo's window.KILO_* boot script is a text node and otherwise reads as "latest message".
    assert "SCRIPT" in vp._JS_TEXT_NODES
    assert "STYLE" in vp._JS_TEXT_NODES


def test_identity_uses_extension_globals_not_model_name():
    # Model strings change (subq-savant -> deepseek-flash) and collapse two panels to one name.
    assert "KILO_TOP_BAR" in vp._JS_WHOAMI
    assert "kilocode" in vp._JS_WHOAMI
    assert "subq" not in vp._JS_WHOAMI.lower()


def test_copilot_input_uses_native_edit_context_not_the_readonly_textarea():
    # VS Code 1.144: textarea.ime-text-area is readOnly, so Input.insertText against it is a
    # silent no-op (cost four failed sends). The real editable is DIV.native-edit-context.
    assert "native-edit-context" in vp._JS_COPILOT_INPUT
    assert "scrollIntoView" in vp._JS_COPILOT_INPUT


def test_copilot_input_never_targets_the_readonly_textarea():
    # Guard against regressing to the selector that silently does nothing.
    assert "s.querySelector('textarea.ime-text-area')" not in vp._JS_COPILOT_INPUT


# ---------- behaviour with a fake session ----------

class FakeSession:
    """Minimal stand-in for vp.Session, driven by canned eval responses."""

    def __init__(self, buttons=None, text=None, copilot=None, submit_ok=True):
        self.buttons = buttons or []
        self.text = text if text is not None else []
        self.copilot = copilot or {}
        self.submit_ok = submit_ok
        self.clicks = []
        self.enters = 0
        self.inserted = None

    def eval(self, expr):
        if "chat-input-surface" in expr:
            return self.copilot
        if "offsetParent" in expr:
            return self.buttons
        if "TreeWalker" in expr:
            return self.text
        return True  # the webview composer setter

    def click(self, x, y):
        self.clicks.append((x, y))

    def press_enter(self):
        self.enters += 1
        if self.submit_ok:
            self.text = list(self.text) + ["echo"]

    def cmd(self, method, **params):
        self.inserted = params.get("text", self.inserted)
        return {}

    def close(self):
        pass


def _panels(session):
    p = vp.Panels()
    p._sessions = {"kilo": session}
    return p


def test_status_running_only_on_visible_stop():
    s = FakeSession(buttons=["Stop", "Send"])
    assert _panels(s).status("kilo")["state"] == "running"


def test_status_idle_without_stop():
    s = FakeSession(buttons=["Send"])
    assert _panels(s).status("kilo")["state"] == "idle"


def test_status_ignores_hidden_cancel_label():
    # Hidden controls never reach the filtered list, so an empty list means idle.
    s = FakeSession(buttons=[])
    assert _panels(s).status("kilo")["state"] == "idle"


def test_status_all_survives_an_unavailable_panel():
    class Boom(FakeSession):
        def eval(self, expr):
            raise vp.CDPError("panel not open")

    p = vp.Panels()
    p._sessions = {"kilo": Boom()}
    out = p.status_all()
    assert out["kilo"]["state"] == "unavailable"
    assert "panel not open" in out["kilo"]["error"]


def test_newest_turn_slices_after_marker():
    s = FakeSession(text=["OLD STEP A1 BLOCKED", "Mode is now Code", "STEP A1 DONE: x"])
    p = _panels(s)
    newest = p.newest_turn("kilo", "Mode is now Code")
    assert "DONE" in newest
    assert "BLOCKED" not in newest


def test_copilot_idle_when_send_disabled():
    s = FakeSession(buttons=[""], copilot={"x": 1334, "y": 906, "send_disabled": True})
    p = vp.Panels()
    p._sessions = {"copilot": s}
    assert p.status("copilot")["state"] == "idle"


def test_copilot_running_when_cancel_visible_even_if_send_disabled():
    s = FakeSession(buttons=["Cancel (Alt+Backspace)"], copilot={"x": 1, "y": 2, "send_disabled": True})
    p = vp.Panels()
    p._sessions = {"copilot": s}
    assert p.status("copilot")["state"] == "running"


def test_send_reports_failure_when_text_never_reaches_transcript():
    # A composer that clears without the message appearing is a silent no-op.
    s = FakeSession(buttons=[], text=[])
    ok = _panels(s).send("kilo", "hello world", verify=True)
    assert ok is False
    assert s.enters == 1  # it did try


def test_send_reports_success_when_transcript_contains_it():
    s = FakeSession(buttons=[], text=["hello world echoed"])
    ok = _panels(s).send("kilo", "hello world", verify=True)
    assert ok is True
