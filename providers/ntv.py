"""
ntv provider - edge diretto famiglia ntv.cx/Daddy.
Ogni canale e' un ID numerico: <edge>/premium<ID>/index.m3u8 con token da
<edge>/api/playlist-token?slug=premium<ID> (richiede il referer del player).
Edge host in base.json con fallback: i domini edge ruotano, aggiornali li'.
"""

import json
import time
from pathlib import Path
from urllib.parse import quote

import requests

WORKER_BASE = "https://sim11.val.run/ntv-stream"
BASE_FILE = Path("base.json")
TIMEOUT = 15

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://ntv.cx/",
    "Origin": "https://ntv.cx",
}

REFERERS = [
    "https://ntv.cx/",
    "https://tvnow247.top/",
    "https://bembed.sbs/premiumtv/daddy.php",
    "",
]

CORS_PROXIES = [
    lambda u: "https://api.allorigins.win/raw?url=" + quote(u, safe=""),
    lambda u: "https://api.codetabs.com/v1/proxy?quest=" + u,
    lambda u: "https://api.cors.lol/?url=" + quote(u, safe=""),
]

_edge_map = {}


def get_edge_map():
    return dict(_edge_map)


def load_base():
    if BASE_FILE.exists():
        return json.loads(BASE_FILE.read_text(encoding="utf-8"))
    return {"edge": "https://edge.cowedd4855ws.sbs", "fallbacks": []}


def save_base(cfg):
    BASE_FILE.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def _get_token(edge, slug):
    for ref in REFERERS:
        try:
            h = dict(HEADERS)
            if ref:
                h["Referer"] = ref
            r = requests.get(edge + "/api/playlist-token?slug=" + slug,
                             headers=h, timeout=TIMEOUT)
            if r.ok:
                j = r.json()
                if j and j.get("token"):
                    return j["token"]
        except Exception:
            pass
    return None


def _playlist_ok(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code == 200 and "#EXTM3U" in r.text[:200]:
            return True
    except Exception:
        pass
    for make_proxy in CORS_PROXIES:
        try:
            r = requests.get(make_proxy(url), headers=HEADERS, timeout=TIMEOUT + 8)
            if r.status_code == 200 and "#EXTM3U" in r.text[:200]:
                return True
        except Exception:
            continue
    return False


def channel_ok(edge, cid):
    slug = "premium" + str(cid)
    token = _get_token(edge, slug)
    if not token:
        return False
    url = f"{edge}/{slug}/index.m3u8?t={token}&_={int(time.time() * 1000)}"
    return _playlist_ok(url)


def resolve(channel, stream):
    cfg = load_base()
    cid = str(stream.get("query") or channel.get("name", "")).strip()
    if not cid.isdigit():
        raise ValueError(f"query non numerica: '{cid}' (serve l'ID NTV, es. 577)")

    ok = False
    edge = cfg["edge"]
    for cand in [cfg["edge"]] + cfg.get("fallbacks", []):
        if channel_ok(cand, cid):
            edge = cand
            ok = True
            break
    if not ok:
        raise RuntimeError(f"premium{cid}: nessun edge raggiungibile o token valido")

    _edge_map[cid] = {"id": cid}
    print(f"[ntv] OK: {channel.get('name')} (id {cid} via {edge})")
    return {
        "url": f"{WORKER_BASE}/live?ch={cid}",
        "provider": "ntv",
        "quality": "HD",
        "headers": {},
        "extra_vlcopts": ["network-caching=15000"],
        "proxy": "direct",
        "proxy_required": False,
    }
  
