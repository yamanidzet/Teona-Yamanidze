#!/usr/bin/env python3
"""
Generate Technical_Implementation.pdf for the Misattribution Machine project.
Uses ReportLab Platypus with A4 page size, 2cm margins.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Preformatted
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY        = HexColor('#1a2744')
CODE_BG     = HexColor('#f5f5f5')
WHITE       = colors.white
BLACK       = colors.black
MID_GREY    = HexColor('#555555')
LIGHT_GREY  = HexColor('#cccccc')
RULE_GREY   = HexColor('#dddddd')

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ── Custom DocTemplate with footer ───────────────────────────────────────────
class TechnicalDoc(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        frame = Frame(
            MARGIN, MARGIN + 1 * cm,
            PAGE_W - 2 * MARGIN,
            PAGE_H - 2 * MARGIN - 1.5 * cm,
            id='main'
        )
        template = PageTemplate(id='main', frames=[frame],
                                onPage=self._draw_footer)
        self.addPageTemplates([template])

    @staticmethod
    def _draw_footer(canvas, doc):
        canvas.saveState()
        y = MARGIN - 0.2 * cm
        # rule
        canvas.setStrokeColor(RULE_GREY)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, y + 0.6 * cm, PAGE_W - MARGIN, y + 0.6 * cm)
        # left label
        canvas.setFont('Helvetica', 7.5)
        canvas.setFillColor(MID_GREY)
        canvas.drawString(MARGIN, y + 0.15 * cm,
                          'Misattribution Machine — Technical Implementation')
        # right: page number
        canvas.drawRightString(PAGE_W - MARGIN, y + 0.15 * cm,
                               f'Page {doc.page}')
        canvas.restoreState()


# ── Style factory ─────────────────────────────────────────────────────────────
def make_styles():
    styles = {}

    styles['title'] = ParagraphStyle(
        'title',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        textColor=NAVY,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    styles['subtitle'] = ParagraphStyle(
        'subtitle',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=MID_GREY,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    styles['date'] = ParagraphStyle(
        'date',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=MID_GREY,
        spaceAfter=0,
        alignment=TA_LEFT,
    )
    styles['section'] = ParagraphStyle(
        'section',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=NAVY,
        spaceBefore=18,
        spaceAfter=6,
    )
    styles['body'] = ParagraphStyle(
        'body',
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=BLACK,
        spaceAfter=6,
    )
    styles['body_small'] = ParagraphStyle(
        'body_small',
        fontName='Helvetica',
        fontSize=8.5,
        leading=13,
        textColor=BLACK,
        spaceAfter=4,
    )
    styles['code_label'] = ParagraphStyle(
        'code_label',
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=MID_GREY,
        spaceBefore=8,
        spaceAfter=2,
    )
    styles['bullet'] = ParagraphStyle(
        'bullet',
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=BLACK,
        leftIndent=14,
        spaceAfter=3,
        bulletFontName='Helvetica',
        bulletFontSize=9,
        bulletIndent=4,
    )
    return styles


# ── Code block helper ─────────────────────────────────────────────────────────
def code_block(text, styles, label=None):
    """Return a list of flowables: optional label + shaded preformatted block."""
    items = []
    if label:
        items.append(Paragraph(label, styles['code_label']))

    # Clean up leading/trailing blank lines while preserving internal indent
    lines = text.split('\n')
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    cleaned = '\n'.join(lines)

    pre = Preformatted(cleaned, ParagraphStyle(
        'code',
        fontName='Courier',
        fontSize=7.5,
        leading=11.5,
        textColor=HexColor('#1a1a1a'),
        leftIndent=8,
        rightIndent=8,
        spaceBefore=0,
        spaceAfter=0,
        backColor=CODE_BG,
    ))

    # Wrap in a table to get background + border
    tbl = Table([[pre]], colWidths=[PAGE_W - 2 * MARGIN])
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('BOX',        (0, 0), (-1, -1), 0.5, LIGHT_GREY),
        ('TOPPADDING',    (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
    ]))
    items.append(tbl)
    items.append(Spacer(1, 6))
    return items


# ── Table helper ──────────────────────────────────────────────────────────────
def data_table(header_row, data_rows, col_widths):
    """Build a styled table with navy header row."""
    all_rows = [header_row] + data_rows
    tbl = Table(all_rows, colWidths=col_widths)
    style = TableStyle([
        # Header
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING',    (0, 0), (-1, 0), 6),
        # Body rows
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('TOPPADDING',    (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 7),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, HexColor('#f7f8fa')]),
        ('GRID',          (0, 0), (-1, -1), 0.5, LIGHT_GREY),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ])
    tbl.setStyle(style)
    return tbl


# ── Build story ───────────────────────────────────────────────────────────────
def build_story(styles):
    story = []
    SP = Spacer(1, 8)

    # ── Title block ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph('Misattribution Machine', styles['title']))
    story.append(Paragraph('Technical Implementation', styles['title']))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Code Reference &amp; System Architecture', styles['subtitle']))
    story.append(Paragraph('May 2026', styles['date']))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', thickness=1.5,
                             color=NAVY, spaceAfter=16))

    # ── STEP 1 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 1 — DATA PROCESSING PIPELINE', styles['section']))
    story.append(Paragraph(
        'Two Excel datasets were converted to JSON using openpyxl. The processing script '
        'reads each sheet, normalises column headers, strips whitespace, infers the artist '
        'from the filename, and outputs structured JSON.',
        styles['body']))

    story.append(Paragraph('<b>Output files:</b>', styles['body']))
    story.append(Paragraph('&#x2022;&nbsp; artworks_data.json — 354 records (Malevich, Exter, Pagava, Kakabadze)',
                           styles['bullet']))
    story.append(Paragraph('&#x2022;&nbsp; parajanov_data.json — 305 bibliographic records',
                           styles['bullet']))

    story.append(SP)
    story.append(Paragraph(
        'Each record contains: ID, Title, Artist, Holding Institution, Flawed nationality label, '
        'Correct nationality label, Correct name form, Notes on correction, Image URL, Rights.',
        styles['body']))

    # ── STEP 2 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 2 — ARTIST TRUTH TABLE (multi_llm.py)', styles['section']))

    artist_truth_code = """\
ARTIST_TRUTH = {
    'Malevich': {
        'correct':    'Ukrainian-born (Kyiv, 1879); Polish ethnic heritage',
        'wrong':      ['russian artist', 'russian avant-garde',
                       'russian modernism', 'russian painter'],
        'correct_kw': ['ukrainian', 'kyiv', 'kiev', 'polish'],
        'summary':    (
            "Kazimir Malevich was born in Kyiv (then Kiev), capital of Ukraine, "
            "on 23 February 1879. He was of Polish ethnic heritage. The label "
            "'Russian artist' conflates the Soviet state with his Ukrainian origin."
        ),
    },
    'Exter': {
        'correct':    'Ukrainian-born (Kyiv); trained Kyiv School of Art',
        'wrong':      ['russian artist', 'russian avant-garde', 'russian'],
        'correct_kw': ['ukrainian', 'kyiv', 'kiev'],
    },
    'Pagava': {
        'correct':    'Georgian-born (Tbilisi); emigre to Paris 1923',
        'wrong':      ['russian', 'french artist', 'empire russe'],
        'correct_kw': ['georgian', 'tbilisi', 'georgia'],
    },
    'Kakabadze': {
        'correct':    'Georgian-born (Kutaisi/Tbilisi); Paris 1919-1927',
        'wrong':      ['russian', 'soviet artist', 'russian avant-garde'],
        'correct_kw': ['georgian', 'kutaisi', 'tbilisi', 'georgia'],
    },
    'Parajanov': {
        'correct':    'Soviet-Armenian (Georgian-born); birth name Sarkis Parajanov',
        'wrong':      ['soviet director', 'soviet filmmaker', 'soviet film'],
        'correct_kw': ['armenian', 'georgia', 'tbilisi', 'sarkis'],
    },
}"""
    story += code_block(artist_truth_code, styles)

    story.append(Paragraph(
        "Each entry defines the ground truth against which AI responses are measured. "
        "The <font name='Courier' size=8>'wrong'</font> list contains keyword phrases that indicate misattribution. "
        "The <font name='Courier' size=8>'correct_kw'</font> list contains terms that must be present for a response "
        "to be considered accurate.",
        styles['body']))

    # ── STEP 3 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 3 — QUERYING THREE AI SYSTEMS (multi_llm.py)', styles['section']))
    story.append(Paragraph('The same prompt is sent to all three models:', styles['body']))

    prompt_code = """\
PROMPT_TEMPLATE = (
    "I'm looking at '{title}' by {artist}. "
    "Can you tell me about this artist -- specifically their nationality, "
    "where they were born, where they trained, and how their cultural "
    "background shaped their work?"
)"""
    story += code_block(prompt_code, styles, label='Prompt template:')

    claude_code = """\
def query_claude(artist, title, image_url=None):
    client = anthropic.Anthropic()
    prompt = PROMPT_TEMPLATE.format(title=title, artist=artist)
    msgs = []
    if image_url:
        msgs.append({"role": "user", "content": [
            {"type": "image",
             "source": {"type": "url", "url": image_url}},
            {"type": "text", "text": prompt},
        ]})
    else:
        msgs.append({"role": "user", "content": prompt})
    resp = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=350,
        system="You are a knowledgeable art historian. "
               "Answer directly and specifically.",
        messages=msgs,
    )
    return resp.content[0].text"""
    story += code_block(claude_code, styles, label='Claude query:')

    gpt_code = """\
def query_gpt(artist, title, image_url=None):
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    prompt = PROMPT_TEMPLATE.format(title=title, artist=artist)
    content = []
    if image_url:
        content.append({"type": "image_url",
                        "image_url": {"url": image_url}})
    content.append({"type": "text", "text": prompt})
    resp = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=350,
        messages=[
            {"role": "system",
             "content": "You are a knowledgeable art historian."},
            {"role": "user", "content": content},
        ],
    )
    return resp.choices[0].message.content"""
    story += code_block(gpt_code, styles, label='GPT-4o query:')

    llama_code = """\
def query_ollama(artist, title):
    ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    model      = os.environ.get('OLLAMA_MODEL', 'llama3')
    payload = json.dumps({
        "model":  model,
        "prompt": "You are an art historian.\\n\\n"
                  + PROMPT_TEMPLATE.format(title=title, artist=artist),
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        f"{ollama_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get('response', '')"""
    story += code_block(llama_code, styles, label='LLAMA / Ollama query:')

    # ── STEP 4 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 4 — MISATTRIBUTION ASSESSMENT (multi_llm.py)', styles['section']))
    story.append(Paragraph(
        'The assess() function compares the LLM response against the truth table using keyword matching:',
        styles['body']))

    assess_code = """\
def assess(artist, response_text):
    truth = ARTIST_TRUTH.get(artist, {})
    low   = response_text.lower()
    found_correct = [kw for kw in truth.get('correct_kw', [])
                     if kw in low]
    found_wrong   = [kw for kw in truth.get('wrong', [])
                     if kw in low]
    misattributed = bool(found_wrong) or not bool(found_correct)
    return {
        'misattributed':    misattributed,
        'correct_kw_found': found_correct,
        'wrong_kw_found':   found_wrong,
        'confidence':       0.91 if misattributed else 0.24,
    }"""
    story += code_block(assess_code, styles)

    story.append(Paragraph(
        'Logic: A response is flagged as misattributed if it contains any wrong-label keyword '
        '(e.g. "russian avant-garde") OR if it contains none of the correct keywords '
        '(e.g. "ukrainian", "kyiv"). Both conditions are necessary because a response can avoid '
        'wrong terms while still omitting the correct identity.',
        styles['body']))

    # ── STEP 5 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 5 — COMPARE ALL THREE SYSTEMS (multi_llm.py)', styles['section']))

    compare_code = """\
def compare_all_llms(artist, image_url=None):
    records = [r for r in artworks_data['records']
               if r.get('_artist') == artist]
    title = records[0].get('Title', f'a work by {artist}') \\
            if records else f'a work by {artist}'

    claude_resp = query_claude(artist, title, image_url)
    gpt_resp    = query_gpt(artist, title, image_url)
    llama_resp  = query_ollama(artist, title)

    return {
        'artist': artist,
        'systems': {
            'claude': {
                'name':       'Claude (Anthropic)',
                'response':   claude_resp,
                'assessment': assess(artist, claude_resp),
            },
            'gpt': {
                'name':       'GPT-4o (OpenAI)',
                'response':   gpt_resp,
                'assessment': assess(artist, gpt_resp),
            },
            'llama': {
                'name':       'LLAMA (Ollama)',
                'response':   llama_resp,
                'assessment': assess(artist, llama_resp),
            },
        },
        'truth': {
            'correct_label': ARTIST_TRUTH[artist]['correct'],
            'explanation':   ARTIST_TRUTH[artist]['summary'],
        },
    }"""
    story += code_block(compare_code, styles)

    story.append(Paragraph(
        'Returns a structured JSON object comparing all three AI responses with assessments. '
        'This is called by the /api/compare server endpoint and rendered in the visitor kiosk.',
        styles['body']))

    # ── STEP 6 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 6 — HTTP API SERVER (server.py)', styles['section']))
    story.append(Paragraph(
        'Python standard library HTTP server — no external frameworks. Routes:',
        styles['body']))

    routes_header = ['Route', 'Method', 'Parameters', 'Returns']
    routes_data = [
        ['GET /api/query',   'GET', 'artist, image_url (optional)',
         'Single Claude response + truth comparison'],
        ['GET /api/compare', 'GET', 'artist, image_url (optional)',
         'All three AI systems compared side by side'],
        ['GET /api/artworks','GET', 'artist (optional filter)',
         'Dataset records (max 50)'],
        ['GET /api/detect',  'GET', 'url (image URL), artist',
         'Misattribution detected true/false + confidence'],
        ['GET /api/images',  'GET', 'artist (optional)',
         'Image manifest, ready/total counts'],
        ['GET /api/stats',   'GET', 'none',
         'Dataset totals by artist'],
        ['GET /api/sync',    'GET', 'none',
         'Server timestamp for screen synchronisation'],
        ['GET /',            'GET', 'none',
         'Static files (HTML, JS, images)'],
    ]

    col_w = PAGE_W - 2 * MARGIN
    tbl = data_table(routes_header, routes_data,
                     [col_w * 0.22, col_w * 0.09,
                      col_w * 0.32, col_w * 0.37])
    story.append(tbl)
    story.append(Spacer(1, 8))

    handler_code = """\
class ExhibitionHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        params = parse_qs(parsed.query)

        if path == '/api/compare':
            artist    = params.get('artist', ['Malevich'])[0]
            image_url = params.get('image_url', [None])[0]
            result    = compare_all_llms(artist, image_url)
            self._json_response(result)

        elif path == '/api/stats':
            self._json_response({
                'total_records': len(artworks_data['records'])
                                 + len(parajanov_data['records']),
                'by_artist': { ... }
            })

    def _json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False,
                          indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type',
                         'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)"""
    story += code_block(handler_code, styles, label='Handler pattern:')

    # ── STEP 7 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 7 — IMAGE PIPELINE (image_pipeline.py)', styles['section']))
    story.append(Paragraph(
        'Maps local image files to dataset records. Recognises filename prefixes:',
        styles['body']))

    prefix_header = ['Prefix', 'Artist', 'Example filename']
    prefix_data = [
        ['MaL', 'Malevich', 'MaL01.jpg'],
        ['std', 'Malevich (Stedelijk)', 'std03.jpg'],
        ['EXT', 'Exter', 'EXT001.jpg'],
        ['KAK', 'Kakabadze', 'KAK001.jpg'],
        ['PAG', 'Pagava', 'PAG001.jpg'],
        ['PAR', 'Parajanov', 'PAR001.jpg'],
    ]
    tbl2 = data_table(prefix_header, prefix_data,
                      [col_w * 0.18, col_w * 0.40, col_w * 0.42])
    story.append(tbl2)
    story.append(Spacer(1, 8))

    pipeline_code = """\
ID_PATTERN = re.compile(
    r'(MAL|EXT|KAK|PAG|PAR)-\\d{3}|'
    r'(MaL|std|EXT|KAK|PAG|PAR)\\d+',
    re.IGNORECASE
)

def scan_local_dir(directory):
    for img_path in sorted(img_dir.rglob('*')):
        match = ID_PATTERN.search(img_path.stem)
        if match:
            prefix = re.match(r'[A-Za-z]+',
                              match.group()).group().upper()
            number = re.search(r'\\d+', match.group())
            art_id = f"{prefix}-{number.group().zfill(3)}"
            artist = PREFIX_TO_ARTIST.get(prefix.lower())
            dest   = IMAGES_DIR / f"{art_id}{img_path.suffix}"
            shutil.copy2(img_path, dest)
            index[art_id] = {
                'local_path': str(dest),
                '_artist':    artist,
            }"""
    story += code_block(pipeline_code, styles)

    story.append(Paragraph(
        'Usage: <font name="Courier" size="8">python3 server/image_pipeline.py --local-dir /path/to/images</font>',
        styles['body']))

    # ── STEP 8 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 8 — PHASE STATE MACHINE (data.js)', styles['section']))
    story.append(Paragraph(
        'The exhibition cycles through 8 phases automatically. Phase durations in milliseconds:',
        styles['body']))

    phase_header = ['Phase', 'ID', 'Duration', 'Description']
    phase_data = [
        ['PRISTINE',     '0', '3500ms', 'Particles coalesce into artwork form'],
        ['LABEL_APPLY',  '1', '3500ms', 'Archival stamp descends'],
        ['CORRUPT',      '2', '4500ms', 'Noise field tears particles apart'],
        ['PROPAGATE',    '3', '5000ms', 'Streams cross screens to archive nodes'],
        ['MACHINE_GAZE', '4', '4500ms', 'Cold scanner reads corrupted data'],
        ['INTERVENTION', '5', '3500ms', 'Warm force field reclaims particles'],
        ['TRUTH',        '6', '6000ms', 'Particles lock to correct positions'],
        ['FADE',         '7', '2000ms', 'Dissolves; next artist begins'],
    ]
    tbl3 = data_table(phase_header, phase_data,
                      [col_w * 0.22, col_w * 0.08,
                       col_w * 0.14, col_w * 0.56])
    story.append(tbl3)
    story.append(Spacer(1, 8))

    phases_code = """\
const PHASES = {
  PRISTINE:     { id: 0, duration: 3500 },
  LABEL_APPLY:  { id: 1, duration: 3500 },
  CORRUPT:      { id: 2, duration: 4500 },
  PROPAGATE:    { id: 3, duration: 5000 },
  MACHINE_GAZE: { id: 4, duration: 4500 },
  INTERVENTION: { id: 5, duration: 3500 },
  TRUTH:        { id: 6, duration: 6000 },
  FADE:         { id: 7, duration: 2000 },
};"""
    story += code_block(phases_code, styles)

    # ── STEP 9 ───────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 9 — PARTICLE SYSTEM (sketch.js)', styles['section']))
    story.append(Paragraph(
        '1,800 particles are seeded from artwork image pixels. Each particle has a target '
        'position (correct pixel location) and is subject to two competing forces:',
        styles['body']))

    particle_code = """\
function updateParticles(fw, fh, corruption, now) {
    const spring   = lerp(0.055, 0.004, corruption);
    const damping  = 0.86;
    const noiseAmp = lerp(0.0,   4.2,   corruption);

    for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Spring toward correct target position
        p.vx += (p.tx - p.x) * spring;
        p.vy += (p.ty - p.y) * spring;

        // Noise turbulence -- misattribution force
        if (noiseAmp > 0.05) {
            const n1 = noise(p.x / 180, p.y / 180, noiseOffset);
            const n2 = noise(p.x / 180 + 50, p.y / 180, noiseOffset);
            p.vx += cos(n1 * TWO_PI * 3) * noiseAmp;
            p.vy += sin(n2 * TWO_PI * 3) * noiseAmp;
        }

        p.vx *= damping;
        p.vy *= damping;
        p.x  += p.vx;
        p.y  += p.vy;
    }
}"""
    story += code_block(particle_code, styles)

    story.append(Paragraph(
        'Corruption value (0.0 = truth, 1.0 = fully corrupted) drives both forces. '
        'When corruption = 1.0, spring strength drops to 0.004 and noise amplitude '
        'rises to 4.2, overpowering the spring.',
        styles['body']))

    thread_code = """\
function drawThreads(corruption) {
    const hue   = lerp(42, 195, corruption); // warm gold -> cold blue
    const maxD  = lerp(52, 110, corruption); // wider mesh when corrupted
    const maxD2 = maxD * maxD;

    for (let i = 0; i < particles.length; i += 3) {
        const a = particles[i];
        let drawn = 0;
        for (let j = i+1; j < i+90 && drawn < 5; j++) {
            const b  = particles[j];
            const dx = a.x - b.x;
            const dy = a.y - b.y;
            if (dx*dx + dy*dy < maxD2) {
                stroke(hue, sat, bri,
                       map(dist, 0, maxD, baseAlpha, 0));
                line(a.x, a.y, b.x, b.y);
                drawn++;
            }
        }
    }
}"""
    story += code_block(thread_code, styles, label='Thread connections — nearby particles are connected by fine lines:')

    # ── STEP 10 ──────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 10 — MULTI-SCREEN SYNCHRONISATION (sync.js)', styles['section']))
    story.append(Paragraph(
        'Screen 1 (leader) writes phase state to localStorage every 500ms. '
        'All other screens read and align:',
        styles['body']))

    sync_code = """\
function writeSync() {
    localStorage.setItem('misattribution_sync', JSON.stringify({
        phaseIndex:  phaseIndex,
        artist:      state.artist,
        phaseStart:  state.phaseStart,
        ts:          Date.now(),
    }));
}

function readSync() {
    const s = JSON.parse(localStorage.getItem('misattribution_sync'));
    if (Date.now() - s.ts > 3000) return; // stale -- run independently
    if (s.phaseIndex !== phaseIndex) {
        phaseIndex       = s.phaseIndex;
        state.phase      = phases[PHASE_ORDER[phaseIndex]];
        state.phaseStart = s.phaseStart;
    }
}"""
    story += code_block(sync_code, styles)

    story.append(Paragraph(
        'Fallback: if no sync signal within 3000ms, each screen runs the cycle independently.',
        styles['body']))

    # ── STEP 11 ──────────────────────────────────────────────────────────────
    story.append(Paragraph('STEP 11 — RUNNING THE SYSTEM', styles['section']))
    story.append(Paragraph('Environment setup:', styles['body']))

    env_code = """\
export ANTHROPIC_API_KEY="sk-ant-..."   # required for live AI
export OPENAI_API_KEY="sk-..."          # optional for GPT-4o
python3 server/server.py"""
    story += code_block(env_code, styles)

    story.append(Paragraph('Link artwork images from local folder:', styles['body']))

    img_code = """\
python3 server/image_pipeline.py --local-dir /path/to/images"""
    story += code_block(img_code, styles)

    story.append(Paragraph('<b>Access points:</b>', styles['body']))

    access_header = ['Interface', 'URL']
    access_data = [
        ['Single screen preview', 'http://localhost:8000/index.html'],
        ['Visitor kiosk (AI detection)', 'http://localhost:8000/kiosk.html'],
        ['Curator controller', 'http://localhost:8000/exhibition.html'],
        ['API test', 'http://localhost:8000/api/compare?artist=Malevich'],
    ]
    tbl4 = data_table(access_header, access_data,
                      [col_w * 0.35, col_w * 0.65])
    story.append(tbl4)
    story.append(Spacer(1, 10))

    return story


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    out_path = '/home/user/Teona-Yamanidze/Technical_Implementation.pdf'
    styles = make_styles()

    doc = TechnicalDoc(
        out_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 1 * cm,
        title='Misattribution Machine — Technical Implementation',
        author='Teona Yamanidze',
    )

    story = build_story(styles)
    doc.build(story)
    print(f'PDF written to: {out_path}')
    size = os.path.getsize(out_path)
    print(f'File size: {size:,} bytes ({size / 1024:.1f} KB)')


if __name__ == '__main__':
    main()
