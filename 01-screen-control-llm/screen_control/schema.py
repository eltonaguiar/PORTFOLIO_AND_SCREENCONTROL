"""Action schema for LLM-driven screen control.

An LLM cannot click. It can only emit a structured decision. This module defines the
*only* verbs the loop will execute, so that a model's output is either a well-formed
action or a hard error — never a free-form gesture that the runtime improvises on.

Design notes that came out of building this:

  * Every verb is expressed in ELEMENT space (backend node id / selector / ax-id), not
    pixel space. Pixel coordinates break on scroll, resize, zoom, DPI change and
    sticky headers, which is where most "the agent clicked the wrong thing" reports
    come from.
  * Click coordinates are resolved at ACT time from the live box model, not baked in
    at DECIDE time.
  * There is an explicit `DONE` and an explicit `FAIL` verb. Without them the loop
    cannot distinguish "finished" from "out of ideas" and will keep clicking.
  * Destructive verbs are not modelled as separate actions; they are the same verbs
    plus a `confirm` token, so the guard has one place to look.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional

# The complete verb set. Adding a verb is a schema change and requires a guard update.
VERBS = {
    "click",        # click an element by handle, or by coordinate as last resort
    "type",         # focus an element and type text
    "key",          # press a key combination, e.g. "Enter", "Control+a"
    "scroll",       # scroll the page or a scrollable element
    "navigate",     # go to a URL
    "wait",         # explicit pause for async UI
    "read",         # extract text / structured data from the page
    "done",         # task complete, with a summary
    "fail",         # cannot proceed, with a reason
}

# Verbs that can cause an irreversible external effect if the target is wrong.
IRREVERSIBLE_VERBS = {"type", "key"}
# Words in an element name that make an action irreversible regardless of verb.
IRREVERSIBLE_WORDS = {
    "delete", "remove", "pay", "purchase", "buy", "send", "submit", "confirm",
    "transfer", "withdraw", "close account", "cancel subscription", "unsubscribe",
    "publish", "deploy", "approve", "authorize", "revoke",
}


@dataclass
class Action:
    """A single decision. `thought` is required: it is the audit trail."""

    verb: str
    thought: str
    target: Optional[str] = None          # element handle / selector / ax name
    text: Optional[str] = None            # for type
    key: Optional[str] = None             # for key
    url: Optional[str] = None             # for navigate
    x: Optional[float] = None             # last-resort coordinate click
    y: Optional[float] = None
    dy: Optional[int] = None              # for scroll
    confirm: bool = False                 # must be True for irreversible actions
    expect: Optional[str] = None          # post-condition the verifier will check
    meta: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> "Action":
        if self.verb not in VERBS:
            raise ValueError(f"unknown verb {self.verb!r}; allowed: {sorted(VERBS)}")
        if not self.thought or len(self.thought.strip()) < 3:
            raise ValueError("every action needs a `thought` (audit trail)")
        if self.verb == "type" and not (self.text or self.key):
            raise ValueError("type requires text or key")
        if self.verb == "key" and not self.key:
            raise ValueError("key requires key")
        if self.verb == "navigate" and not self.url:
            raise ValueError("navigate requires url")
        if self.verb == "click" and not (self.target or (self.x is not None and self.y is not None)):
            raise ValueError("click requires target or x/y")
        if self.verb == "read" and not (self.target or self.meta.get("selector")):
            raise ValueError("read requires target or meta.selector")
        return self

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v not in (None, {}, False) or k == "confirm"}

    @classmethod
    def from_dict(cls, d: dict) -> "Action":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class StepResult:
    step: int
    action: Action
    ok: bool
    detail: str
    observation_after: Optional[dict] = None
    screenshot: Optional[str] = None
    blocked: bool = False
