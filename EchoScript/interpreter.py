# interpreter.py

"""
Tree-walking interpreter for chatlang.

Usage:
    interp = Interpreter()
    interp.register_native("broadcast", some_python_fn)
    interp.load(source_text)          # runs top-level var/func/on declarations
    interp.call_handler("connect", [client_id, username])
"""

import plic.EchoScript.chatlang_ast as ast
from plic.EchoScript.lexer import Lexer
from plic.EchoScript.parser import parse


class ChatlangError(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def define(self, name, value):
        self.vars[name] = value

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise ChatlangError(f"undefined variable '{name}'")

    def set(self, name, value):
        env = self
        while env is not None:
            if name in env.vars:
                env.vars[name] = value
                return
            env = env.parent
        # implicit global define on first assignment
        self.define_at_root(name, value)

    def define_at_root(self, name, value):
        env = self
        while env.parent is not None:
            env = env.parent
        env.vars[name] = value


class ChatlangFunction:
    def __init__(self, name, params, block, closure):
        self.name = name
        self.params = params
        self.block = block
        self.closure = closure

    def __call__(self, interp, args):
        env = Environment(self.closure)
        for i, p in enumerate(self.params):
            env.define(p, args[i] if i < len(args) else None)
        try:
            interp.exec_block(self.block, env)
        except ReturnSignal as r:
            return r.value
        return None


class NativeFunction:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __call__(self, interp, args):
        return self.fn(*args)


def is_truthy(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def stringify(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, list):
        return "[" + ", ".join(stringify(v) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{k}: {stringify(v)}" for k, v in value.items()) + "}"
    return str(value)


class Interpreter:
    def __init__(self, print_fn=None):
        self.globals = Environment()
        self.handlers = {}
        self.print_fn = print_fn or (lambda s: print(s))

    def register_native(self, name, fn):
        self.globals.define(name, NativeFunction(name, fn))

    def load(self, source):
        tokens = Lexer(source).tokenize()
        program = parse(tokens)
        for stmt in program.statements:
            self.exec_stmt(stmt, self.globals)

    def call_handler(self, event_name, args):
        handler = self.handlers.get(event_name)
        if handler is None:
            return None
        env = Environment(self.globals)
        for i, p in enumerate(handler.params):
            env.define(p, args[i] if i < len(args) else None)
        try:
            self.exec_block(handler.block, env)
        except ReturnSignal:
            pass

    # ---- statement execution ----

    def exec_block(self, block, env):
        for stmt in block.statements:
            self.exec_stmt(stmt, env)

    def exec_stmt(self, node, env):
        method = getattr(self, f"stmt_{type(node).__name__}", None)
        if method is None:
            raise ChatlangError(f"cannot execute node {type(node).__name__}")
        method(node, env)

    def stmt_VarDecl(self, node, env):
        value = self.eval(node.expr, env)
        env.define(node.name, value)

    def stmt_Assign(self, node, env):
        value = self.eval(node.expr, env)
        if isinstance(node.target, ast.Identifier):
            env.set(node.target.name, value)
        elif isinstance(node.target, ast.Index):
            container = self.eval(node.target.collection, env)
            index = self.eval(node.target.index, env)
            if isinstance(container, list):
                container[int(index)] = value
            elif isinstance(container, dict):
                container[index] = value
            else:
                raise ChatlangError("cannot index-assign into this value")
        else:
            raise ChatlangError("invalid assignment target")

    def stmt_If(self, node, env):
        if is_truthy(self.eval(node.cond, env)):
            self.exec_block(node.then_block, Environment(env))
        elif node.else_block is not None:
            if isinstance(node.else_block, ast.If):
                self.exec_stmt(node.else_block, env)
            else:
                self.exec_block(node.else_block, Environment(env))

    def stmt_While(self, node, env):
        while is_truthy(self.eval(node.cond, env)):
            self.exec_block(node.block, Environment(env))

    def stmt_FuncDecl(self, node, env):
        env.define(node.name, ChatlangFunction(node.name, node.params, node.block, env))

    def stmt_OnHandler(self, node, env):
        self.handlers[node.event_name] = node

    def stmt_Return(self, node, env):
        value = self.eval(node.expr, env) if node.expr is not None else None
        raise ReturnSignal(value)

    def stmt_PrintStmt(self, node, env):
        value = self.eval(node.expr, env)
        self.print_fn(stringify(value))

    def stmt_ExprStmt(self, node, env):
        self.eval(node.expr, env)

    def stmt_Block(self, node, env):
        self.exec_block(node, Environment(env))

    # ---- expression evaluation ----

    def eval(self, node, env):
        method = getattr(self, f"eval_{type(node).__name__}", None)
        if method is None:
            raise ChatlangError(f"cannot evaluate node {type(node).__name__}")
        return method(node, env)

    def eval_Number(self, node, env):
        return node.value

    def eval_String(self, node, env):
        return node.value

    def eval_Bool(self, node, env):
        return node.value

    def eval_Null(self, node, env):
        return None

    def eval_Identifier(self, node, env):
        return env.get(node.name)

    def eval_ListLit(self, node, env):
        return [self.eval(item, env) for item in node.items]

    def eval_DictLit(self, node, env):
        result = {}
        for key_expr, value_expr in node.pairs:
            key = self.eval(key_expr, env)
            result[key] = self.eval(value_expr, env)
        return result

    def eval_Index(self, node, env):
        container = self.eval(node.collection, env)
        index = self.eval(node.index, env)
        if isinstance(container, list):
            return container[int(index)]
        if isinstance(container, dict):
            return container.get(index)
        if isinstance(container, str):
            return container[int(index)]
        raise ChatlangError("value is not indexable")

    def eval_UnaryOp(self, node, env):
        value = self.eval(node.operand, env)
        if node.op == "-":
            return -value
        if node.op == "not":
            return not is_truthy(value)
        raise ChatlangError(f"unknown unary operator {node.op}")

    def eval_LogicalOp(self, node, env):
        left = self.eval(node.left, env)
        if node.op == "and":
            return self.eval(node.right, env) if is_truthy(left) else left
        if node.op == "or":
            return left if is_truthy(left) else self.eval(node.right, env)
        raise ChatlangError(f"unknown logical operator {node.op}")

    def eval_BinOp(self, node, env):
        left = self.eval(node.left, env)
        right = self.eval(node.right, env)
        op = node.op

        if op == "+":
            if isinstance(left, str) or isinstance(right, str):
                return stringify(left) + stringify(right)
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right
        if op == "%":
            return left % right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
        raise ChatlangError(f"unknown binary operator {op}")

    def eval_Call(self, node, env):
        if not isinstance(node.callee, ast.Identifier):
            raise ChatlangError("only named functions can be called")
        name = node.callee.name
        fn = env.get(name)
        args = [self.eval(a, env) for a in node.args]
        if isinstance(fn, (ChatlangFunction, NativeFunction)):
            return fn(self, args)
        raise ChatlangError(f"'{name}' is not callable")
