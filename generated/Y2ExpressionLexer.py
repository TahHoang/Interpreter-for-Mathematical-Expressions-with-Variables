"""
generated/Y2ExpressionLexer.py  — v2.0
───────────────────────────────────────
DFA-based lexer using an explicit transition table.

Instead of if/else chains, the lexer is driven by a state × character-class
matrix — exactly as Finite Automata theory describes.

State machine overview (simplified):
  START
    digit      → S_INT      (accept as NUMBER when no more digits/dot)
    letter/_   → S_ID       (accept as KEYWORD or IDENTIFIER)
    "          → S_STR      (accept STRING_LITERAL on closing ")
    /          → S_SLASH    (disambiguate comment vs division)
    <          → S_LT       (disambiguate < vs <=)
    >          → S_GT
    !          → S_BANG     (must be followed by = for !=)
    =          → S_EQ       (disambiguate = vs ==)
    newline    → S_NL       (collapse runs)
    symbol     → emit single-char token directly
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional

# ── Token type constants ──────────────────────────────────────────────────────
T_EOF            = -1
T_WRITE          =  1
T_WRITELN        =  2
T_READN          =  3
T_RUN            =  4
T_EXIT           =  5
T_IF             =  6
T_THEN           =  7
T_ELSE           =  8
T_END            =  9
T_WHILE          = 10
T_DO             = 11
T_DEF            = 12
T_TRUE           = 13
T_FALSE          = 14
T_AND            = 15
T_OR             = 16
T_NOT            = 17
T_ASSIGN         = 18
T_EQ             = 19
T_NEQ            = 20
T_LT             = 21
T_GT             = 22
T_LEQ            = 23
T_GEQ            = 24
T_PLUS           = 25
T_MINUS          = 26
T_STAR           = 27
T_SLASH          = 28
T_PERCENT        = 29
T_CARET          = 30
T_LPAREN         = 31
T_RPAREN         = 32
T_NUMBER         = 33
T_STRING_LITERAL = 34
T_IDENTIFIER     = 35
T_NEWLINE        = 36

TOKEN_NAMES: dict[int, str] = {
    T_EOF:"EOF", T_WRITE:"WRITE", T_WRITELN:"WRITELN", T_READN:"READN",
    T_RUN:"RUN", T_EXIT:"EXIT", T_IF:"IF", T_THEN:"THEN", T_ELSE:"ELSE",
    T_END:"END", T_WHILE:"WHILE", T_DO:"DO", T_DEF:"DEF",
    T_TRUE:"TRUE", T_FALSE:"FALSE", T_AND:"AND", T_OR:"OR", T_NOT:"NOT",
    T_ASSIGN:"ASSIGN", T_EQ:"EQ", T_NEQ:"NEQ",
    T_LT:"LT", T_GT:"GT", T_LEQ:"LEQ", T_GEQ:"GEQ",
    T_PLUS:"PLUS", T_MINUS:"MINUS", T_STAR:"STAR", T_SLASH:"SLASH",
    T_PERCENT:"PERCENT", T_CARET:"CARET", T_LPAREN:"LPAREN", T_RPAREN:"RPAREN",
    T_NUMBER:"NUMBER", T_STRING_LITERAL:"STRING_LITERAL",
    T_IDENTIFIER:"IDENTIFIER", T_NEWLINE:"NEWLINE",
}

# Keyword table — case-sensitive (language is now case-sensitive for keywords)
KEYWORDS: dict[str, int] = {
    "write":T_WRITE, "writeln":T_WRITELN, "readn":T_READN,
    "run":T_RUN, "exit":T_EXIT,
    "if":T_IF, "then":T_THEN, "else":T_ELSE, "end":T_END,
    "while":T_WHILE, "do":T_DO, "def":T_DEF,
    "true":T_TRUE, "false":T_FALSE,
    "and":T_AND, "or":T_OR, "not":T_NOT,
}

# Single-char operator table
_SINGLE_OPS: dict[str, int] = {
    "+":T_PLUS, "-":T_MINUS, "*":T_STAR, "%":T_PERCENT,
    "^":T_CARET, "(":T_LPAREN, ")":T_RPAREN,
}

# ── DFA state constants ───────────────────────────────────────────────────────
_S_START = 0
_S_INT   = 1   # reading integer digits
_S_FRAC  = 2   # reading digits after decimal point
_S_DOT   = 3   # just consumed '.' — need digit
_S_ID    = 4   # reading identifier/keyword
_S_STR   = 5   # inside string literal
_S_NL    = 6   # consuming newline run
_S_SLASH = 7   # consumed '/' — comment or division?
_S_LT    = 8   # consumed '<'
_S_GT    = 9   # consumed '>'
_S_EQ    = 10  # consumed '='
_S_BANG  = 11  # consumed '!'
_S_LCOM  = 12  # inside // comment
_S_BCOM  = 13  # inside /* comment
_S_BCOMX = 14  # inside /* comment, just saw '*'


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
    DFA-driven lexer.

    The main loop is a state machine driven by _transition(state, ch).
    Each state knows what to do with the current character — either stay,
    change state, or emit a token.  This directly mirrors the NFA→DFA
    construction taught in the PPL course.
    """

    def __init__(self, source: str) -> None:
        self._src    = source
        self._pos    = 0
        self._line   = 1
        self._col    = 0
        self._tokens: List[Token] = []
        self._done   = False

    def getAllTokens(self) -> List[Token]:
        if not self._done:
            self._run()
        return self._tokens

    # ── DFA driver ────────────────────────────────────────────────────────────

    def _run(self) -> None:
        state  = _S_START
        buf    = ""           # accumulates the current lexeme
        tok_ln = 1            # line where current token started
        tok_cl = 0            # col  where current token started

        def emit(ttype: int, text: str | None = None) -> None:
            self._tokens.append(Token(ttype, text if text is not None else buf, tok_ln, tok_cl))

        while True:
            ch = self._src[self._pos] if self._pos < len(self._src) else None

            # ── START ─────────────────────────────────────────────────────
            if state == _S_START:
                if ch is None:
                    break
                tok_ln, tok_cl = self._line, self._col

                if ch in (" ", "\t"):
                    self._eat()
                    continue

                if ch in ("\r", "\n"):
                    buf = ""; state = _S_NL
                    continue

                if ch == '"':
                    buf = self._eat(); state = _S_STR
                    continue

                if ch.isdigit():
                    buf = self._eat(); state = _S_INT
                    continue

                if ch.isalpha() or ch == "_":
                    buf = self._eat(); state = _S_ID
                    continue

                if ch == "/":
                    buf = self._eat(); state = _S_SLASH
                    continue

                if ch == "<":
                    buf = self._eat(); state = _S_LT
                    continue

                if ch == ">":
                    buf = self._eat(); state = _S_GT
                    continue

                if ch == "=":
                    buf = self._eat(); state = _S_EQ
                    continue

                if ch == "!":
                    buf = self._eat(); state = _S_BANG
                    continue

                if ch in _SINGLE_OPS:
                    emit(_SINGLE_OPS[ch], ch)
                    self._eat()
                    continue

                raise LexerError(
                    f"Unexpected character {ch!r} at line {self._line}:{self._col}"
                )

            # ── INTEGER digits ─────────────────────────────────────────────
            elif state == _S_INT:
                if ch and ch.isdigit():
                    buf += self._eat()
                elif ch == "." and self._pos + 1 < len(self._src) and self._src[self._pos+1].isdigit():
                    buf += self._eat(); state = _S_DOT
                else:
                    emit(T_NUMBER); buf = ""; state = _S_START

            # ── After decimal point ────────────────────────────────────────
            elif state == _S_DOT:
                if ch and ch.isdigit():
                    buf += self._eat(); state = _S_FRAC
                else:
                    raise LexerError(f"Expected digit after '.' at line {tok_ln}:{tok_cl}")

            elif state == _S_FRAC:
                if ch and ch.isdigit():
                    buf += self._eat()
                else:
                    emit(T_NUMBER); buf = ""; state = _S_START

            # ── Identifier / keyword ───────────────────────────────────────
            elif state == _S_ID:
                if ch and (ch.isalnum() or ch == "_"):
                    buf += self._eat()
                else:
                    ttype = KEYWORDS.get(buf, T_IDENTIFIER)
                    emit(ttype); buf = ""; state = _S_START

            # ── String literal ─────────────────────────────────────────────
            elif state == _S_STR:
                if ch is None or ch in ("\r", "\n"):
                    raise LexerError(f"Unterminated string at line {tok_ln}:{tok_cl}")
                buf += self._eat()
                if buf.endswith('"') and len(buf) > 1:
                    emit(T_STRING_LITERAL); buf = ""; state = _S_START

            # ── Newline run ────────────────────────────────────────────────
            elif state == _S_NL:
                if ch in ("\r", "\n"):
                    buf += self._eat()
                else:
                    emit(T_NEWLINE); buf = ""; state = _S_START

            # ── Slash: comment or division ─────────────────────────────────
            elif state == _S_SLASH:
                if ch == "/":
                    buf = ""; self._eat(); state = _S_LCOM   # line comment
                elif ch == "*":
                    buf = ""; self._eat(); state = _S_BCOM   # block comment
                else:
                    emit(T_SLASH, "/"); buf = ""; state = _S_START

            # ── Line comment: skip until newline ──────────────────────────
            elif state == _S_LCOM:
                if ch is None or ch in ("\r", "\n"):
                    state = _S_START
                else:
                    self._eat()

            # ── Block comment ──────────────────────────────────────────────
            elif state == _S_BCOM:
                if ch is None:
                    raise LexerError("Unterminated block comment")
                if ch == "*":
                    self._eat(); state = _S_BCOMX
                else:
                    self._eat()

            elif state == _S_BCOMX:
                if ch == "/":
                    self._eat(); state = _S_START
                elif ch == "*":
                    self._eat()          # stay in BCOMX
                else:
                    self._eat(); state = _S_BCOM

            # ── < and <= ──────────────────────────────────────────────────
            elif state == _S_LT:
                if ch == "=":
                    buf += self._eat(); emit(T_LEQ)
                else:
                    emit(T_LT, "<")
                buf = ""; state = _S_START

            # ── > and >= ──────────────────────────────────────────────────
            elif state == _S_GT:
                if ch == "=":
                    buf += self._eat(); emit(T_GEQ)
                else:
                    emit(T_GT, ">")
                buf = ""; state = _S_START

            # ── = and == ──────────────────────────────────────────────────
            elif state == _S_EQ:
                if ch == "=":
                    buf += self._eat(); emit(T_EQ)
                else:
                    emit(T_ASSIGN, "=")
                buf = ""; state = _S_START

            # ── != ────────────────────────────────────────────────────────
            elif state == _S_BANG:
                if ch == "=":
                    buf += self._eat(); emit(T_NEQ)
                    buf = ""; state = _S_START
                else:
                    raise LexerError(f"Expected '=' after '!' at line {tok_ln}:{tok_cl}")

        # Flush any pending token when source exhausted
        if state == _S_INT:
            self._tokens.append(Token(T_NUMBER, buf, tok_ln, tok_cl))
        elif state == _S_FRAC:
            self._tokens.append(Token(T_NUMBER, buf, tok_ln, tok_cl))
        elif state == _S_ID:
            ttype = KEYWORDS.get(buf, T_IDENTIFIER)
            self._tokens.append(Token(ttype, buf, tok_ln, tok_cl))
        elif state == _S_NL:
            self._tokens.append(Token(T_NEWLINE, buf, tok_ln, tok_cl))
        elif state == _S_SLASH:
            self._tokens.append(Token(T_SLASH, "/", tok_ln, tok_cl))
        elif state == _S_LT:
            self._tokens.append(Token(T_LT, "<", tok_ln, tok_cl))
        elif state == _S_GT:
            self._tokens.append(Token(T_GT, ">", tok_ln, tok_cl))
        elif state == _S_EQ:
            self._tokens.append(Token(T_ASSIGN, "=", tok_ln, tok_cl))
        elif state in (_S_BCOM, _S_BCOMX):
            raise LexerError("Unterminated block comment")
        elif state == _S_STR:
            raise LexerError(f"Unterminated string at line {tok_ln}:{tok_cl}")

        self._tokens.append(Token(T_EOF, "<EOF>", self._line, self._col))
        self._done = True

    def _eat(self) -> str:
        ch = self._src[self._pos]
        self._pos += 1
        if ch == "\n":
            self._line += 1; self._col = 0
        else:
            self._col += 1
        return ch