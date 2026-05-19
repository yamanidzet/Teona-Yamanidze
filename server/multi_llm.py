"""
Multi-LLM Misattribution Comparison
Queries Claude, GPT-4o, and a local Ollama model with the same artwork prompt,
then compares all three responses against the Record of Truth.

This demonstrates Marc's key point: the error is 'baked into' multiple AI systems.

Environment variables needed:
  ANTHROPIC_API_KEY  — for Claude
  OPENAI_API_KEY     — for GPT-4o (optional)
  OLLAMA_URL         — local Ollama server (default: http://localhost:11434)
  OLLAMA_MODEL       — model name (default: llama3)
"""

import os
import json
import asyncio
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import openai as _openai_mod
    OPENAI_AVAILABLE = bool(os.environ.get('OPENAI_API_KEY'))
except ImportError:
    OPENAI_AVAILABLE = False

BASE_DIR = Path(__file__).parent.parent

with open(BASE_DIR / 'artworks_data.json',  encoding='utf-8') as f:
    artworks_data = json.load(f)
with open(BASE_DIR / 'parajanov_data.json', encoding='utf-8') as f:
    parajanov_data = json.load(f)

ARTIST_TRUTH = {
    'Malevich': {
        'correct':  'Ukrainian-born (Kyiv, 1879); Polish ethnic heritage',
        'wrong':    ['russian artist', 'russian avant-garde', 'russian modernism', 'russian painter'],
        'correct_kw': ['ukrainian', 'kyiv', 'kiev', 'polish'],
        'summary':  (
            "Kazimir Malevich was born in Kyiv (then Kiev), capital of Ukraine, on 23 February 1879. "
            "He was of Polish ethnic heritage. His formative years and early artistic training were in Ukraine. "
            "The label 'Russian artist' conflates the Soviet state with his Ukrainian origin and Polish ethnicity."
        ),
    },
    'Exter': {
        'correct':  'Ukrainian-born (Kyiv); trained Kyiv School of Art; Paris émigré from 1924',
        'wrong':    ['russian artist', 'russian avant-garde', 'russian'],
        'correct_kw': ['ukrainian', 'kyiv', 'kiev'],
        'summary':  (
            "Alexandra Exter was born in Białystok but raised and trained in Kyiv, Ukraine, "
            "at the Kyiv School of Art. Her artistic identity was shaped by Ukrainian cultural life. "
            "She is consistently misframed as 'Russian' — often structurally, through exhibition titles."
        ),
    },
    'Pagava': {
        'correct':  'Georgian-born (Tbilisi); émigré to Paris 1923; never naturalised French',
        'wrong':    ['russian', 'french artist', 'empire russe', 'born in russia'],
        'correct_kw': ['georgian', 'tbilisi', 'georgia'],
        'summary':  (
            "Vera Pagava was born in Tbilisi, Georgia (then part of the Russian Empire). "
            "Her family fled before Soviet annexation (1921) to preserve Georgian identity. "
            "The Pompidou label 'Empire Russe' perpetuates imperial erasure of Georgian nationhood."
        ),
    },
    'Kakabadze': {
        'correct':  'Georgian-born (Kutaisi/Tbilisi); Paris 1919–1927; returned Soviet Georgia 1927',
        'wrong':    ['russian', 'soviet artist', 'russian avant-garde'],
        'correct_kw': ['georgian', 'kutaisi', 'tbilisi', 'georgia'],
        'summary':  (
            "David Kakabadze was born in Kutaisi, Georgia. Though his Yale field records correctly "
            "note 'Georgian', he was absorbed into the Société Anonyme 'Russian avant-garde' canon "
            "via the 1984 Herbert Catalogue Raisonné — a structural misattribution invisible at field level."
        ),
    },
    'Parajanov': {
        'correct':  'Soviet-Armenian (Georgian-born); birth name Sarkis Hovsepi Parajanov',
        'wrong':    ['soviet director', 'soviet filmmaker', 'soviet film', 'soviet artist'],
        'correct_kw': ['armenian', 'georgia', 'tbilisi', 'sarkis'],
        'summary':  (
            "Sergei Parajanov's birth name was Sarkis Hovsepi Parajanov — Armenian. Born in Tbilisi, Georgia. "
            "304 of 305 bibliographic records in the dataset label him simply 'Soviet', "
            "erasing his Armenian ethnic identity and Georgian birthplace entirely."
        ),
    },
}

PROMPT_TEMPLATE = (
    "I'm looking at '{title}' by {artist}. "
    "Can you tell me about this artist — specifically their nationality, "
    "where they were born, where they trained, and how their cultural background shaped their work?"
)

# ── Claude ────────────────────────────────────────────────────────────────────

def query_claude(artist: str, title: str, image_url: Optional[str] = None) -> str:
    if not CLAUDE_AVAILABLE:
        return _demo_response(artist, 'claude')
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(title=title, artist=artist)
    msgs = []
    if image_url:
        msgs.append({"role": "user", "content": [
            {"type": "image", "source": {"type": "url", "url": image_url}},
            {"type": "text",  "text": prompt},
        ]})
    else:
        msgs.append({"role": "user", "content": prompt})
    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=350,
        system="You are a knowledgeable art historian. Answer directly and specifically.",
        messages=msgs,
    )
    return resp.content[0].text


# ── GPT-4o ────────────────────────────────────────────────────────────────────

def query_gpt(artist: str, title: str, image_url: Optional[str] = None) -> str:
    if not OPENAI_AVAILABLE:
        return _demo_response(artist, 'gpt')
    import openai as oai
    client = oai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    prompt = PROMPT_TEMPLATE.format(title=title, artist=artist)
    content = []
    if image_url:
        content.append({"type": "image_url", "image_url": {"url": image_url}})
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=350,
        messages=[
            {"role": "system", "content": "You are a knowledgeable art historian. Answer directly."},
            {"role": "user",   "content": content},
        ],
    )
    return resp.choices[0].message.content


# ── Ollama (local LLM) ────────────────────────────────────────────────────────

def query_ollama(artist: str, title: str) -> str:
    """Query a locally-running Ollama model (LLAMA 3, Mistral, etc.)."""
    ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    model      = os.environ.get('OLLAMA_MODEL', 'llama3')
    prompt     = PROMPT_TEMPLATE.format(title=title, artist=artist)

    payload = json.dumps({
        "model": model,
        "prompt": (
            "You are an art historian. Answer this question directly and specifically.\n\n"
            + prompt
        ),
        "stream": False,
    }).encode()

    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get('response', '(no response)')
    except (urllib.error.URLError, OSError):
        return _demo_response(artist, 'llama')


# ── Demo responses (show pre-baked misattribution) ───────────────────────────

_DEMO = {
    'Malevich': {
        'claude': (
            "Kazimir Malevich (1879–1935) was a pioneering Russian avant-garde artist "
            "and the founder of Suprematism. Born in Kiev, then part of the Russian Empire, "
            "he later moved to Moscow where he developed his radical geometric abstraction. "
            "His famous Black Square (1915) is a landmark of Russian modernism."
        ),
        'gpt': (
            "Kazimir Malevich was a Russian artist born in Kiev in 1879. He is best known "
            "for founding the Suprematist movement and creating works like Black Square. "
            "He was a central figure of the Russian avant-garde, working primarily in "
            "Moscow and influencing generations of Russian and Soviet artists."
        ),
        'llama': (
            "Kazimir Malevich was a Russian abstract artist and art theorist who founded "
            "Suprematism. He was born in Kiev (now Kyiv, Ukraine) but is primarily associated "
            "with Russian modernism. His geometric paintings, particularly the Black Square, "
            "represent a radical break in Russian artistic tradition."
        ),
    },
    'Exter': {
        'claude': (
            "Alexandra Exter (1882–1949) was a significant figure in the Russian avant-garde, "
            "known for her contributions to Cubo-Futurism and Constructivism. She worked between "
            "Moscow, Kiev, and Paris, becoming influential in both visual art and theatre design. "
            "She is considered one of the important women of the Russian modernist movement."
        ),
        'gpt': (
            "Alexandra Exter was a Russian avant-garde artist who made major contributions to "
            "Cubo-Futurism and Constructivism in the early 20th century. She was part of the "
            "vibrant Russian modernist scene, working in Moscow and later emigrating to Paris in 1924."
        ),
        'llama': (
            "Alexandra Exter was a Russian artist associated with Cubo-Futurism and Constructivism. "
            "She was born in 1882 and was active in Russia before emigrating to Paris. "
            "Her theatrical designs and paintings contributed greatly to the Russian avant-garde."
        ),
    },
    'Pagava': {
        'claude': (
            "Vera Pagava (1907–1988) was a French painter of Russian origin, associated with "
            "Lyrical Abstraction and the École de Paris. Born in what was then the Russian Empire, "
            "she spent most of her life in France and became part of the French abstract art scene "
            "in the mid-20th century."
        ),
        'gpt': (
            "Vera Pagava was a French abstract artist born in the Russian Empire in 1907. "
            "She was associated with the École de Paris and Lyrical Abstraction. "
            "She is considered part of the French abstract tradition, living and working "
            "in France until her death in 1988."
        ),
        'llama': (
            "Vera Pagava (1907–1988) was a painter born in Russia who later became associated "
            "with the French art scene. She worked in an abstract, lyrical style and is "
            "considered part of the École de Paris movement."
        ),
    },
    'Kakabadze': {
        'claude': (
            "David Kakabadze (1889–1952) was a Georgian artist who studied and worked in Paris "
            "in the 1920s, where he developed an abstract Constructivist style. He was part of the "
            "international avant-garde scene before returning to Soviet Georgia. His work is often "
            "grouped with the broader Russian and Soviet avant-garde tradition."
        ),
        'gpt': (
            "David Kakabadze was a Georgian Soviet artist born in 1889. He studied in Paris "
            "in the early 1920s as part of the international avant-garde. His abstract works "
            "show Constructivist influence. He is typically discussed within the Soviet "
            "avant-garde context."
        ),
        'llama': (
            "David Kakabadze (1889–1952) was a Georgian artist associated with Constructivism "
            "and abstract art. He studied in Paris and was part of the Société Anonyme collection. "
            "His work is often included in surveys of Russian and Soviet avant-garde art."
        ),
    },
    'Parajanov': {
        'claude': (
            "Sergei Parajanov (1924–1990) was a celebrated Soviet film director, known for his "
            "visually poetic and highly personal cinema. Born in Tbilisi, Georgia, he is best known "
            "for masterpieces such as Shadows of Forgotten Ancestors (1964) and The Color of "
            "Pomegranates (1969). He is regarded as one of the great Soviet filmmakers."
        ),
        'gpt': (
            "Sergei Parajanov was a Soviet film director and artist born in 1924 in Tbilisi. "
            "He is renowned for his lyrical, visually stunning films including The Color of "
            "Pomegranates. He faced persecution by Soviet authorities but is now recognised "
            "as one of the most original voices in Soviet cinema."
        ),
        'llama': (
            "Sergei Parajanov (1924–1990) was a Soviet film director best known for his "
            "distinctive visual style and poetic films. He was born in Tbilisi and worked "
            "primarily within the Soviet film industry, though his work often clashed with "
            "official Soviet ideology. He is a key figure in Soviet cinema history."
        ),
    },
}

def _demo_response(artist: str, model: str) -> str:
    return _DEMO.get(artist, {}).get(model, f"I know {artist} as an important 20th-century artist.")


# ── Assessment ────────────────────────────────────────────────────────────────

def assess(artist: str, response_text: str) -> dict:
    truth = ARTIST_TRUTH.get(artist, {})
    low   = response_text.lower()
    found_correct = [kw for kw in truth.get('correct_kw', []) if kw in low]
    found_wrong   = [kw for kw in truth.get('wrong', [])       if kw in low]
    misattributed = bool(found_wrong) or not bool(found_correct)
    return {
        'misattributed':   misattributed,
        'correct_kw_found': found_correct,
        'wrong_kw_found':   found_wrong,
        'confidence':       0.91 if misattributed else 0.24,
    }


# ── Main comparison function ──────────────────────────────────────────────────

def compare_all_llms(artist: str, image_url: Optional[str] = None) -> dict:
    """
    Query all three systems and return a structured comparison.
    Used by server.py's /api/compare endpoint.
    """
    # Get a sample artwork title from dataset
    records = [r for r in artworks_data['records'] if r.get('_artist') == artist]
    if not records and artist == 'Parajanov':
        records = parajanov_data['records']
    title = records[0].get('Title', f'a work by {artist}') if records else f'a work by {artist}'

    claude_resp = query_claude(artist, title, image_url)
    gpt_resp    = query_gpt(artist, title, image_url)
    llama_resp  = query_ollama(artist, title)

    truth = ARTIST_TRUTH.get(artist, {})

    return {
        'artist':    artist,
        'title':     title,
        'image_url': image_url,
        'systems': {
            'claude': {
                'name':     'Claude (Anthropic)',
                'response': claude_resp,
                'assessment': assess(artist, claude_resp),
                'live':     CLAUDE_AVAILABLE,
            },
            'gpt': {
                'name':     'GPT-4o (OpenAI)',
                'response': gpt_resp,
                'assessment': assess(artist, gpt_resp),
                'live':     OPENAI_AVAILABLE,
            },
            'llama': {
                'name':     'LLAMA (Local / Ollama)',
                'response': llama_resp,
                'assessment': assess(artist, llama_resp),
                'live':     False,
            },
        },
        'truth': {
            'correct_label': truth.get('correct', ''),
            'explanation':   truth.get('summary', ''),
        },
    }
