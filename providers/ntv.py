"""Provider NTV - risoluzione diretta (senza Val.town)."""
import logging
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://ntv.cx/",
    "Origin": "https://ntv.cx",
}

EDGE = "https://edge.cowedd4855ws.sbs"
TIMEOUT = 15

def resolve(channel, stream):
    cid = str(stream.get("query") or "").strip()
    if not cid:
        raise ValueError("NTV: query mancante")

    slug = f"premium{cid}"
    
    # Ottieni token
    token_res = requests.get(
        f"{EDGE}/api/playlist-token?slug={slug}",
        headers=HEADERS,
        timeout=TIMEOUT
    )
    token_res.raise_for_status()
    token_data = token_res.json()
    token = token_data.get("token")
    if not token:
        raise ValueError("NTV: token non restituito")

    url = f"{EDGE}/{slug}/index.m3u8?t={token}&_={__import__('time').time()}"
    logger.info("NTV: %s -> %s", cid, url)

    return {
        "url": url,
        "provider": "NTV",
        "quality": "HD",
        "headers": {"Referer": "https://ntv.cx/"},
        "extra_vlcopts": ["network-caching=15000"],
    }
