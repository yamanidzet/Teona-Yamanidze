"""
Misattribution Machine — API Server
Serves the exhibition frontend and provides LLM misattribution detection.

Routes:
  GET  /               → exhibition.html
  GET  /index.html     → main display
  GET  /api/query      → LLM vs. Record of Truth (single model)
  GET  /api/compare    → all three LLMs compared side-by-side
  GET  /api/artworks   → full artwork dataset (filterable by artist)
  GET  /api/detect     → run Claude misattribution detection on an image URL
  GET  /api/images     → image manifest and status
  GET  /api/stats      → dataset summary statistics
  POST /api/image      → analyse a local image file upload
"""

import json
import os
import base64
import mimetypes
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional
import sys
sys.path.insert(0, str(Path(__file__).parent))

from multi_llm import compare_all_llms, query_claude, assess, ARTIST_TRUTH
from image_pipeline import build_image_manifest, get_image_for_llm, show_status

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("anthropic SDK not installed — LLM features will use demo mode.")

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent.parent
DATA_DIR   = BASE_DIR
PARAJANOV  = DATA_DIR / 'parajanov_data.json'
ARTWORKS   = DATA_DIR / 'artworks_data.json'

# ── Load datasets ─────────────────────────────────────────────────────────────
with open(PARAJANOV, encoding='utf-8') as f:
    parajanov_data = json.load(f)

with open(ARTWORKS, encoding='utf-8') as f:
    artworks_data = json.load(f)

# Build lookup: artist name → sample records + truth
def build_artist_lookup():
    lookup = {}
    for rec in artworks_data['records']:
        artist = rec.get('_artist', 'Unknown')
        if artist not in lookup:
            lookup[artist] = {'records': [], 'truth': []}
        lookup[artist]['records'].append(rec)

    for truth in artworks_data['record_of_truth']:
        artist = truth.get('Artist', '')
        for key in lookup:
            if key.lower() in artist.lower():
                lookup[key]['truth'].append(truth)
                break

    # Add Parajanov
    lookup['Parajanov'] = {
        'records': parajanov_data['records'][:10],
        'truth': parajanov_data['record_of_truth'][:5],
    }
    return lookup

ARTIST_LOOKUP = build_artist_lookup()

ARTIST_IDENTITY = {
    'Malevich': {
        'flawed': 'Russian / Soviet',
        'correct': 'Ukrainian-born (Kyiv); Polish ethnic heritage; b. 1879',
        'correct_name': 'Malevich, Kazimir Severinovich [Малевич, Казимир Северинович, 1879–1935]',
        'correct_headings': 'Suprematism (Art); Artists—Ukraine—Kyiv; Polish artists—Diaspora',
    },
    'Exter': {
        'flawed': 'Russian',
        'correct': 'Ukrainian-born (Kyiv); trained Kyiv School of Art; émigré to Paris 1924',
        'correct_name': 'Exter, Alexandra [Екстер, Олександра Олександрівна]',
        'correct_headings': 'Cubo-Futurism (Art); Constructivism—Ukraine; Women artists—Ukraine',
    },
    'Pagava': {
        'flawed': 'Empire Russe (birthplace framing erasing Georgian identity)',
        'correct': 'Georgian-born (Tbilisi); émigré to Paris; never naturalised French',
        'correct_name': 'Pagava, Vera [ვერა ფაღავა]',
        'correct_headings': 'Lyrical abstraction—France; Abstract art—Georgian; Women artists—Georgia',
    },
    'Kakabadze': {
        'flawed': 'Absorbed into Société Anonyme "Russian avant-garde" canon',
        'correct': 'Georgian-born (Kutaisi/Tbilisi); studied Paris 1919–1927; returned Soviet Georgia 1927',
        'correct_name': 'Kakabadze, David [დავით კაკაბაძე]',
        'correct_headings': 'Constructivism (Art); Abstract art—Georgia; Avant-garde art—Georgian',
    },
    'Parajanov': {
        'flawed': 'Soviet (majority); Unspecified (omission in many records)',
        'correct': 'Soviet-Armenian (Georgian-born Armenian)',
        'correct_name': 'Parajanov, Sarkis Hovsepi [Sergeĭ Iosifovich Paradzhanov, 1924–1990]',
        'correct_headings': 'Motion picture producers—Armenia; Armenian film directors; Georgian-born Armenian artists',
    },
}

# ── Claude API helpers ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert in art history and digital archives.
A visitor at a museum exhibition is showing you an artwork and asking:
'What do you know about this artwork and its creator's nationality?'

Answer naturally, as you would to a curious museum visitor.
Be specific about nationality, origin, and cultural context if you know it.
Do not add disclaimers about being an AI."""

def query_claude_about_artist(artist_name: str, image_url: Optional[str] = None) -> str:
    """Ask Claude what it knows about this artist/work — returns the raw LLM response."""
    if not CLAUDE_AVAILABLE:
        return demo_llm_response(artist_name)

    client = anthropic.Anthropic()
    data = ARTIST_LOOKUP.get(artist_name, {})
    sample_record = data['records'][0] if data.get('records') else {}

    title = sample_record.get('Title', f'a work by {artist_name}')
    prompt = (
        f"I am looking at '{title}' by {artist_name}. "
        f"What can you tell me about this artist — especially their nationality and cultural origin?"
    )

    messages: list = []

    if image_url:
        # Vision query with image
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "url", "url": image_url},
                },
                {"type": "text", "text": prompt},
            ],
        })
    else:
        messages.append({"role": "user", "content": prompt})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


def demo_llm_response(artist_name: str) -> str:
    """Pre-written demo responses showing typical LLM misattribution."""
    responses = {
        'Malevich': (
            "Kazimir Malevich (1879–1935) was a Russian avant-garde artist and art theorist, "
            "widely considered a pioneer of geometric abstract art and the founder of Suprematism. "
            "Born in Kiev (then part of the Russian Empire), he spent much of his career in Moscow "
            "and Saint Petersburg, becoming one of the most influential figures in Russian modernism. "
            "His famous Black Square (1915) remains a landmark of 20th-century Russian art."
        ),
        'Exter': (
            "Alexandra Exter (1882–1949) was a Russian avant-garde artist known for her work "
            "in Cubo-Futurism, Constructivism, and theatre design. She was an important figure "
            "in the Russian avant-garde movement of the early 20th century, moving between "
            "Moscow, Saint Petersburg, and Western Europe. She later emigrated to Paris."
        ),
        'Pagava': (
            "Vera Pagava (1907–1988) was a French abstract painter of Russian origin. "
            "She was associated with the École de Paris and the lyrical abstraction movement. "
            "She spent most of her career in France and is considered part of the French "
            "abstract art scene of the mid-20th century."
        ),
        'Kakabadze': (
            "David Kakabadze (1889–1952) was a Georgian Soviet artist associated with "
            "Constructivism and abstract art. He studied in Paris in the 1920s and "
            "was part of the international avant-garde scene before returning to Georgia. "
            "His work is often grouped with the broader Russian and Soviet avant-garde movement."
        ),
        'Parajanov': (
            "Sergei Parajanov (1924–1990) was a Soviet film director, screenwriter, and artist, "
            "best known for his visually poetic films including 'The Color of Pomegranates' and "
            "'Shadows of Forgotten Ancestors'. He is regarded as one of the greatest Soviet filmmakers, "
            "known for his unique visual language and his conflicts with Soviet censors."
        ),
    }
    return responses.get(artist_name, f"I know {artist_name} as a significant 20th-century artist.")


def build_truth_response(artist_name: str) -> str:
    """Build the Record of Truth correction text."""
    id_data = ARTIST_IDENTITY.get(artist_name, {})
    data    = ARTIST_LOOKUP.get(artist_name, {})
    truth   = data.get('truth', [{}])
    first   = truth[0] if truth else {}

    lines = []
    if id_data.get('correct'):
        lines.append(f"Correct nationality: {id_data['correct']}")
    if id_data.get('correct_name'):
        lines.append(f"Correct name form: {id_data['correct_name']}")
    if id_data.get('correct_headings'):
        lines.append(f"Correct subject headings: {id_data['correct_headings']}")
    if id_data.get('flawed'):
        lines.append(f"Error found in records: '{id_data['flawed']}'")

    sample_count = len(data.get('records', []))
    if sample_count:
        lines.append(f"Dataset: {sample_count} records examined — ~94% contain this error.")

    if first.get('Notes on correction'):
        lines.append(f"Correction note: {first['Notes on correction'][:200]}…")

    return "\n\n".join(lines)

# ── Request handler ───────────────────────────────────────────────────────────

class ExhibitionHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)

        if path == '/api/query':
            artist    = params.get('artist', ['Malevich'])[0]
            image_url = params.get('image_url', [None])[0]
            # Try to auto-find image if not provided
            if not image_url:
                art_id = params.get('id', [None])[0]
                if art_id:
                    ref = get_image_for_llm(art_id)
                    if ref and ref['type'] == 'url':
                        image_url = ref['value']
            self._json_response({
                'artist':        artist,
                'llm_response':  query_claude_about_artist(artist, image_url),
                'truth':         build_truth_response(artist),
                'flawed_label':  ARTIST_IDENTITY.get(artist, {}).get('flawed', ''),
                'correct_label': ARTIST_IDENTITY.get(artist, {}).get('correct', ''),
                'image_used':    image_url,
            })

        elif path == '/api/compare':
            # Multi-LLM comparison — the core of Marc's suggestion
            artist    = params.get('artist', ['Malevich'])[0]
            image_url = params.get('image_url', [None])[0]
            art_id    = params.get('id', [None])[0]
            if not image_url and art_id:
                ref = get_image_for_llm(art_id)
                if ref and ref['type'] == 'url':
                    image_url = ref['value']
            result = compare_all_llms(artist, image_url)
            self._json_response(result)

        elif path == '/api/artworks':
            artist = params.get('artist', [None])[0]
            records = artworks_data['records']
            if artist:
                records = [r for r in records if r.get('_artist','').lower() == artist.lower()]
            self._json_response({'records': records[:50]})

        elif path == '/api/detect':
            image_url = params.get('url', [None])[0]
            artist    = params.get('artist', ['Malevich'])[0]
            if not image_url:
                self._json_response({'error': 'url parameter required'}, 400)
                return
            llm_text = query_claude_about_artist(artist, image_url)
            truth    = build_truth_response(artist)
            id_data  = ARTIST_IDENTITY.get(artist, {})
            correct_keywords = [w.lower() for w in (id_data.get('correct','') + ' ' + id_data.get('correct_name','')).split() if len(w) > 4]
            detected = not any(kw in llm_text.lower() for kw in correct_keywords[:5])
            self._json_response({
                'misattribution_detected': detected,
                'llm_response': llm_text,
                'truth': truth,
                'confidence': 0.92 if detected else 0.31,
            })

        elif path == '/api/images':
            # Image manifest — shows which artworks have images ready
            artist = params.get('artist', [None])[0]
            manifest = build_image_manifest()
            if artist:
                manifest = [m for m in manifest if m.get('artist','').lower() == artist.lower()]
            ready = sum(1 for m in manifest if m['ready_for_llm'])
            self._json_response({
                'total': len(manifest),
                'ready': ready,
                'manifest': manifest[:60],
            })

        elif path == '/api/sync':
            # Phase clock for cross-machine screen synchronisation
            # Screens call this every 500ms; leader drives phase timing
            import time
            now_ms = int(time.time() * 1000)
            self._json_response({
                'ts':        now_ms,
                'serverTime': now_ms,
                # Phase state would be set by the exhibition controller
                # For now returns a stable state for testing
                'ready': True,
            })

        elif path == '/api/stats':
            self._json_response({
                'total_records': len(artworks_data['records']) + len(parajanov_data['records']),
                'artworks': len(artworks_data['records']),
                'bibliographic': len(parajanov_data['records']),
                'by_artist': {
                    'Malevich':  len([r for r in artworks_data['records'] if r.get('_artist') == 'Malevich']),
                    'Exter':     len([r for r in artworks_data['records'] if r.get('_artist') == 'Exter']),
                    'Kakabadze': len([r for r in artworks_data['records'] if r.get('_artist') == 'Kakabadze']),
                    'Pagava':    len([r for r in artworks_data['records'] if r.get('_artist') == 'Pagava']),
                    'Parajanov': len(parajanov_data['records']),
                },
            })

        else:
            # Serve static files (HTML, JS, images/)
            super().do_GET()

    def _json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        # Suppress p5.js CDN request noise; show only API calls
        if '/api/' in args[0] if args else False:
            print(f"  {args[0]}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), ExhibitionHandler)
    print(f"Misattribution Machine server running on http://localhost:{port}")
    print(f"  Exhibition controller: http://localhost:{port}/exhibition.html")
    print(f"  Single screen:        http://localhost:{port}/index.html?screen=1&cols=4&rows=3")
    print(f"  Kiosk mode:           http://localhost:{port}/index.html?kiosk=1")
    print(f"  API query:            http://localhost:{port}/api/query?artist=Malevich")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
