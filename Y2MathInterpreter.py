"""
Y2MathInterpreter.py — v2.0
─────────────────────────────
Full interpreter for extended Y2 language.

New in v2.0:
  - Boolean type: true / false
  - Comparison operators: == != < > <= >=
  - Logical operators: and / or / not
  - if … then … else … end
  - while … do … end  (with iteration limit guard)
  - User-defined functions: def f(x) = expr
  - Semantic Analysis pass (SemanticAnalyzer) runs before evaluation
"""

from __future__ import annotations

import math
import os
import sys
import io
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generated import LexerError
from generated.Y2ExpressionLexer import Y2ExpressionLexer
from generated.Y2ExpressionParser import Y2ExpressionParser, ParseException
from generated.Y2ExpressionVisitor import Y2ExpressionVisitor
from generated.Y2ExpressionAST import *

# ── Sentinel signals ──────────────────────────────────────────────────────────
class _ExitSignal(Exception): pass


class InterpreterError(Exception): pass


class SemanticError(Exception): pass


# ── Built-in math functions ───────────────────────────────────────────────────
_BUILTINS: Dict[str, Any] = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
    "tan":  math.tan,  "abs": abs,      "log": math.log,
    "exp":  math.exp,  "ceil": math.ceil, "floor": math.floor,
}

_MAX_ITERATIONS = 100_000   # while-loop guard


# ═══════════════════════════════════════════════════════════════════════════════
# Semantic Analyser — Visitor pass that runs BEFORE evaluation
# ═══════════════════════════════════════════════════════════════════════════════

class SemanticAnalyzer(Y2ExpressionVisitor):
    """
    Checks the AST for semantic errors without executing anything:
      - Variables used before being assigned
      - Calls to unknown functions
      - Type mismatches (numeric op applied to boolean literal, etc.)

    Collects all errors rather than stopping at the first one.
    """

    def __init__(self) -> None:
        self.errors: List[str] = []
        self._vars:  set[str]  = set()   # variables seen so far (assigned)
        self._funcs: set[str]  = set()   # user-defined functions

    # ── helpers ───────────────────────────────────────────────────────────────

    def _err(self, msg: str) -> None:
        self.errors.append(msg)

    # ── Visitor implementations ───────────────────────────────────────────────

    def visitProgram(self, node: ProgramNode):
        for s in node.statements:
            s.accept(self)

    def visitAssignment(self, node: AssignmentNode):
        node.expr.accept(self)
        self._vars.add(node.name)

    def visitWriteCmd(self, node: WriteCmdNode):
        node.arg.accept(self)

    def visitWriteString(self, node: WriteStringNode):
        pass

    def visitReadnCmd(self, node: ReadnCmdNode):
        self._vars.add(node.name)   # readn defines the variable

    def visitRunCmd(self, node: RunCmdNode):
        if not os.path.isfile(node.filename):
            self._err(f"run: file not found: '{node.filename}'")

    def visitExitCmd(self, node: ExitCmdNode):
        pass

    def visitIf(self, node: IfNode):
        node.cond.accept(self)
        for s in node.then_block: s.accept(self)
        for s in node.else_block: s.accept(self)

    def visitWhile(self, node: WhileNode):
        node.cond.accept(self)
        for s in node.block: s.accept(self)

    def visitFuncDef(self, node: FuncDefNode):
        # Analyse body with param in scope
        self._vars.add(node.param)
        node.body.accept(self)
        self._vars.discard(node.param)
        self._funcs.add(node.name)

    def visitBinaryOp(self, node: BinaryOpNode):
        node.left.accept(self)
        node.right.accept(self)

    def visitCompare(self, node: CompareNode):
        node.left.accept(self)
        node.right.accept(self)

    def visitLogical(self, node: LogicalNode):
        node.left.accept(self)
        node.right.accept(self)

    def visitNot(self, node: NotNode):
        node.operand.accept(self)

    def visitUnaryMinus(self, node: UnaryMinusNode):
        node.operand.accept(self)
        if isinstance(node.operand, BoolNode):
            self._err("Semantic: cannot negate a boolean literal")

    def visitNumber(self, node: NumberNode): pass

    def visitBool(self, node: BoolNode): pass

    def visitVarRef(self, node: VarRefNode):
        if node.name not in self._vars:
            self._err(f"Semantic: variable '{node.name}' used before assignment")

    def visitFuncCall(self, node: FuncCallNode):
        if node.name not in _BUILTINS:
            self._err(f"Semantic: unknown built-in function '{node.name}'")
        node.arg.accept(self)

    def visitUserFuncCall(self, node: UserFuncCallNode):
        if node.name not in self._funcs:
            self._err(f"Semantic: function '{node.name}' not defined")
        node.arg.accept(self)


# ═══════════════════════════════════════════════════════════════════════════════
# Main Interpreter
# ═══════════════════════════════════════════════════════════════════════════════

class Y2MathInterpreter(Y2ExpressionVisitor):
    """
    Evaluates an AST produced by Y2ExpressionParser.

    Symbol table stores both float and bool values.
    User-defined functions are stored separately in _functions.
    """

    def __init__(
        self,
        stdin:  io.TextIOBase = sys.stdin,
        stdout: io.TextIOBase = sys.stdout,
        stderr: io.TextIOBase = sys.stderr,
        *,
        allow_run: bool = True,
        _depth: int = 0,
    ) -> None:
        self._variables: Dict[str, Any]          = {}
        self._functions: Dict[str, FuncDefNode]  = {}
        self._stdin   = stdin
        self._stdout  = stdout
        self._stderr  = stderr
        self._allow_run = allow_run and (_depth == 0)
        self._depth   = _depth

    # ── Public API ────────────────────────────────────────────────────────────

    def run_source(self, source: str, *, semantic_check: bool = True) -> None:
        lexer  = Y2ExpressionLexer(source)
        tokens = lexer.getAllTokens()

        parser = Y2ExpressionParser(tokens)
        tree   = parser.program()

        # Report parse errors collected during error recovery
        for err in parser.errors:
            self._stderr.write(f"Parse warning: {err}\n")

        # Semantic analysis pass
        if semantic_check:
            sa = SemanticAnalyzer()
            # Pre-populate known variables so cross-statement checks work
            sa._vars  = set(self._variables.keys())
            sa._funcs = set(self._functions.keys())
            tree.accept(sa)
            if sa.errors:
                raise SemanticError("\n".join(sa.errors))

        tree.accept(self)

    def run_file(self, path: str) -> None:
        with open(path, encoding="utf-8") as fh:
            self.run_source(fh.read())

    def run_line(self, line: str) -> None:
        line = line.strip()
        if line:
            self.run_source(line)

    def repl(self) -> None:
        self._stdout.write("Y2 Math Interpreter v2.0\n")
        self._stdout.write("Operators: + - * / % ^   Comparison: == != < > <= >=\n")
        self._stdout.write("Logic: and or not   Bool: true false\n")
        self._stdout.write("Control: if…then…else…end   while…do…end\n")
        self._stdout.write("Functions: def f(x) = expr   sqrt sin cos tan abs log exp\n\n")
        while True:
            try:
                self._stdout.write(">> ")
                self._stdout.flush()
                line = self._stdin.readline()
                if not line:
                    break
                try:
                    self.run_line(line.rstrip("\r\n"))
                except _ExitSignal:
                    self._stdout.write("Goodbye!\n")
                    break
                except (LexerError, SemanticError, InterpreterError) as exc:
                    self._stderr.write(f"Error: {exc}\n")
            except KeyboardInterrupt:
                self._stdout.write("\nInterrupted.\n")
                break

    def get_variables(self) -> Dict[str, Any]:
        return dict(self._variables)

    # ── Visitor: program & statements ────────────────────────────────────────

    def visitProgram(self, node: ProgramNode):
        for stmt in node.statements:
            stmt.accept(self)

    def visitAssignment(self, node: AssignmentNode):
        self._variables[node.name] = node.expr.accept(self)

    def visitWriteCmd(self, node: WriteCmdNode):
        val = node.arg.accept(self)
        text = _fmt(val)
        if node.newline:
            self._stdout.write(text + "\n")
        else:
            self._stdout.write(text)
        self._stdout.flush()

    def visitWriteString(self, node: WriteStringNode) -> str:
        return node.value

    def visitReadnCmd(self, node: ReadnCmdNode):
        raw = self._stdin.readline().strip()
        try:
            self._variables[node.name] = float(raw)
        except ValueError:
            raise InterpreterError(f"readn: '{raw}' is not a valid number")

    def visitRunCmd(self, node: RunCmdNode):
        if not self._allow_run:
            return
        sub = Y2MathInterpreter(
            stdin=self._stdin, stdout=self._stdout, stderr=self._stderr,
            allow_run=False, _depth=self._depth + 1,
        )
        sub._variables = self._variables
        sub._functions = self._functions
        sub.run_file(node.filename)

    def visitExitCmd(self, node: ExitCmdNode):
        raise _ExitSignal()

    def visitFuncDef(self, node: FuncDefNode):
        """Store the function definition in the function table."""
        self._functions[node.name] = node

    def visitIf(self, node: IfNode):
        cond = node.cond.accept(self)
        if _truthy(cond):
            for stmt in node.then_block:
                stmt.accept(self)
        else:
            for stmt in node.else_block:
                stmt.accept(self)

    def visitWhile(self, node: WhileNode):
        iterations = 0
        while _truthy(node.cond.accept(self)):
            for stmt in node.block:
                stmt.accept(self)
            iterations += 1
            if iterations >= _MAX_ITERATIONS:
                raise InterpreterError(
                    f"while loop exceeded {_MAX_ITERATIONS} iterations — "
                    "possible infinite loop"
                )

    # ── Visitor: expressions ─────────────────────────────────────────────────

    def visitBinaryOp(self, node: BinaryOpNode) -> float:
        left  = node.left.accept(self)
        right = node.right.accept(self)
        op    = node.op
        _require_num(left,  op)
        _require_num(right, op)
        if op == "+": return left + right
        if op == "-": return left - right
        if op == "*": return left * right
        if op == "/":
            if right == 0: raise InterpreterError("Division by zero")
            return left / right
        if op == "%":
            if right == 0: raise InterpreterError("Modulo by zero")
            return left % right
        if op == "^": return left ** right
        raise InterpreterError(f"Unknown operator: {op!r}")

    def visitCompare(self, node: CompareNode) -> bool:
        left  = node.left.accept(self)
        right = node.right.accept(self)
        op    = node.op
        if op == "==": return left == right
        if op == "!=": return left != right
        if op == "<":  return left <  right
        if op == ">":  return left >  right
        if op == "<=": return left <= right
        if op == ">=": return left >= right
        raise InterpreterError(f"Unknown comparison: {op!r}")

    def visitLogical(self, node: LogicalNode) -> bool:
        if node.op == "or":
            return _truthy(node.left.accept(self)) or _truthy(node.right.accept(self))
        if node.op == "and":
            return _truthy(node.left.accept(self)) and _truthy(node.right.accept(self))
        raise InterpreterError(f"Unknown logical op: {node.op!r}")

    def visitNot(self, node: NotNode) -> bool:
        return not _truthy(node.operand.accept(self))

    def visitUnaryMinus(self, node: UnaryMinusNode) -> float:
        val = node.operand.accept(self)
        _require_num(val, "unary -")
        return -val

    def visitNumber(self, node: NumberNode) -> float:
        return node.value

    def visitBool(self, node: BoolNode) -> bool:
        return node.value

    def visitVarRef(self, node: VarRefNode):
        if node.name not in self._variables:
            raise InterpreterError(f"Undefined variable '{node.name}'")
        return self._variables[node.name]

    def visitFuncCall(self, node: FuncCallNode) -> float:
        fn = _BUILTINS.get(node.name)
        if fn is None:
            raise InterpreterError(f"Unknown built-in '{node.name}'")
        arg = node.arg.accept(self)
        _require_num(arg, node.name + "()")
        try:
            return fn(arg)
        except ValueError as exc:
            raise InterpreterError(f"{node.name}({arg}): {exc}") from exc

    def visitUserFuncCall(self, node: UserFuncCallNode):
        fdef = self._functions.get(node.name)
        if fdef is None:
            raise InterpreterError(f"Undefined function '{node.name}'")
        arg_val = node.arg.accept(self)
        # Evaluate body in a temporary scope with the parameter bound
        saved = self._variables.get(fdef.param, _MISSING)
        self._variables[fdef.param] = arg_val
        result = fdef.body.accept(self)
        # Restore previous scope
        if saved is _MISSING:
            self._variables.pop(fdef.param, None)
        else:
            self._variables[fdef.param] = saved
        return result


# ── Helpers ───────────────────────────────────────────────────────────────────

_MISSING = object()


def _truthy(val) -> bool:
    """Both booleans and numbers are valid conditions."""
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    return bool(val)


def _require_num(val, op: str) -> None:
    if isinstance(val, bool):
        raise InterpreterError(
            f"Operator '{op}' requires a number, got boolean"
        )
    if not isinstance(val, (int, float)):
        raise InterpreterError(
            f"Operator '{op}' requires a number, got {type(val).__name__}"
        )


def _fmt(val) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, float):
        return str(int(val)) if val == int(val) else f"{val:.10g}"
    return str(val)