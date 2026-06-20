#!/usr/bin/env python3
"""Fetch per-handler game art off the web into each handler dir.

Source per file, in order:
  1. an explicit URL in the handler.yaml `art:` block (for non-Steam games,
     e.g. Lutris titles like Belts of Iron that aren't on the Steam CDN), then
  2. the Steam CDN by `steam_appid`.

Bundled files (consumed by the app's art resolver, handler-dir-first):
  icon.jpg  <- art.icon | Steam library_600x900.jpg  (portrait cover; list icon)
  hero.jpg  <- art.hero | Steam library_hero.jpg      (wide banner; preview)
  logo.png  <- art.logo | Steam logo.png              (transparent logo overlay)

Usage:  fetch-art.py [HANDLERS_DIR ...]
Defaults to this repo's handlers/ dir. Pass extra dirs (e.g. the installed
~/.local/share/splitux/handlers) to populate them too. Idempotent; skips 404s.
"""
import os, sys, urllib.request, subprocess, shutil

try:
    import yaml
except ImportError:
    os.system("pip install --quiet pyyaml")
    import yaml

CDN = "https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/{f}"
# (output filename, art: key, [Steam CDN filenames to try in order])
# Art comes from the Steam CDN by appid (works for any game on Steam, owned or
# not — incl. Lutris-run titles). Sparse games (e.g. early access) may only have
# library_hero; later files fall back to it so no game is left art-less.
# `icon.jpg` is NOT downloaded directly — it's derived as a square crop of the
# box art (or hero) so the list shows a real square icon, not a whole cover
# squished into one cell.
SPECS = [
    ("box_art.jpg", "box_art", ["library_600x900.jpg", "header.jpg", "library_hero.jpg"]),
    ("hero.jpg", "hero", ["library_hero.jpg", "header.jpg"]),
    ("logo.png", "logo", ["logo.png"]),
]
ICON_PX = 256  # square icon edge
LIBCACHE = os.path.expanduser("~/.steam/steam/appcache/librarycache")

def steam_cache_icon(appid):
    """The real square app icon Steam stores locally (hash-named .jpg in the
    appid folder, not a library_*/header/logo/hero/capsule asset). None if the
    game isn't in this machine's Steam cache."""
    if not appid:
        return None
    d = os.path.join(LIBCACHE, str(appid))
    if not os.path.isdir(d):
        return None
    for f in sorted(os.listdir(d)):
        low = f.lower()
        if low.endswith(".jpg") and not low.startswith(
            ("library_", "header", "logo", "hero", "capsule")
        ):
            return os.path.join(d, f)
    return None

def make_icon(hdir, appid):
    """icon.jpg = the real Steam square icon if cached, else a square crop of the
    box art (so the list always shows a proper square icon, not a squished cover)."""
    dst = os.path.join(hdir, "icon.jpg")
    real = steam_cache_icon(appid)
    if real:
        shutil.copyfile(real, dst)
        return "icon.jpg(real)"
    src = next((os.path.join(hdir, c) for c in ("box_art.jpg", "hero.jpg")
                if os.path.isfile(os.path.join(hdir, c))), None)
    if not src:
        return None
    tool = shutil.which("magick") or shutil.which("convert")
    if not tool:
        shutil.copyfile(src, dst)
        return "icon.jpg(copy)"
    cmd = [tool, src, "-resize", f"{ICON_PX}x{ICON_PX}^",
           "-gravity", "center", "-extent", f"{ICON_PX}x{ICON_PX}", dst]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return "icon.jpg(crop)"
    except Exception:
        shutil.copyfile(src, dst)
        return "icon.jpg(copy)"

def save(data, dest):
    if not data or len(data) < 200:
        return False
    with open(dest, "wb") as f:
        f.write(data)
    return True

def from_url(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "splitux-art/1"})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read() if r.status == 200 else None
    except Exception:
        return None

def resolve(spec):
    """Optional per-slot override: an https URL or an absolute file path."""
    if not spec:
        return None
    if spec.startswith(("http://", "https://")):
        return from_url(spec)
    if os.path.isfile(spec):
        return open(spec, "rb").read()
    return None

def run(hdir):
    if not os.path.isdir(hdir):
        print(f"  (skip, not a dir: {hdir})"); return
    print(f"== {hdir} ==")
    for hid in sorted(os.listdir(hdir)):
        hp = os.path.join(hdir, hid, "handler.yaml")
        if not os.path.isfile(hp):
            continue
        try:
            y = yaml.safe_load(open(hp)) or {}
        except Exception as e:
            print(f"  {hid}: yaml error {e}"); continue
        # Art appid defaults to the game's steam_appid; `art_appid` overrides it
        # for the rare case the art lives under a different Steam app than the one
        # the handler emulates.
        appid = y.get("art_appid") or y.get("steam_appid")
        art = y.get("art") or {}
        got = []
        for out_name, key, cdn_files in SPECS:
            data = resolve(art.get(key))  # configured source wins (URL/lutris/path)
            if data is None and appid:     # else Steam CDN candidates in order
                for cf in cdn_files:
                    data = from_url(CDN.format(appid=appid, f=cf))
                    if data:
                        break
            if save(data, os.path.join(hdir, hid, out_name)):
                got.append(out_name)
        ic = make_icon(os.path.join(hdir, hid), appid)
        if ic:
            got.append(ic)
        print(f"  {hid}: {', '.join(got) if got else 'NONE'}")

if __name__ == "__main__":
    dirs = sys.argv[1:] or [os.path.join(os.path.dirname(__file__), "..", "handlers")]
    for d in dirs:
        run(os.path.abspath(d))
