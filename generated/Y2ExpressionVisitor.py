"""
generated/Y2ExpressionVisitor.py  — v2.0
──────────────────────────────────────────
Abstract Visitor base — extended with all new node types.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from .Y2ExpressionAST import (
    ProgramNode, AssignmentNode, WriteCmdNode, WriteStringNode,
    ReadnCmdNode, RunCmdNode, ExitCmdNode,
    IfNode, WhileNode, FuncDefNode,
    BinaryOpNode, CompareNode, LogicalNode, NotNode,
    UnaryMinusNode, NumberNode, BoolNode, VarRefNode,
    FuncCallNode, UserFuncCallNode,
)


class Y2ExpressionVisitor(ABC):

    # ── Program & statements ──────────────────────────────────────────────────
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
    def visitIf(self, node: IfNode) -> Any: ...

    @abstractmethod
    def visitWhile(self, node: WhileNode) -> Any: ...

    @abstractmethod
    def visitFuncDef(self, node: FuncDefNode) -> Any: ...

    # ── Expressions ───────────────────────────────────────────────────────────
    @abstractmethod
    def visitBinaryOp(self, node: BinaryOpNode) -> Any: ...

    @abstractmethod
    def visitCompare(self, node: CompareNode) -> Any: ...

    @abstractmethod
    def visitLogical(self, node: LogicalNode) -> Any: ...

    @abstractmethod
    def visitNot(self, node: NotNode) -> Any: ...

    @abstractmethod
    def visitUnaryMinus(self, node: UnaryMinusNode) -> Any: ...

    @abstractmethod
    def visitNumber(self, node: NumberNode) -> Any: ...

    @abstractmethod
    def visitBool(self, node: BoolNode) -> Any: ...

    @abstractmethod
    def visitVarRef(self, node: VarRefNode) -> Any: ...

    @abstractmethod
    def visitFuncCall(self, node: FuncCallNode) -> Any: ...

    @abstractmethod
    def visitUserFuncCall(self, node: UserFuncCallNode) -> Any: ...