"""Inicia a interface do Radar Seazone (servidor estático) e abre no navegador."""
import http.server
import socketserver
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
URL = f"http://localhost:{PORT}/interface/"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        print(f"[{self.address_string()}] {fmt % args}")


def ocupada(porta):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", porta)) == 0


try:
    if ocupada(PORT):
        print(f"Porta {PORT} já em uso — abrindo a interface existente.")
        webbrowser.open(URL)
        print(URL)
    else:
        handler = socketserver.TCPServer(("", PORT), Handler)
        print(f"Radar Seazone em {URL}")
        print("Pressione Ctrl+C para encerrar.")
        threading.Timer(1.0, lambda: webbrowser.open(URL)).start()
        handler.serve_forever()
except KeyboardInterrupt:
    print("\nEncerrado.")