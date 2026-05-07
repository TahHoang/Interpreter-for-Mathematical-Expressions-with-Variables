"""
generated/Y2ExpressionLexer.py
──────────────────────────────
Hand-written lexer that exactly mirrors what ANTLR4 would generate from
Y2Expression.g4.  It produces the same Token objects and token-type
constants that the parser (Y2ExpressionParser.py) expects.

When the antlr4-python3-runtime package is available you can regenerate
the real files with:

    antlr4 -Dlanguage=Python3 -visitor Y2Expression.g4

and replace this file.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional


# ── Token type constants (same names ANTLR4 would generate) ──────────────────
T_EOF           = -1
T_WRITE         =  1
T_WRITELN       =  2
T_READN         =  3
T_RUN           =  4
T_EXIT          =  5
T_ASSIGN        =  6
T_PLUS          =  7
T_MINUS         =  8
T_STAR          =  9
T_SLASH         = 10
T_PERCENT       = 11
T_CARET         = 12
T_LPAREN        = 13
T_RPAREN        = 14
T_NUMBER        = 15
T_STRING_LITERAL= 16
T_IDENTIFIER    = 17
T_NEWLINE       = 18

TOKEN_NAMES = {
    T_EOF:            "EOF",
    T_WRITE:          "WRITE",
    T_WRITELN:        "WRITELN",
    T_READN:          "READN",
    T_RUN:            "RUN",
    T_EXIT:           "EXIT",
    T_ASSIGN:         "ASSIGN",
    T_PLUS:           "PLUS",
    T_MINUS:          "MINUS",
    T_STAR:           "STAR",
    T_SLASH:          "SLASH",
    T_PERCENT:        "PERCENT",
    T_CARET:          "CARET",
    T_LPAREN:         "LPAREN",
    T_RPAREN:         "RPAREN",
    T_NUMBER:         "NUMBER",
    T_STRING_LITERAL: "STRING_LITERAL",
    T_IDENTIFIER:     "IDENTIFIER",
    T_NEWLINE:        "NEWLINE",
}

KEYWORDS: dict[str, int] = {
    "write":   T_WRITE,
    "writeln": T_WRITELN,
    "readn":   T_READN,
    "run":     T_RUN,
    "exit":    T_EXIT,
}


@dataclass
class Token:
    type: int
    text: str
    line: int = 0
    column: int = 0

    def __repr__(self) -> str:
        name = TOKEN_NAMES.get(self.type, str(self.type))
        return f"Token({name}, {self.text!r}, line={self.line})"


class LexerError(Exception):
    pass


class Y2ExpressionLexer:
    """
    Tokenises a source string into a flat list of Tokens.
    Mirrors the interface of an ANTLR4-generated lexer.
    """

    _SYMBOL_MAP = {
        "=": T_ASSIGN,
        "+": T_PLUS,
        "-": T_MINUS,
        "*": T_STAR,
        "/": T_SLASH,
        "%": T_PERCENT,
        "^": T_CARET,
        "(": T_LPAREN,
        ")": T_RPAREN,
    }

    def __init__(self, source: str) -> None:
        self._source  = source
        self._pos     = 0
        self._line    = 1
        self._col     = 0
        self._tokens: List[Token] = []
        self._tokenised = False

    # ── Public API ────────────────────────────────────────────────────────────

    def getAllTokens(self) -> List[Token]:
        if not self._tokenised:
            self._tokenise()
        return self._tokens

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _peek(self) -> Optional[str]:
        return self._source[self._pos] if self._pos < len(self._source) else None

    def _advance(self) -> str:
        ch = self._source[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1
            self._col = 0
        else:
            self._col += 1
        return ch

    def _add(self, ttype: int, text: str, line: int, col: int) -> None:
        self._tokens.append(Token(ttype, text, line, col))

    def _tokenise(self) -> None:
        while self._pos < len(self._source):
            line, col = self._line, self._col
            ch = self._peek()

            # ── Skip whitespace (spaces / tabs) ───────────────────────────
            if ch in (" ", "\t"):
                self._advance()
                continue

            # ── Newlines ──────────────────────────────────────────────────
            if ch in ("\r", "\n"):
                text = ""
                while self._peek() in ("\r", "\n"):
                    text += self._advance()
                self._add(T_NEWLINE, text, line, col)
                continue

            # ── Line comments //  ─────────────────────────────────────────
            if ch == "/" and self._source[self._pos:self._pos+2] == "//":
                while self._peek() and self._peek() not in ("\r", "\n"):
                    self._advance()
                continue

            # ── Block comments /* … */ ────────────────────────────────────
            if ch == "/" and self._source[self._pos:self._pos+2] == "/*":
                self._advance(); self._advance()   # consume /*
                while self._pos < len(self._source):
                    if self._source[self._pos:self._pos+2] == "*/":
                        self._advance(); self._advance()
                        break
                    self._advance()
                continue

            # ── String literals "…" ───────────────────────────────────────
            if ch == '"':
                text = self._advance()             # opening "
                while self._peek() and self._peek() not in ('"', "\r", "\n"):
                    text += self._advance()
                if self._peek() == '"':
                    text += self._advance()        # closing "
                else:
                    raise LexerError(
                        f"Unterminated string at line {line}:{col}"
                    )
                self._add(T_STRING_LITERAL, text, line, col)
                continue

            # ── Numbers ───────────────────────────────────────────────────
            if ch and ch.isdigit():
                text = ""
                while self._peek() and self._peek().isdigit():
                    text += self._advance()
                if self._peek() == "." and (
                    self._pos + 1 < len(self._source)
                    and self._source[self._pos + 1].isdigit()
                ):
                    text += self._advance()        # decimal point
                    while self._peek() and self._peek().isdigit():
                        text += self._advance()
                self._add(T_NUMBER, text, line, col)
                continue

            # ── Identifiers / keywords ────────────────────────────────────
            if ch and (ch.isalpha() or ch == "_"):
                text = ""
                while self._peek() and (
                    self._peek().isalnum() or self._peek() == "_"
                ):
                    text += self._advance()
                ttype = KEYWORDS.get(text.lower(), T_IDENTIFIER)
                self._add(ttype, text, line, col)
                continue

            # ── Single-character symbols ──────────────────────────────────
            if ch in self._SYMBOL_MAP:
                self._advance()
                self._add(self._SYMBOL_MAP[ch], ch, line, col)
                continue

            raise LexerError(
                f"Unexpected character {ch!r} at line {line}:{col}"
            )

        self._tokens.append(Token(T_EOF, "<EOF>", self._line, self._col))
        self._tokenised = True
