"""Provider NTV - salva URL del resolver Cloudflare (non risolve direttamente)."""
import logging
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Cloudflare Worker resolver
RESOLVER_BASE = "https://resolvers.simone-scorrano-2011.workers.dev/ntv"

def resolve(channel, stream):
    query = stream.get("query") or ""
    if not query:
        raise ValueError("NTV: query mancante")

    stable_url = f"{RESOLVER_BASE}?ch={quote(query)}"
    logger.info("NTV: %s -> %s", query, stable_url)

    return {
        "url": stable_url,
        "provider": "NTV",
        "quality": "HD",
        "headers": {},
        "extra_vlcopts": ["network-caching=15000"],
    }
