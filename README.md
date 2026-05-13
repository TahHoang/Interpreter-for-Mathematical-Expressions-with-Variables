# Interpreter for Mathematical Expressions with Variables

A math expression interpreter built with **ANTLR4** and **Python**, inspired by YinYang's [Y2 Math Interpreter](https://yinyangit.wordpress.com/2011/03/27/algorthrim-%e2%80%93-tinh-gia-tr%e1%bb%8b-c%e1%bb%a7a-bi%e1%bb%83u-th%e1%bc%a9c-toan-h%e1%bb%8dc-co-s%e1%bb%ad-d%e1%bb%a5ng-bi%e1%ba7n/) (originally written in C#).

The project is structured as a full compiler pipeline — **Lexer → Parser → AST → Visitor Evaluator** — and ships with an animated **Compiler Visualizer** web app that shows every step of the process in real time.

---

## Project Structure

```
Interpreter-for-Mathematical-Expressions-with-Variables/
├── visualizer_app.py                # Flask server — Compiler Visualizer (port 5000)
├── main.py                          # CLI entry point: REPL, script runner, one-liner
├── Y2MathInterpreter.py             # Core evaluator — extends Y2ExpressionVisitor
│
├── grammar/
│   └── Y2Expression.g4              # ANTLR4 grammar (source of truth)
│
├── generated/                       # Mirrors what `antlr4 -Dlanguage=Python3` produces
│   ├── __init__.py
│   ├── Y2ExpressionLexer.py         # Tokenizer
│   ├── Y2ExpressionParser.py        # Recursive-descent parser → AST
│   ├── Y2ExpressionAST.py           # AST node dataclasses
│   └── Y2ExpressionVisitor.py       # Abstract Visitor base class
│
├── visualizer/                      # Visualizer backend
│   ├── __init__.py
│   ├── ast_serializer.py            # Visitor: AST → JSON dict
│   └── tracing_interpreter.py       # Subclass: records each eval step
│
├── templates/
│   └── visualizer.html              # Compiler Visualizer UI (3-panel, animated)
│
├── static/
│   ├── style.css                    # Dark-theme styles
│   └── visualizer.js                # Animation logic
│
├── examples/
│   └── demo.y2                      # Feature demonstration script
└── tests/
    └── test_interpreter.py          # 47 unit tests (Lexer, Parser, Interpreter)
```

---

## Requirements

- Python 3.10 or later
- `flask` and `flask-cors`

```bash
pip install flask flask-cors
```

To regenerate `generated/` from the grammar using the real ANTLR4 tool:

```bash
pip install antlr4-tools antlr4-python3-runtime
antlr4 -Dlanguage=Python3 -visitor grammar/Y2Expression.g4 -o generated/
```

---

## Installation

```bash
git clone https://github.com/your-username/Interpreter-for-Mathematical-Expressions-with-Variables.git
cd Interpreter-for-Mathematical-Expressions-with-Variables
pip install flask flask-cors
```

---

## Usage

### Compiler Visualizer (main UI)

```bash
python visualizer_app.py
```

Open **http://localhost:5000** — type any Y2 expression and watch the full compiler pipeline animate in real time across 3 panels:

| Panel | What it shows |
|---|---|
| **1 — Lexer** | Tokens fly in one by one, each briefly highlighted on arrival |
| **2 — Parser** | AST nodes build top-down from root, each highlighted as it appears |
| **3 — Evaluator** | Eval steps slide in sequentially with active-step glow, symbol table pops in at the end |

A **pipeline progress bar** at the top tracks which phase is running. A **Speed slider** controls animation speed (slow for demo, fast for testing).

### CLI — interactive REPL

```bash
python main.py
```

```
Y2 Math Interpreter  (type 'exit' to quit)
Operators: + - * / % ^    Functions: sqrt sin cos tan abs log exp

>> x = 3 * 4
>> writeln x
12.0
>> exit
Goodbye!
```

### CLI — run a script file

```bash
python main.py examples/demo.y2
```

### CLI — one-liner (`;` as line separator)

```bash
python main.py -e "a = 2 ^ 10; writeln a"
# 1024.0
```

---

## Language Reference

### Operators

| Operator | Description         | Example       |
|----------|---------------------|---------------|
| `+`      | Addition            | `x = 3 + 4`  |
| `-`      | Subtraction         | `x = 10 - 3` |
| `*`      | Multiplication      | `x = 6 * 7`  |
| `/`      | Division            | `x = 10 / 4` |
| `%`      | Modulo              | `x = 10 % 3` |
| `^`      | Power (right-assoc) | `x = 2 ^ 10` |
| `-`      | Unary minus         | `x = -5`     |

Operator precedence (highest to lowest): `^` → unary `-` → `* / %` → `+ -`

### Built-in Functions

| Function    | Description               |
|-------------|---------------------------|
| `sqrt(x)`   | Square root               |
| `sin(x)`    | Sine (radians)            |
| `cos(x)`    | Cosine (radians)          |
| `tan(x)`    | Tangent (radians)         |
| `abs(x)`    | Absolute value            |
| `log(x)`    | Natural logarithm         |
| `exp(x)`    | e to the power of x       |
| `ceil(x)`   | Ceiling                   |
| `floor(x)`  | Floor                     |

### Variables

Variables are dynamically typed as `float`. Assignment uses `=`.

```
radius = 5
area = 3.14159 * radius ^ 2
writeln area
```

### Commands

| Command         | Description                              |
|-----------------|------------------------------------------|
| `write expr`    | Print a value or string (no newline)     |
| `writeln expr`  | Print a value or string (with newline)   |
| `write "text"`  | Print a string literal                   |
| `readn name`    | Read a number from stdin into a variable |
| `run "file.y2"` | Execute a script file (no nesting)       |
| `exit`          | Exit the interpreter                     |

### Comments

```
// line comment

/* block
   comment */
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

```
Source text
    │
    ▼  Y2ExpressionLexer        → Token stream
    │
    ▼  Y2ExpressionParser       → Abstract Syntax Tree
    │
    ├─ ASTSerializer            → JSON  (Compiler Visualizer)
    │
    ├─ Y2MathInterpreter        → Result / side effects  (CLI)
    │
    └─ TracingInterpreter       → Step log + result      (Compiler Visualizer)
```

### Visitor Pattern

`Y2MathInterpreter` extends `Y2ExpressionVisitor` and implements a `visit*` method for every grammar rule. `TracingInterpreter` and `ASTSerializer` are two additional Visitors that reuse the same AST — none of them touch the parser.

```python
class TracingInterpreter(Y2MathInterpreter):
    def visitBinaryOp(self, node):
        result = super().visitBinaryOp(node)   # real logic
        self.steps.append({...})               # log the step
        return result
```

### Switching to the real ANTLR4 runtime

The `generated/` directory contains hand-written files that mirror ANTLR4's output exactly. Once `antlr4-python3-runtime` is installed, regenerate them with:

```bash
antlr4 -Dlanguage=Python3 -visitor grammar/Y2Expression.g4 -o generated/
```

Nothing else needs to change.

---

## Running the Tests

```bash
python tests/test_interpreter.py
```

```
Ran 47 tests in 0.005s

OK
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'generated'`**
Run from the project root:
```bash
cd Interpreter-for-Mathematical-Expressions-with-Variables
python visualizer_app.py
```

**`ModuleNotFoundError: No module named 'visualizer'`**
```bash
touch visualizer/__init__.py
```

**`Address already in use`**
```python
# In visualizer_app.py, change the port:
app.run(debug=True, port=5001)
```

---

## Credits

- Original concept: [YinYang's Y2 Math Interpreter (2011)](https://yinyangit.wordpress.com/2011/03/27/algorthrim-%e2%80%93-tinh-gia-tr%e1%bb%8b-c%e1%bb%a7a-bi%e1%bb%83u-th%e1%bc%a9c-toan-h%e1%bb%8dc-co-s%e1%bb%ad-d%e1%bb%a5ng-bi%e1%ba7n/)
- Grammar toolchain: [ANTLR4](https://www.antlr.org/)
- Course: Principles of Programming Languages — IU HCMC