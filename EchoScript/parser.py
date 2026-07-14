# parser.py

"""
Recursive-descent parser for chatlang.
Turns a token list from lexer.py into an AST (chatlang_ast.py).
"""

import plic.EchoScript.chatlang_ast as ast


class ParseError(Exception):
    pass


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---- token helpers ----

    def peek(self, offset=0):
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def check(self, type_):
        return self.peek().type == type_

    def advance(self):
        tok = self.tokens[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def match(self, *types):
        if self.peek().type in types:
            return self.advance()
        return None

    def expect(self, type_, msg=None):
        if self.check(type_):
            return self.advance()
        tok = self.peek()
        raise ParseError(msg or f"expected {type_} but got {tok.type} ({tok.value!r}) on line {tok.line}")

    # ---- entry point ----

    def parse_program(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.parse_statement())
        return ast.Program(statements)

    # ---- statements ----

    def parse_statement(self):
        t = self.peek().type
        if t == "VAR":
            return self.parse_var_decl()
        if t == "IF":
            return self.parse_if()
        if t == "WHILE":
            return self.parse_while()
        if t == "FUNC":
            return self.parse_func_decl()
        if t == "ON":
            return self.parse_on_handler()
        if t == "RETURN":
            return self.parse_return()
        if t == "PRINT":
            return self.parse_print()
        if t == "LBRACE":
            return self.parse_block()
        return self.parse_expr_or_assign_statement()

    def parse_var_decl(self):
        self.expect("VAR")
        name = self.expect("IDENT").value
        self.expect("ASSIGN")
        expr = self.parse_expression()
        self.match("SEMI")
        return ast.VarDecl(name, expr)

    def parse_if(self):
        self.expect("IF")
        self.expect("LPAREN")
        cond = self.parse_expression()
        self.expect("RPAREN")
        then_block = self.parse_block()
        else_block = None
        if self.match("ELSE"):
            if self.check("IF"):
                else_block = self.parse_if()
            else:
                else_block = self.parse_block()
        return ast.If(cond, then_block, else_block)

    def parse_while(self):
        self.expect("WHILE")
        self.expect("LPAREN")
        cond = self.parse_expression()
        self.expect("RPAREN")
        block = self.parse_block()
        return ast.While(cond, block)

    def parse_func_decl(self):
        self.expect("FUNC")
        name = self.expect("IDENT").value
        params = self.parse_param_list()
        block = self.parse_block()
        return ast.FuncDecl(name, params, block)

    def parse_on_handler(self):
        self.expect("ON")
        event_name = self.expect("IDENT").value
        params = self.parse_param_list()
        block = self.parse_block()
        return ast.OnHandler(event_name, params, block)

    def parse_param_list(self):
        self.expect("LPAREN")
        params = []
        if not self.check("RPAREN"):
            params.append(self.expect("IDENT").value)
            while self.match("COMMA"):
                params.append(self.expect("IDENT").value)
        self.expect("RPAREN")
        return params

    def parse_return(self):
        self.expect("RETURN")
        expr = None
        if not self.check("SEMI") and not self.check("RBRACE"):
            expr = self.parse_expression()
        self.match("SEMI")
        return ast.Return(expr)

    def parse_print(self):
        self.expect("PRINT")
        self.expect("LPAREN")
        expr = self.parse_expression()
        self.expect("RPAREN")
        self.match("SEMI")
        return ast.PrintStmt(expr)

    def parse_block(self):
        self.expect("LBRACE")
        statements = []
        while not self.check("RBRACE") and not self.check("EOF"):
            statements.append(self.parse_statement())
        self.expect("RBRACE")
        return ast.Block(statements)

    def parse_expr_or_assign_statement(self):
        expr = self.parse_expression()
        if self.match("ASSIGN"):
            value = self.parse_expression()
            self.match("SEMI")
            if not isinstance(expr, (ast.Identifier, ast.Index)):
                raise ParseError("invalid assignment target")
            return ast.Assign(expr, value)
        self.match("SEMI")
        return ast.ExprStmt(expr)

    # ---- expressions (precedence climbing) ----

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match("OR"):
            right = self.parse_and()
            left = ast.LogicalOp("or", left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.match("AND"):
            right = self.parse_not()
            left = ast.LogicalOp("and", left, right)
        return left

    def parse_not(self):
        if self.match("NOT"):
            operand = self.parse_not()
            return ast.UnaryOp("not", operand)
        return self.parse_equality()

    def parse_equality(self):
        left = self.parse_comparison()
        while self.check("EQ") or self.check("NEQ"):
            op = self.advance().type
            right = self.parse_comparison()
            left = ast.BinOp("==" if op == "EQ" else "!=", left, right)
        return left

    def parse_comparison(self):
        left = self.parse_term()
        while self.peek().type in ("LT", "LTE", "GT", "GTE"):
            op_tok = self.advance()
            right = self.parse_term()
            op_map = {"LT": "<", "LTE": "<=", "GT": ">", "GTE": ">="}
            left = ast.BinOp(op_map[op_tok.type], left, right)
        return left

    def parse_term(self):
        left = self.parse_factor()
        while self.peek().type in ("PLUS", "MINUS"):
            op_tok = self.advance()
            right = self.parse_factor()
            left = ast.BinOp(op_tok.value, left, right)
        return left

    def parse_factor(self):
        left = self.parse_unary()
        while self.peek().type in ("STAR", "SLASH", "PERCENT"):
            op_tok = self.advance()
            right = self.parse_unary()
            left = ast.BinOp(op_tok.value, left, right)
        return left

    def parse_unary(self):
        if self.match("MINUS"):
            operand = self.parse_unary()
            return ast.UnaryOp("-", operand)
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.match("LPAREN"):
                args = []
                if not self.check("RPAREN"):
                    args.append(self.parse_expression())
                    while self.match("COMMA"):
                        args.append(self.parse_expression())
                self.expect("RPAREN")
                expr = ast.Call(expr, args)
            elif self.match("LBRACKET"):
                index = self.parse_expression()
                self.expect("RBRACKET")
                expr = ast.Index(expr, index)
            else:
                break
        return expr

    def parse_primary(self):
        tok = self.peek()

        if tok.type == "NUMBER":
            self.advance()
            return ast.Number(tok.value)
        if tok.type == "STRING":
            self.advance()
            return ast.String(tok.value)
        if tok.type == "TRUE":
            self.advance()
            return ast.Bool(True)
        if tok.type == "FALSE":
            self.advance()
            return ast.Bool(False)
        if tok.type == "NULL":
            self.advance()
            return ast.Null()
        if tok.type == "IDENT":
            self.advance()
            return ast.Identifier(tok.value)
        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr
        if tok.type == "LBRACKET":
            self.advance()
            items = []
            if not self.check("RBRACKET"):
                items.append(self.parse_expression())
                while self.match("COMMA"):
                    items.append(self.parse_expression())
            self.expect("RBRACKET")
            return ast.ListLit(items)
        if tok.type == "LBRACE":
            self.advance()
            pairs = []
            if not self.check("RBRACE"):
                pairs.append(self._parse_dict_pair())
                while self.match("COMMA"):
                    pairs.append(self._parse_dict_pair())
            self.expect("RBRACE")
            return ast.DictLit(pairs)

        raise ParseError(f"unexpected token {tok.type} ({tok.value!r}) on line {tok.line}")

    def _parse_dict_pair(self):
        key = self.parse_expression()
        self.expect("COLON")
        value = self.parse_expression()
        return (key, value)


def parse(tokens):
    return Parser(tokens).parse_program()
