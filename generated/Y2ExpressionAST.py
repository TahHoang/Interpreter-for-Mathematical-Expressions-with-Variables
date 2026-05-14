"""
generated/Y2ExpressionAST.py  — v2.0
──────────────────────────────────────
AST node classes for the extended Y2 language.

New nodes:
  BoolNode        — true / false literal
  CompareNode     — == != < > <= >=
  LogicalNode     — and / or
  NotNode         — not expr
  IfNode          — if cond then block (else block)? end
  WhileNode       — while cond do block end
  FuncDefNode     — def f(x) = expr
  UserFuncCallNode— f(expr)  (user-defined, single arg)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any


class ASTNode:
    def accept(self, visitor: "Y2ExpressionVisitor") -> Any:
        raise NotImplementedError


# ── Program ───────────────────────────────────────────────────────────────────

@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]
    def accept(self, v): return v.visitProgram(self)


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class AssignmentNode(ASTNode):
    name: str
    expr: ASTNode
    def accept(self, v): return v.visitAssignment(self)


@dataclass
class WriteCmdNode(ASTNode):
    arg: ASTNode
    newline: bool = False
    def accept(self, v): return v.visitWriteCmd(self)


@dataclass
class WriteStringNode(ASTNode):
    value: str
    def accept(self, v): return v.visitWriteString(self)


@dataclass
class ReadnCmdNode(ASTNode):
    name: str
    def accept(self, v): return v.visitReadnCmd(self)


@dataclass
class RunCmdNode(ASTNode):
    filename: str
    def accept(self, v): return v.visitRunCmd(self)


@dataclass
class ExitCmdNode(ASTNode):
    def accept(self, v): return v.visitExitCmd(self)


@dataclass
class IfNode(ASTNode):
    """if cond then then_block (else else_block)? end"""
    cond:       ASTNode
    then_block: List[ASTNode]
    else_block: List[ASTNode] = field(default_factory=list)
    def accept(self, v): return v.visitIf(self)


@dataclass
class WhileNode(ASTNode):
    """while cond do block end"""
    cond:  ASTNode
    block: List[ASTNode]
    def accept(self, v): return v.visitWhile(self)


@dataclass
class FuncDefNode(ASTNode):
    """def f(param) = expr"""
    name:  str
    param: str
    body:  ASTNode
    def accept(self, v): return v.visitFuncDef(self)


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class BinaryOpNode(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode
    def accept(self, v): return v.visitBinaryOp(self)


@dataclass
class CompareNode(ASTNode):
    """== != < > <= >=  — always produces a boolean"""
    op:    str
    left:  ASTNode
    right: ASTNode
    def accept(self, v): return v.visitCompare(self)


@dataclass
class LogicalNode(ASTNode):
    """and / or"""
    op:    str   # 'and' | 'or'
    left:  ASTNode
    right: ASTNode
    def accept(self, v): return v.visitLogical(self)


@dataclass
class NotNode(ASTNode):
    operand: ASTNode
    def accept(self, v): return v.visitNot(self)


@dataclass
class UnaryMinusNode(ASTNode):
    operand: ASTNode
    def accept(self, v): return v.visitUnaryMinus(self)


@dataclass
class NumberNode(ASTNode):
    value: float
    def accept(self, v): return v.visitNumber(self)


@dataclass
class BoolNode(ASTNode):
    value: bool
    def accept(self, v): return v.visitBool(self)


@dataclass
class VarRefNode(ASTNode):
    name: str
    def accept(self, v): return v.visitVarRef(self)


@dataclass
class FuncCallNode(ASTNode):
    """Built-in math functions: sqrt, sin, cos …"""
    name: str
    arg:  ASTNode
    def accept(self, v): return v.visitFuncCall(self)


@dataclass
class UserFuncCallNode(ASTNode):
    """User-defined function call: f(expr)"""
    name: str
    arg:  ASTNode
    def accept(self, v): return v.visitUserFuncCall(self)