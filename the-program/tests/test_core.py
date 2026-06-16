"""Core invariants for The Program.

These tests pin the *dynamics*, not the prose: affect moves in the right
direction, relationships and memory update sanely, and the two showcase arcs
(co-regulation, rupture-and-repair) actually resolve. Speaker selection is
deterministic, and dialogue text never feeds back into the numbers, so the
integration assertions below are reproducible.
"""

from __future__ import annotations

import contextlib
import io

import pytest

from the_program import (
    Agent,
    Affect,
    EmotionalState,
    LexiconAppraiser,
    Memory,
    SocialField,
    Temperament,
    companionship_world,
    reconciliation_world,
)
from the_program.emotion import appraise, clamp, contagion, regulate
from the_program.social import openness


def _run_silent(program, steps: int) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        for _ in range(steps):
            program.step()


# --------------------------------------------------------------------------- #
# emotion
# --------------------------------------------------------------------------- #

def test_clamp():
    assert clamp(2.0, 0.0, 1.0) == 1.0
    assert clamp(-2.0, 0.0, 1.0) == 0.0
    assert clamp(0.5, 0.0, 1.0) == 0.5


def test_appraise_moves_in_signal_direction():
    s = EmotionalState(valence=0.0, arousal=0.4)
    t = Temperament(sensitivity=1.0, regulation=0.0)
    appraise(s, t, Affect(valence=0.5, arousal=-0.2), openness=1.0)
    assert s.valence > 0.0
    assert s.arousal < 0.4


def test_regulation_damps_spikes():
    """A well-regulated agent should move less for the same signal."""
    signal = Affect(valence=-0.8, arousal=0.5)
    calm = EmotionalState(0.0, 0.4)
    reactive = EmotionalState(0.0, 0.4)
    appraise(calm, Temperament(sensitivity=1.0, regulation=0.9), signal, 1.0)
    appraise(reactive, Temperament(sensitivity=1.0, regulation=0.0), signal, 1.0)
    assert abs(calm.valence) < abs(reactive.valence)


def test_regulate_returns_toward_baseline():
    s = EmotionalState(valence=-0.5, arousal=0.9)
    t = Temperament(baseline_valence=0.2, baseline_arousal=0.4, regulation=0.5)
    regulate(s, t)
    assert s.valence > -0.5
    assert s.arousal < 0.9


def test_contagion_sign_follows_speaker():
    pull = contagion(EmotionalState(valence=0.8, arousal=0.8))
    assert pull.valence > 0          # a positive speaker pulls you up
    assert pull.arousal > 0          # an activated speaker activates you


# --------------------------------------------------------------------------- #
# social
# --------------------------------------------------------------------------- #

def test_attuned_builds_trust_misfire_erodes_it():
    field = SocialField()
    field.record_interaction("A", "B", attuned=True, warmth=0.5)
    assert field.rel("A", "B").trust > 0.0
    assert field.rel("A", "B").familiarity > 0.0

    before = field.rel("A", "B").trust
    field.record_interaction("A", "B", attuned=False, warmth=-0.2)
    assert field.rel("A", "B").trust < before


def test_openness_increases_with_trust():
    low = SocialField().rel("A", "B")
    high = SocialField().rel("A", "B")
    high.trust = 0.9
    assert openness(high) > openness(low)


# --------------------------------------------------------------------------- #
# memory
# --------------------------------------------------------------------------- #

def test_conflict_does_not_build_bond_but_repair_does():
    m = Memory("X")
    m.remember(1, "Y", "conflict", hard=True)
    assert m.bond("Y") == 0.0
    assert m.open_rift("Y") is True

    m.remember(2, "Y", "repair", hard=False)
    assert m.open_rift("Y") is False     # the repair closes the rift
    assert m.bond("Y") > 0.0             # ...and deepens the bond


def test_bond_grows_with_shared_hard_moments():
    m = Memory("X")
    m.remember(1, "Y", "share_warmth", hard=False)
    light = m.bond("Y")
    m.remember(2, "Y", "support", hard=True)
    assert m.bond("Y") > light


# --------------------------------------------------------------------------- #
# agent policy
# --------------------------------------------------------------------------- #

def test_is_distressed_excludes_positive_high_arousal():
    assert Agent("A", "", Temperament(), state=EmotionalState(-0.4, 0.5)).is_distressed()
    # elated: high arousal but very positive valence is not distress
    assert not Agent("A", "", Temperament(), state=EmotionalState(0.8, 0.9)).is_distressed()


def test_companion_supports_distressed_partner():
    comp = Agent(
        "C", "", Temperament(empathy=0.8, regulation=0.4),
        role="companion", partner="P", state=EmotionalState(0.3, 0.3),
    )
    partner = Agent("P", "", Temperament(), state=EmotionalState(-0.5, 0.8))
    field = SocialField()
    field.rel("C", "P").trust = 0.5
    field.rel("C", "P").familiarity = 0.5
    decision = comp.decide([partner], field)
    assert decision.intent in ("support", "reflect")
    assert decision.addressee is partner


def test_calm_agent_repairs_an_open_rift():
    a = Agent("A", "", Temperament(), state=EmotionalState(0.1, 0.4))
    b = Agent("B", "", Temperament())
    a.memory.remember(1, "B", "conflict", hard=True)
    assert a.decide([b], SocialField()).intent == "repair"


def test_grievance_is_voiced_once_then_no_re_attack():
    a = Agent("A", "", Temperament(regulation=0.2), state=EmotionalState(-0.2, 0.7))
    b = Agent("B", "", Temperament())
    field = SocialField()
    field.rel("A", "B").rapport = -0.3
    assert a.decide([b], field).intent == "conflict"

    a.memory.remember(1, "B", "conflict", hard=True)   # rift now open
    assert a.decide([b], field).intent != "conflict"   # cools off instead of escalating


# --------------------------------------------------------------------------- #
# appraisal
# --------------------------------------------------------------------------- #

def test_lexicon_appraiser_reads_polarity():
    neg_v, neg_a = LexiconAppraiser().appraise("i am exhausted, anxious and alone")
    assert neg_v < 0.0
    assert neg_a > 0.35
    pos_v, _ = LexiconAppraiser().appraise("i feel great and grateful")
    assert pos_v > 0.0


# --------------------------------------------------------------------------- #
# integration — the two showcase arcs resolve
# --------------------------------------------------------------------------- #

def test_co_regulation_arc_recovers_the_distressed_agent():
    program = companionship_world()
    mara = next(a for a in program.agents if a.name == "Mara")
    v0, a0 = mara.state.valence, mara.state.arousal
    assert mara.is_distressed()
    _run_silent(program, 12)
    assert mara.state.valence > v0 + 0.4   # mood climbs
    assert mara.state.arousal < a0 - 0.2   # arousal settles
    assert not mara.is_distressed()


def test_rupture_and_repair_arc_reconciles():
    program = reconciliation_world()
    assert program.field.rel("Theo", "Mara").rapport < 0   # seeded grievance
    _run_silent(program, 12)

    mara = next(a for a in program.agents if a.name == "Mara")
    theo = next(a for a in program.agents if a.name == "Theo")
    # the rift was opened and then closed
    kinds = {e.kind for e in theo.memory.about("Mara")}
    assert "conflict" in kinds and "repair" in kinds
    assert not mara.memory.open_rift("Theo")
    assert not theo.memory.open_rift("Mara")
    # rapport recovered into the positive
    assert program.field.rel("Theo", "Mara").rapport > 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
