"""Episodic memory — what each agent carries from past exchanges.

Momentary affect (emotion.py) and standing relationships (social.py) capture the
*present* and a running average of the past. Memory is different: it keeps the
specific moments, so an agent can come back to them. Companionship lives here —
being remembered, having a hard night referred back to, a bond that is more than
the sum of the last few minutes.

Three things are read off the episode list:

  bond()            — accumulated closeness; shared *hard* moments weigh most
  hard_streak()     — how often the other has recently been struggling
  recall_category() — the kind of shared past worth referring back to in dialogue
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Intents worth committing to memory at all (banter and greetings are forgotten).
SALIENT_INTENTS = {
    "support", "share_distress", "reflect", "share_warmth", "check_in", "conflict", "repair",
}


@dataclass
class Episode:
    t: int
    other: str      # who the moment was with
    kind: str       # the intent that occurred
    hard: bool      # was it a vulnerable / distressing moment they shared?


@dataclass
class Memory:
    owner: str
    episodes: list[Episode] = field(default_factory=list)

    def remember(self, t: int, other: str, kind: str, hard: bool) -> None:
        self.episodes.append(Episode(t, other, kind, hard))

    def about(self, other: str) -> list[Episode]:
        return [e for e in self.episodes if e.other == other]

    def bond(self, other: str) -> float:
        """Accumulated closeness with `other`, 0..1 (saturating).

        Hard moments — being there for someone, being seen at your lowest, or
        mending a rift — deepen a bond more than easy ones. Conflict on its own
        does not build closeness (only the repair afterwards does).
        """
        score = 0.0
        for e in self.about(other):
            if e.kind == "conflict":
                continue
            score += 0.5 if (e.hard or e.kind == "repair") else 0.22
        return min(1.0, score / 4.0)

    def hard_streak(self, other: str, window: int = 6) -> int:
        """How many of the recent shared moments with `other` were hard ones
        (distress *or* conflict — i.e. signs the relationship needs tending)."""
        return sum(1 for e in self.about(other)[-window:] if e.hard)

    def open_rift(self, other: str) -> bool:
        """Is there an unresolved conflict with `other` — a clash not yet repaired?"""
        ruptures = [e for e in self.about(other) if e.kind in ("conflict", "repair")]
        return bool(ruptures) and ruptures[-1].kind == "conflict"

    def recall_category(self, other: str) -> str | None:
        """What, if anything, is worth referring back to with `other`."""
        eps = self.about(other)
        if any(e.hard and e.kind != "conflict" for e in eps):
            return "past_distress"      # a hard stretch they came through together
        if any(e.kind in ("share_warmth", "check_in", "repair") for e in eps):
            return "warmth"             # easy / mended, warm conversations
        return None

    def phrase(self, other: str) -> str:
        """A human-readable summary of what the owner carries about `other`."""
        cat = self.recall_category(other)
        if cat == "past_distress":
            return "a hard stretch they came through together"
        if cat == "warmth":
            return "easy, warm conversations"
        return "a few first exchanges"
