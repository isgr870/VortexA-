#!/usr/bin/env python3
"""Desktop entry: start Vortexa bridge + static server and open the browser."""
from __future__ import annotations

import os
import sys
import time
import socket
import threading
import webbrowser
import subprocess
from pathlib import Path

# Resolve bundle root (PyInstaller sets _MEIPASS)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    ROOT = Path(sys._MEIPASS)
    APP_ROOT = Path(sys.executable).resolve().parent
else:
    ROOT = Path(__file__).resolve().parents[1]
    APP_ROOT = ROOT


def free_port(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def main() -> None:
    host = os.environ.get("VORTEXA_HOST", "127.0.0.1")
    ws_port = int(os.environ.get("VORTEXA_PORT", "8766"))
    http_port = int(os.environ.get("HTTP_PORT", "8080"))
    os.environ["VORTEXA_HOST"] = host
    os.environ["VORTEXA_PORT"] = str(ws_port)

    # Prefer files next to executable; fall back to bundle
    work = APP_ROOT if (APP_ROOT / "server.py").exists() else ROOT
    os.chdir(work)

    if not free_port(host, ws_port):
        print(f"Port {ws_port} busy — stop other Vortexa instances.")
    if not free_port(host, http_port):
        print(f"Port {http_port} busy — stop other HTTP servers.")

    # Ensure server.py is importable from work dir
    server_py = work / "server.py"
    if not server_py.exists():
        # copy reference from bundle is not available; require server alongside
        print("server.py not found next to app; place full Vortexa tree beside the executable.")
        sys.exit(1)

    env = os.environ.copy()
    bridge = subprocess.Popen(
        [sys.executable, "-u", str(server_py)],
        cwd=str(work),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    http = subprocess.Popen(
        [sys.executable, "-u", "-m", "http.server", str(http_port), "--bind", host],
        cwd=str(work),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://{host}:{http_port}/?v=3510"
    print("Vortexa Studio desktop")
    print("  UI ", url)
    print("  WS ", f"ws://{host}:{ws_port}")
    time.sleep(1.0)
    webbrowser.open(url)
    try:
        while bridge.poll() is None and http.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in (bridge, http):
            try:
                p.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
