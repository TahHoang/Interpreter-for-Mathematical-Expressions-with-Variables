"""
generated/Y2ExpressionParser.py  — v2.0
─────────────────────────────────────────
Recursive-descent parser with error recovery.

Error recovery strategy: "synchronise and continue"
  - When a parse error occurs, record it and skip tokens until
    a safe synchronisation point (newline, 'end', EOF).
  - This lets the parser report multiple errors in one pass
    instead of crashing on the first one.
"""

from __future__ import annotations
from typing import List, Tuple, Optional
from dataclasses import dataclass, field

from .Y2ExpressionLexer import (
    Token,
    T_EOF, T_NEWLINE,
    T_WRITE, T_WRITELN, T_READN, T_RUN, T_EXIT,
    T_IF, T_THEN, T_ELSE, T_END,
    T_WHILE, T_DO, T_DEF,
    T_TRUE, T_FALSE, T_AND, T_OR, T_NOT,
    T_ASSIGN, T_EQ, T_NEQ, T_LT, T_GT, T_LEQ, T_GEQ,
    T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PERCENT, T_CARET,
    T_LPAREN, T_RPAREN,
    T_NUMBER, T_STRING_LITERAL, T_IDENTIFIER,
)
from .Y2ExpressionAST import (
    ASTNode, ProgramNode, AssignmentNode,
    WriteCmdNode, WriteStringNode, ReadnCmdNode, RunCmdNode, ExitCmdNode,
    IfNode, WhileNode, FuncDefNode,
    BinaryOpNode, CompareNode, LogicalNode, NotNode,
    UnaryMinusNode, NumberNode, BoolNode, VarRefNode,
    FuncCallNode, UserFuncCallNode,
)

# Built-in math function names
_BUILTINS = frozenset([
    "sqrt","sin","cos","tan","abs","log","exp","ceil","floor",
])

# Statement-starting keywords (used for error sync)
_STMT_START = frozenset([
    T_IF, T_WHILE, T_DEF, T_WRITE, T_WRITELN, T_READN, T_RUN, T_EXIT,
    T_IDENTIFIER,
])
_BLOCK_END = frozenset([T_ELSE, T_END, T_EOF])


@dataclass
class ParseError:
    """A non-fatal parse error (collected for error recovery)."""
    message: str
    line: int
    col:  int

    def __str__(self) -> str:
        return f"[line {self.line}:{self.col}] {self.message}"


class ParseException(Exception):
    """Fatal — raised only when we cannot recover."""


class Y2ExpressionParser:
    """
    Parses a token list into an AST.
    Collects non-fatal errors in self.errors instead of raising immediately.
    """

    def __init__(self, tokens: List[Token]) -> None:
        self._tokens = tokens
        self._pos    = 0
        self.errors: List[ParseError] = []

    # ── Token helpers ─────────────────────────────────────────────────────────

    def _cur(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        return self._tokens[min(idx, len(self._tokens)-1)]

    def _match(self, *types: int) -> bool:
        return self._cur().type in types

    def _consume(self, ttype: int, msg: str = "") -> Token:
        tok = self._cur()
        if tok.type != ttype:
            err_msg = msg or f"Expected {ttype}, got '{tok.text}'"
            self.errors.append(ParseError(err_msg, tok.line, tok.column))
            # Don't advance — let caller handle
            return tok
        self._pos += 1
        return tok

    def _skip_newlines(self) -> None:
        while self._match(T_NEWLINE):
            self._pos += 1

    def _sync(self) -> None:
        """Skip tokens until a safe restart point."""
        while not self._match(T_EOF, T_NEWLINE, T_END, T_ELSE):
            self._pos += 1
        if self._match(T_NEWLINE):
            self._pos += 1

    # ── Grammar rules ─────────────────────────────────────────────────────────

    def program(self) -> ProgramNode:
        stmts: List[ASTNode] = []
        self._skip_newlines()
        while not self._match(T_EOF):
            stmt = self._statement()
            if stmt is not None:
                stmts.append(stmt)
            self._skip_newlines()
        self._consume(T_EOF)
        return ProgramNode(stmts)

    def _statement(self) -> Optional[ASTNode]:
        self._skip_newlines()
        tok = self._cur()

        try:
            if tok.type == T_NEWLINE:
                self._pos += 1
                return None

            if tok.type == T_DEF:
                return self._func_def()

            if tok.type == T_IF:
                return self._if_stmt()

            if tok.type == T_WHILE:
                return self._while_stmt()

            # assignment: IDENTIFIER ASSIGN ...
            if tok.type == T_IDENTIFIER and self._peek(1).type == T_ASSIGN:
                return self._assignment()

            # command keywords
            if tok.type in (T_WRITE, T_WRITELN, T_READN, T_RUN, T_EXIT):
                return self._command()

            # bare expression statement (e.g. a function call used for side effects)
            if tok.type in (T_IDENTIFIER, T_NUMBER, T_TRUE, T_FALSE, T_LPAREN, T_NOT, T_MINUS):
                expr = self._expr()
                return expr

            # Unknown token
            self.errors.append(ParseError(
                f"Unexpected token '{tok.text}'", tok.line, tok.column
            ))
            self._sync()
            return None

        except ParseException:
            self._sync()
            return None

    def _func_def(self) -> FuncDefNode:
        """def name(param) = expr"""
        self._consume(T_DEF)
        name_tok  = self._consume(T_IDENTIFIER, "Expected function name after 'def'")
        self._consume(T_LPAREN, "Expected '(' after function name")
        param_tok = self._consume(T_IDENTIFIER, "Expected parameter name")
        self._consume(T_RPAREN, "Expected ')' after parameter")
        self._consume(T_ASSIGN,  "Expected '=' after ')'")
        body = self._expr()
        return FuncDefNode(name=name_tok.text, param=param_tok.text, body=body)

    def _if_stmt(self) -> IfNode:
        """if expr then block (else block)? end"""
        self._consume(T_IF)
        cond = self._expr()
        self._consume(T_THEN, "Expected 'then' after if-condition")
        then_block = self._block()

        else_block: List[ASTNode] = []
        if self._match(T_ELSE):
            self._pos += 1
            else_block = self._block()

        self._consume(T_END, "Expected 'end' to close if-statement")
        return IfNode(cond=cond, then_block=then_block, else_block=else_block)

    def _while_stmt(self) -> WhileNode:
        """while expr do block end"""
        self._consume(T_WHILE)
        cond = self._expr()
        self._consume(T_DO, "Expected 'do' after while-condition")
        block = self._block()
        self._consume(T_END, "Expected 'end' to close while-loop")
        return WhileNode(cond=cond, block=block)

    def _block(self) -> List[ASTNode]:
        """Zero or more statements until ELSE / END / EOF."""
        stmts: List[ASTNode] = []
        self._skip_newlines()
        while not self._match(T_EOF, *_BLOCK_END):
            stmt = self._statement()
            if stmt is not None:
                stmts.append(stmt)
            self._skip_newlines()
        return stmts

    def _assignment(self) -> AssignmentNode:
        name = self._consume(T_IDENTIFIER).text
        self._consume(T_ASSIGN)
        return AssignmentNode(name=name, expr=self._expr())

    def _command(self) -> ASTNode:
        tok = self._cur()

        if tok.type == T_WRITELN:
            self._pos += 1
            return WriteCmdNode(arg=self._write_arg(), newline=True)

        if tok.type == T_WRITE:
            self._pos += 1
            return WriteCmdNode(arg=self._write_arg(), newline=False)

        if tok.type == T_READN:
            self._pos += 1
            name = self._consume(T_IDENTIFIER, "readn expects a variable name").text
            return ReadnCmdNode(name=name)

        if tok.type == T_RUN:
            self._pos += 1
            s = self._consume(T_STRING_LITERAL, "run expects a filename string").text
            return RunCmdNode(filename=s[1:-1])

        if tok.type == T_EXIT:
            self._pos += 1
            return ExitCmdNode()

        raise ParseException(f"Unknown command '{tok.text}'")

    def _write_arg(self) -> ASTNode:
        if self._match(T_STRING_LITERAL):
            tok = self._cur(); self._pos += 1
            return WriteStringNode(value=tok.text[1:-1])
        return self._expr()

    # ── Expression hierarchy ──────────────────────────────────────────────────

    def _expr(self) -> ASTNode:
        return self._or_expr()

    def _or_expr(self) -> ASTNode:
        node = self._and_expr()
        while self._match(T_OR):
            self._pos += 1
            node = LogicalNode(op="or", left=node, right=self._and_expr())
        return node

    def _and_expr(self) -> ASTNode:
        node = self._not_expr()
        while self._match(T_AND):
            self._pos += 1
            node = LogicalNode(op="and", left=node, right=self._not_expr())
        return node

    def _not_expr(self) -> ASTNode:
        if self._match(T_NOT):
            self._pos += 1
            return NotNode(operand=self._not_expr())
        return self._cmp_expr()

    def _cmp_expr(self) -> ASTNode:
        left = self._add_expr()
        if self._match(T_EQ, T_NEQ, T_LT, T_GT, T_LEQ, T_GEQ):
            op = self._cur().text; self._pos += 1
            right = self._add_expr()
            return CompareNode(op=op, left=left, right=right)
        return left

    def _add_expr(self) -> ASTNode:
        node = self._mul_expr()
        while self._match(T_PLUS, T_MINUS):
            op = self._cur().text; self._pos += 1
            node = BinaryOpNode(op=op, left=node, right=self._mul_expr())
        return node

    def _mul_expr(self) -> ASTNode:
        node = self._pow_expr()
        while self._match(T_STAR, T_SLASH, T_PERCENT):
            op = self._cur().text; self._pos += 1
            node = BinaryOpNode(op=op, left=node, right=self._pow_expr())
        return node

    def _pow_expr(self) -> ASTNode:
        base = self._unary()
        if self._match(T_CARET):
            self._pos += 1
            return BinaryOpNode(op="^", left=base, right=self._pow_expr())
        return base

    def _unary(self) -> ASTNode:
        if self._match(T_MINUS):
            self._pos += 1
            return UnaryMinusNode(operand=self._unary())
        return self._primary()

    def _primary(self) -> ASTNode:
        tok = self._cur()

        if tok.type == T_NUMBER:
            self._pos += 1
            return NumberNode(value=float(tok.text))

        if tok.type == T_TRUE:
            self._pos += 1
            return BoolNode(value=True)

        if tok.type == T_FALSE:
            self._pos += 1
            return BoolNode(value=False)

        if tok.type == T_IDENTIFIER:
            # function call?
            if self._peek(1).type == T_LPAREN:
                name = tok.text.lower(); self._pos += 1
                self._consume(T_LPAREN)
                arg = self._expr()
                self._consume(T_RPAREN, f"Missing ')' after argument to '{name}'")
                if name in _BUILTINS:
                    return FuncCallNode(name=name, arg=arg)
                return UserFuncCallNode(name=name, arg=arg)
            self._pos += 1
            return VarRefNode(name=tok.text)

        if tok.type == T_LPAREN:
            self._pos += 1
            inner = self._expr()
            self._consume(T_RPAREN, "Missing ')'")
            return inner

        # Error recovery for primary
        self.errors.append(ParseError(
            f"Unexpected token '{tok.text}' in expression",
            tok.line, tok.column
        ))
        # return a dummy node so parsing can continue
        self._pos += 1
        return NumberNode(value=0.0)