"""
Runtime services for the chatlang chat room: tracks connected clients and
message history, and exposes built-in functions that .cl scripts can call
(broadcast, send, history, users, plus general-purpose helpers on
strings/lists/dicts).
"""

import threading
import time
from datetime import datetime

from plic.EchoScript.interpreter import stringify, ChatlangError


class ChatRuntime:
    def __init__(self, max_history=200):
        self.lock = threading.RLock()
        self.clients = {}          # id -> {"socket": ..., "username": ...}
        self.history = []          # list of formatted strings
        self.max_history = max_history

    # -- connection bookkeeping (called from server.py, not from scripts) --

    def add_client(self, client_id, sock, username):
        with self.lock:
            self.clients[client_id] = {"socket": sock, "username": username}

    def remove_client(self, client_id):
        with self.lock:
            self.clients.pop(client_id, None)

    # -- built-ins exposed to chatlang scripts --

    def broadcast(self, text):
        text = stringify(text)
        with self.lock:
            self.history.append(text)
            if len(self.history) > self.max_history:
                self.history.pop(0)
            targets = list(self.clients.values())
        for info in targets:
            self._safe_send(info["socket"], text)
        return None

    def send(self, client_id, text):
        text = stringify(text)
        with self.lock:
            info = self.clients.get(client_id)
        if info is not None:
            self._safe_send(info["socket"], text)
        return None

    def history_fn(self, n=10):
        with self.lock:
            n = int(n)
            return list(self.history[-n:]) if n > 0 else []

    def users_fn(self):
        with self.lock:
            return [info["username"] for info in self.clients.values()]

    def disconnect_fn(self, client_id):
        with self.lock:
            info = self.clients.get(client_id)
        if info is not None:
            try:
                info["socket"].close()
            except OSError:
                pass
        return None

    @staticmethod
    def _safe_send(sock, text):
        try:
            sock.sendall((text + "\n").encode("utf-8"))
        except OSError:
            pass


# ---- general-purpose built-ins (pure functions, no runtime state) ----

def bi_len(x):
    return len(x)


def bi_push(lst, item):
    if not isinstance(lst, list):
        raise ChatlangError("push() expects a list")
    lst.append(item)
    return lst


def bi_pop(lst):
    if not isinstance(lst, list):
        raise ChatlangError("pop() expects a list")
    return lst.pop()


def bi_keys(d):
    if not isinstance(d, dict):
        raise ChatlangError("keys() expects a dict")
    return list(d.keys())


def bi_values(d):
    if not isinstance(d, dict):
        raise ChatlangError("values() expects a dict")
    return list(d.values())


def bi_get(d, key, default=None):
    if not isinstance(d, dict):
        raise ChatlangError("get() expects a dict")
    return d.get(key, default)


def bi_set(d, key, value):
    if not isinstance(d, dict):
        raise ChatlangError("set() expects a dict")
    d[key] = value
    return d


def bi_str(x):
    return stringify(x)


def bi_num(x):
    return float(x) if not isinstance(x, str) else float(x)


def bi_upper(s):
    return str(s).upper()


def bi_lower(s):
    return str(s).lower()


def bi_join(lst, sep=", "):
    return sep.join(stringify(x) for x in lst)


def bi_split(s, sep=" "):
    return s.split(sep)


def bi_now():
    return datetime.now().strftime("%H:%M:%S")


def register_builtins(interp, runtime: "ChatRuntime"):
    interp.register_native("broadcast", runtime.broadcast)
    interp.register_native("send", runtime.send)
    interp.register_native("history", runtime.history_fn)
    interp.register_native("users", runtime.users_fn)
    interp.register_native("disconnect", runtime.disconnect_fn)

    interp.register_native("len", bi_len)
    interp.register_native("push", bi_push)
    interp.register_native("pop", bi_pop)
    interp.register_native("keys", bi_keys)
    interp.register_native("values", bi_values)
    interp.register_native("get", bi_get)
    interp.register_native("set", bi_set)
    interp.register_native("str", bi_str)
    interp.register_native("num", bi_num)
    interp.register_native("upper", bi_upper)
    interp.register_native("lower", bi_lower)
    interp.register_native("join", bi_join)
    interp.register_native("split", bi_split)
    interp.register_native("now", bi_now)
