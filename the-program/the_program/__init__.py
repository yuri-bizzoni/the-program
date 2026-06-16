"""The Program — a lightweight multi-agent conversational environment.

A small, dependency-free sandbox where a handful of agents talk to one another.
Each agent carries a *dimensional* emotional state (valence x arousal), regulates
that state back toward a temperamental baseline, and is pulled around by the
people it talks to. On top of that base sits a *companionship* layer: a companion
agent attunes to a partner, validates them, and co-regulates them out of distress.

The package separates three concerns so any one can be swapped:

    emotion.py   — affect, appraisal, and emotional regulation (the inner loop)
    social.py    — relationships and the social field (who is close to whom)
    agent.py     — an agent's decision policy (what to express, and to whom)
    backends.py  — how an intent becomes words (templates, or the Claude API)
    program.py   — the orchestrator: turns, contagion, scenarios, the chat loop
"""

from .emotion import EmotionalState, Temperament, Affect, label
from .social import Relationship, SocialField
from .memory import Memory, Episode
from .agent import Agent, Decision
from .backends import DialogueBackend, TemplateBackend, ClaudeBackend
from .appraisal import Appraiser, LexiconAppraiser, ClaudeAppraiser
from .program import Program, companionship_world, reconciliation_world, chat_world

__all__ = [
    "EmotionalState",
    "Temperament",
    "Affect",
    "label",
    "Relationship",
    "SocialField",
    "Memory",
    "Episode",
    "Agent",
    "Decision",
    "DialogueBackend",
    "TemplateBackend",
    "ClaudeBackend",
    "Appraiser",
    "LexiconAppraiser",
    "ClaudeAppraiser",
    "Program",
    "companionship_world",
    "reconciliation_world",
    "chat_world",
]
