/**
 * Y2Expression.g4
 * ANTLR4 Grammar for Y2 Math Interpreter
 *
 * Inspired by YinYang's Y2 Math Interpreter (2011):
 *   https://yinyangit.wordpress.com/2011/03/27/...
 *
 * Supports:
 *   - Arithmetic: +  -  *  /  %  ^
 *   - Functions:  sqrt  sin  cos  tan  abs  log  exp
 *   - Variables:  assignment and lookup
 *   - Commands:   write  writeln  readn  run  exit
 *   - Comparison: ==  !=  <  >  <=  >=   (for future use)
 *
 * Generate Python runtime code with:
 *   antlr4 -Dlanguage=Python3 -visitor Y2Expression.g4
 */

grammar Y2Expression;

// ─────────────────────────────────────────────
// Parser Rules
// ─────────────────────────────────────────────

/** Top-level program: one or more statements */
program
    : statement+ EOF
    ;

/** A single line of input */
statement
    : assignment NEWLINE?        # AssignStmt
    | command    NEWLINE?        # CmdStmt
    | NEWLINE                    # EmptyLine
    ;

/** Variable assignment:  name = expr */
assignment
    : IDENTIFIER ASSIGN expr
    ;

/** Built-in commands */
command
    : WRITE   writeArg           # WriteCmd
    | WRITELN writeArg           # WritelnCmd
    | READN   IDENTIFIER         # ReadnCmd
    | RUN     STRING_LITERAL     # RunCmd
    | EXIT                       # ExitCmd
    ;

writeArg
    : STRING_LITERAL             # WriteString
    | expr                       # WriteExpr
    ;

/** Expression hierarchy (lowest to highest precedence) */
expr
    : expr (PLUS | MINUS) term   # AddSub
    | term                       # PassTerm
    ;

term
    : term (STAR | SLASH | PERCENT) power   # MulDiv
    | power                                 # PassPower
    ;

power
    : unary CARET power          # PowerOp   // right-associative
    | unary                      # PassUnary
    ;

unary
    : MINUS unary                # Negate
    | primary                    # PassPrimary
    ;

primary
    : NUMBER                     # NumberLit
    | IDENTIFIER LPAREN expr RPAREN  # FuncCall
    | IDENTIFIER                 # VarRef
    | LPAREN expr RPAREN         # Grouped
    ;

// ─────────────────────────────────────────────
// Lexer Rules
// ─────────────────────────────────────────────

// Keywords (must come before IDENTIFIER)
WRITE   : [Ww][Rr][Ii][Tt][Ee] ;
WRITELN : [Ww][Rr][Ii][Tt][Ee][Ll][Nn] ;
READN   : [Rr][Ee][Aa][Dd][Nn] ;
RUN     : [Rr][Uu][Nn] ;
EXIT    : [Ee][Xx][Ii][Tt] ;

// Operators
ASSIGN  : '=' ;
PLUS    : '+' ;
MINUS   : '-' ;
STAR    : '*' ;
SLASH   : '/' ;
PERCENT : '%' ;
CARET   : '^' ;
LPAREN  : '(' ;
RPAREN  : ')' ;

// Literals
NUMBER
    : DIGIT+ ('.' DIGIT+)?
    ;

STRING_LITERAL
    : '"' (~["\r\n])* '"'
    ;

IDENTIFIER
    : [a-zA-Z_] [a-zA-Z0-9_]*
    ;

NEWLINE
    : [\r\n]+
    ;

// Skip whitespace (not newlines, those are significant)
WS
    : [ \t]+ -> skip
    ;

// Skip comments  //  ...  or  /* ... */
LINE_COMMENT
    : '//' ~[\r\n]* -> skip
    ;

BLOCK_COMMENT
    : '/*' .*? '*/' -> skip
    ;

// Fragments
fragment DIGIT : [0-9] ;
