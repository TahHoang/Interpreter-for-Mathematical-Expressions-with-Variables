"""
visualizer_app.py — Compiler Visualizer chạy độc lập
Chạy: python visualizer_app.py
Mở:   http://localhost:5001
"""

import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from generated import LexerError, ParseError, TOKEN_NAMES
from generated.Y2ExpressionLexer import Y2ExpressionLexer
from generated.Y2ExpressionParser import Y2ExpressionParser
from visualizer.ast_serializer import ASTSerializer
from visualizer.tracing_interpreter import TracingInterpreter
from Y2MathInterpreter import InterpreterError

app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    return render_template("visualizer.html")


@app.route("/api/visualize", methods=["POST"])
def visualize():
    data   = request.get_json(force=True)
    source = data.get("source", "").strip()

    result = {"tokens": [], "ast": None, "steps": [],
              "variables": {}, "output": "", "error": None}

    if not source:
        return jsonify(result)

    # Phase 1: Lexer
    try:
        lexer  = Y2ExpressionLexer(source)
        tokens = lexer.getAllTokens()
        result["tokens"] = [
            {"type": TOKEN_NAMES.get(t.type, str(t.type)),
             "value": t.text, "line": t.line, "col": t.column}
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


if __name__ == "__main__":
    print("Compiler Visualizer →  http://localhost:5001")
    app.run(debug=True, port=5001)