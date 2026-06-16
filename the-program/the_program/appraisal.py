"""Appraisers — reading the affect in a line of text.

In the chat loop, whatever you type has to be turned into a felt charge (valence,
arousal) before the companion's emotion model can respond to it. That reading is
its own pluggable concern, mirroring the dialogue backends:

  LexiconAppraiser — a tiny, transparent keyword scorer. Offline default.
  ClaudeAppraiser  — asks Claude to rate the line via structured output, with the
                     lexicon kept as a fallback if a call fails.

Both return ``(valence -1..1, arousal 0..1)`` so the chat loop is agnostic to
which one is in use.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod

from .emotion import clamp


class Appraiser(ABC):
    #: short label for the chat banner ("lexicon" / "Claude")
    kind: str = "appraiser"

    @abstractmethod
    def appraise(self, text: str) -> tuple[float, float]:
        """Return (valence -1..1, arousal 0..1) for a single line of text."""


# --------------------------------------------------------------------------- #
# Lexicon appraiser (offline default)
# --------------------------------------------------------------------------- #

_NEG = {
    "sad", "tired", "exhausted", "anxious", "scared", "afraid", "alone", "lonely",
    "overwhelmed", "awful", "terrible", "cant", "hate", "hopeless", "stressed",
    "worried", "down", "empty", "numb", "lost", "hurt", "crying", "panic", "sinking",
    "drowning", "broken", "worthless", "ashamed", "guilty", "angry",
}
_POS = {
    "good", "great", "happy", "glad", "love", "grateful", "thanks", "thank",
    "better", "calm", "excited", "relieved", "okay", "fine", "nice", "wonderful",
    "hopeful", "proud", "peaceful", "safe", "warm",
}


class LexiconAppraiser(Appraiser):
    """Counts affect-laden words. Deliberately crude — not a real classifier."""

    kind = "lexicon"

    def appraise(self, text: str) -> tuple[float, float]:
        words = [w.replace("'", "") for w in re.findall(r"[a-z']+", text.lower())]
        pos = sum(w in _POS for w in words)
        neg = sum(w in _NEG for w in words)
        valence = (pos - neg) / (pos + neg) if (pos + neg) else 0.0

        bangs = text.count("!")
        caps = sum(1 for w in re.findall(r"[A-Za-z]+", text) if len(w) > 2 and w.isupper())
        arousal = 0.35 + 0.10 * bangs + 0.08 * caps + 0.20 * neg
        return clamp(valence, -1.0, 1.0), clamp(arousal, 0.0, 1.0)


# --------------------------------------------------------------------------- #
# Claude appraiser (opt-in)
# --------------------------------------------------------------------------- #

_SCHEMA = {
    "type": "object",
    "properties": {
        "valence": {
            "type": "number",
            "description": "Emotional tone from -1 (very negative / distressed) to +1 (very positive).",
        },
        "arousal": {
            "type": "number",
            "description": "Activation from 0 (calm, flat, settled) to 1 (highly activated / agitated).",
        },
    },
    "required": ["valence", "arousal"],
    "additionalProperties": False,
}

_SYSTEM = (
    "You rate the emotional tone of a single short message from one person. "
    "Return only the two numbers as specified by the schema. "
    "valence: -1 very negative/distressed .. +1 very positive. "
    "arousal: 0 calm/flat .. 1 highly activated/agitated."
)


class ClaudeAppraiser(Appraiser):
    """Reads affect via the Claude API using a constrained JSON schema.

    Falls back to the lexicon appraiser if the SDK call fails for any reason, so a
    transient network error never breaks the conversation.
    """

    kind = "Claude"

    def __init__(self, model: str = "claude-opus-4-8") -> None:
        import anthropic  # imported lazily so offline use needs no dependency

        self.client = anthropic.Anthropic()
        self.model = model
        self._fallback = LexiconAppraiser()

    def appraise(self, text: str) -> tuple[float, float]:
        try:
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
                system=_SYSTEM,
                messages=[{"role": "user", "content": text}],
            )
            raw = next(b.text for b in resp.content if b.type == "text")
            data = json.loads(raw)
            return clamp(float(data["valence"]), -1.0, 1.0), clamp(float(data["arousal"]), 0.0, 1.0)
        except Exception:
            return self._fallback.appraise(text)
