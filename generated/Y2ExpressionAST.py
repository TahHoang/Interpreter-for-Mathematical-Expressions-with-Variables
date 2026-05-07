"""
generated/Y2ExpressionAST.py
────────────────────────────
Abstract Syntax Tree node classes.
These correspond directly to the grammar rules in Y2Expression.g4 and
would normally be generated automatically by ANTLR4.

Each node has an `accept(visitor)` method for the Visitor pattern,
mirroring ANTLR4's ParseTree.accept() interface.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any


class ASTNode:
    """Base class for all AST nodes."""
    def accept(self, visitor: "Y2ExpressionVisitor") -> Any:
        raise NotImplementedError


# ── Program ───────────────────────────────────────────────────────────────────

@dataclass
class ProgramNode(ASTNode):
    statements: List[ASTNode]

    def accept(self, visitor):
        return visitor.visitProgram(self)


# ── Statements ────────────────────────────────────────────────────────────────

@dataclass
class AssignmentNode(ASTNode):
    """name = expr"""
    name: str
    expr: ASTNode

    def accept(self, visitor):
        return visitor.visitAssignment(self)


@dataclass
class WriteCmdNode(ASTNode):
    arg: ASTNode          # WriteStringNode | expr
    newline: bool = False  # True → writeln

    def accept(self, visitor):
        return visitor.visitWriteCmd(self)


@dataclass
class WriteStringNode(ASTNode):
    value: str            # the raw string content (quotes already stripped)

    def accept(self, visitor):
        return visitor.visitWriteString(self)


@dataclass
class ReadnCmdNode(ASTNode):
    name: str

    def accept(self, visitor):
        return visitor.visitReadnCmd(self)


@dataclass
class RunCmdNode(ASTNode):
    filename: str

    def accept(self, visitor):
        return visitor.visitRunCmd(self)


@dataclass
class ExitCmdNode(ASTNode):
    def accept(self, visitor):
        return visitor.visitExitCmd(self)


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass
class BinaryOpNode(ASTNode):
    op: str               # '+' '-' '*' '/' '%' '^'
    left: ASTNode
    right: ASTNode

    def accept(self, visitor):
        return visitor.visitBinaryOp(self)


@dataclass
class UnaryMinusNode(ASTNode):
    operand: ASTNode

    def accept(self, visitor):
        return visitor.visitUnaryMinus(self)


@dataclass
class NumberNode(ASTNode):
    value: float

    def accept(self, visitor):
        return visitor.visitNumber(self)


@dataclass
class VarRefNode(ASTNode):
    name: str

    def accept(self, visitor):
        return visitor.visitVarRef(self)


@dataclass
class FuncCallNode(ASTNode):
    name: str             # 'sqrt' 'sin' 'cos' 'tan' 'abs' 'log' 'exp'
    arg: ASTNode

    def accept(self, visitor):
        return visitor.visitFuncCall(self)
