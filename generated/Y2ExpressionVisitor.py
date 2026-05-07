"""
generated/Y2ExpressionVisitor.py
─────────────────────────────────
Abstract Visitor base — mirrors what ANTLR4 generates for a grammar
decorated with the `@visitor` directive.

Subclass this and override the visit* methods you care about.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from .Y2ExpressionAST import (
    ProgramNode, AssignmentNode, WriteCmdNode, WriteStringNode,
    ReadnCmdNode, RunCmdNode, ExitCmdNode,
    BinaryOpNode, UnaryMinusNode, NumberNode, VarRefNode, FuncCallNode,
)


class Y2ExpressionVisitor(ABC):

    @abstractmethod
    def visitProgram(self, node: ProgramNode) -> Any: ...

    @abstractmethod
    def visitAssignment(self, node: AssignmentNode) -> Any: ...

    @abstractmethod
    def visitWriteCmd(self, node: WriteCmdNode) -> Any: ...

    @abstractmethod
    def visitWriteString(self, node: WriteStringNode) -> Any: ...

    @abstractmethod
    def visitReadnCmd(self, node: ReadnCmdNode) -> Any: ...

    @abstractmethod
    def visitRunCmd(self, node: RunCmdNode) -> Any: ...

    @abstractmethod
    def visitExitCmd(self, node: ExitCmdNode) -> Any: ...

    @abstractmethod
    def visitBinaryOp(self, node: BinaryOpNode) -> Any: ...

    @abstractmethod
    def visitUnaryMinus(self, node: UnaryMinusNode) -> Any: ...

    @abstractmethod
    def visitNumber(self, node: NumberNode) -> Any: ...

    @abstractmethod
    def visitVarRef(self, node: VarRefNode) -> Any: ...

    @abstractmethod
    def visitFuncCall(self, node: FuncCallNode) -> Any: ...
