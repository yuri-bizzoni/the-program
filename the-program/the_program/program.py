"""The Program — the orchestrator that ties everyone together.

`Program` runs the turn loop. On each turn it picks whoever has the strongest
*urge* to speak (a companion whose partner is hurting, someone in distress, a
lonely agent, then everyone else), lets them choose an intent, renders it to
words, and then propagates the consequences through the room:

  * the addressee (and, faintly, anyone overhearing) appraises the intentional
    charge, gated by how open they are to the speaker;
  * everyone catches a little of the speaker's expressed state (contagion);
  * relationships update, attuned exchanges build trust, misfires erode it;
  * connection is nourished by attuned contact and decays with time;
  * everyone regulates one tick back toward baseline.

Two ready-made worlds are provided: a `companionship_world` that plays out a
co-regulation arc on its own, and a `chat_world` that puts you in the room with
a companion agent.
"""

from __future__ import annotations

from .agent import Agent, Decision
from .appraisal import Appraiser, LexiconAppraiser
from .backends import DialogueBackend, TemplateBackend
from .emotion import (
    Affect,
    EmotionalState,
    Temperament,
    appraise,
    clamp,
    contagion,
    label,
    regulate,
)
from .memory import SALIENT_INTENTS
from .social import SocialField, openness


# Intents that fit a person in distress vs. a settled one. Used to score whether
# an exchange was *attuned* — the right move at the right moment.
_SOOTHING = {"support", "reflect", "check_in"}
_LIGHT = {"share_warmth", "banter", "greet"}


def _attuned(intent: str, addressee_was_distressed: bool) -> bool:
    if intent == "conflict":
        return False                           # a grievance ruptures trust
    if intent == "repair":
        return True                            # mending rebuilds it
    if intent in _SOOTHING:
        return addressee_was_distressed       # comfort lands when comfort is needed
    if intent in _LIGHT:
        return not addressee_was_distressed    # levity misfires on a hurting person
    return True                                # reaching out / asking is always a valid bid


class Program:
    def __init__(
        self,
        agents: list[Agent],
        backend: DialogueBackend | None = None,
        appraiser: Appraiser | None = None,
    ) -> None:
        self.agents = agents
        self.backend = backend or TemplateBackend()
        self.appraiser = appraiser or LexiconAppraiser()  # reads affect from your chat lines
        self.field = SocialField()
        self._t = 0
        self._last_spoken: dict[str, int] = {a.name: -1 for a in agents}

    # ------------------------------------------------------------------ #
    # Turn loop
    # ------------------------------------------------------------------ #

    def _urge(self, agent: Agent) -> float:
        """How much this agent wants the floor right now."""
        if agent.role == "companion":
            partner = next((a for a in self.agents if a.name == agent.partner), None)
            if partner is not None and partner.is_distressed():
                return 0.95
        if agent.is_distressed():
            return 0.75
        # An unresolved rift, or live irritation, presses to be addressed.
        if any(agent.memory.open_rift(o.name) for o in self.agents if o is not agent):
            return 0.60
        if agent.state.valence < -0.10 and agent.state.arousal > 0.55:
            return 0.60
        if agent.connection < 0.4:
            return 0.45
        return 0.25

    def _pick_speaker(self) -> Agent:
        def key(a: Agent):
            urge = self._urge(a)
            if self._last_spoken[a.name] == self._t - 1:
                urge -= 0.40  # discourage monologue
            # tie-break: whoever has spoken least recently goes first
            return (-urge, self._last_spoken[a.name])

        return sorted(self.agents, key=key)[0]

    def step(self) -> None:
        self._t += 1
        speaker = self._pick_speaker()
        others = [a for a in self.agents if a is not speaker]
        decision = speaker.decide(others, self.field)
        self._exchange(speaker, decision)
        self._last_spoken[speaker.name] = self._t

    def _run_steps(self, n: int) -> None:
        for _ in range(n):
            self.step()

    def run(self, steps: int = 14, reunion: bool = False) -> None:
        self._banner()
        self._snapshot("opening")
        start = {a.name: a.state.copy() for a in self.agents}
        self._run_steps(steps)
        self._snapshot("closing")
        self._verdict(start)
        self._memory_summary()
        if reunion:
            self._reunion()

    def _reunion(self) -> None:
        """Let time pass — moods reset, but memory and relationships persist — then
        bring the partner back mildly low and watch the companion draw on the past."""
        companion = next((a for a in self.agents if a.role == "companion"), None)
        partner = next((a for a in self.agents if a.name == getattr(companion, "partner", None)), None)
        if companion is None or partner is None:
            return

        print("\n" + "." * 28 + "  days pass  " + "." * 27 + "\n")
        for a in self.agents:
            # Momentary affect fades back to baseline; the connection cools a little.
            a.state = EmotionalState(a.temperament.baseline_valence, a.temperament.baseline_arousal)
            a.connection = clamp(a.connection - 0.25, 0.0, 1.0)
        self._last_spoken = {a.name: -1 for a in self.agents}
        # The partner comes back carrying a fresh, milder weight.
        partner.state = EmotionalState(valence=-0.30, arousal=0.62)

        self._snapshot("reunion")
        start = {a.name: a.state.copy() for a in self.agents}
        self._run_steps(6)
        self._snapshot("after reunion")
        self._verdict(start)
        self._memory_summary()

    # ------------------------------------------------------------------ #
    # The core mechanic: one utterance, fully propagated
    # ------------------------------------------------------------------ #

    def _openness(self, listener: Agent, speaker: Agent) -> float:
        """How open `listener` is to `speaker` — relationship plus remembered bond."""
        base = openness(self.field.rel(listener.name, speaker.name))
        return clamp(base + 0.30 * listener.memory.bond(speaker.name), 0.15, 1.40)

    def _exchange(self, speaker: Agent, decision: Decision, text: str | None = None) -> str:
        addressee = decision.addressee
        rel_words = self.field.rel(speaker.name, addressee.name)
        if text is None:
            recall = speaker.memory.recall_category(addressee.name)
            text = self.backend.render(
                speaker=speaker,
                addressee=addressee,
                intent=decision.intent,
                relationship=rel_words,
                recall=recall,
            )

        addressee_was_distressed = addressee.is_distressed()

        # 1. Everyone but the speaker is affected: the addressee head-on, the rest
        #    as overhearers. Each appraises the intentional charge (gated by how
        #    open they are to the speaker) and catches the speaker's mood.
        for listener in self.agents:
            if listener is speaker:
                continue
            weight = 1.0 if listener is addressee else 0.35
            open_to = self._openness(listener, speaker)
            appraise(listener.state, listener.temperament, decision.affect.scaled(weight), open_to)
            spread = weight * listener.temperament.empathy * speaker.temperament.expressiveness
            appraise(listener.state, listener.temperament, contagion(speaker.state).scaled(spread))

        # 2. Relationships and connection respond to the exchange.
        attuned = _attuned(decision.intent, addressee_was_distressed)
        self.field.record_interaction(
            addressee.name, speaker.name, attuned=attuned, warmth=decision.affect.valence
        )
        self.field.record_interaction(
            speaker.name, addressee.name, attuned=attuned, warmth=0.15 if attuned else -0.05
        )
        if attuned:
            addressee.connection = clamp(addressee.connection + 0.15, 0.0, 1.0)
            speaker.connection = clamp(speaker.connection + 0.12, 0.0, 1.0)

        # 3. The moment is committed to memory if it mattered — a vulnerable or
        #    warm exchange both participants will carry forward.
        if decision.intent in SALIENT_INTENTS or abs(decision.affect.valence) > 0.35:
            hard = addressee_was_distressed or decision.intent in {
                "support", "reflect", "share_distress", "conflict"
            }
            addressee.memory.remember(self._t, speaker.name, decision.intent, hard)
            speaker.memory.remember(self._t, addressee.name, decision.intent, hard)

        # 4. Time passes: connection decays and everyone regulates one tick.
        for a in self.agents:
            a.connection = clamp(a.connection - 0.03, 0.0, 1.0)
            regulate(a.state, a.temperament, a.connection)

        self._print_turn(speaker, addressee, decision.intent, text)
        return text

    # ------------------------------------------------------------------ #
    # Interactive chat
    # ------------------------------------------------------------------ #

    def chat(self, human_name: str = "You") -> None:
        human = next(a for a in self.agents if a.name == human_name)
        companion = next(a for a in self.agents if a.role == "companion")
        self._banner()
        print(
            f"You're talking with {companion.first_name}. "
            f"(affect read by: {self.appraiser.kind}. Ctrl-C or empty line to leave.)\n"
        )
        while True:
            try:
                line = input("you > ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                break

            # Read the human's affect from their words and set their state.
            v, a = self.appraiser.appraise(line)
            human.state.valence = clamp(0.6 * v + 0.4 * human.state.valence, -1.0, 1.0)
            human.state.arousal = clamp(a, 0.0, 1.0)
            intent = "share_distress" if v < -0.15 else ("share_warmth" if v > 0.2 else "ask")
            human_affect = Affect(valence=0.5 * v, arousal=a - 0.35)

            # The companion hears it, then chooses how to respond.
            self._t += 1
            self._exchange(human, Decision(companion, intent, human_affect), text=line)
            self._t += 1
            decision = companion.decide([human], self.field)
            self._exchange(companion, decision)
            self._last_spoken[companion.name] = self._t

    # ------------------------------------------------------------------ #
    # Presentation
    # ------------------------------------------------------------------ #

    def _banner(self) -> None:
        print("=" * 68)
        print("THE PROGRAM -- affect | social dynamics | co-regulation")
        print("v = valence (-1..+1)   a = arousal (0..1)   conn = connection")
        print("=" * 68)

    def _agent_line(self, a: Agent) -> str:
        return (
            f"  {a.first_name:<6} v{a.state.valence:+.2f} a{a.state.arousal:.2f} "
            f"{label(a.state):<10} conn {a.connection:.2f}"
        )

    def _snapshot(self, when: str) -> None:
        print(f"\n--- {when} state ---")
        for a in self.agents:
            tag = "(companion)" if a.role == "companion" else ""
            print(self._agent_line(a), tag)
        print()

    def _print_turn(self, speaker: Agent, addressee: Agent, intent: str, text: str) -> None:
        self._t  # noqa: B018  (kept for readability of the timeline)
        print(f"[t{self._t:>2}] {speaker.first_name} -> {addressee.first_name}   {intent}")
        print(f'       "{text}"')
        print("      ", self._agent_line(speaker).strip())
        rel = self.field.rel(addressee.name, speaker.name)
        print(
            "      ",
            self._agent_line(addressee).strip(),
            f" | {addressee.first_name}->{speaker.first_name}"
            f" rapport {rel.rapport:+.2f} trust {rel.trust:.2f}",
        )
        print()

    def _verdict(self, start: dict[str, EmotionalState]) -> None:
        print("--- shift over the session ---")
        for a in self.agents:
            s0 = start[a.name]
            dv = a.state.valence - s0.valence
            da = a.state.arousal - s0.arousal
            print(
                f"  {a.first_name:<6} valence {dv:+.2f}  arousal {da:+.2f}"
                f"   ({label(s0)} -> {label(a.state)})"
            )
        print()

    def _memory_summary(self) -> None:
        """What each agent now carries about the others — the residue of the session."""
        print("--- what they'll carry ---")
        for a in self.agents:
            others = [o for o in self.agents if o is not a and a.memory.about(o.name)]
            if not others:
                continue
            strongest = max(others, key=lambda o: a.memory.bond(o.name))
            print(
                f"  {a.first_name} remembers {strongest.first_name}: "
                f"{a.memory.phrase(strongest.name)} (bond {a.memory.bond(strongest.name):.2f})"
            )
        print()


# ---------------------------------------------------------------------- #
# Ready-made worlds
# ---------------------------------------------------------------------- #

def companionship_world(backend: DialogueBackend | None = None) -> Program:
    """Three agents; one arrives in distress; a companion co-regulates them."""
    iris = Agent(
        name="Iris",
        persona="a steady, attentive friend who listens before she speaks",
        temperament=Temperament(
            baseline_valence=0.35, baseline_arousal=0.30, sensitivity=0.9,
            regulation=0.40, empathy=0.85, expressiveness=0.6,
        ),
        role="companion",
        partner="Mara",
        state=EmotionalState(valence=0.30, arousal=0.30),
        connection=0.7,
    )
    mara = Agent(
        name="Mara",
        persona="warm but easily flooded; feels everything at full volume",
        temperament=Temperament(
            baseline_valence=0.10, baseline_arousal=0.40, sensitivity=1.15,
            regulation=0.15, empathy=0.60, expressiveness=0.75,
        ),
        role="peer",
        state=EmotionalState(valence=-0.60, arousal=0.80),   # arrives in distress
        connection=0.35,
    )
    theo = Agent(
        name="Theo",
        persona="easy-going and upbeat, quick with a joke",
        temperament=Temperament(
            baseline_valence=0.40, baseline_arousal=0.45, sensitivity=0.85,
            regulation=0.30, empathy=0.55, expressiveness=0.7,
        ),
        role="peer",
        state=EmotionalState(valence=0.35, arousal=0.45),
        connection=0.6,
    )
    return Program([iris, mara, theo], backend=backend)


def reconciliation_world(backend: DialogueBackend | None = None) -> Program:
    """Two friends with a standing grievance clash, then find their way back.

    Watch the rupture (rapport drops, both agitate) and the repair (once each has
    cooled, they reach to mend it, and rapport climbs back toward warmth)."""
    mara = Agent(
        name="Mara",
        persona="warm but quick to feel slighted; she speaks before she cools",
        temperament=Temperament(
            baseline_valence=0.15, baseline_arousal=0.40, sensitivity=1.05,
            regulation=0.22, empathy=0.55, expressiveness=0.7,
        ),
        role="peer",
        state=EmotionalState(valence=-0.15, arousal=0.68),   # arrives irritated
        connection=0.5,
    )
    theo = Agent(
        name="Theo",
        persona="easy-going and conflict-averse; he wants things smoothed over",
        temperament=Temperament(
            baseline_valence=0.40, baseline_arousal=0.45, sensitivity=0.95,
            regulation=0.30, empathy=0.65, expressiveness=0.7,
        ),
        role="peer",
        state=EmotionalState(valence=0.30, arousal=0.45),
        connection=0.6,
    )
    prog = Program([mara, theo], backend=backend)
    # A standing grievance between them — the spark for the clash.
    prog.field.rel("Mara", "Theo").rapport = -0.35
    prog.field.rel("Theo", "Mara").rapport = -0.20
    return prog


def chat_world(
    backend: DialogueBackend | None = None,
    appraiser: Appraiser | None = None,
    human_name: str = "You",
) -> Program:
    """You and a companion agent, one on one."""
    iris = Agent(
        name="Iris",
        persona="a steady, attentive companion who listens before she speaks",
        temperament=Temperament(
            baseline_valence=0.35, baseline_arousal=0.30, sensitivity=0.9,
            regulation=0.40, empathy=0.85, expressiveness=0.6,
        ),
        role="companion",
        partner=human_name,
        state=EmotionalState(valence=0.30, arousal=0.30),
        connection=0.7,
    )
    you = Agent(
        name=human_name,
        persona="the person Iris is keeping company",
        temperament=Temperament(
            baseline_valence=0.15, baseline_arousal=0.40, sensitivity=1.0,
            regulation=0.25, empathy=0.6, expressiveness=0.7,
        ),
        role="peer",
        state=EmotionalState(valence=0.0, arousal=0.40),
        connection=0.5,
    )
    return Program([you, iris], backend=backend, appraiser=appraiser)
