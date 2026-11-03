"""Build SymPy expressions from a small AST whitelist; never eval user input."""

import ast
import math
import re

import sympy as sp

X = sp.Symbol("x", real=True)
Y = sp.Symbol("y", real=True)
T = sp.Symbol("t", real=True)
FUNCTIONS = {
    name: getattr(sp, name)
    for name in ("sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh", "exp", "log")
}
FUNCTIONS.update({"sqrt": sp.sqrt, "abs": sp.Abs, "Abs": sp.Abs, "ln": sp.log})
CONSTANTS = {"pi": sp.pi, "e": sp.E, "E": sp.E}
_IMPLICIT_CALL = re.compile(
    r"\b(sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|exp|log|ln|sqrt|abs|Abs)(?!\s*\()\s*(pi|e|E|x|y|t|\d+(?:\.\d+)?)"
)


def _from_latex(source: str) -> str:
    """Accept a formula pasted from a model, including common LaTeX."""
    source = source.replace(r"\left", "").replace(r"\right", "")
    source = source.replace(r"\cdot", "*").replace(r"\times", "*").replace(r"\pi", "pi")
    for name in ("arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "sin", "cos", "tan", "ln", "log", "exp", "sqrt"):
        source = source.replace("\\" + name, name)
    source = re.sub(r"\^\{([^{}]+)\}", r"^(\1)", source)
    previous = None
    while previous != source:
        previous = source
        source = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))", source)
    source = re.sub(r"\)\s*(?!(?:if|else)\b)(?=[A-Za-z(\\])", ")*", source)
    source = re.sub(
        r"(\d)\s*(?=(?:sin|cos|tan|asin|acos|atan|sinh|cosh|tanh|exp|log|ln|sqrt|abs|Abs|pi)\b)",
        r"\1*",
        source,
    )
    return source.replace("{", "").replace("}", "").replace("\\", "")


def _close_implicit_calls(source: str) -> str:
    """Let sinπ and sin x mean sin(π) and sin(x). Parentheses already present are left alone."""
    previous = None
    while previous != source:
        previous = source
        source = _IMPLICIT_CALL.sub(lambda match: f"{match.group(1)}({match.group(2)})", source)
    return source


def _parse(formula: str, variables: dict[str, sp.Expr], prefix: str, empty_hint: str, syntax_hint: str, reject_hint: str) -> sp.Expr:
    if not isinstance(formula, str) or not formula.strip() or len(formula) > 500:
        raise ValueError(empty_hint)
    body = re.sub(prefix, "", formula.strip())
    source = _close_implicit_calls(_from_latex(body).replace("^", "**").replace("π", "pi"))
    names = {**CONSTANTS, **variables}
    try:
        tree = ast.parse(source, mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise ValueError(syntax_hint) from exc
    if sum(1 for _ in ast.walk(tree)) > 100:
        raise ValueError("Formula is too complex; split it into simpler expressions.")

    def build(node: ast.AST, depth: int = 0) -> sp.Expr:
        if depth > 16:
            raise ValueError("Formula nesting is too deep (maximum 16).")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if not math.isfinite(node.value) or abs(node.value) > 1_000_000:
                raise ValueError("Numeric literals must be finite and at most 1,000,000 in magnitude.")
            return sp.Number(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            return names[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = build(node.operand, depth + 1)
            return value if isinstance(node.op, ast.UAdd) else sp.Mul(-1, value, evaluate=False)
        if isinstance(node, ast.BinOp):
            a, b = build(node.left, depth + 1), build(node.right, depth + 1)
            if isinstance(node.op, ast.Add):
                return sp.Add(a, b, evaluate=False)
            if isinstance(node.op, ast.Sub):
                return sp.Add(a, sp.Mul(-1, b, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Mult):
                return sp.Mul(a, b, evaluate=False)
            if isinstance(node.op, ast.Div):
                return sp.Mul(a, sp.Pow(b, -1, evaluate=False), evaluate=False)
            if isinstance(node.op, ast.Pow):
                exponent_node = node.right
                while isinstance(exponent_node, ast.UnaryOp):
                    exponent_node = exponent_node.operand
                if isinstance(exponent_node, ast.Constant) and abs(exponent_node.value) > 100:
                    raise ValueError("Numeric exponents must be between -100 and 100.")
                return sp.Pow(a, b, evaluate=False)
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS
            and len(node.args) == 1
            and not node.keywords
        ):
            return FUNCTIONS[node.func.id](build(node.args[0], depth + 1), evaluate=False)
        if isinstance(node, ast.IfExp):
            return sp.Piecewise(
                (build(node.body, depth + 1), condition(node.test, depth + 1)),
                (build(node.orelse, depth + 1), True),
            )
        raise ValueError(reject_hint)

    def condition(node: ast.AST, depth: int) -> sp.Basic:
        if depth > 16:
            raise ValueError("Formula nesting is too deep (maximum 16).")
        if isinstance(node, ast.Compare) and node.ops and node.comparators:
            pieces = []
            left = build(node.left, depth + 1)
            for op, comparator in zip(node.ops, node.comparators):
                right = build(comparator, depth + 1)
                relation = {
                    ast.Lt: sp.Lt,
                    ast.LtE: sp.Le,
                    ast.Gt: sp.Gt,
                    ast.GtE: sp.Ge,
                    ast.Eq: sp.Eq,
                    ast.NotEq: sp.Ne,
                }.get(type(op))
                if relation is None:
                    break
                pieces.append(relation(left, right))
                left = right
            if len(pieces) == len(node.ops):
                return pieces[0] if len(pieces) == 1 else sp.And(*pieces)
        if isinstance(node, ast.BoolOp) and isinstance(node.op, (ast.And, ast.Or)):
            parts = [condition(value, depth + 1) for value in node.values]
            return sp.And(*parts) if isinstance(node.op, ast.And) else sp.Or(*parts)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return sp.Not(condition(node.operand, depth + 1))
        raise ValueError("A piecewise condition uses <, <=, >, >=, ==, !=, and, or, or not.")

    return build(tree.body)


def parse_formula(formula: str) -> sp.Expr:
    return _parse(
        formula,
        {"x": X},
        r"^\s*y\s*=\s*",
        "Enter a non-empty formula of at most 500 characters, e.g. y = sin(x).",
        "Use x^2, sin(x), y = 2*x + 1, or x^2 if x < 0 else x. Write multiplication explicitly as *.",
        "Supported syntax: numbers, x, pi, e, + - * / ^, piecewise if/else, and single-argument math functions. "
        "Use plot_3d_surface for z=f(x,y). Use plot_parametric for expressions in t.",
    )


def parse_surface(formula: str) -> sp.Expr:
    return _parse(
        formula,
        {"x": X, "y": Y},
        r"^\s*z\s*=\s*",
        "Enter a non-empty surface of at most 500 characters, e.g. z = sin(x)*cos(y).",
        "Use z = sin(x)*cos(y) or x^2 + y^2. Write multiplication explicitly as *.",
        "Surfaces use numbers, x, y, pi, e, + - * / ^, and single-argument math functions.",
    )


def parse_component(formula: str) -> sp.Expr:
    return _parse(
        formula,
        {"t": T},
        r"^\s*[xyz]\s*=\s*",
        "Enter a component in t, for example cos(t).",
        "Use cos(t), sin(t), or t. Write multiplication explicitly as *.",
        "Parametric components use numbers, t, pi, e, + - * / ^, piecewise if/else, and single-argument math functions.",
    )


def looks_like_surface(formula: str) -> bool:
    """True when a failed 2D formula should be sent to plot_3d_surface instead."""
    if not isinstance(formula, str):
        return False
    body = re.sub(r"^\s*y\s*=\s*", "", formula.strip(), flags=re.IGNORECASE)
    return bool(re.match(r"z\s*=", body, flags=re.IGNORECASE) or re.search(r"(?<![A-Za-z])y(?![A-Za-z])", body))


def validate_range(values: list[float] | None, default: tuple[float, float] | None = None):
    if values is None:
        return list(default) if default else None
    if (
        len(values) != 2
        or any(not math.isfinite(v) for v in values)
        or values[0] >= values[1]
        or any(abs(v) > 1e6 for v in values)
    ):
        raise ValueError("A range must contain two finite increasing numbers within [-1e6, 1e6], e.g. [-10, 10].")
    return values
