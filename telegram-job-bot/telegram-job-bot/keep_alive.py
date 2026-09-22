"""
24/7 Keep-Alive & Self-Awake Sentinel Server
Keeps the cloud instance on Render permanently awake 24/7 even when the user's laptop is closed.
"""

import os
import time
import urllib.request
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Telegram Verified Jobs AI Bot is Active 24/7!\nMulti-Layer Watchdog: ONLINE.")

    def log_message(self, format, *args):
        # Suppress noisy HTTP access logs
        pass


def run_health_server():
    port = int(os.getenv("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"24/7 Health Server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health server encountered error: {e}")


def run_self_awake_pinger():
    """
    Background Autonomous Sentinel:
    Pings the service's public Render URL every 7 minutes.
    This prevents Render's free tier from going to sleep when the user closes their laptop.
    """
    # Wait 60 seconds after startup before starting ping loop
    time.sleep(60)

    external_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
    if not external_url:
        # Fallback to known deployed Render service URL
        external_url = "https://telegram-job-bot-jnp0.onrender.com"

    logger.info(f"[KeepAwake Sentinel] Active. Auto-pinging {external_url} every 7 mins to ensure 24/7 uptime.")

    while True:
        try:
            req = urllib.request.Request(
                external_url,
                headers={"User-Agent": "WatchdogKeepAwakeSentinel/2.0"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                status = resp.getcode()
                logger.info(f"[KeepAwake Sentinel] Heartbeat OK (Status {status}) - Service kept awake 24/7.")
        except Exception as err:
            logger.info(f"[KeepAwake Sentinel] Ping sent to {external_url}: {err}")

        # Sleep for 7 minutes (420 seconds) - well below Render's 15 min sleep threshold
        time.sleep(420)


def start_health_server():
    """Starts the health check web server and the self-awake ping sentinel in daemon threads."""
    server_thread = threading.Thread(target=run_health_server, daemon=True)
    server_thread.start()

    pinger_thread = threading.Thread(target=run_self_awake_pinger, daemon=True)
    pinger_thread.start()
