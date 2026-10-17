import os
import time
import urllib.request
import logging
import threading

logger = logging.getLogger(__name__)

def start_keep_alive_daemon():
    """
    Self-ping keep-alive daemon for Render Free Tier.
    Render automatically spins down after 15 minutes of inactivity.
    This daemon pings the public HTTPS URL every 12 minutes (720 seconds),
    ensuring Render's edge router registers an active inbound HTTP request,
    keeping the container running 24/7/365 with ZERO cold starts and $0 cost.
    """
    # 1. Determine public URL
    url = (
        os.environ.get("RENDER_EXTERNAL_URL")
        or os.environ.get("KEEP_ALIVE_URL")
        or (os.environ.get("RENDER") and "https://kashii-updatez.onrender.com")
    )
    if not url:
        return

    ping_url = f"{url.rstrip('/')}/api/ping"

    def _ping_loop():
        # Wait 45 seconds after container boot before initial ping
        time.sleep(45)
        logger.info(f"🚀 [Keep-Alive Daemon] Initialized 24/7 Anti-Sleep Shield. Target: {ping_url}")
        
        # 12 minutes = 720 seconds (Render timeout is 15 minutes)
        PING_INTERVAL = 12 * 60

        while True:
            try:
                req = urllib.request.Request(
                    ping_url,
                    headers={
                        'User-Agent': 'KashiiKeepAlive/1.0 (Render 24/7 Shield; Python)',
                        'Accept': 'application/json',
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    status = response.getcode()
                    logger.info(f"⚡ [Keep-Alive Daemon] Self-ping successful: {status} OK (Render 15m sleep timer reset)")
            except Exception as e:
                logger.warning(f"⚠️ [Keep-Alive Daemon] Self-ping warning (will retry in next cycle): {e}")

            time.sleep(PING_INTERVAL)

    t = threading.Thread(target=_ping_loop, daemon=True, name="RenderKeepAliveDaemon")
    t.start()
