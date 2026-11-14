"""Provider NTV (rete tvnow247/cfbu247) via worker Cloudflare.

Non risolve piu' i token alla generazione (scadono entro 24h): restituisce
URL STABILI del worker, che fa il resolve al volo su
chat.cfbu247.sbs/api/resolve-dlstream/<id> e rinnova i token da solo
(proattivo a 23h + reattivo su 401/403). La playlist non cambia MAI.
"""

WORKER_BASE = "https://resolvers.simone-scorrano-2011.workers.dev"


def resolve(channel, stream):
    slug = str(stream.get("slug") or channel.get("slug") or "").strip()
    query = str(stream.get("query") or "").strip()
    ch = slug or query
    if not ch:
        raise ValueError("servono slug o query")
    return {
        "url": f"{WORKER_BASE}/live?ch={ch}",
        "provider": "ntv",
        "quality": "HD",
        "headers": {},
        "extra_vlcopts": ["network-caching=10000"],
    }


def get_edge_map():
    # il vecchio edge.cowedd4855ws.sbs e' morto (530): la mappa edge non serve piu'
    return {}
