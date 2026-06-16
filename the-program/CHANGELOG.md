# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-16

First public release. A small, dependency-free multi-agent sandbox for affect,
social dynamics, and companionship.

### Added
- **Affect model** (`emotion.py`): valence×arousal state with appraisal,
  homeostatic regulation, and emotional contagion.
- **Social dynamics** (`social.py`): directed familiarity / rapport / trust, and
  trust-gated openness to others' affect.
- **Episodic memory** (`memory.py`): per-agent memory, an accumulated bond
  (vulnerable moments weigh most), pattern-noticing, and rift tracking.
- **Companion role** (`agent.py`): co-regulation of a distressed partner, with a
  support charge shaped to counter their deviation from calm.
- **Conflict & repair**: `conflict` / `repair` intents, voiced-once / cool-down
  de-escalation, and rupture tracking that a repair closes.
- **Pluggable backends** (`backends.py`): offline `TemplateBackend` and a
  `ClaudeBackend` using the Anthropic API.
- **Pluggable appraisers** (`appraisal.py`): offline `LexiconAppraiser` and a
  `ClaudeAppraiser` using structured output, with lexicon fallback.
- **Scenarios & CLI**: `demo`, `demo --reunion`, `rift`, and an interactive
  `chat`; runnable via `the-program`, `python -m the_program`, or `run.py`.
- Test suite, packaging, and contributor docs.

[Unreleased]: https://github.com/yuri-bizzoni/the-program/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yuri-bizzoni/the-program/releases/tag/v0.1.0
