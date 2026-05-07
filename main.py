#!/usr/bin/env python3
"""
main.py – Entry point for Y2 Math Interpreter
──────────────────────────────────────────────
Usage:
    python main.py               # interactive REPL
    python main.py script.y2    # run a script file
    python main.py -e "x=3+4; writeln x"   # one-liner (semicolons as newlines)
"""

import sys
import os
import argparse

# Make sure the project root is on the path regardless of cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Y2MathInterpreter import Y2MathInterpreter, InterpreterError, _ExitSignal
from generated import LexerError, ParseError


def main():
    ap = argparse.ArgumentParser(
        description="Y2 Math Interpreter — ANTLR4/Python edition"
    )
    ap.add_argument(
        "script",
        nargs="?",
        help="Script file to execute (.y2 or plain text)"
    )
    ap.add_argument(
        "-e", "--eval",
        metavar="CODE",
        help="Evaluate a one-liner (use newlines or semicolons as separators)"
    )
    args = ap.parse_args()

    interp = Y2MathInterpreter()

    if args.eval:
        # Replace semicolons with newlines for convenience
        source = args.eval.replace(";", "\n")
        try:
            interp.run_source(source)
        except (LexerError, ParseError, InterpreterError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except _ExitSignal:
            pass

    elif args.script:
        if not os.path.isfile(args.script):
            print(f"File not found: {args.script!r}", file=sys.stderr)
            sys.exit(1)
        try:
            interp.run_file(args.script)
        except (LexerError, ParseError, InterpreterError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)
        except _ExitSignal:
            pass

    else:
        try:
            interp.repl()
        except _ExitSignal:
            pass


if __name__ == "__main__":
    main()