import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Telegram Job Bot is Running 24/7!")

    def log_message(self, format, *args):
        # Suppress noisy logs
        pass

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def start_health_server():
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
