"""
AST node classes for chatlang. Plain data holders, no behavior.
"""


class Node:
    pass


# ---- Statements ----

class Program(Node):
    def __init__(self, statements):
        self.statements = statements


class VarDecl(Node):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr


class Assign(Node):
    def __init__(self, target, expr):
        self.target = target  # Identifier or Index
        self.expr = expr


class If(Node):
    def __init__(self, cond, then_block, else_block):
        self.cond = cond
        self.then_block = then_block
        self.else_block = else_block  # Block, If (elseif), or None


class While(Node):
    def __init__(self, cond, block):
        self.cond = cond
        self.block = block


class FuncDecl(Node):
    def __init__(self, name, params, block):
        self.name = name
        self.params = params
        self.block = block


class OnHandler(Node):
    def __init__(self, event_name, params, block):
        self.event_name = event_name
        self.params = params
        self.block = block


class Return(Node):
    def __init__(self, expr):
        self.expr = expr


class PrintStmt(Node):
    def __init__(self, expr):
        self.expr = expr


class ExprStmt(Node):
    def __init__(self, expr):
        self.expr = expr


class Block(Node):
    def __init__(self, statements):
        self.statements = statements


# ---- Expressions ----

class Number(Node):
    def __init__(self, value):
        self.value = value


class String(Node):
    def __init__(self, value):
        self.value = value


class Bool(Node):
    def __init__(self, value):
        self.value = value


class Null(Node):
    pass


class Identifier(Node):
    def __init__(self, name):
        self.name = name


class ListLit(Node):
    def __init__(self, items):
        self.items = items


class DictLit(Node):
    def __init__(self, pairs):
        self.pairs = pairs  # list of (key_expr, value_expr)


class Index(Node):
    def __init__(self, collection, index):
        self.collection = collection
        self.index = index


class BinOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class LogicalOp(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand


class Call(Node):
    def __init__(self, callee, args):
        self.callee = callee
        self.args = args
