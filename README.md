# Y2 Math Interpreter

A math expression interpreter built with **ANTLR4** and **Python**, inspired by YinYang's [Y2 Math Interpreter](https://yinyangit.wordpress.com/2011/03/27/algorthrim-%e2%80%93-tinh-gia-tr%e1%bb%8b-c%e1%bb%a7a-bi%e1%bb%83u-th%e1%bc%a9c-toan-h%e1%bb%8dc-co-s%e1%bb%ad-d%e1%bb%a5ng-bi%e1%ba7n/) (originally written in C#).

The interpreter supports arithmetic expressions, variables, built-in math functions, and simple I/O commands. It is structured as a proper compiler pipeline — Lexer → Parser → AST → Visitor Evaluator — mirroring the architecture that ANTLR4 generates.

---

## Project Structure

```
PPL_Project/
├── main.py                        # Entry point: REPL, script runner, one-liner
├── Y2MathInterpreter.py           # Evaluator — extends Y2ExpressionVisitor
├── grammar/
│   └── Y2Expression.g4            # ANTLR4 grammar (source of truth)
├── generated/                     # Mirrors what `antlr4 -Dlanguage=Python3` produces
│   ├── __init__.py
│   ├── Y2ExpressionLexer.py       # Tokenizer
│   ├── Y2ExpressionParser.py      # Recursive-descent parser → AST
│   ├── Y2ExpressionAST.py         # AST node dataclasses
│   └── Y2ExpressionVisitor.py     # Abstract Visitor base class
├── examples/
│   └── demo.y2                    # Feature demonstration script
└── tests/
    └── test_interpreter.py        # 47 unit tests (Lexer, Parser, Interpreter)
```

---

## Requirements

- Python 3.10 or later
- No third-party packages required to run

To use the real ANTLR4 tool to regenerate the `generated/` files from the grammar:

```bash
pip install antlr4-tools antlr4-python3-runtime
antlr4 -Dlanguage=Python3 -visitor grammar/Y2Expression.g4 -o generated/
```

---

## Installation

```bash
git clone https://github.com/your-username/PPL_Project.git
cd PPL_Project
```

No further setup is needed — the interpreter runs with the Python standard library only.

---

## Usage

### Interactive REPL

```bash
python main.py
```

```
Y2 Math Interpreter  (type 'exit' to quit)
Operators: + - * / % ^    Functions: sqrt sin cos tan abs log exp

>> x = 3 * 4
>> writeln x
12.0
>> writeln sqrt(x)
3.4641016151377544
>> exit
Goodbye!
```

### Run a script file

```bash
python main.py examples/demo.y2
```

### One-liner (use `;` as a line separator)

```bash
python main.py -e "a = 2 ^ 10; writeln a"
# 1024.0
```

---

## Language Reference

### Operators

| Operator | Description          | Example        |
|----------|----------------------|----------------|
| `+`      | Addition             | `x = 3 + 4`   |
| `-`      | Subtraction          | `x = 10 - 3`  |
| `*`      | Multiplication       | `x = 6 * 7`   |
| `/`      | Division             | `x = 10 / 4`  |
| `%`      | Modulo               | `x = 10 % 3`  |
| `^`      | Power (right-assoc)  | `x = 2 ^ 10`  |
| `-`      | Unary minus          | `x = -5`      |

Operator precedence (highest to lowest): `^` → unary `-` → `* / %` → `+ -`

### Built-in Functions

| Function    | Description                   |
|-------------|-------------------------------|
| `sqrt(x)`   | Square root                   |
| `sin(x)`    | Sine (radians)                |
| `cos(x)`    | Cosine (radians)              |
| `tan(x)`    | Tangent (radians)             |
| `abs(x)`    | Absolute value                |
| `log(x)`    | Natural logarithm             |
| `exp(x)`    | e raised to the power of x   |
| `ceil(x)`   | Ceiling                       |
| `floor(x)`  | Floor                         |

### Variables

Variables are dynamically typed as `float`. Assignment uses `=`.

```
radius = 5
area = 3.14159 * radius ^ 2
writeln area
```

### Commands

| Command            | Description                                    |
|--------------------|------------------------------------------------|
| `write expr`       | Print a value or string (no newline)           |
| `writeln expr`     | Print a value or string (with newline)         |
| `write "text"`     | Print a string literal                         |
| `readn varname`    | Read a number from stdin into a variable       |
| `run "file.y2"`    | Execute another script file (no nesting)       |
| `exit`             | Exit the interpreter                           |

### Comments

```
// This is a line comment

/* This is a
   block comment */
```

---

## Example Script

```
// Quadratic formula: x^2 - 5x + 6 = 0
a = 1
b = -5
c = 6

disc = b^2 - 4*a*c
x1 = (-b + sqrt(disc)) / (2*a)
x2 = (-b - sqrt(disc)) / (2*a)

write "x1 = "
writeln x1
write "x2 = "
writeln x2
```

Output:
```
x1 = 3.0
x2 = 2.0
```

---

## Architecture

The interpreter follows the classic compiler pipeline described in the ANTLR4 book and the course lectures:

```
Source text
    │
    ▼  Y2ExpressionLexer
Token stream
    │
    ▼  Y2ExpressionParser
Abstract Syntax Tree (AST)
    │
    ▼  Y2MathInterpreter (Visitor)
Result / Side effects
```

### Visitor Pattern

`Y2MathInterpreter` extends the abstract `Y2ExpressionVisitor` class and implements a `visit*` method for every grammar rule. This cleanly separates parsing from evaluation and makes it easy to add a second pass (e.g. a type-checker or a pretty-printer) without touching the parser.

```python
class Y2MathInterpreter(Y2ExpressionVisitor):

    def visitBinaryOp(self, node: BinaryOpNode) -> float:
        left  = node.left.accept(self)
        right = node.right.accept(self)
        if node.op == "+": return left + right
        if node.op == "-": return left - right
        ...
```

### Switching to the real ANTLR4 runtime

The `generated/` directory contains hand-written files that mirror ANTLR4's output exactly (same class names, method signatures, and token constants). Once `antlr4-python3-runtime` is installed, regenerate the files with:

```bash
antlr4 -Dlanguage=Python3 -visitor grammar/Y2Expression.g4 -o generated/
```

`Y2MathInterpreter.py` does not need any changes.

---

## Running the Tests

```bash
python tests/test_interpreter.py
```

```
Ran 47 tests in 0.005s

OK
```

The test suite covers:

- **Lexer** — numbers, strings, identifiers, operators, keywords, comments, error cases
- **Parser** — assignments, operator precedence, right-associative power, error recovery
- **Arithmetic** — all operators, precedence, parentheses, unary minus, division by zero
- **Variables** — assignment, re-assignment, undefined variable errors
- **Functions** — all 9 built-ins, nested calls, domain errors
- **Commands** — `write`, `writeln`, `readn`, invalid input
- **Integration** — quadratic formula, iterative Fibonacci

---

## Credits

- Original concept: [YinYang's Y2 Math Interpreter (2011)](https://yinyangit.wordpress.com/2011/03/27/algorthrim-%e2%80%93-tinh-gia-tr%e1%bb%8b-c%e1%bb%a7a-bi%e1%bb%83u-th%e1%bc%a9c-toan-h%e1%bb%8dc-co-s%e1%bb%ad-d%e1%bb%a5ng-bi%e1%ba7n/)
- Grammar toolchain: [ANTLR4](https://www.antlr.org/)
- Course: Principles of Programming Languages — IU HCMC