# Launch drafts

These are **drafts for you to review, edit, and post yourself.** Nothing here has
been (or will be) posted automatically — announcing a project is an outward-facing
action that should go out under your name, when you're ready.

> Before posting anything, run the **Before you publish** checklist at the bottom.

---

## One-line pitch

> The Program — a tiny, dependency-free Python sandbox where multi-agent
> conversations get an inner life: agents feel, regulate their emotions, build
> bonds, co-regulate each other through hard moments, and even fight and make up.

## Two-sentence blurb (social)

> I open-sourced **The Program**: a small Python sandbox for multi-agent social
> dynamics with real emotional regulation — agents have a valence/arousal state,
> catch each other's moods, remember shared moments, and a companion agent can
> talk a distressed friend back down. It also models rupture-and-repair: two
> friends clash, then reconcile. Code + demos: https://github.com/yuri-bizzoni/the-program

---

## Show HN draft

**Title:** Show HN: The Program – a multi-agent sandbox for emotion and companionship

**Body:**

> I've been prototyping a small multi-agent conversational environment and pushing
> it toward *companionship*: not just agents that talk, but agents that feel,
> regulate those feelings, and tend to each other.
>
> Each agent has a dimensional emotional state (valence × arousal) that drifts back
> toward a temperamental baseline (homeostatic regulation), gets perturbed by what
> others say (appraisal), and catches others' moods (contagion). On top of that:
> directed relationships (familiarity / rapport / trust), episodic memory with an
> accumulated bond, a companion role that co-regulates a distressed partner, and a
> conflict/repair cycle where two friends clash and then reconcile.
>
> It's deliberately legible — hand-built, inspectable policies, no ML black box —
> and the core is pure standard library, so `python run.py demo` just works. The
> dialogue layer is pluggable: an offline template backend, or the Claude API.
>
> I'd love feedback on the model (the affect/regulation parameters especially) and
> on where to take the social dynamics next — group dynamics and cross-session
> persistence are the obvious frontiers. Roadmap and "good first issues" are in the
> repo.
>
> Repo: https://github.com/yuri-bizzoni/the-program

## Reddit draft (r/Python or r/MachineLearning "Show & Tell")

**Title:** [P] The Program: a dependency-free multi-agent sandbox for emotion, social dynamics, and companionship

**Body:** (same as the Show HN body; add a short transcript snippet from
`python run.py rift` so people can see the rupture→repair arc in the
rapport/trust numbers, and link the repo).

---

## Before you publish

1. ~~Find-and-replace `OWNER` with your GitHub slug~~ — done (`yuri-bizzoni`).
2. Confirm the **LICENSE** copyright holder and the **CODE_OF_CONDUCT** contact email.
3. Decide on the **package name** — `the-program` is generic and may be taken on
   PyPI; check before publishing there.
4. Create the GitHub repo, enable **Issues** and **Discussions**, add repo
   **topics** (e.g. `multi-agent`, `affective-computing`, `simulation`), and add
   labels including `good first issue`.
5. Push, tag `v0.1.0`, and (optionally) publish to PyPI.
6. *Then* post the announcement(s) above.

A community grows from low-friction on-ramps more than from the launch post:
clearly-scoped good-first-issues (see ROADMAP.md), fast and kind responses to the
first few issues/PRs, and a visible CODE_OF_CONDUCT all do more than reach.
