"""
Image Pipeline — Drive folder integration
Maps artwork images from Google Drive to dataset records (by ID: MAL-001, EXT-001, etc.)
and prepares them for the exhibition server and LLM vision queries.

Usage:
  # Share your Drive folder with a service account or use gdown
  python image_pipeline.py --folder-id <GOOGLE_DRIVE_FOLDER_ID>
  python image_pipeline.py --local-dir ./images   # if already downloaded
  python image_pipeline.py --status               # show what's linked
"""

import os
import re
import json
import shutil
import argparse
import urllib.request
from pathlib import Path

BASE_DIR   = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / 'images'
INDEX_FILE = BASE_DIR / 'image_index.json'

with open(BASE_DIR / 'artworks_data.json',  encoding='utf-8') as f:
    artworks_data = json.load(f)
with open(BASE_DIR / 'parajanov_data.json', encoding='utf-8') as f:
    parajanov_data = json.load(f)

# Artwork ID patterns — structured IDs and Drive filename prefixes
# MAL-001 / EXT-001 / KAK-001 / PAG-001 / PAR-001 (dataset IDs)
# MaL###  — Malevich individual Drive files
# std###  — Stedelijk Museum Malevich files
# EXT###, KAK###, PAG###, PAR### — shorthand variants
ID_PATTERN = re.compile(
    r'(MAL|EXT|KAK|PAG|PAR)-\d{3}|'   # structured: MAL-001
    r'(MaL|std|EXT|KAK|PAG|PAR)\d+',   # prefix + number: MaL01, std03
    re.IGNORECASE
)

PREFIX_TO_ARTIST = {
    'mal': 'Malevich',
    'std': 'Malevich',
    'ext': 'Exter',
    'kak': 'Kakabadze',
    'pag': 'Pagava',
    'par': 'Parajanov',
}


def load_index() -> dict:
    if INDEX_FILE.exists():
        with open(INDEX_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_index(index: dict):
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"  Index saved: {INDEX_FILE}")


def scan_local_dir(directory: str) -> dict:
    """
    Scan a local directory for image files. Matches filenames containing artwork IDs
    (e.g. MAL-001_suprematist_teapot.jpg → links to record MAL-001).
    Returns {artwork_id: local_path}.
    """
    img_dir = Path(directory)
    if not img_dir.exists():
        print(f"  Directory not found: {img_dir}")
        return {}

    index = load_index()
    IMAGES_DIR.mkdir(exist_ok=True)

    found = 0
    for img_path in sorted(img_dir.rglob('*')):
        if img_path.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.tiff', '.tif'):
            continue
        match = ID_PATTERN.search(img_path.stem) or ID_PATTERN.search(img_path.name)
        if match:
            raw = match.group()
            # Normalise to uppercase storage key, e.g. MaL01 → MAL-01, std03 → STD-03
            prefix = re.match(r'[A-Za-z]+', raw).group().upper()
            number = re.search(r'\d+', raw)
            if '-' in raw:
                art_id = raw.upper()          # already structured: MAL-001
            elif number:
                art_id = f"{prefix}-{number.group().zfill(3)}"
            else:
                art_id = prefix

            artist = PREFIX_TO_ARTIST.get(prefix.lower(), 'Unknown')
            dest   = IMAGES_DIR / f"{art_id}{img_path.suffix.lower()}"
            shutil.copy2(img_path, dest)
            index[art_id] = {
                'local_path': str(dest),
                'source':     'local',
                'original':   str(img_path),
                '_artist':    artist,
            }
            print(f"  Linked: {art_id} ({artist}) ← {img_path.name}")
            found += 1

    save_index(index)
    print(f"\n  Total linked: {found} images")
    return index


def download_from_drive(folder_id: str) -> dict:
    """
    Download images from a Google Drive folder using gdown.
    Install: pip install gdown
    The folder should contain image files named with artwork IDs.
    """
    try:
        import gdown
    except ImportError:
        print("  gdown not installed. Run: pip install gdown")
        print(f"  Then: gdown --folder https://drive.google.com/drive/folders/{folder_id}")
        return {}

    IMAGES_DIR.mkdir(exist_ok=True)
    tmp_dir = BASE_DIR / '_drive_tmp'
    tmp_dir.mkdir(exist_ok=True)

    print(f"  Downloading from Drive folder: {folder_id}")
    try:
        gdown.download_folder(
            id=folder_id,
            output=str(tmp_dir),
            quiet=False,
            use_cookies=False,
        )
    except Exception as e:
        print(f"  Drive download failed: {e}")
        print(f"  Try: gdown --folder https://drive.google.com/drive/folders/{folder_id} -O images/")
        return {}

    return scan_local_dir(str(tmp_dir))


def build_image_manifest() -> list:
    """
    Build a manifest of all dataset records with their image status:
    local path, source URL, rights, and whether the image is ready for LLM queries.
    """
    index  = load_index()
    result = []

    for rec in artworks_data['records']:
        art_id = rec.get('ID', '')
        entry = {
            'id':         art_id,
            'artist':     rec.get('_artist', ''),
            'title':      rec.get('Title', ''),
            'institution':rec.get('Holding Institution', ''),
            'source_url': rec.get('Image: URL / File', '').split('\n')[0],
            'rights':     rec.get('Image: Rights / Licence', ''),
            'local_path': None,
            'ready_for_llm': False,
        }

        if art_id in index:
            raw_lp = index[art_id].get('local_path', '')
            lp_abs = Path(raw_lp) if Path(raw_lp).is_absolute() else BASE_DIR / raw_lp
            entry['local_path']    = str(lp_abs)
            entry['ready_for_llm'] = lp_abs.exists()
            if index[art_id].get('_artist'):
                entry['artist'] = index[art_id]['_artist']

        # Mark open-access records as ready via source URL
        rights = rec.get('Image: Rights / Licence', '').lower()
        src    = rec.get('Image: URL / File', '')
        if ('no copyright' in rights or 'cc0' in rights or 'open access' in rights) and 'http' in src:
            direct_urls = [u.strip() for u in src.split('\n') if u.strip().startswith('http')]
            if direct_urls:
                entry['direct_url']    = direct_urls[0]
                entry['ready_for_llm'] = True

        result.append(entry)

    # Also include locally-indexed images not matched by dataset ID (e.g. MaL/std Drive files)
    seen_ids = {r['id'] for r in result}
    for art_id, info in index.items():
        if art_id not in seen_ids:
            lp = info.get('local_path', '')
            # Support both relative (new) and absolute (legacy) paths
            lp_abs = Path(lp) if Path(lp).is_absolute() else BASE_DIR / lp
            result.append({
                'id':          art_id,
                'artist':      info.get('_artist', ''),
                'title':       art_id,
                'institution': 'Drive / Local',
                'source_url':  '',
                'rights':      '',
                'local_path':  str(lp_abs),
                'ready_for_llm': bool(lp and lp_abs.exists()),
            })

    return result


def show_status():
    manifest = build_image_manifest()
    index    = load_index()

    total      = len(manifest)
    ready      = sum(1 for r in manifest if r['ready_for_llm'])
    local      = len(index)
    open_access = sum(1 for r in manifest if r.get('direct_url'))

    print(f"\n  Image Status")
    print(f"  {'─'*50}")
    print(f"  Total artwork records:  {total}")
    print(f"  Ready for LLM queries: {ready}")
    print(f"    ├─ Local images:     {local}")
    print(f"    └─ Open-access URLs: {open_access}")
    print(f"  Awaiting Drive upload: {total - ready}\n")

    by_artist = {}
    for r in manifest:
        a = r['artist']
        by_artist.setdefault(a, {'total': 0, 'ready': 0})
        by_artist[a]['total'] += 1
        if r['ready_for_llm']:
            by_artist[a]['ready'] += 1

    for artist, counts in sorted(by_artist.items()):
        bar = '█' * counts['ready'] + '░' * (counts['total'] - counts['ready'])
        print(f"  {artist:12s}  [{bar}] {counts['ready']}/{counts['total']}")
    print()


def get_image_for_llm(art_id: str) -> dict:
    """
    Return the best available image reference for a given artwork ID.
    Used by the server when building LLM vision queries.
    Returns: {type: 'url'|'local', value: str} or None.
    """
    index = load_index()
    if art_id in index:
        lp = index[art_id].get('local_path')
        if lp and Path(lp).exists():
            return {'type': 'local', 'value': lp}

    manifest = build_image_manifest()
    for rec in manifest:
        if rec['id'] == art_id:
            if rec.get('direct_url'):
                return {'type': 'url', 'value': rec['direct_url']}
            if rec.get('source_url') and rec['source_url'].startswith('http'):
                return {'type': 'url', 'value': rec['source_url']}
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Image Pipeline — Misattribution Machine')
    parser.add_argument('--folder-id',  help='Google Drive folder ID')
    parser.add_argument('--local-dir',  help='Local directory of images to scan')
    parser.add_argument('--status',     action='store_true', help='Show image status')
    parser.add_argument('--manifest',   action='store_true', help='Print full manifest as JSON')
    args = parser.parse_args()

    if args.status:
        show_status()
    elif args.manifest:
        print(json.dumps(build_image_manifest(), indent=2, ensure_ascii=False))
    elif args.folder_id:
        download_from_drive(args.folder_id)
        show_status()
    elif args.local_dir:
        scan_local_dir(args.local_dir)
        show_status()
    else:
        show_status()
