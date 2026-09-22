"""
24/7 Keep-Alive & Self-Awake Sentinel Server
Keeps the cloud instance on Render permanently awake 24/7 even when the user's laptop is closed.
"""

import os
import time
import json
import html
import urllib.request
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

# In-memory storage for rich job detail cards (up to 500 entries)
JOB_DETAILS_DB = {}

def store_job_detail(job_id: str, data: dict):
    """Stores detailed job metadata in memory for rich web preview."""
    JOB_DETAILS_DB[job_id] = data
    if len(JOB_DETAILS_DB) > 500:
        oldest = next(iter(JOB_DETAILS_DB))
        del JOB_DETAILS_DB[oldest]


def render_job_detail_html(job_id: str) -> str:
    """Generates a clean, mobile-responsive dark theme HTML card for the job."""
    job = JOB_DETAILS_DB.get(job_id)
    if not job:
        return """<!DOCTYPE html><html><body style="background:#0f172a;color:#fff;font-family:sans-serif;text-align:center;padding:50px;">
        <h2>Job details not found or expired.</h2><p>Please search again on Telegram to get updated live listings.</p></body></html>"""

    def esc(s):
        return html.escape(str(s or ""))

    skills_html = "".join(f"<li>{esc(s)}</li>" for s in job.get("skills", []))
    tools_html = "".join(f"<li>{esc(t)}</li>" for t in job.get("tools", []))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(job.get('title'))} at {esc(job.get('company'))}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    line-height: 1.6;
    padding: 16px;
    max-width: 720px;
    margin: 0 auto;
  }}
  .card {{
    background: #1e293b;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
  }}
  .header {{
    text-align: center;
    padding: 32px 24px;
    background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
    border-radius: 16px;
    margin-bottom: 16px;
  }}
  .header h1 {{
    font-size: 24px;
    color: #fff;
    margin-bottom: 8px;
  }}
  .header .company {{
    font-size: 18px;
    color: #c7d2fe;
    font-weight: 500;
  }}
  .badge {{
    display: inline-block;
    background: rgba(255,255,255,0.2);
    color: #fff;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    margin-top: 12px;
  }}
  .section-title {{
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    margin-bottom: 12px;
    font-weight: 600;
  }}
  .info-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }}
  .info-item {{
    background: #0f172a;
    padding: 12px;
    border-radius: 10px;
  }}
  .info-item .label {{
    font-size: 11px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .info-item .value {{
    font-size: 15px;
    color: #f1f5f9;
    font-weight: 600;
    margin-top: 4px;
  }}
  .salary {{
    color: #10b981 !important;
    font-size: 18px !important;
  }}
  ul {{
    list-style: none;
    padding: 0;
  }}
  ul li {{
    padding: 8px 0 8px 24px;
    position: relative;
    border-bottom: 1px solid #334155;
    color: #cbd5e1;
  }}
  ul li:last-child {{ border-bottom: none; }}
  ul li::before {{
    content: "✓";
    position: absolute;
    left: 0;
    color: #10b981;
    font-weight: bold;
  }}
  .tools-list li::before {{ content: "🔧"; }}
  .apply-btn {{
    display: block;
    width: 100%;
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #fff;
    text-align: center;
    padding: 16px;
    border-radius: 12px;
    text-decoration: none;
    font-weight: 700;
    font-size: 16px;
    margin-top: 16px;
    box-shadow: 0 4px 12px rgba(16,185,129,0.3);
  }}
  .apply-btn:active {{ transform: scale(0.98); }}
  .footer {{
    text-align: center;
    color: #64748b;
    font-size: 12px;
    padding: 16px;
  }}
  .warning {{
    background: #7c2d12;
    border-left: 4px solid #f59e0b;
    padding: 12px;
    border-radius: 8px;
    font-size: 13px;
    color: #fed7aa;
  }}
</style>
</head>
<body>

<div class="header">
  <h1>{esc(job.get('title'))}</h1>
  <div class="company">🏢 {esc(job.get('company'))}</div>
  <div class="badge">✅ Verified Opening</div>
</div>

<div class="card">
  <div class="section-title">📋 Job Overview</div>
  <div class="info-grid">
    <div class="info-item">
      <div class="label">📍 Location</div>
      <div class="value">{esc(job.get('location'))}</div>
    </div>
    <div class="info-item">
      <div class="label">💰 Salary</div>
      <div class="value salary">{esc(job.get('salary'))}</div>
    </div>
    <div class="info-item">
      <div class="label">⏱️ Hiring Status</div>
      <div class="value">{esc(job.get('freshness'))}</div>
    </div>
    <div class="info-item">
      <div class="label">🥊 Competition</div>
      <div class="value">{esc(job.get('competition'))}</div>
    </div>
    <div class="info-item">
      <div class="label">⭐ Rating</div>
      <div class="value">{esc(job.get('rating'))}</div>
    </div>
    <div class="info-item">
      <div class="label">👻 Ghost Risk</div>
      <div class="value">{esc(job.get('ghost_risk'))}</div>
    </div>
  </div>
</div>

<div class="card">
  <div class="section-title">🛠️ Skills Required</div>
  <ul>{skills_html}</ul>
</div>

<div class="card">
  <div class="section-title">🧰 Tools You'll Use</div>
  <ul class="tools-list">{tools_html}</ul>
</div>

<div class="card">
  <div class="section-title">💡 Pro Tip</div>
  <div class="warning">{esc(job.get('tip'))}</div>
</div>

<a href="{esc(job.get('apply_link'))}" class="apply-btn" target="_blank">
  🚀 Apply Now
</a>

<div class="footer">
  🔒 Verified by Multi-Layer Anti-Scam Engine<br>
  No registration fee • Direct company portal
</div>

</body>
</html>"""


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Job detail rich web preview route: /job/<job_id>
        if self.path.startswith("/job/"):
            job_id = self.path.replace("/job/", "").split("?")[0]
            html_content = render_job_detail_html(job_id)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
            return

        # 2. Health check (default endpoint)
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Telegram Verified Jobs AI Bot is Active 24/7!\nMulti-Layer Watchdog: ONLINE.")

    def log_message(self, format, *args):
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
