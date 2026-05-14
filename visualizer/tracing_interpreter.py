"""
visualizer/tracing_interpreter.py  — v2.0
───────────────────────────────────────────
Subclass of Y2MathInterpreter — records every evaluation step.
Now handles all v2.0 nodes: if, while, compare, logical, user functions.
"""

import sys, os, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Y2MathInterpreter import Y2MathInterpreter, _fmt, _truthy
from generated.Y2ExpressionAST import *


class TracingInterpreter(Y2MathInterpreter):

    def __init__(self):
        out = io.StringIO()
        err = io.StringIO()
        super().__init__(stdout=out, stderr=err)
        self._out_buf = out
        self._err_buf = err
        self.steps: list[dict] = []

    def _log(self, phase: str, expr: str, result, note: str = ""):
        self.steps.append({"phase": phase, "expr": expr,
                            "result": _fmt(result), "note": note})

    # ── Expression visitors ───────────────────────────────────────────────────

    def visitBinaryOp(self, node: BinaryOpNode):
        left  = node.left.accept(self)
        right = node.right.accept(self)
        result = super().visitBinaryOp(node)
        self._log("eval", f"{_fmt(left)} {node.op} {_fmt(right)}", result)
        return result

    def visitCompare(self, node: CompareNode):
        left  = node.left.accept(self)
        right = node.right.accept(self)
        result = super().visitCompare(node)
        self._log("compare", f"{_fmt(left)} {node.op} {_fmt(right)}", result)
        return result

    def visitLogical(self, node: LogicalNode):
        result = super().visitLogical(node)
        self._log("logical", node.op, result)
        return result

    def visitNot(self, node: NotNode):
        result = super().visitNot(node)
        self._log("logical", "not", result)
        return result

    def visitUnaryMinus(self, node: UnaryMinusNode):
        operand = node.operand.accept(self)
        result = -operand
        self._log("eval", f"-{_fmt(operand)}", result)
        return result

    def visitFuncCall(self, node: FuncCallNode):
        arg    = node.arg.accept(self)
        result = super().visitFuncCall(node)
        self._log("func", f"{node.name}({_fmt(arg)})", result, "built-in")
        return result

    def visitUserFuncCall(self, node: UserFuncCallNode):
        arg    = node.arg.accept(self)
        result = super().visitUserFuncCall(node)
        self._log("func", f"{node.name}({_fmt(arg)})", result, "user-defined")
        return result

    # ── Statement visitors ────────────────────────────────────────────────────

    def visitAssignment(self, node: AssignmentNode):
        value = node.expr.accept(self)
        self._variables[node.name] = value
        self._log("assign", f"{node.name} = {_fmt(value)}", value, "lưu vào symbol table")

    def visitIf(self, node: IfNode):
        cond = node.cond.accept(self)
        branch = "then" if _truthy(cond) else "else"
        self._log("control", f"if → {branch}", cond, f"condition = {_fmt(cond)}")
        super().visitIf(node)

    def visitWhile(self, node: WhileNode):
        count = 0
        while _truthy(node.cond.accept(self)):
            count += 1
            self._log("control", f"while  iter {count}", True, "loop body")
            for stmt in node.block:
                stmt.accept(self)
            if count >= 100_000:
                break
        self._log("control", f"while  done", False, f"{count} iterations")

    def visitFuncDef(self, node: FuncDefNode):
        super().visitFuncDef(node)
        self._log("func", f"def {node.name}({node.param})", node.name, "registered")

    def visitWriteCmd(self, node: WriteCmdNode):
        before = self._out_buf.getvalue()
        super().visitWriteCmd(node)
        after  = self._out_buf.getvalue()
        output = after[len(before):]
        self._log("output", "writeln" if node.newline else "write",
                  output.strip(), "in ra màn hình")

    def get_output(self) -> str:
        return self._out_buf.getvalue()