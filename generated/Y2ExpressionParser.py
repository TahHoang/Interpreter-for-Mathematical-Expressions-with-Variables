"""
generated/Y2ExpressionParser.py
────────────────────────────────
Recursive-descent parser that consumes the token stream produced by
Y2ExpressionLexer and builds an AST from Y2ExpressionAST.

The method names map 1-to-1 to the grammar rules in Y2Expression.g4.
When the real ANTLR4 runtime is installed, swap this file for the
auto-generated one; the Visitor and Interpreter won't need to change.
"""

from __future__ import annotations
from typing import List, Optional

from .Y2ExpressionLexer import (
    Token,
    Y2ExpressionLexer,
    T_EOF, T_WRITE, T_WRITELN, T_READN, T_RUN, T_EXIT,
    T_ASSIGN, T_PLUS, T_MINUS, T_STAR, T_SLASH, T_PERCENT,
    T_CARET, T_LPAREN, T_RPAREN, T_NUMBER, T_STRING_LITERAL,
    T_IDENTIFIER, T_NEWLINE,
)
from .Y2ExpressionAST import (
    ProgramNode, AssignmentNode, WriteCmdNode, WriteStringNode,
    ReadnCmdNode, RunCmdNode, ExitCmdNode,
    BinaryOpNode, UnaryMinusNode, NumberNode, VarRefNode, FuncCallNode,
    ASTNode,
)


class ParseError(Exception):
    pass


class Y2ExpressionParser:
    """
    Parses a list of tokens into an AST.

    Usage:
        lexer  = Y2ExpressionLexer(source)
        tokens = lexer.getAllTokens()
        parser = Y2ExpressionParser(tokens)
        tree   = parser.program()
    """

    def __init__(self, tokens: List[Token]) -> None:
        # Filter out newline tokens only where they are meaningful
        # (used as statement terminators).  Keep them in the stream.
        self._tokens = tokens
        self._pos    = 0

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _peek(self, offset: int = 0) -> Token:
        idx = self._pos + offset
        if idx < len(self._tokens):
            return self._tokens[idx]
        return self._tokens[-1]  # EOF

    def _match(self, *types: int) -> bool:
        return self._current().type in types

    def _consume(self, ttype: int, msg: str = "") -> Token:
        tok = self._current()
        if tok.type != ttype:
            raise ParseError(
                msg or f"Expected token {ttype}, got {tok!r}"
            )
        self._pos += 1
        return tok

    def _skip_newlines(self) -> None:
        while self._match(T_NEWLINE):
            self._pos += 1

    # ── Grammar rules (mirror Y2Expression.g4) ───────────────────────────────

    def program(self) -> ProgramNode:
        """program : statement+ EOF"""
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
        """statement : assignment | command"""
        tok = self._current()

        if tok.type == T_NEWLINE:
            self._pos += 1
            return None

        # Lookahead: is this  IDENTIFIER '='  ?
        if tok.type == T_IDENTIFIER and self._peek(1).type == T_ASSIGN:
            return self._assignment()

        # Otherwise it's a command
        return self._command()

    def _assignment(self) -> AssignmentNode:
        """assignment : IDENTIFIER ASSIGN expr"""
        name_tok = self._consume(T_IDENTIFIER)
        self._consume(T_ASSIGN)
        value = self._expr()
        return AssignmentNode(name=name_tok.text, expr=value)

    def _command(self) -> ASTNode:
        """command : WRITE | WRITELN | READN | RUN | EXIT"""
        tok = self._current()

        if tok.type == T_WRITELN:
            self._pos += 1
            arg = self._write_arg()
            return WriteCmdNode(arg=arg, newline=True)

        if tok.type == T_WRITE:
            self._pos += 1
            arg = self._write_arg()
            return WriteCmdNode(arg=arg, newline=False)

        if tok.type == T_READN:
            self._pos += 1
            name_tok = self._consume(
                T_IDENTIFIER,
                f"readn expects a variable name at line {tok.line}"
            )
            return ReadnCmdNode(name=name_tok.text)

        if tok.type == T_RUN:
            self._pos += 1
            str_tok = self._consume(
                T_STRING_LITERAL,
                f"run expects a filename string at line {tok.line}"
            )
            filename = str_tok.text[1:-1]   # strip quotes
            return RunCmdNode(filename=filename)

        if tok.type == T_EXIT:
            self._pos += 1
            return ExitCmdNode()

        raise ParseError(
            f"Unknown statement starting with {tok!r} at line {tok.line}"
        )

    def _write_arg(self) -> ASTNode:
        """writeArg : STRING_LITERAL | expr"""
        if self._match(T_STRING_LITERAL):
            tok = self._current()
            self._pos += 1
            content = tok.text[1:-1]   # strip surrounding quotes
            return WriteStringNode(value=content)
        return self._expr()

    # ── Expression hierarchy ──────────────────────────────────────────────────

    def _expr(self) -> ASTNode:
        """expr : expr (PLUS | MINUS) term | term"""
        node = self._term()
        while self._match(T_PLUS, T_MINUS):
            op  = self._current().text
            self._pos += 1
            right = self._term()
            node = BinaryOpNode(op=op, left=node, right=right)
        return node

    def _term(self) -> ASTNode:
        """term : term (STAR | SLASH | PERCENT) power | power"""
        node = self._power()
        while self._match(T_STAR, T_SLASH, T_PERCENT):
            op  = self._current().text
            self._pos += 1
            right = self._power()
            node = BinaryOpNode(op=op, left=node, right=right)
        return node

    def _power(self) -> ASTNode:
        """power : unary CARET power | unary   (right-assoc)"""
        base = self._unary()
        if self._match(T_CARET):
            self._pos += 1
            exp = self._power()  # right-recursive for right-associativity
            return BinaryOpNode(op="^", left=base, right=exp)
        return base

    def _unary(self) -> ASTNode:
        """unary : MINUS unary | primary"""
        if self._match(T_MINUS):
            self._pos += 1
            operand = self._unary()
            return UnaryMinusNode(operand=operand)
        return self._primary()

    def _primary(self) -> ASTNode:
        """primary : NUMBER | IDENTIFIER '(' expr ')' | IDENTIFIER | '(' expr ')'"""
        tok = self._current()

        if tok.type == T_NUMBER:
            self._pos += 1
            return NumberNode(value=float(tok.text))

        if tok.type == T_IDENTIFIER:
            # Lookahead: function call?
            if self._peek(1).type == T_LPAREN:
                func_name = tok.text.lower()
                self._pos += 1                    # identifier
                self._consume(T_LPAREN)
                arg = self._expr()
                self._consume(T_RPAREN, f"Missing ')' after function argument at line {tok.line}")
                return FuncCallNode(name=func_name, arg=arg)
            # Variable reference
            self._pos += 1
            return VarRefNode(name=tok.text)

        if tok.type == T_LPAREN:
            self._pos += 1
            inner = self._expr()
            self._consume(T_RPAREN, f"Missing ')' at line {tok.line}")
            return inner

        raise ParseError(
            f"Unexpected token {tok!r} in expression at line {tok.line}"
        )
