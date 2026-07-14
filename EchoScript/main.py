# main.py
"""
Entry point.

Usage:
    python main.py [script.cl] [port]

Defaults to examples/chat.cl on port 9000.
"""

import sys
from plic.EchoScript.server import ChatServer

if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else "examples/chat.cl"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    ChatServer(script, port=port).start()
