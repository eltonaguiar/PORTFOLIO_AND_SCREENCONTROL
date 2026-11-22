"""Planners: the thing that turns an observation into an Action.

Three implementations, deliberately:

  ScriptedPlanner  — a deterministic policy. Used to certify that the *mechanics*
                     (perceive/act/verify/guard) work, with zero dependence on a model.
                     If the loop only works with an LLM in it, you cannot tell a
                     mechanics bug from a model error.
  LLMPlanner       — OpenAI-compatible chat completion. Constrained to emit one JSON
                     action per turn. Retries once on malformed JSON, then fails.
  AgentPlanner     — the human/agent-in-the-loop adapter: the observation is printed
                     as JSON and the action is read back on stdin. This is how an
                     operator drives the same loop by hand, and how a Hermes-style
                     agent can be substituted for a chat model.

The prompt is part of the contract: it names the allowed verbs, forbids coordinates
unless there is no element handle, and requires a post-condition on every action.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Callable, Dict, List, Optional

from .schema import Action, VERBS


SYSTEM_PROMPT = """You are a screen-control agent. Each turn you receive an observation of
the current screen and must reply with EXACTLY ONE JSON object describing one action.

Allowed verbs: {verbs}.

Rules:
1. Prefer `target` (an element handle from the observation) over x/y coordinates.
   Coordinates are a last resort and must be justified in `thought`.
2. Every action must include `thought` (one sentence: why this action, now).
3. Set `expect` to a short description of the visible change you expect. The runtime
   verifies it; an action whose expectation does not materialise counts as a failure.
4. Never invent element handles. Only use handles that appear in the observation.
5. If the task is complete, reply {{"verb":"done","thought":"...","text":"summary"}}.
   If it cannot be completed, reply {{"verb":"fail","thought":"...","text":"reason"}}.
6. Irreversible actions (buy, send, submit, delete, pay) require "confirm": true.

Reply with the JSON object only. No prose, no code fences.
"""


class Planner:
    def act(self, observation: dict, history: List[dict]) -> Action:  # pragma: no cover
        raise NotImplementedError


class ScriptedPlanner(Planner):
    """Deterministic policy: a list of callables or literal Actions, in order."""

    def __init__(self, script: List):
        self.script = list(script)
        self.i = 0

    def act(self, observation: dict, history: List[dict]) -> Action:
        if self.i >= len(self.script):
            return Action(verb="done", thought="script exhausted", text="script complete")
        step = self.script[self.i]
        self.i += 1
        if callable(step):
            return step(observation, history)
        # Not validated here on purpose: the loop validates, so an invalid scripted
        # action lands in the same "invalid action" code path as a bad model output.
        if isinstance(step, dict):
            return Action.from_dict(step)
        return step


class AgentPlanner(Planner):
    """Agent-in-the-loop: prints the observation, reads one JSON action from stdin.

    This is the adapter that lets a human operator, or an external agent process,
    drive the same guarded loop that an LLM would drive.
    """

    def __init__(self, infile=None, outfile=None):
        import sys

        self.infile = infile or sys.stdin
        self.outfile = outfile or sys.stdout

    def act(self, observation: dict, history: List[dict]) -> Action:
        payload = {
            "observation": observation,
            "history": [{"verb": h.get("verb"), "ok": h.get("ok"), "detail": h.get("detail")} for h in history[-5:]],
        }
        self.outfile.write("\n=== OBSERVATION ===\n")
        self.outfile.write(json.dumps(payload, indent=1)[:6000])
        self.outfile.write("\n=== ACTION (JSON) ===\n")
        self.outfile.flush()
        line = self.infile.readline()
        return Action.from_dict(json.loads(line)).validate()


class LLMPlanner(Planner):
    """OpenAI-compatible chat completion, one action per turn.

    Config via env: SC_LLM_BASE_URL, SC_LLM_MODEL, SC_LLM_API_KEY.
    Kept dependency-free (urllib) so it runs anywhere without an SDK.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        timeout: int = 60,
    ):
        self.base_url = (base_url or os.environ.get("SC_LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("SC_LLM_MODEL") or "gpt-4o-mini"
        self.api_key = api_key or os.environ.get("SC_LLM_API_KEY") or ""
        self.temperature = temperature
        self.timeout = timeout
        self.system = SYSTEM_PROMPT.format(verbs=", ".join(sorted(VERBS)))

    def _call(self, messages: List[dict]) -> str:
        body = json.dumps(
            {"model": self.model, "messages": messages, "temperature": self.temperature}
        ).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"},
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            d = json.load(r)
        return d["choices"][0]["message"]["content"]

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = text.strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, flags=re.S)
            if not m:
                raise
            return json.loads(m.group(0))

    def act(self, observation: dict, history: List[dict]) -> Action:
        user = json.dumps(
            {
                "observation": observation,
                "history": [
                    {"step": h.get("step"), "verb": h.get("verb"), "ok": h.get("ok"), "detail": h.get("detail")}
                    for h in history[-6:]
                ],
            }
        )
        messages = [
            {"role": "system", "content": self.system},
            {"role": "user", "content": user},
        ]
        last_err = None
        for attempt in range(2):
            raw = self._call(messages)
            try:
                d = self._extract_json(raw)
                return Action.from_dict(d).validate()
            except Exception as exc:  # malformed JSON or invalid action
                last_err = exc
                messages.append({"role": "assistant", "content": raw})
                messages.append(
                    {
                        "role": "user",
                        "content": f"That was not a valid action ({exc}). Reply with one JSON action object only.",
                    }
                )
        return Action(verb="fail", thought=f"planner produced invalid output twice: {last_err}",
                      text=str(last_err))
