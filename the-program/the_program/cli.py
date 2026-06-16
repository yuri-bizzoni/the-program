"""Command-line interface for The Program.

Examples
--------
    the-program demo              # co-regulation simulation (offline, no deps)
    the-program demo --steps 20   # longer run
    the-program demo --reunion    # let time pass and meet again (memory persists)
    the-program rift              # rupture-and-repair: two friends clash, then reconcile
    the-program demo --llm        # render lines with Claude (needs ANTHROPIC_API_KEY)
    the-program chat              # talk to the companion agent yourself
    the-program chat --llm        # ...with Claude-generated replies and affect reading

The same commands are available without installing via ``python run.py <command>``
or ``python -m the_program <command>``.
"""

from __future__ import annotations

import argparse
import sys

from .appraisal import ClaudeAppraiser, LexiconAppraiser
from .backends import ClaudeBackend, TemplateBackend
from .program import chat_world, companionship_world, reconciliation_world


def _enable_utf8() -> None:
    # Some Windows consoles default to cp1252 and can't encode UTF-8 output; ask
    # for UTF-8 where the runtime supports it (no-op elsewhere).
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _build_backend(use_llm: bool):
    if not use_llm:
        return TemplateBackend()
    try:
        return ClaudeBackend()
    except Exception as exc:  # missing package or missing key
        print(f"[!] Falling back to the template backend ({exc}).", file=sys.stderr)
        return TemplateBackend()


def _build_appraiser(use_llm: bool):
    if not use_llm:
        return LexiconAppraiser()
    try:
        return ClaudeAppraiser()
    except Exception as exc:  # missing package or missing key
        print(f"[!] Falling back to the lexicon appraiser ({exc}).", file=sys.stderr)
        return LexiconAppraiser()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="the-program",
        description="The Program — a multi-agent companionship sandbox.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_demo = sub.add_parser("demo", help="run the co-regulation scenario")
    p_demo.add_argument("--steps", type=int, default=14)
    p_demo.add_argument("--llm", action="store_true", help="use the Claude dialogue backend")
    p_demo.add_argument(
        "--reunion",
        action="store_true",
        help="after the arc, let time pass and meet again — memory persists, mood resets",
    )

    p_rift = sub.add_parser("rift", help="run the rupture-and-repair scenario")
    p_rift.add_argument("--steps", type=int, default=12)
    p_rift.add_argument("--llm", action="store_true", help="use the Claude dialogue backend")

    p_chat = sub.add_parser("chat", help="talk to the companion agent")
    p_chat.add_argument("--llm", action="store_true", help="use the Claude dialogue backend")

    return parser


def main(argv: list[str] | None = None) -> None:
    _enable_utf8()
    args = build_parser().parse_args(argv)
    backend = _build_backend(getattr(args, "llm", False))

    if args.command == "demo":
        companionship_world(backend=backend).run(steps=args.steps, reunion=args.reunion)
    elif args.command == "rift":
        reconciliation_world(backend=backend).run(steps=args.steps)
    elif args.command == "chat":
        appraiser = _build_appraiser(getattr(args, "llm", False))
        chat_world(backend=backend, appraiser=appraiser).chat()


if __name__ == "__main__":
    main()
