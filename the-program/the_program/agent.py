"""Agents and their decision policy.

An agent is a persona + a temperament + a current emotional state + a small
amount of social bookkeeping (a `connection` level — how socially nourished it
feels). Its one interesting method is `decide()`: given the room and the social
field, what does it want to express, and to whom?

The policy is deliberately legible rather than learned:

  * a *companion* whose partner is hurting moves to support / co-regulate them;
  * an agent in distress reaches toward whoever it trusts most;
  * a socially-depleted agent seeks warmth or checks in on a close other;
  * otherwise it keeps the social fabric warm with banter, warmth, or a question.

The affective charge each intent carries is what listeners actually appraise.
Support is special: its charge is computed to *counter* the partner's deviation
from calm — more warmth the lower they are, more soothing the more activated
they are. That adaptive charge is the mechanical heart of co-regulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .emotion import Affect, EmotionalState, Temperament, clamp
from .memory import Memory
from .social import SocialField


# Fixed affective charge for the non-adaptive intents. (support is computed.)
_INTENT_AFFECT: dict[str, Affect] = {
    "greet": Affect(0.10, 0.00),
    "share_warmth": Affect(0.40, 0.05),
    "share_distress": Affect(-0.30, 0.30),   # venting pulls the listener down a little
    "reflect": Affect(0.22, -0.18),
    "check_in": Affect(0.16, -0.05),
    "banter": Affect(0.26, 0.16),
    "ask": Affect(0.06, 0.06),
    "conflict": Affect(-0.55, 0.45),    # a grievance: cold and agitating
    "repair": Affect(0.42, -0.10),      # mending: warm and a touch settling
}


@dataclass
class Decision:
    """What an agent has chosen to do on its turn."""

    addressee: "Agent"
    intent: str
    affect: Affect


@dataclass
class Agent:
    name: str
    persona: str
    temperament: Temperament
    role: str = "peer"                      # "peer" or "companion"
    partner: str | None = None             # name of the agent a companion attends to
    state: EmotionalState = field(default_factory=EmotionalState)
    connection: float = 0.6                 # 0..1 social satisfaction; decays over time
    memory: Memory | None = None            # episodic memory of others (set in __post_init__)

    def __post_init__(self) -> None:
        if self.memory is None:
            self.memory = Memory(self.name)

    @property
    def first_name(self) -> str:
        return self.name.split()[0]

    # -- self-knowledge -------------------------------------------------- #

    def is_distressed(self) -> bool:
        # Unpleasant low mood, or *unpleasant* activation — high arousal with
        # positive valence is excitement/elation, not distress.
        return self.state.valence < -0.15 or (self.state.valence < 0.10 and self.state.arousal > 0.70)

    # -- the policy ------------------------------------------------------ #

    def decide(self, others: list["Agent"], field: SocialField) -> Decision:
        """Choose an intent and a target. `others` excludes self."""
        if not others:  # nobody to talk to
            return Decision(self, "reflect", _INTENT_AFFECT["reflect"])

        # 1. A companion prioritizes a partner who is struggling — and, even once
        #    they've settled, proactively checks in if they've had a rough patch.
        if self.role == "companion":
            target = self._find(others, self.partner)
            if target is not None and target.is_distressed():
                rel = field.rel(self.name, target.name)
                # Validate first while still strangers; co-regulate once trusted.
                if rel.trust < 0.25 and rel.familiarity < 0.4:
                    return Decision(target, "reflect", _INTENT_AFFECT["reflect"])
                return Decision(target, "support", self._support_affect(target, rel))
            if target is not None and self.memory.hard_streak(target.name) >= 2:
                return Decision(target, "check_in", _INTENT_AFFECT["check_in"])

        # 2. Mend an open rift — but only once I've cooled down enough to do it well.
        rifts = [o for o in others if self.memory.open_rift(o.name)]
        if rifts and self.state.arousal < 0.60:
            return Decision(rifts[0], "repair", _INTENT_AFFECT["repair"])

        # 3. Friction: if I'm irritated and sour on someone, I let it out — but only
        #    once (an existing rift blocks me from re-attacking; I cool off instead).
        if self.state.valence < -0.10 and self.state.arousal > 0.55:
            sour = min(others, key=lambda o: field.rel(self.name, o.name).rapport)
            if field.rel(self.name, sour.name).rapport < -0.05 and not self.memory.open_rift(sour.name):
                return Decision(sour, "conflict", _INTENT_AFFECT["conflict"])

        # 4. If I'm the one hurting, reach toward whoever I trust most.
        if self.is_distressed():
            confidant = max(others, key=lambda o: field.rel(self.name, o.name).trust)
            return Decision(confidant, "share_distress", _INTENT_AFFECT["share_distress"])

        # 5. If I'm running low on connection, seek it from my closest tie.
        if self.connection < 0.4:
            closest = max(others, key=lambda o: field.rel(self.name, o.name).rapport)
            intent = "check_in" if closest.is_distressed() else "share_warmth"
            return Decision(closest, intent, _INTENT_AFFECT[intent])

        # 6. Otherwise keep the fabric warm. Tend to a struggling other if present.
        struggling = [o for o in others if o.is_distressed()]
        if struggling:
            target = struggling[0]
            return Decision(target, "check_in", _INTENT_AFFECT["check_in"])
        target = max(others, key=lambda o: field.rel(self.name, o.name).rapport)
        intent = "banter" if self.state.valence > 0.3 else "ask"
        return Decision(target, intent, _INTENT_AFFECT[intent])

    # -- helpers --------------------------------------------------------- #

    def _support_affect(self, target: "Agent", rel) -> Affect:
        """Co-regulation: a charge shaped to pull `target` back toward calm."""
        deficit = max(0.0, -target.state.valence)        # how far below neutral
        excess = max(0.0, target.state.arousal - 0.40)   # how over-activated
        warmth = 0.40 + 0.45 * deficit
        soothe = -(0.30 + 0.55 * excess)
        # Comfort lands harder from an empathetic companion, and the deeper the
        # history (rapport now, plus the bond built from past hard moments).
        bond = self.memory.bond(target.name)
        gain = self.temperament.empathy * (0.50 + 0.30 * max(0.0, rel.rapport) + 0.30 * bond)
        return Affect(clamp(warmth * gain, 0.0, 1.0), clamp(soothe * gain, -1.0, 0.0))

    @staticmethod
    def _find(agents: list["Agent"], name: str | None) -> "Agent | None":
        if name is None:
            return None
        return next((a for a in agents if a.name == name), None)
