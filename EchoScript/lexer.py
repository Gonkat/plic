"""
Lexer for chatlang (.cl files).
Turns raw source text into a flat list of Token objects.
"""

KEYWORDS = {
    "var": "VAR",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "func": "FUNC",
    "return": "RETURN",
    "print": "PRINT",
    "on": "ON",
    "and": "AND",
    "or": "OR",
    "not": "NOT",
    "true": "TRUE",
    "false": "FALSE",
    "null": "NULL",
}

SYMBOLS = {
    "(": "LPAREN", ")": "RPAREN",
    "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACKET", "]": "RBRACKET",
    ",": "COMMA", ":": "COLON", ";": "SEMI",
    "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
}


class Token:
    __slots__ = ("type", "value", "line")

    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


class LexError(Exception):
    pass


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.pos = 0
        self.line = 1
        self.length = len(source)

    def error(self, msg):
        raise LexError(f"Lex error on line {self.line}: {msg}")

    def peek(self, offset=0):
        p = self.pos + offset
        if p < self.length:
            return self.src[p]
        return ""

    def advance(self):
        ch = self.src[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
        return ch

    def tokenize(self):
        tokens = []
        while self.pos < self.length:
            ch = self.peek()

            if ch in " \t\r\n":
                self.advance()
                continue

            if ch == "/" and self.peek(1) == "/":
                while self.pos < self.length and self.peek() != "\n":
                    self.advance()
                continue

            if ch.isdigit():
                tokens.append(self._read_number())
                continue

            if ch == '"':
                tokens.append(self._read_string())
                continue

            if ch.isalpha() or ch == "_":
                tokens.append(self._read_ident())
                continue

            # two-char operators
            two = ch + self.peek(1)
            if two == "==":
                self.advance(); self.advance()
                tokens.append(Token("EQ", "==", self.line)); continue
            if two == "!=":
                self.advance(); self.advance()
                tokens.append(Token("NEQ", "!=", self.line)); continue
            if two == "<=":
                self.advance(); self.advance()
                tokens.append(Token("LTE", "<=", self.line)); continue
            if two == ">=":
                self.advance(); self.advance()
                tokens.append(Token("GTE", ">=", self.line)); continue

            if ch == "<":
                self.advance(); tokens.append(Token("LT", "<", self.line)); continue
            if ch == ">":
                self.advance(); tokens.append(Token("GT", ">", self.line)); continue
            if ch == "=":
                self.advance(); tokens.append(Token("ASSIGN", "=", self.line)); continue

            if ch in SYMBOLS:
                line = self.line
                self.advance()
                tokens.append(Token(SYMBOLS[ch], ch, line))
                continue

            self.error(f"unexpected character {ch!r}")

        tokens.append(Token("EOF", None, self.line))
        return tokens

    def _read_number(self):
        start_line = self.line
        start = self.pos
        is_float = False
        while self.peek().isdigit():
            self.advance()
        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            self.advance()
            while self.peek().isdigit():
                self.advance()
        text = self.src[start:self.pos]
        value = float(text) if is_float else int(text)
        return Token("NUMBER", value, start_line)

    def _read_string(self):
        start_line = self.line
        self.advance()  # opening quote
        chars = []
        while True:
            if self.pos >= self.length:
                self.error("unterminated string literal")
            ch = self.advance()
            if ch == '"':
                break
            if ch == "\\":
                esc = self.advance()
                mapping = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}
                chars.append(mapping.get(esc, esc))
                continue
            chars.append(ch)
        return Token("STRING", "".join(chars), start_line)

    def _read_ident(self):
        start_line = self.line
        start = self.pos
        while self.peek().isalnum() or self.peek() == "_":
            self.advance()
        text = self.src[start:self.pos]
        kind = KEYWORDS.get(text, "IDENT")
        return Token(kind, text, start_line)
