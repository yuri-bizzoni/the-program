"""Relationships and the social field.

Each agent holds a *directed* view of every other agent — how well it knows them
(familiarity), how warm it feels toward them (rapport), and how much it will let
them move its emotions (trust). These are not symmetric: a companion can trust a
partner long before the partner trusts back.

Relationships are what make the same words land differently depending on who says
them. `openness()` turns a relationship into the gain used by emotion.appraise():
a warm, trusted voice gets through; a stranger barely registers.
"""

from __future__ import annotations

from dataclasses import dataclass

from .emotion import clamp


@dataclass
class Relationship:
    """A's standing model of B (one direction of the pair)."""

    familiarity: float = 0.0   # 0..1  how well A knows B
    rapport: float = 0.0       # -1..1 warmth / closeness
    trust: float = 0.0         # 0..1  willingness to be moved by B


def openness(rel: Relationship) -> float:
    """How wide A holds the door open to B's affect — the appraisal gain."""
    return clamp(0.30 + 0.55 * rel.trust + 0.25 * max(0.0, rel.rapport), 0.15, 1.25)


class SocialField:
    """The full matrix of who-feels-what-about-whom, plus its update rules."""

    def __init__(self) -> None:
        self._rel: dict[tuple[str, str], Relationship] = {}

    def rel(self, a: str, b: str) -> Relationship:
        """A's relationship toward B, created lazily on first access."""
        key = (a, b)
        if key not in self._rel:
            self._rel[key] = Relationship()
        return self._rel[key]

    def record_interaction(
        self,
        observer: str,
        other: str,
        *,
        attuned: bool,
        warmth: float,
    ) -> None:
        """Update `observer`'s view of `other` after one exchange between them.

        Familiarity always grows a little (saturating). Rapport eases toward the
        warmth that was exchanged. Trust climbs when the exchange was *attuned* —
        the right response at the right moment — and erodes slightly when it
        misfired (e.g. breezy banter aimed at someone in distress).
        """
        r = self.rel(observer, other)
        r.familiarity = clamp(r.familiarity + 0.06 * (1.0 - r.familiarity), 0.0, 1.0)
        r.rapport = clamp(r.rapport + 0.18 * (clamp(warmth, -1.0, 1.0) - r.rapport), -1.0, 1.0)
        if attuned:
            r.trust = clamp(r.trust + 0.12 * (1.0 - r.trust), 0.0, 1.0)
        else:
            r.trust = clamp(r.trust - 0.05, 0.0, 1.0)
