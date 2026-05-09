"""
visualizer/tracing_interpreter.py
───────────────────────────────────
Subclass của Y2MathInterpreter — override các visitXxx để
ghi lại từng bước tính toán vào self.steps.

Mỗi step có dạng:
{
    "phase":  "eval" | "assign" | "output" | "func",
    "expr":   "3 + 4",          ← biểu thức đang tính
    "result": 7.0,              ← kết quả
    "note":   "lưu vào x"       ← ghi chú thêm (tùy)
}
"""

import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Y2MathInterpreter import Y2MathInterpreter
from generated.Y2ExpressionAST import (
    BinaryOpNode, UnaryMinusNode, FuncCallNode,
    AssignmentNode, WriteCmdNode, WriteStringNode,
)


def _fmt(n) -> str:
    """Định dạng số: bỏ .0 nếu là số nguyên."""
    if isinstance(n, float):
        return str(int(n)) if n == int(n) else f"{n:.6g}"
    return str(n)


class TracingInterpreter(Y2MathInterpreter):
    """
    Ghi lại từng bước của quá trình evaluate để hiển thị trên UI.
    Dùng cho Compiler Visualizer, không dùng cho REPL thường.
    """

    def __init__(self):
        out = io.StringIO()
        err = io.StringIO()
        super().__init__(stdout=out, stderr=err)
        self._out_buf = out
        self._err_buf = err
        self.steps: list[dict] = []

    # ── Override expression visitors ──────────────────────────────────────────

    def visitBinaryOp(self, node: BinaryOpNode) -> float:
        left  = node.left.accept(self)
        right = node.right.accept(self)

        result = super().visitBinaryOp(node)

        self.steps.append({
            "phase":  "eval",
            "expr":   f"{_fmt(left)} {node.op} {_fmt(right)}",
            "result": result,
            "note":   "",
        })
        return result

    def visitUnaryMinus(self, node: UnaryMinusNode) -> float:
        operand = node.operand.accept(self)
        result  = -operand
        self.steps.append({
            "phase":  "eval",
            "expr":   f"-{_fmt(operand)}",
            "result": result,
            "note":   "",
        })
        return result

    def visitFuncCall(self, node: FuncCallNode) -> float:
        arg    = node.arg.accept(self)
        result = super().visitFuncCall(node)
        self.steps.append({
            "phase":  "func",
            "expr":   f"{node.name}({_fmt(arg)})",
            "result": result,
            "note":   f"built-in function",
        })
        return result

    # ── Override statement visitors ───────────────────────────────────────────

    def visitAssignment(self, node: AssignmentNode):
        value = node.expr.accept(self)
        self._set_var(node.name, value)
        self.steps.append({
            "phase":  "assign",
            "expr":   f"{node.name} = {_fmt(value)}",
            "result": value,
            "note":   f"lưu vào symbol table",
        })

    def visitWriteCmd(self, node: WriteCmdNode):
        # Gọi parent để thực thi, capture output
        super().visitWriteCmd(node)
        output = self._out_buf.getvalue()
        # Chỉ lấy dòng vừa in
        self.steps.append({
            "phase":  "output",
            "expr":   f'{"writeln" if node.newline else "write"}',
            "result": output.strip(),
            "note":   "in ra màn hình",
        })

    def get_output(self) -> str:
        return self._out_buf.getvalue()