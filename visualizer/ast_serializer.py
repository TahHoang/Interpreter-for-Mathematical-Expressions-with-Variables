"""
visualizer/ast_serializer.py  — v2.0
──────────────────────────────────────
Visitor: AST → JSON-serializable dict.
Handles all v2.0 node types.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated.Y2ExpressionVisitor import Y2ExpressionVisitor
from generated.Y2ExpressionAST import *


class ASTSerializer(Y2ExpressionVisitor):

    def _node(self, type_: str, label: str, *children) -> dict:
        return {"type": type_, "label": label, "children": list(children)}

    def visitProgram(self, node: ProgramNode):
        return self._node("Program", "Program", *[s.accept(self) for s in node.statements])

    def visitAssignment(self, node: AssignmentNode):
        return self._node("Assignment", f"{node.name} =", node.expr.accept(self))

    def visitWriteCmd(self, node: WriteCmdNode):
        cmd = "writeln" if node.newline else "write"
        return self._node("WriteCmd", cmd, node.arg.accept(self))

    def visitWriteString(self, node: WriteStringNode):
        return self._node("StringLiteral", f'"{node.value}"')

    def visitReadnCmd(self, node: ReadnCmdNode):
        return self._node("ReadnCmd", f"readn {node.name}")

    def visitRunCmd(self, node: RunCmdNode):
        return self._node("RunCmd", f'run "{node.filename}"')

    def visitExitCmd(self, node: ExitCmdNode):
        return self._node("ExitCmd", "exit")

    def visitIf(self, node: IfNode):
        cond = node.cond.accept(self)
        then = self._node("ThenBlock", "then", *[s.accept(self) for s in node.then_block])
        children = [cond, then]
        if node.else_block:
            else_ = self._node("ElseBlock", "else", *[s.accept(self) for s in node.else_block])
            children.append(else_)
        return {"type": "IfNode", "label": "if … then … end", "children": children}

    def visitWhile(self, node: WhileNode):
        cond  = node.cond.accept(self)
        block = self._node("WhileBlock", "do", *[s.accept(self) for s in node.block])
        return {"type": "WhileNode", "label": "while … do … end", "children": [cond, block]}

    def visitFuncDef(self, node: FuncDefNode):
        return self._node("FuncDef", f"def {node.name}({node.param})", node.body.accept(self))

    def visitBinaryOp(self, node: BinaryOpNode):
        return self._node("BinaryOp", f"op  '{node.op}'",
                          node.left.accept(self), node.right.accept(self))

    def visitCompare(self, node: CompareNode):
        return self._node("CompareOp", f"cmp  '{node.op}'",
                          node.left.accept(self), node.right.accept(self))

    def visitLogical(self, node: LogicalNode):
        return self._node("LogicalOp", node.op,
                          node.left.accept(self), node.right.accept(self))

    def visitNot(self, node: NotNode):
        return self._node("NotOp", "not", node.operand.accept(self))

    def visitUnaryMinus(self, node: UnaryMinusNode):
        return self._node("UnaryMinus", "negate  '-'", node.operand.accept(self))

    def visitNumber(self, node: NumberNode):
        val = int(node.value) if node.value == int(node.value) else node.value
        return self._node("Number", str(val))

    def visitBool(self, node: BoolNode):
        return self._node("Bool", "true" if node.value else "false")

    def visitVarRef(self, node: VarRefNode):
        return self._node("VarRef", node.name)

    def visitFuncCall(self, node: FuncCallNode):
        return self._node("FuncCall", f"{node.name}()", node.arg.accept(self))

    def visitUserFuncCall(self, node: UserFuncCallNode):
        return self._node("UserFuncCall", f"{node.name}()", node.arg.accept(self))