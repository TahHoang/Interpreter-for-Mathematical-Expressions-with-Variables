"""
tests/test_interpreter.py
──────────────────────────
Unit tests for the Y2 Math Interpreter.
Run with:  python -m pytest tests/ -v
       or: python tests/test_interpreter.py
"""

import sys, os, io, math, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from Y2MathInterpreter import Y2MathInterpreter, InterpreterError, SemanticError
from generated import LexerError, ParseError
from generated.Y2ExpressionLexer import Y2ExpressionLexer, Token, T_NUMBER, T_PLUS, T_IDENTIFIER
from generated.Y2ExpressionParser import Y2ExpressionParser


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _run(source: str, stdin_data: str = "") -> tuple[str, str]:
    """Run source, return (stdout, stderr)."""
    out = io.StringIO()
    err = io.StringIO()
    inp = io.StringIO(stdin_data)
    interp = Y2MathInterpreter(stdin=inp, stdout=out, stderr=err)
    interp.run_source(source)
    return out.getvalue(), err.getvalue()


def _eval(source: str) -> dict:
    """Run source and return the symbol table."""
    interp = Y2MathInterpreter(stdout=io.StringIO(), stderr=io.StringIO())
    interp.run_source(source)
    return interp.get_variables()


# ─────────────────────────────────────────────────────────────────────────────
# Lexer tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLexer(unittest.TestCase):

    def _lex(self, src: str):
        tokens = Y2ExpressionLexer(src).getAllTokens()
        return [(t.type, t.text) for t in tokens]

    def test_number_integer(self):
        toks = self._lex("42")
        self.assertEqual(toks[0], (T_NUMBER, "42"))

    def test_number_float(self):
        toks = self._lex("3.14")
        self.assertEqual(toks[0], (T_NUMBER, "3.14"))

    def test_identifier(self):
        toks = self._lex("myVar")
        self.assertEqual(toks[0], (T_IDENTIFIER, "myVar"))

    def test_string_literal(self):
        from generated.Y2ExpressionLexer import T_STRING_LITERAL
        toks = self._lex('"hello world"')
        self.assertEqual(toks[0], (T_STRING_LITERAL, '"hello world"'))

    def test_operators(self):
        from generated.Y2ExpressionLexer import (
            T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PERCENT, T_CARET
        )
        toks = self._lex("+ - * / % ^")
        types = [t for t, _ in toks[:-1]]  # exclude EOF
        self.assertEqual(types, [T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PERCENT, T_CARET])

    def test_line_comment_skipped(self):
        toks = self._lex("42 // this is a comment\n")
        self.assertEqual(toks[0], (T_NUMBER, "42"))
        self.assertEqual(len(toks), 3)   # NUMBER, NEWLINE, EOF

    def test_unknown_char_raises(self):
        with self.assertRaises(LexerError):
            Y2ExpressionLexer("@").getAllTokens()


# ─────────────────────────────────────────────────────────────────────────────
# Parser tests
# ─────────────────────────────────────────────────────────────────────────────

class TestParser(unittest.TestCase):

    def _parse(self, src: str):
        tokens = Y2ExpressionLexer(src).getAllTokens()
        return Y2ExpressionParser(tokens).program()

    def test_simple_assignment(self):
        from generated.Y2ExpressionAST import ProgramNode, AssignmentNode, NumberNode
        tree = self._parse("x = 5")
        self.assertIsInstance(tree, ProgramNode)
        stmt = tree.statements[0]
        self.assertIsInstance(stmt, AssignmentNode)
        self.assertEqual(stmt.name, "x")
        self.assertIsInstance(stmt.expr, NumberNode)
        self.assertEqual(stmt.expr.value, 5.0)

    def test_binary_add(self):
        from generated.Y2ExpressionAST import BinaryOpNode
        tree = self._parse("z = 3 + 4")
        expr = tree.statements[0].expr
        self.assertIsInstance(expr, BinaryOpNode)
        self.assertEqual(expr.op, "+")

    def test_power_right_assoc(self):
        from generated.Y2ExpressionAST import BinaryOpNode
        tree = self._parse("r = 2 ^ 3 ^ 2")
        # Should parse as 2 ^ (3 ^ 2)
        outer = tree.statements[0].expr
        self.assertIsInstance(outer, BinaryOpNode)
        self.assertIsInstance(outer.right, BinaryOpNode)

    def test_missing_rparen_raises(self):
        from generated.Y2ExpressionParser import Y2ExpressionParser
        from generated.Y2ExpressionLexer import Y2ExpressionLexer
        toks = Y2ExpressionLexer("x = (3 + 4").getAllTokens()
        p = Y2ExpressionParser(toks)
        p.program()
        self.assertTrue(len(p.errors) > 0, "Parser should have recorded an error")


# ─────────────────────────────────────────────────────────────────────────────
# Interpreter – arithmetic
# ─────────────────────────────────────────────────────────────────────────────

class TestArithmetic(unittest.TestCase):

    def test_add(self):
        self.assertAlmostEqual(_eval("x = 3 + 4")["x"], 7.0)

    def test_sub(self):
        self.assertAlmostEqual(_eval("x = 10 - 3")["x"], 7.0)

    def test_mul(self):
        self.assertAlmostEqual(_eval("x = 6 * 7")["x"], 42.0)

    def test_div(self):
        self.assertAlmostEqual(_eval("x = 10 / 4")["x"], 2.5)

    def test_modulo(self):
        self.assertAlmostEqual(_eval("x = 10 % 3")["x"], 1.0)

    def test_power(self):
        self.assertAlmostEqual(_eval("x = 2 ^ 10")["x"], 1024.0)

    def test_precedence(self):
        self.assertAlmostEqual(_eval("x = 2 + 3 * 4")["x"], 14.0)

    def test_unary_minus(self):
        self.assertAlmostEqual(_eval("x = -5")["x"], -5.0)

    def test_parentheses(self):
        self.assertAlmostEqual(_eval("x = (2 + 3) * 4")["x"], 20.0)

    def test_nested_expr(self):
        self.assertAlmostEqual(_eval("x = (1 + 2) * (3 + 4) ^ 2")["x"], 147.0)

    def test_division_by_zero(self):
        with self.assertRaises(InterpreterError):
            _eval("x = 1 / 0")


# ─────────────────────────────────────────────────────────────────────────────
# Interpreter – variables
# ─────────────────────────────────────────────────────────────────────────────

class TestVariables(unittest.TestCase):

    def test_assign_and_use(self):
        result = _eval("a = 5\nb = a * 2")
        self.assertAlmostEqual(result["b"], 10.0)

    def test_reassign(self):
        result = _eval("x = 1\nx = x + 1\nx = x + 1")
        self.assertAlmostEqual(result["x"], 3.0)

    def test_undefined_variable(self):
        with self.assertRaises((InterpreterError, SemanticError)):
            _eval("y = z + 1")

    def test_underscore_name(self):
        result = _eval("_tmp = 99")
        self.assertAlmostEqual(result["_tmp"], 99.0)


# ─────────────────────────────────────────────────────────────────────────────
# Interpreter – built-in functions
# ─────────────────────────────────────────────────────────────────────────────

class TestFunctions(unittest.TestCase):

    def test_sqrt(self):
        self.assertAlmostEqual(_eval("x = sqrt(16)")["x"], 4.0)

    def test_sin(self):
        self.assertAlmostEqual(_eval("x = sin(0)")["x"], 0.0)

    def test_cos(self):
        self.assertAlmostEqual(_eval("x = cos(0)")["x"], 1.0)

    def test_tan(self):
        self.assertAlmostEqual(_eval("x = tan(0)")["x"], 0.0)

    def test_abs(self):
        self.assertAlmostEqual(_eval("x = abs(-7)")["x"], 7.0)

    def test_log(self):
        self.assertAlmostEqual(_eval("x = log(1)")["x"], 0.0)

    def test_exp(self):
        self.assertAlmostEqual(_eval("x = exp(0)")["x"], 1.0)

    def test_nested_function(self):
        self.assertAlmostEqual(_eval("x = sqrt(abs(-25))")["x"], 5.0)

    def test_sqrt_of_negative(self):
        with self.assertRaises(InterpreterError):
            _eval("x = sqrt(-1)")

    def test_unknown_function(self):
        with self.assertRaises((InterpreterError, SemanticError)):
            _eval("x = magic(3)")


# ─────────────────────────────────────────────────────────────────────────────
# Interpreter – commands
# ─────────────────────────────────────────────────────────────────────────────

class TestCommands(unittest.TestCase):

    def test_write_string(self):
        out, _ = _run('write "hello"')
        self.assertEqual(out, "hello")

    def test_writeln_string(self):
        out, _ = _run('writeln "hello"')
        self.assertEqual(out, "hello\n")

    def test_write_expr(self):
        out, _ = _run("write 3 + 4")
        self.assertEqual(out, "7")

    def test_writeln_expr(self):
        out, _ = _run("writeln 2 ^ 8")
        self.assertEqual(out, "256\n")

    def test_readn(self):
        result = _eval.__wrapped__ if hasattr(_eval, "__wrapped__") else None
        out = io.StringIO()
        inp = io.StringIO("42\n")
        interp = Y2MathInterpreter(stdin=inp, stdout=out, stderr=io.StringIO())
        interp.run_source("readn n\nm = n * 2")
        self.assertAlmostEqual(interp.get_variables()["n"], 42.0)
        self.assertAlmostEqual(interp.get_variables()["m"], 84.0)

    def test_readn_invalid(self):
        inp = io.StringIO("abc\n")
        interp = Y2MathInterpreter(stdin=inp, stdout=io.StringIO(), stderr=io.StringIO())
        with self.assertRaises(InterpreterError):
            interp.run_source("readn n")

    def test_multiline(self):
        src = """
a = 10
b = 20
c = a + b
write c
"""
        out, _ = _run(src)
        self.assertEqual(out, "30")

    def test_comments_ignored(self):
        src = """
// This is a comment
x = 5 // inline comment
"""
        result = _eval(src)
        self.assertAlmostEqual(result["x"], 5.0)


# ─────────────────────────────────────────────────────────────────────────────
# Integration — classic Y2 demo
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration(unittest.TestCase):

    def test_y2_demo_sqrt(self):
        """Replicate the blog's sqrt demo (without interactive readn)."""
        src = """
a = 144
result = sqrt(a)
write result
"""
        out, _ = _run(src)
        self.assertEqual(out, "12")

    def test_compound_formula(self):
        """Quadratic formula discriminant."""
        src = """
a = 1
b = -5
c = 6
disc = b^2 - 4*a*c
x1 = (-b + sqrt(disc)) / (2*a)
x2 = (-b - sqrt(disc)) / (2*a)
write x1
"""
        out, _ = _run(src)
        self.assertAlmostEqual(float(out), 3.0)

    def test_fibonacci_iterative(self):
        """Compute fib(8) iteratively through repeated assignment."""
        src = """
a = 0
b = 1
// 8 manual steps to get fib(8) = 21
t = a + b
a = b
b = t
t = a + b
a = b
b = t
t = a + b
a = b
b = t
t = a + b
a = b
b = t
t = a + b
a = b
b = t
t = a + b
a = b
b = t
t = a + b
a = b
b = t
write b
"""
        out, _ = _run(src)
        self.assertAlmostEqual(float(out), 21.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — Boolean, Comparison, Logical
# ─────────────────────────────────────────────────────────────────────────────

class TestBoolean(unittest.TestCase):

    def test_true_literal(self):
        self.assertEqual(_eval("x = true")["x"], True)

    def test_false_literal(self):
        self.assertEqual(_eval("x = false")["x"], False)

    def test_compare_eq(self):
        self.assertEqual(_eval("x = (3 == 3)")["x"], True)

    def test_compare_neq(self):
        self.assertEqual(_eval("x = (3 != 4)")["x"], True)

    def test_compare_lt(self):
        self.assertEqual(_eval("x = (2 < 5)")["x"], True)

    def test_compare_gt(self):
        self.assertEqual(_eval("x = (5 > 2)")["x"], True)

    def test_compare_leq(self):
        self.assertEqual(_eval("x = (3 <= 3)")["x"], True)

    def test_compare_geq(self):
        self.assertEqual(_eval("x = (4 >= 3)")["x"], True)

    def test_logical_and_true(self):
        self.assertEqual(_eval("x = true and true")["x"], True)

    def test_logical_and_false(self):
        self.assertEqual(_eval("x = true and false")["x"], False)

    def test_logical_or(self):
        self.assertEqual(_eval("x = false or true")["x"], True)

    def test_logical_not(self):
        self.assertEqual(_eval("x = not false")["x"], True)

    def test_complex_bool(self):
        self.assertEqual(_eval("x = 3 > 2 and not false")["x"], True)

    def test_bool_in_var(self):
        result = _eval("a = true\nb = not a")
        self.assertEqual(result["b"], False)


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — if/else
# ─────────────────────────────────────────────────────────────────────────────

class TestIfElse(unittest.TestCase):

    def test_if_true_branch(self):
        out, _ = _run('if true then\n  writeln "yes"\nend')
        self.assertEqual(out.strip(), "yes")

    def test_if_false_branch(self):
        out, _ = _run('if false then\n  writeln "yes"\nelse\n  writeln "no"\nend')
        self.assertEqual(out.strip(), "no")

    def test_if_compare_condition(self):
        out, _ = _run('x = 5\nif x > 3 then\n  writeln "big"\nelse\n  writeln "small"\nend')
        self.assertEqual(out.strip(), "big")

    def test_if_assigns_variable(self):
        result = _eval('x = 10\nif x == 10 then\n  y = 1\nelse\n  y = 0\nend')
        self.assertEqual(result["y"], 1)

    def test_if_no_else(self):
        result = _eval('x = 1\nif false then\n  x = 99\nend')
        self.assertEqual(result["x"], 1)

    def test_nested_if(self):
        src = 'x = 5\nif x > 0 then\n  if x > 3 then\n    r = 2\n  else\n    r = 1\n  end\nend'
        self.assertEqual(_eval(src)["r"], 2)


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — while loop
# ─────────────────────────────────────────────────────────────────────────────

class TestWhile(unittest.TestCase):

    def test_while_basic(self):
        src = 'i = 0\nwhile i < 5 do\n  i = i + 1\nend'
        self.assertEqual(_eval(src)["i"], 5)

    def test_while_sum(self):
        src = 'i = 1\ns = 0\nwhile i <= 10 do\n  s = s + i\n  i = i + 1\nend'
        self.assertEqual(_eval(src)["s"], 55)

    def test_while_factorial(self):
        src = 'n = 5\nf = 1\nwhile n > 1 do\n  f = f * n\n  n = n - 1\nend'
        self.assertEqual(_eval(src)["f"], 120)

    def test_while_zero_iterations(self):
        result = _eval('x = 0\nwhile false do\n  x = 99\nend')
        self.assertEqual(result["x"], 0)

    def test_while_output(self):
        out, _ = _run('i = 1\nwhile i <= 3 do\n  writeln i\n  i = i + 1\nend')
        self.assertEqual(out, "1\n2\n3\n")


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — User-defined functions
# ─────────────────────────────────────────────────────────────────────────────

class TestUserFunctions(unittest.TestCase):

    def test_def_and_call(self):
        result = _eval('def square(x) = x^2\ny = square(5)')
        self.assertEqual(result["y"], 25)

    def test_def_linear(self):
        result = _eval('def double(x) = x * 2\ny = double(7)')
        self.assertEqual(result["y"], 14)

    def test_def_with_builtin(self):
        result = _eval('def hyp(x) = sqrt(x^2 + x^2)\ny = hyp(3)')
        self.assertAlmostEqual(result["y"], 3 * (2**0.5))

    def test_def_scope_isolation(self):
        # parameter 'x' should not leak into outer scope
        result = _eval('x = 99\ndef f(x) = x + 1\ny = f(10)')
        self.assertEqual(result["x"], 99)
        self.assertEqual(result["y"], 11)

    def test_undefined_function_raises(self):
        with self.assertRaises((InterpreterError, SemanticError)):
            _eval("y = unknown(5)")


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — Semantic Analyzer
# ─────────────────────────────────────────────────────────────────────────────

class TestSemanticAnalyzer(unittest.TestCase):

    def test_undefined_variable_caught(self):
        with self.assertRaises((InterpreterError, SemanticError)):
            _eval("y = z + 1")

    def test_undefined_function_caught(self):
        with self.assertRaises((InterpreterError, SemanticError)):
            _eval("y = ghost(3)")

    def test_negate_bool_caught(self):
        with self.assertRaises((InterpreterError, SemanticError)):
            _eval("x = -true")

    def test_valid_program_no_errors(self):
        # Should not raise anything
        _eval('x = 5\ny = x + 1')

    def test_readn_defines_var(self):
        # After readn, variable is defined — no semantic error
        import io as _io
        out = _io.StringIO()
        inp = _io.StringIO("10\n")
        from Y2MathInterpreter import Y2MathInterpreter
        interp = Y2MathInterpreter(stdin=inp, stdout=out, stderr=_io.StringIO())
        interp.run_source("readn n\ny = n * 2")
        self.assertAlmostEqual(interp.get_variables()["y"], 20.0)


# ─────────────────────────────────────────────────────────────────────────────
# v2.0 — DFA Lexer new tokens
# ─────────────────────────────────────────────────────────────────────────────

class TestLexerV2(unittest.TestCase):

    def _lex(self, src):
        from generated.Y2ExpressionLexer import Y2ExpressionLexer, TOKEN_NAMES
        toks = Y2ExpressionLexer(src).getAllTokens()
        return [(TOKEN_NAMES[t.type], t.text) for t in toks]

    def test_lex_true_false(self):
        toks = self._lex("true false")
        self.assertEqual(toks[0], ("TRUE",  "true"))
        self.assertEqual(toks[1], ("FALSE", "false"))

    def test_lex_eq_neq(self):
        toks = self._lex("== !=")
        self.assertEqual(toks[0][0], "EQ")
        self.assertEqual(toks[1][0], "NEQ")

    def test_lex_leq_geq(self):
        toks = self._lex("<= >=")
        self.assertEqual(toks[0][0], "LEQ")
        self.assertEqual(toks[1][0], "GEQ")

    def test_lex_keywords(self):
        for kw in ["if","then","else","end","while","do","def","and","or","not"]:
            toks = self._lex(kw)
            self.assertEqual(toks[0][1], kw)

    def test_lex_lt_gt_not_confused(self):
        # Single < and > should NOT become LEQ/GEQ
        toks = self._lex("< >")
        self.assertEqual(toks[0][0], "LT")
        self.assertEqual(toks[1][0], "GT")


if __name__ == "__main__":
    unittest.main(verbosity=2)