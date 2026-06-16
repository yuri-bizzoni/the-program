# Contributing to The Program

Thanks for being here. The Program is a small, readable sandbox for multi-agent
affect, social dynamics, and companionship. It's meant to be *hackable* — if you
can read the code, you can extend it. Contributions of all sizes are welcome:
new intents, scenarios, backends, appraisers, tuning, docs, and tests.

## Quick start

```bash
git clone https://github.com/yuri-bizzoni/the-program
cd the-program
python -m pip install -e ".[dev]"   # core has no deps; this adds pytest
python -m pytest                    # run the tests
python run.py demo                  # see it work
```

No API key is needed for anything in the test suite or the offline scenarios.
The Claude backend/appraiser (`pip install -e ".[llm]"`, `--llm`) is optional.

## The shape of the code

| File | What lives there |
|------|------------------|
| `the_program/emotion.py`   | Affect (valence×arousal), `appraise` / `regulate` / `contagion`. |
| `the_program/social.py`    | Relationships (familiarity/rapport/trust) and `openness`. |
| `the_program/memory.py`    | Episodic memory, `bond`, `open_rift`, recall. |
| `the_program/agent.py`     | `Agent.decide` — the decision policy and intent charges. |
| `the_program/backends.py`  | Dialogue rendering: `TemplateBackend`, `ClaudeBackend`. |
| `the_program/appraisal.py` | Reading affect from text: `LexiconAppraiser`, `ClaudeAppraiser`. |
| `the_program/program.py`   | The orchestrator: turns, propagation, scenarios, chat loop. |
| `the_program/cli.py`       | Command-line interface. |

**Design rule that keeps it clean:** the *decision* of what to express (agent.py)
is separate from *rendering it to words* (backends.py) and from *reading affect in*
(appraisal.py). Keep dynamics in the policy/affect layers; keep prose in backends.

## Common recipes

**Add a new intent** (e.g. `tease`):
1. `agent.py` → add its affective charge to `_INTENT_AFFECT`, and a branch in
   `Agent.decide` that picks it.
2. `backends.py` → add phrasings to `_TEMPLATES`, and a line to `_INTENT_BRIEF`
   (used by the Claude backend).
3. If it should be remembered, add it to `SALIENT_INTENTS` in `memory.py`.
4. If it changes how relationships update, extend `_attuned` in `program.py`.

**Add a dialogue backend:** subclass `DialogueBackend` and implement `render`.

**Add an appraiser:** subclass `Appraiser` and implement `appraise` → `(valence, arousal)`.

**Add a scenario:** write a function returning a `Program` with your `Agent` list
(see `companionship_world` / `reconciliation_world`), wire it into `cli.py`.

**Always add or update a test** in `tests/` for behavior you change — assert on
states/relationships/memory, not on the exact dialogue text.

## Style

- Standard library only in the core; put anything heavier behind an optional extra.
- Keep functions small and commented at the *why* level. Match the surrounding tone.
- Tunable numbers (gains, thresholds) live near the top of the function that uses
  them — if you retune the feel, say so in the PR.

## Submitting

1. Fork, branch (`git checkout -b my-change`).
2. `python -m pytest` green.
3. Open a PR describing the behavior change and how you verified it. Small,
   focused PRs get reviewed fastest.

By contributing you agree your work is licensed under the project's [MIT License](LICENSE),
and to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

New here? See [ROADMAP.md](ROADMAP.md) for issues labeled **good first issue**.
