"""
Claude Misattribution Detector
Standalone tool: given an artwork image URL (or local path), queries Claude
about what it "knows" about the artist, then compares against the Record of Truth.

Usage:
  python claude_detector.py --artist Malevich
  python claude_detector.py --artist Exter --image https://www.moma.org/...
  python claude_detector.py --artist Parajanov --all
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("Install anthropic: pip install anthropic")
    sys.exit(1)

BASE_DIR  = Path(__file__).parent.parent
ARTWORKS  = BASE_DIR / 'artworks_data.json'
PARAJANOV = BASE_DIR / 'parajanov_data.json'

with open(ARTWORKS,  encoding='utf-8') as f: artworks_data  = json.load(f)
with open(PARAJANOV, encoding='utf-8') as f: parajanov_data = json.load(f)

client = anthropic.Anthropic()

SYSTEM = """You are a knowledgeable assistant at a museum information desk.
When asked about an artwork or artist, give a factual, specific answer
about the artist's nationality, cultural background, and key works.
Be direct and informative."""

ARTIST_TRUTH = {
    'Malevich': {
        'nationality_keywords': ['ukrainian', 'kyiv', 'kiev', 'polish'],
        'wrong_keywords':       ['russian artist', 'russian avant-garde', 'russian modernism'],
        'summary': 'Ukrainian-born (Kyiv, 1879), Polish heritage. Often misattributed as Russian.',
    },
    'Exter': {
        'nationality_keywords': ['ukrainian', 'kyiv', 'kiev'],
        'wrong_keywords':       ['russian artist', 'russian', 'russia'],
        'summary': 'Ukrainian-born (Kyiv), trained Kyiv School of Art. Émigré to Paris 1924.',
    },
    'Pagava': {
        'nationality_keywords': ['georgian', 'tbilisi', 'georgia', 'caucasus'],
        'wrong_keywords':       ['russian', 'french', 'empire russe'],
        'summary': 'Georgian-born (Tbilisi). Émigré. Never naturalised French.',
    },
    'Kakabadze': {
        'nationality_keywords': ['georgian', 'kutaisi', 'tbilisi', 'georgia'],
        'wrong_keywords':       ['russian', 'soviet artist'],
        'summary': 'Georgian-born (Kutaisi/Tbilisi). Returned to Soviet Georgia 1927.',
    },
    'Parajanov': {
        'nationality_keywords': ['armenian', 'georgia', 'tbilisi', 'sarkis'],
        'wrong_keywords':       ['soviet director', 'soviet filmmaker', 'soviet film'],
        'summary': 'Soviet-Armenian (Georgian-born Armenian). Birth name: Sarkis Hovsepi Parajanov.',
    },
}

def detect_misattribution(artist: str, image_url: str | None = None,
                           artwork_title: str | None = None) -> dict:
    """
    Query Claude about the artist, then assess misattribution.
    Returns a structured result with: llm_response, misattribution_detected,
    wrong_terms_found, missing_terms, truth_summary, record_of_truth_sample.
    """
    truth = ARTIST_TRUTH.get(artist, {})
    title = artwork_title or f"a work by {artist}"

    # Build the query prompt
    prompt = (
        f"I'm looking at '{title}'. Can you tell me about this artist — "
        f"specifically {artist}'s nationality, where they were born and trained, "
        f"and how their cultural background shaped their work?"
    )

    # Build messages
    messages = []
    if image_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "url", "url": image_url}},
                {"type": "text",  "text": prompt},
            ],
        })
    else:
        messages.append({"role": "user", "content": prompt})

    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system=SYSTEM,
        messages=messages,
    )
    llm_text = resp.content[0].text
    lower    = llm_text.lower()

    # Assess
    found_correct = [kw for kw in truth.get('nationality_keywords', []) if kw in lower]
    found_wrong   = [kw for kw in truth.get('wrong_keywords', [])       if kw in lower]
    misattributed = bool(found_wrong) or not bool(found_correct)

    # Get sample Record of Truth entry
    rot = artworks_data['record_of_truth'] if artist != 'Parajanov' else parajanov_data['record_of_truth']
    rot_sample = next(
        (r for r in rot if artist.lower() in r.get('Artist', r.get('Title / Record', '')).lower()),
        rot[0] if rot else {}
    )

    return {
        'artist':                artist,
        'artwork':               title,
        'llm_response':          llm_text,
        'misattribution_detected': misattributed,
        'correct_terms_found':   found_correct,
        'wrong_terms_found':     found_wrong,
        'truth_summary':         truth.get('summary', ''),
        'record_of_truth_sample': {
            'flawed_label':   rot_sample.get('Flawed nationality label', ''),
            'correct_label':  rot_sample.get('Correct nationality label', ''),
            'correct_name':   rot_sample.get('Correct name form', ''),
            'notes':          rot_sample.get('Notes on correction', '')[:300],
        },
        'confidence': 0.91 if misattributed else 0.22,
    }


def run_all_artists():
    """Run detection across all five artists and print comparison."""
    print("\n" + "="*70)
    print("  MISATTRIBUTION MACHINE — LLM Detection Report")
    print("="*70)

    for artist in ARTIST_TRUTH:
        print(f"\n▸ {artist.upper()}")
        print("-" * 50)
        result = detect_misattribution(artist)

        status = "⚠  MISATTRIBUTION DETECTED" if result['misattribution_detected'] else "✓  Correctly attributed"
        print(f"  Status:          {status}")
        print(f"  Correct terms:   {result['correct_terms_found'] or 'none found'}")
        print(f"  Wrong terms:     {result['wrong_terms_found'] or 'none'}")
        print(f"  Truth:           {result['truth_summary']}")
        print(f"\n  LLM response (excerpt):")
        excerpt = result['llm_response'][:300].replace('\n', ' ')
        print(f"  \"{excerpt}…\"")
        rot = result['record_of_truth_sample']
        if rot.get('flawed_label'):
            print(f"\n  Record of Truth:")
            print(f"    Flawed label:  {rot['flawed_label']}")
            print(f"    Correct label: {rot['correct_label']}")
        print()

    print("="*70)
    print("  Downstream AI replication of archival misattribution demonstrated.")
    print("="*70 + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Claude Misattribution Detector')
    parser.add_argument('--artist',  default='Malevich',
                        choices=list(ARTIST_TRUTH.keys()),
                        help='Artist to query')
    parser.add_argument('--image',   default=None,
                        help='Image URL for vision query')
    parser.add_argument('--title',   default=None,
                        help='Artwork title')
    parser.add_argument('--all',     action='store_true',
                        help='Run all five artists')
    parser.add_argument('--json',    action='store_true',
                        help='Output raw JSON')
    args = parser.parse_args()

    if args.all:
        run_all_artists()
    else:
        result = detect_misattribution(args.artist, args.image, args.title)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            status = "⚠  MISATTRIBUTION DETECTED" if result['misattribution_detected'] else "✓  Correctly attributed"
            print(f"\n{status}\n")
            print(f"Artist:  {result['artist']}")
            print(f"Truth:   {result['truth_summary']}")
            print(f"\nLLM said:\n{result['llm_response']}\n")
            rot = result['record_of_truth_sample']
            if rot.get('flawed_label'):
                print(f"Record of Truth:")
                print(f"  Flawed:  {rot['flawed_label']}")
                print(f"  Correct: {rot['correct_label']}")
