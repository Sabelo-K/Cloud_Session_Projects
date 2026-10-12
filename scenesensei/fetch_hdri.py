"""Download a free HDRI (CC0, no credit needed) from Poly Haven into scenesensei/assets/hdri/.

    python -m scenesensei.fetch_hdri studio_small_09
    python -m scenesensei.fetch_hdri studio_small_09 --res 4k

The ID is the last part of the asset's page address: https://polyhaven.com/a/<id>. Browse
https://polyhaven.com/hdris (try the "studio" category first for product and logo shots).
`logo_reveal` uses the first .hdr/.exr file in that folder automatically.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from scenesensei.scene_args import PACKAGE_DIR

HDRI_DIR = PACKAGE_DIR / "assets" / "hdri"
API = "https://api.polyhaven.com/files/{id}"
USER_AGENT = "scenesensei-starter (+https://github.com/Sabelo-K/Cloud_Session_Projects)"


class FetchError(Exception):
    pass


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise FetchError("no such asset; check the ID on polyhaven.com") from None
        raise FetchError(f"Poly Haven answered HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise FetchError(f"could not reach Poly Haven: {exc}") from None


def _download(url: str, dest: Path) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        raise FetchError(f"download failed: {exc}") from None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data


def pick_file(files: dict, res: str) -> tuple[str, dict, str]:
    """(resolution, {'url', 'md5', ...}, extension) for the HDRI at `res`, preferring .hdr over .exr."""
    hdri = files.get("hdri")
    if not isinstance(hdri, dict) or not hdri:
        raise FetchError("this asset has no HDRI files (is it a texture or a model?)")
    if res not in hdri:
        raise FetchError(f"no {res} version; available: {', '.join(sorted(hdri))}")
    for ext in ("hdr", "exr"):
        if isinstance(hdri[res].get(ext), dict):
            return res, hdri[res][ext], ext
    raise FetchError(f"no .hdr or .exr file at {res}")


def fetch(asset_id: str, res: str = "2k", dest_dir: Path = HDRI_DIR) -> Path:
    _, entry, ext = pick_file(_get_json(API.format(id=asset_id)), res)
    dest = dest_dir / f"{asset_id}_{res}.{ext}"
    data = _download(entry["url"], dest)
    expected = entry.get("md5")
    if expected and hashlib.md5(data).hexdigest() != expected:   # noqa: S324 (integrity check only)
        dest.unlink(missing_ok=True)
        raise FetchError("downloaded file is corrupt (checksum mismatch); try again")
    return dest


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m scenesensei.fetch_hdri", description=__doc__.split("\n\n")[0])
    p.add_argument("asset_id", help="Poly Haven asset ID, e.g. studio_small_09")
    p.add_argument("--res", default="2k", help="1k, 2k (default), 4k, 8k ... larger = sharper reflections, bigger file")
    args = p.parse_args(argv)
    try:
        path = fetch(args.asset_id, args.res)
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"Saved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
