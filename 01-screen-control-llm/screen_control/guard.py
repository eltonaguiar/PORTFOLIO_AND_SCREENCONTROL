"""Guardrails. The guard is the reason this is safe to run unattended.

Three independent limits, because any one of them alone has a failure mode:

  1. ALLOWLIST of hosts. A navigation to an off-list host is refused before it happens.
     Without this, a prompt-injected page can walk the agent anywhere.
  2. IRREVERSIBILITY GATE. Verbs that can commit an external effect require
     `confirm=True`, and an element whose accessible name contains a destructive word
     requires it even if the verb looks benign. This is the only thing standing between
     "the agent filled the form" and "the agent submitted the form".
  3. BUDGET. Max steps, max seconds, max consecutive failures, max repeats of the same
     action signature. A model that has lost the plot repeats itself; the repeat limit
     turns an infinite loop into a clean failure.

The guard returns a decision; it never raises on policy. Policy refusal is data that
the loop records, so a refused step shows up in the transcript and can be reviewed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urlparse

from .schema import Action, IRREVERSIBLE_WORDS


@dataclass
class GuardConfig:
    allowed_hosts: Set[str] = field(default_factory=set)   # empty = deny all navigation
    allow_any_host: bool = False
    max_steps: int = 25
    max_seconds: float = 180.0
    max_consecutive_failures: int = 3
    max_repeats: int = 2
    allow_irreversible: bool = False     # global kill switch for committing actions


class Guard:
    def __init__(self, cfg: GuardConfig):
        self.cfg = cfg
        self.t0 = time.time()
        self.failures = 0
        self.signatures: Dict[str, int] = {}
        self.refusals: List[dict] = []

    # ------------------------------------------------------------------ checks
    def _host_ok(self, url: str) -> bool:
        if self.cfg.allow_any_host:
            return True
        host = (urlparse(url).hostname or "").lower()
        return any(host == h or host.endswith("." + h) for h in self.cfg.allowed_hosts)

    def _signature(self, a: Action) -> str:
        return "|".join(str(v) for v in (a.verb, a.target, a.url, a.text, a.key))

    def check(self, a: Action, element_name: Optional[str] = None) -> Optional[str]:
        """Return a refusal reason, or None if the action may proceed."""
        if self.failures >= self.cfg.max_consecutive_failures:
            return f"budget: {self.failures} consecutive failures"
        if time.time() - self.t0 > self.cfg.max_seconds:
            return f"budget: exceeded {self.cfg.max_seconds}s"

        if a.verb == "navigate" and not self._host_ok(a.url or ""):
            return f"policy: host not in allowlist ({urlparse(a.url or '').hostname})"

        name = (element_name or a.target or "").lower()
        destructive = any(w in name for w in IRREVERSIBLE_WORDS)
        if not self.cfg.allow_irreversible:
            if destructive and not a.confirm:
                return f"policy: irreversible target {name!r} requires confirm=True"
            if a.verb in ("type", "key") and a.key in ("Enter", "Return") and destructive and not a.confirm:
                return "policy: Enter on a destructive element requires confirm=True"

        sig = self._signature(a)
        self.signatures[sig] = self.signatures.get(sig, 0) + 1
        if self.signatures[sig] > self.cfg.max_repeats:
            return f"budget: repeated action x{self.signatures[sig]} (max {self.cfg.max_repeats})"
        return None

    # ------------------------------------------------------------------ state
    def record(self, ok: bool) -> None:
        self.failures = 0 if ok else self.failures + 1

    def refuse(self, a: Action, reason: str) -> None:
        self.refusals.append({"verb": a.verb, "target": a.target, "reason": reason})

    def exhausted(self) -> Optional[str]:
        if self.failures >= self.cfg.max_consecutive_failures:
            return f"{self.failures} consecutive failures"
        if time.time() - self.t0 > self.cfg.max_seconds:
            return f"wall clock {time.time() - self.t0:.0f}s > {self.cfg.max_seconds:.0f}s"
        return None
