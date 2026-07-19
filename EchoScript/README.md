# plic — chatlang

A tiny custom language ("chatlang", `.cl` files) plus a tree-walking
interpreter and TCP chat server written in it, submitted for the plic
langjam. Platform: **CPython** (no external dependencies — standard
library only).

## Run it

```bash
# start the server (defaults to chat.cl on port 9000)
python3 main.py chat.cl 9000

# in other terminals, connect with the bundled client...
python3 client.py 127.0.0.1 9000

# ...or with a plain TCP client like netcat / telnet
nc 127.0.0.1 9000
```

You'll be prompted for a username, then dropped straight into the room.
Type a line to broadcast it to everyone. Built-in commands from
`chat.cl`: `/history`, `/users`, `/quit`.

## What's in the box

| Requirement                     | Where                                    |
|----------------------------------|-------------------------------------------|
| Language source (lexer/parser/interpreter) | `lexer.py`, `chatlang_ast.py`, `parser.py`, `interpreter.py` |
| Chat runtime + built-ins         | `runtime.py`                              |
| Chat server (add/broadcast/history/remove user) | `server.py`                     |
| Chat program written *in* chatlang | `chat.cl`                      |
| Test client                      | `client.py`                               |

## Language: chatlang

chatlang is a small, dynamically-typed, event-driven scripting
language. A `.cl` file is a sequence of top-level `var`/`func`
declarations and `on <event>(...)` handlers; the server calls those
handlers as connections come and go.

### Types
`number` (int/float), `string`, `bool`, `null`, `list` (`[1, 2, 3]`),
`dict` (`{"a": 1, "b": 2}`).

### Variables
```
var count = 0
count = count + 1
```

### Conditionals
```
if (count > 10) {
    print("busy")
} else if (count > 0) {
    print("some people here")
} else {
    print("empty")
}
```

### Loops
chatlang has `while` (no separate recursion primitive is needed since
user functions can call themselves):
```
var i = 0
while (i < len(names)) {
    print(names[i])
    i = i + 1
}
```

### Functions
```
func greet(name) {
    return "hi, " + name
}
```

### Collections
```
var users = ["alice", "bob"]
push(users, "carol")

var scores = {"alice": 10}
set(scores, "bob", 5)
print(get(scores, "bob"))
```

### Event handlers (the actual chat logic)
The server invokes these three handlers; each parameter is passed by
the server itself.
```
on connect(id, username) { ... }        // fired when a user joins
on message(id, username, text) { ... }  // fired on every line they send
on disconnect(id, username) { ... }     // fired when they leave
```

### Built-in functions
- **Chat runtime**: `broadcast(text)`, `send(id, text)`, `history(n)`,
  `users()`, `disconnect(id)`
- **General purpose**: `len`, `push`, `pop`, `keys`, `values`, `get`,
  `set`, `str`, `num`, `upper`, `lower`, `join`, `split`, `now`, `print`

## Architecture notes

- `lexer.py` → tokens → `parser.py` → AST (`chatlang_ast.py`) →
  `interpreter.py` walks the tree with lexically-scoped `Environment`
  objects (closures work: functions capture their defining scope).
- `runtime.py` owns the shared chat state (connected clients, message
  history) and exposes it to scripts only through the built-in
  functions above — the script itself never touches sockets directly.
- `server.py` runs one thread per TCP connection (accept/read loop
  only). All calls into the interpreter go through a single lock, so
  handler execution is serialized — the shared `var`s in a `.cl`
  script and the message history behave like a single-mailbox
  actor, without needing real STM/locks inside the language itself.

## Known simplifications (day-one MVP scope)

- No user-defined error handling (`try`/`catch`) — runtime errors in a
  handler are caught by the server and logged, without crashing other
  clients.
- No persistence — history resets when the server restarts.
- No `/kick`, rooms, or auth — straightforward to add as more built-ins
  in `runtime.py` plus a bit more logic in `chat.cl`.
