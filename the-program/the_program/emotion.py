"""Affect model and emotional regulation.

A compact dimensional model of emotion (Russell's circumplex): every feeling is a
point in two dimensions — *valence* (unpleasant .. pleasant) and *arousal* (calm ..
activated). On top of that sit the three mechanisms that make the state move:

  appraise()  — an external event (something said) perturbs the state
  regulate()  — the state drifts back toward a temperamental baseline (homeostasis)
  contagion() — simply witnessing another's state exerts a pull of its own

Emotional *regulation* in this model is the interplay of two things: the agent's
own `regulation` trait (how fast it returns to baseline and how much it damps
spikes), and co-regulation — another agent deliberately pushing it back toward
calm. The companion layer in agent.py leans entirely on this file.
"""

from __future__ import annotations

from dataclasses import dataclass


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


@dataclass
class Temperament:
    """Stable individual differences — the dial settings an agent is born with."""

    baseline_valence: float = 0.2   # the mood it rests at when left alone
    baseline_arousal: float = 0.35
    sensitivity: float = 1.0        # how strongly events move its affect
    regulation: float = 0.25        # 0..1 self-regulation: return speed + spike damping
    empathy: float = 0.5            # susceptibility to others' expressed affect
    expressiveness: float = 0.6     # how much of its inner state leaks into its words


@dataclass
class EmotionalState:
    """Where an agent is *right now* in affect space."""

    valence: float = 0.0    # -1 unpleasant .. +1 pleasant
    arousal: float = 0.35   #  0 calm       ..  1 activated

    def copy(self) -> "EmotionalState":
        return EmotionalState(self.valence, self.arousal)


@dataclass
class Affect:
    """A directed affective charge carried by an utterance toward a listener.

    Positive valence is warm/pleasant; negative is cold/unpleasant. Positive
    arousal is activating; negative arousal is *calming* — which is exactly what
    a soothing, co-regulating message carries.
    """

    valence: float = 0.0
    arousal: float = 0.0

    def scaled(self, k: float) -> "Affect":
        return Affect(self.valence * k, self.arousal * k)


def label(state: EmotionalState) -> str:
    """A human-readable word for a region of affect space (for the readout)."""
    v, a = state.valence, state.arousal
    if a >= 0.6:
        if v >= 0.25:
            return "elated"
        if v <= -0.25:
            return "distressed"
        return "tense"
    if a <= 0.30:
        if v >= 0.25:
            return "content"
        if v <= -0.25:
            return "low"
        return "calm"
    if v >= 0.25:
        return "warm"
    if v <= -0.25:
        return "uneasy"
    return "neutral"


def appraise(
    state: EmotionalState,
    temperament: Temperament,
    signal: Affect,
    openness: float = 1.0,
) -> None:
    """Let an incoming affective signal move the state, in place.

    `openness` scales how much *this* source gets through — trust and rapport open
    the door, distance closes it. A well-regulated agent damps the magnitude of
    any spike (a stand-in for cognitive reappraisal).
    """
    damp = 1.0 - 0.5 * temperament.regulation
    gain = temperament.sensitivity * openness * damp
    state.valence = clamp(state.valence + gain * signal.valence, -1.0, 1.0)
    state.arousal = clamp(state.arousal + gain * signal.arousal, 0.0, 1.0)


def regulate(
    state: EmotionalState,
    temperament: Temperament,
    connection: float | None = None,
) -> None:
    """Drift the state back toward baseline — endogenous emotional regulation.

    If `connection` (social satisfaction, 0..1) is supplied, loneliness lowers the
    mood the agent settles toward and connectedness raises it: companionship
    matters even when nothing is wrong.
    """
    r = temperament.regulation
    target_v = temperament.baseline_valence
    if connection is not None:
        target_v = clamp(target_v + 0.5 * (connection - 0.6), -1.0, 1.0)
    state.valence += r * (target_v - state.valence)
    state.arousal += r * (temperament.baseline_arousal - state.arousal)


def contagion(speaker: EmotionalState, listener_baseline_arousal: float = 0.35) -> Affect:
    """The ambient pull of simply being near someone in a given state.

    Valence is mildly catching; arousal pulls the listener toward the speaker's
    level — an agitated speaker activates you, a serene one settles you.
    """
    return Affect(
        valence=0.40 * speaker.valence,
        arousal=0.30 * (speaker.arousal - listener_baseline_arousal),
    )
