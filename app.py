"""
app.py — Flask backend cho Y2 Math REPL
Chạy: python app.py
Mở:   http://localhost:5000
"""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from Y2MathInterpreter import Y2MathInterpreter, InterpreterError, _ExitSignal
from generated import LexerError, ParseError
from generated.Y2ExpressionLexer import Y2ExpressionLexer, TOKEN_NAMES
from generated.Y2ExpressionParser import Y2ExpressionParser
from visualizer.ast_serializer import ASTSerializer
from visualizer.tracing_interpreter import TracingInterpreter

app = Flask(__name__)
CORS(app)

# ── Mỗi session giữ một interpreter riêng (lưu biến giữa các lần gửi) ────────
# Trong demo đơn giản này dùng một interpreter toàn cục.
# Nếu cần multi-user thật sự → dùng Flask-Session hoặc database.
_interpreter: Y2MathInterpreter | None = None


def get_interpreter() -> Y2MathInterpreter:
    global _interpreter
    if _interpreter is None:
        _interpreter = _make_interpreter()
    return _interpreter


def _make_interpreter() -> Y2MathInterpreter:
    """Tạo interpreter mới với stdout/stderr được capture."""
    out = io.StringIO()
    err = io.StringIO()
    interp = Y2MathInterpreter(stdout=out, stderr=err)
    interp._out_buf = out
    interp._err_buf = err
    return interp


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run", methods=["POST"])
def run_code():
    """
    POST /api/run
    Body: { "code": "x = 3 + 4\nwriteln x" }
    Response: {
        "output": "7.0\n",
        "error":  null,
        "variables": {"x": 7.0}
    }
    """
    data = request.get_json(force=True)
    code = data.get("code", "").strip()

    if not code:
        return jsonify(output="", error=None, variables={})

    interp = get_interpreter()

    # Reset output buffers nhưng giữ nguyên bảng biến
    interp._out_buf.truncate(0)
    interp._out_buf.seek(0)
    interp._err_buf.truncate(0)
    interp._err_buf.seek(0)

    error = None
    exited = False

    try:
        interp.run_source(code)
    except _ExitSignal:
        exited = True
        # Reset toàn bộ interpreter khi user gõ exit
        global _interpreter
        _interpreter = None
    except (LexerError, ParseError, InterpreterError) as exc:
        error = str(exc)
    except Exception as exc:
        error = f"Internal error: {exc}"

    output = interp._out_buf.getvalue()

    if exited:
        output += "\n[Session reset — interpreter cleared]"

    variables = interp.get_variables() if not exited else {}

    return jsonify(
        output=output,
        error=error,
        variables=variables,
    )


@app.route("/api/reset", methods=["POST"])
def reset_session():
    """Xóa toàn bộ bảng biến, bắt đầu phiên mới."""
    global _interpreter
    _interpreter = None
    return jsonify(ok=True, message="Session reset.")


# ── Dev server ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Y2 Math REPL đang chạy tại http://localhost:5000")
    app.run(debug=True, port=5000)


# ── Visualizer routes ─────────────────────────────────────────────────────────

@app.route("/visualizer")
def visualizer_page():
    return render_template("visualizer.html")


@app.route("/api/visualize", methods=["POST"])
def visualize():
    data   = request.get_json(force=True)
    source = data.get("source", "").strip()

    result = {"tokens": [], "ast": None, "steps": [], "variables": {}, "output": "", "error": None}

    if not source:
        return jsonify(result)

    # Phase 1: Lexer
    try:
        lexer  = Y2ExpressionLexer(source)
        tokens = lexer.getAllTokens()
        result["tokens"] = [
            {"type": TOKEN_NAMES.get(t.type, str(t.type)), "value": t.text, "line": t.line, "col": t.column}
            for t in tokens
        ]
    except LexerError as exc:
        result["error"] = {"phase": "lexer", "message": str(exc)}
        return jsonify(result)

    # Phase 2: Parser → AST
    try:
        parser = Y2ExpressionParser(tokens)
        tree   = parser.program()
        result["ast"] = ASTSerializer().visitProgram(tree)
    except ParseError as exc:
        result["error"] = {"phase": "parser", "message": str(exc)}
        return jsonify(result)

    # Phase 3: Tracing evaluation
    interp = TracingInterpreter()
    try:
        interp.run_source(source)
        result["steps"]     = interp.steps
        result["variables"] = interp.get_variables()
        result["output"]    = interp.get_output()
    except Exception as exc:
        result["error"]  = {"phase": "eval", "message": str(exc)}
        result["steps"]  = interp.steps
    return jsonify(result)