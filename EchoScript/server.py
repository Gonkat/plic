"""
Multi-user chat server. Accepts raw TCP connections (works with `nc` / telnet
or client.py) and drives a chatlang script's on connect/on message/on
disconnect handlers for every event.

Usage:
    python main.py examples/chat.cl 9000
"""

import socket
import threading
import itertools

from plic.EchoScript.interpreter import Interpreter, ChatlangError
from plic.EchoScript.runtime import ChatRuntime, register_builtins


class ChatServer:
    def __init__(self, script_path, host="0.0.0.0", port=9000):
        self.host = host
        self.port = port
        self.runtime = ChatRuntime()
        self.interp = Interpreter(print_fn=self._log)
        register_builtins(self.interp, self.runtime)

        with open(script_path, "r", encoding="utf-8") as f:
            source = f.read()
        self.interp.load(source)

        self._id_counter = itertools.count(1)
        # chatlang handlers mutate shared global state (vars, history);
        # a single lock serializes events, similar in spirit to routing
        # everything through one mailbox/actor.
        self.handler_lock = threading.Lock()

    def _log(self, msg):
        print(f"[chatlang] {msg}")

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen()
            print(f"plic chat server listening on {self.host}:{self.port}")
            while True:
                conn, addr = srv.accept()
                t = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                t.start()

    def _handle_client(self, conn, addr):
        client_id = next(self._id_counter)
        reader = conn.makefile("r", encoding="utf-8", newline="\n")

        try:
            conn.sendall(b"Enter username: ")
            username = reader.readline().strip() or f"guest{client_id}"
        except OSError:
            conn.close()
            return

        self.runtime.add_client(client_id, conn, username)
        self._run_handler("connect", [client_id, username])

        try:
            while True:
                line = reader.readline()
                if line == "":
                    break
                text = line.rstrip("\n").rstrip("\r")
                if text == "":
                    continue
                if text == "/quit":
                    break
                self._run_handler("message", [client_id, username, text])
        except OSError:
            pass
        finally:
            self.runtime.remove_client(client_id)
            self._run_handler("disconnect", [client_id, username])
            try:
                conn.close()
            except OSError:
                pass

    def _run_handler(self, name, args):
        with self.handler_lock:
            try:
                self.interp.call_handler(name, args)
            except ChatlangError as e:
                self._log(f"runtime error in on {name}: {e}")


if __name__ == "__main__":
    import sys
    script = sys.argv[1] if len(sys.argv) > 1 else "examples/chat.cl"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    ChatServer(script, port=port).start()
