/**
 * Y2Expression.g4  — v2.0
 * ANTLR4 Grammar for extended Y2 Math Interpreter
 *
 * New in v2.0:
 *   - Boolean literals: true false
 *   - Comparison operators: == != < > <= >=
 *   - Logical operators: and or not
 *   - Control flow: if…then…else…end   while…do…end
 *   - User-defined functions: def f(x) = expr
 *   - DFA-based lexer (transition table, not if/else)
 *   - Error recovery: parser collects errors instead of crashing
 *   - Semantic Analysis pass before evaluation
 *
 * Generate with:
 *   antlr4 -Dlanguage=Python3 -visitor Y2Expression.g4
 */

grammar Y2Expression;

// ── Parser Rules ─────────────────────────────────────────────────────────────

program     : statement+ EOF ;

statement
    : funcDef   NEWLINE?   # FuncDefStmt
    | ifStmt    NEWLINE?   # IfStmt
    | whileStmt NEWLINE?   # WhileStmt
    | assignment NEWLINE?  # AssignStmt
    | command   NEWLINE?   # CmdStmt
    | NEWLINE              # EmptyLine
    ;

funcDef     : DEF IDENTIFIER LPAREN IDENTIFIER RPAREN ASSIGN expr ;

ifStmt      : IF expr THEN block (ELSE block)? END ;

whileStmt   : WHILE expr DO block END ;

block       : statement* ;

assignment  : IDENTIFIER ASSIGN expr ;

command
    : (WRITE | WRITELN) writeArg   # WriteCmd
    | READN IDENTIFIER             # ReadnCmd
    | RUN STRING_LITERAL           # RunCmd
    | EXIT                         # ExitCmd
    ;

writeArg    : STRING_LITERAL | expr ;

// ── Expression hierarchy ─────────────────────────────────────────────────────

expr        : orExpr ;

orExpr      : andExpr  (OR  andExpr)* ;
andExpr     : notExpr  (AND notExpr)* ;
notExpr     : NOT notExpr | cmpExpr ;

cmpExpr     : addExpr ((EQ|NEQ|LT|GT|LEQ|GEQ) addExpr)? ;

addExpr     : mulExpr  ((PLUS|MINUS) mulExpr)* ;
mulExpr     : powExpr  ((STAR|SLASH|PERCENT) powExpr)* ;
powExpr     : unary (CARET powExpr)? ;       // right-associative

unary       : MINUS unary | primary ;

primary
    : NUMBER
    | TRUE | FALSE
    | IDENTIFIER LPAREN expr RPAREN     // function call (built-in or user)
    | IDENTIFIER                        // variable reference
    | LPAREN expr RPAREN
    ;

// ── Lexer Rules ───────────────────────────────────────────────────────────────

// Keywords
DEF     : 'def' ;
IF      : 'if' ;
THEN    : 'then' ;
ELSE    : 'else' ;
END     : 'end' ;
WHILE   : 'while' ;
DO      : 'do' ;
TRUE    : 'true' ;
FALSE   : 'false' ;
AND     : 'and' ;
OR      : 'or' ;
NOT     : 'not' ;
WRITE   : 'write' ;
WRITELN : 'writeln' ;
READN   : 'readn' ;
RUN     : 'run' ;
EXIT    : 'exit' ;

// Operators
ASSIGN  : '=' ;
EQ      : '==' ;
NEQ     : '!=' ;
LT      : '<' ;
GT      : '>' ;
LEQ     : '<=' ;
GEQ     : '>=' ;
PLUS    : '+' ;
MINUS   : '-' ;
STAR    : '*' ;
SLASH   : '/' ;
PERCENT : '%' ;
CARET   : '^' ;
LPAREN  : '(' ;
RPAREN  : ')' ;

// Literals
NUMBER          : DIGIT+ ('.' DIGIT+)? ;
STRING_LITERAL  : '"' (~["\r\n])* '"' ;
IDENTIFIER      : [a-zA-Z_][a-zA-Z0-9_]* ;
NEWLINE         : [\r\n]+ ;

// Skip
WS          : [ \t]+          -> skip ;
LINE_COMMENT: '//' ~[\r\n]*   -> skip ;
BLOCK_COMMENT: '/*' .*? '*/'  -> skip ;

fragment DIGIT : [0-9] ;
