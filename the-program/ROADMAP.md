# Roadmap

The Program is an early prototype with a deliberately legible core. The point of
open-sourcing it is to grow it with others. Below is where it's headed and where
help is most welcome. Issues mirroring these will be labeled on the tracker.

## Guiding principles

- **Legible over clever.** Hand-built, inspectable policies beat opaque ones until
  we have a reason otherwise.
- **Offline-first.** The core stays dependency-free; anything heavier is optional.
- **Separation of concerns.** Decision (agent) ≠ rendering (backend) ≠ reading
  affect (appraiser). New work should respect that seam.

## Good first issues

Small, well-scoped, and a nice way in:

- **Expand the phrase banks** in `backends.py` so transcripts repeat less.
- **Add a `--seed` flag** to make a run's dialogue fully reproducible.
- **New appraiser**: a VADER- or emoji-based `Appraiser` alongside the lexicon.
- **New intent**: e.g. `tease`, `encourage`, `boundary` — charge + templates + a
  `decide` branch (see CONTRIBUTING → recipes).
- **A metrics readout**: print per-agent "regulation quality" (how fast they
  return to baseline) at the end of a run.
- **Docs**: a diagram of how one utterance propagates through a turn.

## Larger features

- **Group dynamics (3+ agents):** alliances, triangulation, an ambient group mood,
  and the bystander effect on who speaks. The contagion plumbing is already there.
- **Persistence:** save/load memory + relationships to JSON so a companion
  remembers you across process runs (this is the big companionship payoff).
- **Visualizer:** a small TUI or web view of the affect space and social graph
  evolving over time.
- **Model-guided policy:** let an LLM (or a learned policy) propose the next
  intent, with the current rule-based policy as a baseline/guardrail.

## Research directions

- Parameter sweeps and metrics for co-regulation effectiveness.
- Grounding the affect/regulation parameters in the affective-computing and
  emotion-regulation literature, and validating emergent patterns against it.

Have an idea that isn't here? Open a discussion or a "Propose a scenario" issue.
