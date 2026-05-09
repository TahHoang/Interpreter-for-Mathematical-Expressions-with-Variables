"""
visualizer/ast_serializer.py
─────────────────────────────
Visitor thứ hai — chỉ có nhiệm vụ chuyển AST sang dict để JSON serialize.
Không evaluate, không side effect.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generated.Y2ExpressionVisitor import Y2ExpressionVisitor
from generated.Y2ExpressionAST import (
    ProgramNode, AssignmentNode, WriteCmdNode, WriteStringNode,
    ReadnCmdNode, RunCmdNode, ExitCmdNode,
    BinaryOpNode, UnaryMinusNode, NumberNode, VarRefNode, FuncCallNode,
)


class ASTSerializer(Y2ExpressionVisitor):
    """
    Duyệt AST và trả về dict lồng nhau, sẵn sàng để json.dumps().

    Mỗi node có dạng:
    {
        "type": "BinaryOp",
        "op": "+",
        "label": "3 + 4",       ← nhãn hiển thị trên UI
        "children": [...]
    }
    """

    def visitProgram(self, node: ProgramNode):
        return {
            "type": "Program",
            "label": "Program",
            "children": [s.accept(self) for s in node.statements],
        }

    def visitAssignment(self, node: AssignmentNode):
        return {
            "type": "Assignment",
            "label": f"{node.name} =",
            "name": node.name,
            "children": [node.expr.accept(self)],
        }

    def visitWriteCmd(self, node: WriteCmdNode):
        cmd = "writeln" if node.newline else "write"
        return {
            "type": "WriteCmd",
            "label": cmd,
            "children": [node.arg.accept(self)],
        }

    def visitWriteString(self, node: WriteStringNode):
        return {
            "type": "StringLiteral",
            "label": f'"{node.value}"',
            "children": [],
        }

    def visitReadnCmd(self, node: ReadnCmdNode):
        return {
            "type": "ReadnCmd",
            "label": f"readn {node.name}",
            "children": [],
        }

    def visitRunCmd(self, node: RunCmdNode):
        return {
            "type": "RunCmd",
            "label": f'run "{node.filename}"',
            "children": [],
        }

    def visitExitCmd(self, node: ExitCmdNode):
        return {
            "type": "ExitCmd",
            "label": "exit",
            "children": [],
        }

    def visitBinaryOp(self, node: BinaryOpNode):
        return {
            "type": "BinaryOp",
            "label": f"op  '{node.op}'",
            "op": node.op,
            "children": [
                node.left.accept(self),
                node.right.accept(self),
            ],
        }

    def visitUnaryMinus(self, node: UnaryMinusNode):
        return {
            "type": "UnaryMinus",
            "label": "negate  '-'",
            "children": [node.operand.accept(self)],
        }

    def visitNumber(self, node: NumberNode):
        val = int(node.value) if node.value == int(node.value) else node.value
        return {
            "type": "Number",
            "label": str(val),
            "value": node.value,
            "children": [],
        }

    def visitVarRef(self, node: VarRefNode):
        return {
            "type": "VarRef",
            "label": node.name,
            "name": node.name,
            "children": [],
        }

    def visitFuncCall(self, node: FuncCallNode):
        return {
            "type": "FuncCall",
            "label": f"{node.name}()",
            "name": node.name,
            "children": [node.arg.accept(self)],
        }