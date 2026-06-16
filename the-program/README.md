# The Program

![CI](https://github.com/yuri-bizzoni/the-program/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

A lightweight, **dependency-free** sandbox for a multi-agent conversational
environment, extended toward **companionship**: a few agents talk, each carries a
felt emotional state, regulates that state, and is moved by the others — and a
*companion* agent attunes to a partner and co-regulates them out of distress.

It is an early prototype: the dynamics are legible by design (hand-built policies
and a small affect model, not learned), so you can read every mechanism and tune
it. The dialogue layer is pluggable — the same simulation runs on a built-in
template backend (offline) or on the Claude API.

> Built with others in mind — see [CONTRIBUTING](CONTRIBUTING.md) and the
> [ROADMAP](ROADMAP.md) (issues labeled **good first issue** are a friendly way in).

## Run it

The core has no dependencies. Run straight from a checkout:

```bash
python run.py demo            # co-regulation scenario, prints a turn-by-turn readout
python run.py demo --steps 20 # longer run
python run.py demo --reunion  # ...then let time pass and meet again (memory persists)
python run.py rift            # rupture-and-repair: two friends clash, then reconcile
python run.py chat            # talk to the companion agent yourself
```

Or install it as a package (gives you the `the-program` command and `python -m the_program`):

```bash
python -m pip install -e .          # core; add ".[llm]" for the Claude backend, ".[dev]" for tests
the-program demo
python -m pytest                    # run the tests
```

Optional — render the dialogue with Claude (`pip install anthropic`, set
`ANTHROPIC_API_KEY`):

```bash
python run.py demo --llm
python run.py chat --llm
```

`demo --llm` swaps the dialogue backend for Claude. `chat --llm` does that *and*
reads the affect in your typed lines with Claude (constrained JSON valence/arousal
via structured output) instead of the keyword scorer. If the SDK or key is
missing, it falls back to the template backend / lexicon appraiser automatically
(with a printed notice), so nothing here ever hard-requires the network.

## The model

Three concerns are kept separate so any one can be replaced:

| Module        | Responsibility |
|---------------|----------------|
| `emotion.py`  | Affect as **valence × arousal** (Russell's circumplex) plus the regulation machinery: `appraise` (events perturb state), `regulate` (homeostatic drift to a temperamental baseline), `contagion` (witnessing someone pulls you toward them). |
| `social.py`   | Directed **relationships** (familiarity, rapport, trust) and the rule that turns them into how open you are to someone's affect. |
| `memory.py`   | Per-agent **episodic memory**: the specific moments shared, the **bond** built from them (hard moments weigh most), and what's worth referring back to. |
| `agent.py`    | Each agent's **decision policy** — what to express and to whom, given its state, role, relationships, and memory. |
| `backends.py` | Rendering an intent to **words** — `TemplateBackend` (offline) or `ClaudeBackend` (Claude API). Interchangeable; they don't touch the dynamics. |
| `appraisal.py`| Reading the **affect in your chat lines** — `LexiconAppraiser` (offline keyword scorer) or `ClaudeAppraiser` (Claude structured output → valence/arousal, lexicon fallback). |
| `program.py`  | The **orchestrator**: turn-taking, propagation of each utterance, the scenarios, and the chat loop. |

### How a turn works

1. The agent with the strongest *urge* takes the floor (a companion whose partner
   is hurting → someone in distress → a lonely agent → everyone else).
2. It picks an **intent** (support, reflect, share_distress, banter, …) and a
   target; the intent carries an **affective charge**.
3. The addressee — and, faintly, overhearers — **appraise** that charge, gated by
   how much they trust the speaker, and **catch** the speaker's mood (contagion).
4. **Relationships** update: attuned exchanges (comfort when comfort is needed)
   build trust; misfires (levity at someone in distress) erode it.
5. **Connection** is nourished by attuned contact and decays with time; loneliness
   lowers the mood each agent settles toward.
6. Everyone **regulates** one tick back toward baseline.

### Co-regulation (the companionship layer)

A companion's `support` intent isn't a fixed charge — it's computed to *counter*
the partner's deviation from calm: more warmth the lower they are, more soothing
the more activated they are, scaled by empathy and the strength of the bond. Run
`demo` and watch the distressed agent's valence climb and arousal fall over the
session while their trust in the companion grows — emotional regulation happening
*between* agents, not just within one.

### Memory and bonding (being known over time)

Each agent keeps the specific moments it shares with others. From that it derives a
**bond** — closeness accumulated from shared history, with vulnerable moments
weighing most — that is more than the current mood. Memory changes behavior in
three visible ways:

- **Callbacks in dialogue.** Once there's a history, the companion's lines refer
  back to it ("We came through the last hard night together — we'll come through
  this one too").
- **Noticing patterns.** After a partner has had a rough patch, the companion
  *proactively* checks in even when nothing is wrong right now.
- **Faster regulation.** A deeper bond widens how open you are to someone's
  affect, so comfort from a trusted companion lands harder than from a stranger.

`demo --reunion` makes the point: it plays the arc, lets **time pass** (moods reset
to baseline, but memory and relationships persist), then brings the partner back
mildly low. The companion opens by drawing on the shared past, and the partner —
who already trusts them — settles faster the second time. That gap between *mood
resets* and *bond persists* is the heart of companionship.

### Rupture and repair (conflict, then reconciliation)

Companionship isn't only comfort — it's also surviving friction. Two intents close
the loop: `conflict` (a grievance — cold, agitating, and trust-eroding) and
`repair` (owning the rift and reaching to mend it, which rebuilds trust). The
policy keeps it constructive:

- a grievance is voiced **once** — an open rift then blocks re-attacking, so
  agents cool off instead of escalating;
- an agent **mends only after it has calmed down** (repair is gated on lower
  arousal), modeling the fact that you can't repair well while flooded;
- memory tracks the **open rift** until a repair closes it; conflict alone never
  builds a bond — only the repair afterward does.

`run.py rift` seeds two friends with a standing grievance. Watch the rapport drop
into the negative on the clash, then climb back toward warmth as they reconcile —
visible in the per-turn `rapport`/`trust` readout.

## Extending it

- **New behavior:** add an intent to `_INTENT_AFFECT` (agent.py) and a branch in
  `Agent.decide`, plus phrasings in `_TEMPLATES` (backends.py).
- **New backend:** subclass `DialogueBackend` and implement `render`.
- **New world:** build a `Program` with your own `Agent` list (see
  `companionship_world` for the pattern).

The numbers (gains, thresholds, decay rates) are illustrative starting points,
gathered at the top of each module's functions — tune them to change the feel.

For the full picture — the architecture map and step-by-step recipes for adding
intents, backends, appraisers, and scenarios — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing

Contributions of all sizes are welcome — new intents, scenarios, backends,
appraisers, tuning, docs, and tests. Start with [CONTRIBUTING.md](CONTRIBUTING.md)
and the [ROADMAP](ROADMAP.md); issues labeled **good first issue** are a friendly
way in. Please be kind — see the [Code of Conduct](CODE_OF_CONDUCT.md). A fitting
ask, for a project about getting along.

## Testing

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## License

[MIT](LICENSE). If you use The Program in research, there's a [CITATION.cff](CITATION.cff).
