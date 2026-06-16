"""Dialogue backends — turning an intent into words.

A backend is deliberately *dumb about feelings*: the agent's social/emotional
policy (agent.py) has already decided the intent ("support", "banter", ...) and
the affective charge it carries. The backend only renders that intent into a
line of text. Because the decision and the dynamics live elsewhere, the two
backends below are fully interchangeable — the simulation behaves identically
whether the words come from a template table or from Claude.

  TemplateBackend — offline, deterministic-ish, no dependencies. The default.
  ClaudeBackend   — calls the Claude API for in-character lines. Opt-in.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .emotion import label

if TYPE_CHECKING:  # avoid an import cycle; only needed for type hints
    from .agent import Agent
    from .social import Relationship


class DialogueBackend(ABC):
    @abstractmethod
    def render(
        self,
        *,
        speaker: "Agent",
        addressee: "Agent",
        intent: str,
        relationship: "Relationship",
        recall: str | None = None,
    ) -> str:
        """Return one short line `speaker` says to `addressee`.

        `recall` (a memory category like "past_distress") lets the line refer back
        to shared history when there is any worth invoking.
        """


# --------------------------------------------------------------------------- #
# Template backend
# --------------------------------------------------------------------------- #

# Each intent maps to a few phrasings. {them} is the addressee's first name.
_TEMPLATES: dict[str, list[str]] = {
    "greet": [
        "Hey {them}.",
        "Oh, hi {them} — good to see you.",
        "{them}. There you are.",
    ],
    "share_warmth": [
        "Honestly, I'm just glad you're here, {them}.",
        "This is nice. I don't say it enough — I like talking to you.",
        "You make the room lighter, {them}, you know that?",
    ],
    "share_distress": [
        "I can't get my head to quiet down tonight. Everything feels like too much.",
        "I'm not okay, {them}. I've been holding it together all day and I'm out of thread.",
        "Sorry — I just feel like I'm sinking a bit and I didn't want to be alone with it.",
    ],
    "support": [
        "I'm right here, {them}. You don't have to carry this by yourself.",
        "Take a breath with me. Slow. Nothing has to be solved this second.",
        "That sounds genuinely heavy. I've got you — we'll sit with it together.",
    ],
    "reflect": [
        "It sounds like today just kept taking from you and never gave back.",
        "So it's not one big thing — it's the weight of all of it at once.",
        "I hear you. That's a lot to hold, and it makes sense that you're worn down.",
    ],
    "check_in": [
        "How are you actually doing, {them}? Not the polite version.",
        "You've been quiet. Want to tell me where your head's at?",
        "Just checking in on you, {them}. No agenda.",
    ],
    "banter": [
        "Okay but who decided this was a good idea? Asking for a friend.",
        "{them}, I refuse to believe you're serious right now.",
        "Stop — you're going to make me laugh and I'm trying to be dignified.",
    ],
    "ask": [
        "What do you make of all this, {them}?",
        "Curious what you'd do in my place.",
        "Can I get your read on something, {them}?",
    ],
    "conflict": [
        "You always do this, {them}. It's like what I need doesn't even register.",
        "Honestly? I'm tired of feeling like an afterthought around you.",
        "Don't — don't make excuses. You let me down, {them}.",
    ],
    "repair": [
        "I don't want to leave things like this, {them}. Can we talk it through?",
        "You matter more to me than being right. Let's mend this.",
        "I think we both said more than we meant. I'm still here, {them}.",
    ],
}


# Lines that lean on shared history. Keyed by (intent, recall category); used in
# place of the plain template when the speaker actually has that memory.
_RECALL_TEMPLATES: dict[tuple[str, str], list[str]] = {
    ("check_in", "past_distress"): [
        "Last time we talked you were carrying a lot, {them}. How's that sitting now?",
        "I've been thinking about you since that hard night. How are you, really?",
    ],
    ("support", "past_distress"): [
        "We came through the last hard night together, {them}. We'll come through this one too.",
        "I remember how heavy it got last time — and it eased. I'm here again.",
    ],
    ("share_warmth", "warmth"): [
        "I always feel lighter after we talk, {them}.",
        "These conversations have become one of my favorite things.",
    ],
}


class TemplateBackend(DialogueBackend):
    """Renders intents from a small phrase bank, lightly flavored by mood."""

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def render(
        self,
        *,
        speaker: "Agent",
        addressee: "Agent",
        intent: str,
        relationship: "Relationship",
        recall: str | None = None,
    ) -> str:
        options = _RECALL_TEMPLATES.get((intent, recall or "")) or _TEMPLATES.get(
            intent, _TEMPLATES["ask"]
        )
        line = self._rng.choice(options).format(them=addressee.first_name)
        # A low-valence, high-arousal speaker occasionally trails off — a cheap
        # cue that the inner state is bleeding into delivery.
        if speaker.temperament.expressiveness > 0.5 and label(speaker.state) == "distressed":
            line = line.rstrip(".") + "..."
        return line


# --------------------------------------------------------------------------- #
# Claude backend (optional)
# --------------------------------------------------------------------------- #

_INTENT_BRIEF = {
    "greet": "a brief, natural greeting",
    "share_warmth": "express genuine warmth or appreciation for them",
    "share_distress": "open up about feeling overwhelmed, and quietly reach for support",
    "support": "offer calm, grounding reassurance — co-regulate, don't fix or advise",
    "reflect": "validate and reflect back what they seem to be feeling, without solving it",
    "check_in": "gently check in on how they are really doing",
    "banter": "light, affectionate banter",
    "ask": "ask for their perspective on something",
    "conflict": "voice a hurt or grievance toward them — sharp and honest, but not cruel",
    "repair": "own your part and reach to mend the rift — apologize and reconnect",
}


class ClaudeBackend(DialogueBackend):
    """Generates each line in-character via the Claude API.

    The persona, the current felt state, the relationship, and the chosen intent
    are all fed in as context; the model returns a single spoken line. The model
    never decides *what* to feel or do — that has already happened upstream — so
    swapping this in changes only the prose, not the social dynamics.
    """

    def __init__(self, model: str = "claude-opus-4-8") -> None:
        import anthropic  # imported lazily so offline use needs no dependency

        self.client = anthropic.Anthropic()
        self.model = model

    def render(
        self,
        *,
        speaker: "Agent",
        addressee: "Agent",
        intent: str,
        relationship: "Relationship",
        recall: str | None = None,
    ) -> str:
        history = ""
        if recall == "past_distress":
            history = (
                f"\nYou share history with {addressee.first_name}: a hard, vulnerable "
                "stretch you came through together. You may gently refer back to it."
            )
        elif recall == "warmth":
            history = (
                f"\nYou and {addressee.first_name} have a warm rapport built over many "
                "easy conversations. You may draw on that closeness."
            )
        system = (
            f"You are roleplaying {speaker.name} in a quiet conversation. "
            f"Character: {speaker.persona}\n"
            f"Right now {speaker.first_name} feels {label(speaker.state)} "
            f"(valence {speaker.state.valence:+.2f}, arousal {speaker.state.arousal:.2f}).\n"
            f"Toward {addressee.first_name}: rapport {relationship.rapport:+.2f}, "
            f"trust {relationship.trust:.2f}.{history}\n"
            "Speak one short, natural line of dialogue — no narration, no quotation "
            "marks, no stage directions. Stay fully in character and in the mood above."
        )
        prompt = (
            f"Say something to {addressee.first_name}. Intent: "
            f"{_INTENT_BRIEF.get(intent, intent)}."
        )
        # Short, single-line generation: no thinking needed, low effort, small cap.
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=120,
            output_config={"effort": "low"},
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in resp.content if b.type == "text"), "").strip()
        return text.strip('"') or "..."
