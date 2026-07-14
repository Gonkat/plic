# client.py
"""
Minimal console client for the plic chat server.

Usage:
    python client.py 127.0.0.1 9000
"""

import socket
import sys
import threading


def reader_loop(sock):
    buf = b""
    while True:
        try:
            chunk = sock.recv(4096)
        except OSError:
            break
        if not chunk:
            print("\n(disconnected)")
            break
        buf += chunk
        while b"\n" in buf:
            line, buf = buf.split(b"\n", 1)
            print(line.decode("utf-8", errors="replace"))


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000

    sock = socket.create_connection((host, port))
    t = threading.Thread(target=reader_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            line = input()
            sock.sendall((line + "\n").encode("utf-8"))
            if line.strip() == "/quit":
                break
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        sock.close()


if __name__ == "__main__":
    main()
