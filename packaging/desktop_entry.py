#!/usr/bin/env python3
"""Vortexa Studio desktop launcher — starts bridge + HTTP in-process and opens browser."""
from __future__ import annotations

import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

def app_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Prefer files next to the executable (full tree shipped beside binary)
        beside = Path(sys.executable).resolve().parent
        if (beside / "server.py").exists() or (beside / "index.html").exists():
            return beside
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]

ROOT = app_root()
os.chdir(ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("VORTEXA_HOST", "127.0.0.1")
os.environ.setdefault("VORTEXA_PORT", "8766")
HTTP_PORT = int(os.environ.get("HTTP_PORT", "8080"))
HOST = os.environ["VORTEXA_HOST"]
WS_PORT = int(os.environ["VORTEXA_PORT"])

class RootHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def log_message(self, fmt, *args):
        pass

def port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False

def start_http():
    httpd = ThreadingHTTPServer((HOST, HTTP_PORT), RootHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd

def start_bridge():
    # Import server module and run its asyncio main in this process
    import asyncio
    import server as vortexa_server
    asyncio.run(vortexa_server.main())

def main():
    if not (ROOT / "index.html").exists():
        print("index.html missing — incomplete install at", ROOT)
        sys.exit(1)
    if not port_free(HOST, WS_PORT):
        print(f"Port {WS_PORT} in use. Close other Vortexa instances.")
    if not port_free(HOST, HTTP_PORT):
        print(f"Port {HTTP_PORT} in use. Close other HTTP servers.")

    httpd = start_http()
    url = f"http://{HOST}:{HTTP_PORT}/?v=360"
    print("Vortexa Studio")
    print("  UI ", url)
    print("  WS ", f"ws://{HOST}:{WS_PORT}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        start_bridge()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            httpd.shutdown()
        except Exception:
            pass

if __name__ == "__main__":
    main()
