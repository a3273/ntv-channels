#!/usr/bin/env python3
"""
Generate playlist.m3u from channels.json with multi-provider support.

Providers are discovered from the "provider" field in channels.json.
Each provider should implement: resolve(channel, stream) -> dict with:
  - url (stream URL)
  - proxy (optional: "direct" or "proxy")
  - headers (optional: dict of HTTP headers)
  - quality (optional)
  - extra_vlcopts (optional: list of extra #EXTVLCOPT values)
"""

import importlib
import json
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHANNELS_FILE = BASE_DIR / "channels.json"
PLAYLIST_FILE = BASE_DIR / "playlist.m3u"
STATUS_FILE = BASE_DIR / "status.json"
VERSION_FILE = BASE_DIR / "version.txt"
EDGE_FILE = BASE_DIR / "edge.json"


def load_channels():
    with CHANNELS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def merge_channels(active: dict, new: dict) -> dict:
    existing = {c["name"]: c for c in active.get("channels", [])}
    for channel in new.get("channels", []):
        if channel["name"] not in existing:
            active.setdefault("channels", []).append(channel)
    return active


def next_version() -> int:
    try:
        with VERSION_FILE.open("r", encoding="utf-8") as f:
            return int(f.read().strip()) + 1
    except Exception:
        return 1


def build_status(version: int, playlist_count: int):
    return {
        "version": version,
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "channels_in_playlist": playlist_count,
    }


def _write_if_changed(path: Path, content: str) -> None:
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        print(f"{path.name}: no changes")
        return
    path.write_text(content, encoding="utf-8")
    print(f"{path.name}: updated")


def load_active_channels(path: Path):
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    channels = load_channels()
    lines = ["#EXTM3U"]

    total = 0
    for channel in channels.get("channels", []):
        if not channel.get("enabled", True):
            continue
        streams = channel.get("streams", [])
        if not streams:
            continue

        name = channel.get("name", "Unknown")
        logo = channel.get("logo", "")
        group = channel.get("group", "")
        resolved = []

        for stream in streams:
            if not stream.get("enabled", True):
                continue
            provider_name = stream.get("provider")
            if not provider_name:
                continue
            try:
                provider = importlib.import_module(f"providers.{provider_name}")
                info = provider.resolve(channel, stream)
                if info.get("url"):
                    resolved.append(info)
            except Exception as e:
                print(f"  [{provider_name}] {name}: {e}")

        resolved.sort(key=lambda x: x.get("priority", 0))
        if not resolved:
            continue

        first = True
        for info in resolved:
            vlcopts = [f'http-user-agent={info.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")}']
            if info.get("extra_vlcopts"):
                vlcopts.extend(info["extra_vlcopts"])
            vlcopts_str = "\n".join(f"#EXTVLCOPT:{opt}" for opt in vlcopts)
            prefix = "" if first else f'#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=1500000\n'
            lines.append(f'{vlcopts_str}\n#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n{info["url"]}')
            first = False
            total += 1

    # edge.json dopo il ciclo: mappa popolata dai resolve
    try:
        import providers.ntv as ntv_mod
        edge_map = ntv_mod.get_edge_map()
        if edge_map:
            with EDGE_FILE.open("w", encoding="utf-8") as f:
                json.dump(edge_map, f)
            print(f"edge.json: {len(edge_map)} canali mappati")
    except Exception as e:
        print(f"edge.json non scritto: {e}")

    playlist_content = "\n".join(lines) + "\n"
    _write_if_changed(PLAYLIST_FILE, playlist_content)

    version = next_version()
    status = build_status(version, total)
    _write_if_changed(STATUS_FILE, json.dumps(status, indent=2) + "\n")
    VERSION_FILE.write_text(str(version) + "\n", encoding="utf-8")

    print(f"Playlist generated with {total} streams -> {PLAYLIST_FILE}")


if __name__ == "__main__":
    sys.exit(main())
  
