"""
Y2MathInterpreter.py
────────────────────
Main interpreter for the Y2 Math language.

Architecture (mirrors what the blog post describes, ported to Python
and upgraded to use ANTLR4 + Visitor pattern):

    Source text
        │  Lexer (Y2ExpressionLexer)
        ▼
    Token stream
        │  Parser (Y2ExpressionParser)
        ▼
    AST
        │  Evaluator(Y2ExpressionVisitor)
        ▼
    Side effects + values

Supports:
    Variables       x = 3 * 4
    Arithmetic      + - * / % ^
    Functions       sqrt sin cos tan abs log exp
    Commands        write  writeln  readn  run  exit
"""

from __future__ import annotations

import math
import os
import sys
from typing import Dict, Optional, IO

# Ensure the directory containing this file is always on sys.path,
# so `generated` is importable regardless of where Python is invoked from.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generated import (
    Y2ExpressionLexer,
    Y2ExpressionParser,
    Y2ExpressionVisitor,
    LexerError,
    ParseError,
)
from generated.Y2ExpressionAST import (
    ProgramNode, AssignmentNode, WriteCmdNode, WriteStringNode,
    ReadnCmdNode, RunCmdNode, ExitCmdNode,
    BinaryOpNode, UnaryMinusNode, NumberNode, VarRefNode, FuncCallNode,
)

# Sentinel: raised internally to exit the REPL cleanly
class _ExitSignal(Exception):
    pass


class InterpreterError(Exception):
    pass


# ── Built-in math functions ───────────────────────────────────────────────────

_BUILTINS: Dict[str, object] = {
    "sqrt": math.sqrt,
    "sin":  math.sin,
    "cos":  math.cos,
    "tan":  math.tan,
    "abs":  abs,
    "log":  math.log,    # natural log
    "exp":  math.exp,
    "ceil": math.ceil,
    "floor":math.floor,
}


class Y2MathInterpreter(Y2ExpressionVisitor):
    """
    Walks the AST produced by Y2ExpressionParser and evaluates it.
    Inherits from Y2ExpressionVisitor (the generated Visitor base).

    The symbol table (_variables) is a simple dict[str, float], exactly
    as described in the original Y2 Math Interpreter blog post.
    """

    def __init__(
        self,
        stdin:  IO = sys.stdin,
        stdout: IO = sys.stdout,
        stderr: IO = sys.stderr,
        *,
        allow_run: bool = True,
        _depth: int = 0,           # recursion guard for 'run'
    ) -> None:
        self._variables: Dict[str, float] = {}
        self._stdin  = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._allow_run = allow_run and (_depth == 0)
        self._depth  = _depth

    # ── Public API ────────────────────────────────────────────────────────────

    def run_source(self, source: str) -> None:
        """Lex, parse, and evaluate a complete source string."""
        lexer  = Y2ExpressionLexer(source)
        tokens = lexer.getAllTokens()
        parser = Y2ExpressionParser(tokens)
        tree   = parser.program()
        tree.accept(self)

    def run_file(self, path: str) -> None:
        """Execute a script file."""
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        self.run_source(source)

    def run_line(self, line: str) -> None:
        """Evaluate a single line (REPL use)."""
        line = line.strip()
        if not line:
            return
        self.run_source(line)

    def repl(self) -> None:
        """Interactive read-eval-print loop."""
        self._stdout.write("Y2 Math Interpreter  (type 'exit' to quit)\n")
        self._stdout.write("Operators: + - * / % ^    Functions: sqrt sin cos tan abs log exp\n")
        self._stdout.write("Commands:  write  writeln  readn  run  exit\n\n")
        while True:
            try:
                self._stdout.write(">> ")
                self._stdout.flush()
                line = self._stdin.readline()
                if not line:           # EOF
                    break
                line = line.rstrip("\r\n")
                if not line:
                    continue
                try:
                    self.run_line(line)
                except _ExitSignal:
                    self._stdout.write("Goodbye!\n")
                    break
                except (LexerError, ParseError, InterpreterError) as exc:
                    self._stderr.write(f"Error: {exc}\n")
            except KeyboardInterrupt:
                self._stdout.write("\nInterrupted.\n")
                break

    # ── Visitor implementations ───────────────────────────────────────────────

    def visitProgram(self, node: ProgramNode):
        for stmt in node.statements:
            stmt.accept(self)

    def visitAssignment(self, node: AssignmentNode):
        value = node.expr.accept(self)
        self._set_var(node.name, value)

    def visitWriteCmd(self, node: WriteCmdNode):
        text = node.arg.accept(self)
        if node.newline:
            self._stdout.write(str(text) + "\n")
        else:
            self._stdout.write(str(text))
        self._stdout.flush()

    def visitWriteString(self, node: WriteStringNode) -> str:
        return node.value

    def visitReadnCmd(self, node: ReadnCmdNode):
        self._stdout.write(f"")
        self._stdout.flush()
        raw = self._stdin.readline().strip()
        try:
            value = float(raw)
        except ValueError:
            raise InterpreterError(
                f"readn: '{raw}' is not a valid number"
            )
        self._set_var(node.name, value)

    def visitRunCmd(self, node: RunCmdNode):
        if not self._allow_run:
            # Mirrors the blog's StackOverflow-prevention: disable
            # nested 'run' commands to avoid infinite recursion.
            return
        if not os.path.isfile(node.filename):
            raise InterpreterError(f"run: file not found: '{node.filename}'")
        sub = Y2MathInterpreter(
            stdin=self._stdin,
            stdout=self._stdout,
            stderr=self._stderr,
            allow_run=False,     # disable further nesting (depth > 0)
            _depth=self._depth + 1,
        )
        # Share the variable table with the sub-interpreter
        sub._variables = self._variables
        sub.run_file(node.filename)

    def visitExitCmd(self, node: ExitCmdNode):
        raise _ExitSignal()

    # ── Expression visitors ───────────────────────────────────────────────────

    def visitBinaryOp(self, node: BinaryOpNode) -> float:
        left  = node.left.accept(self)
        right = node.right.accept(self)
        op    = node.op
        if op == "+":  return left + right
        if op == "-":  return left - right
        if op == "*":  return left * right
        if op == "/":
            if right == 0:
                raise InterpreterError("Division by zero")
            return left / right
        if op == "%":
            if right == 0:
                raise InterpreterError("Modulo by zero")
            return left % right
        if op == "^":  return left ** right
        raise InterpreterError(f"Unknown operator: {op!r}")

    def visitUnaryMinus(self, node: UnaryMinusNode) -> float:
        return -node.operand.accept(self)

    def visitNumber(self, node: NumberNode) -> float:
        return node.value

    def visitVarRef(self, node: VarRefNode) -> float:
        return self._get_var(node.name)

    def visitFuncCall(self, node: FuncCallNode) -> float:
        fn = _BUILTINS.get(node.name)
        if fn is None:
            raise InterpreterError(
                f"Unknown function '{node.name}'. "
                f"Available: {', '.join(_BUILTINS)}"
            )
        arg = node.arg.accept(self)
        try:
            return fn(arg)
        except ValueError as exc:
            raise InterpreterError(f"{node.name}({arg}): {exc}") from exc

    # ── Symbol table helpers ──────────────────────────────────────────────────

    def _get_var(self, name: str) -> float:
        if name not in self._variables:
            raise InterpreterError(f"Undefined variable '{name}'")
        return self._variables[name]

    def _set_var(self, name: str, value: float) -> None:
        self._variables[name] = value

    def get_variables(self) -> Dict[str, float]:
        """Read-only snapshot of the symbol table (useful for debugging)."""
        return dict(self._variables)