"""
generate_doc.py
Generates Misattribution_Machine_Documentation.pdf using reportlab Platypus.
"""

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
import os

OUTPUT_PATH = "/home/user/Teona-Yamanidze/Misattribution_Machine_Documentation.pdf"

# ---------------------------------------------------------------------------
# Custom document template with page numbers
# ---------------------------------------------------------------------------

class NumberedDocTemplate(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id='normal'
        )
        template = PageTemplate(id='main', frames=frame, onPage=self._on_page)
        self.addPageTemplates([template])

    def _on_page(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#888888'))
        page_num = canvas.getPageNumber()
        # Skip page number on title page (page 1)
        if page_num > 1:
            canvas.drawCentredString(
                doc.pagesize[0] / 2,
                doc.bottomMargin / 2,
                f"{page_num}"
            )
        canvas.restoreState()


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------

def build_styles():
    base = getSampleStyleSheet()

    styles = {}

    styles['title'] = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=6,
    )
    styles['subtitle'] = ParagraphStyle(
        'DocSubtitle',
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#444444'),
        spaceAfter=4,
    )
    styles['meta'] = ParagraphStyle(
        'Meta',
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#555555'),
        spaceAfter=2,
    )
    styles['section'] = ParagraphStyle(
        'SectionHeader',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceBefore=18,
        spaceAfter=6,
        borderPad=0,
    )
    styles['subsection'] = ParagraphStyle(
        'SubsectionHeader',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#2a2a2a'),
        spaceBefore=10,
        spaceAfter=4,
    )
    styles['body'] = ParagraphStyle(
        'BodyText',
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#222222'),
        spaceAfter=6,
    )
    styles['bullet'] = ParagraphStyle(
        'Bullet',
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        leftIndent=14,
        firstLineIndent=0,
        textColor=colors.HexColor('#222222'),
        spaceAfter=3,
    )
    styles['code'] = ParagraphStyle(
        'Code',
        fontName='Courier',
        fontSize=9,
        leading=13,
        leftIndent=14,
        textColor=colors.HexColor('#2a2a2a'),
        backColor=colors.HexColor('#f5f5f5'),
        spaceAfter=3,
    )
    styles['url'] = ParagraphStyle(
        'URL',
        fontName='Courier',
        fontSize=8.5,
        leading=13,
        leftIndent=14,
        textColor=colors.HexColor('#2a2a2a'),
        spaceAfter=2,
    )
    styles['caption'] = ParagraphStyle(
        'Caption',
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666'),
        spaceAfter=6,
    )

    return styles


def hr(width=1, color='#cccccc'):
    return HRFlowable(
        width='100%',
        thickness=width,
        color=colors.HexColor(color),
        spaceAfter=4,
        spaceBefore=4,
    )


def section_rule():
    return HRFlowable(
        width='100%',
        thickness=0.5,
        color=colors.HexColor('#bbbbbb'),
        spaceAfter=6,
        spaceBefore=2,
    )


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

TABLE_HEADER_BG = colors.HexColor('#2a2a2a')
TABLE_ALT_BG    = colors.HexColor('#f7f7f7')
TABLE_BORDER    = colors.HexColor('#cccccc')
WHITE           = colors.white

def data_table(headers, rows, col_widths=None):
    """Build a styled Platypus Table from headers + row data."""
    data = [headers] + rows
    t = Table(data, colWidths=col_widths, hAlign='LEFT')
    style = TableStyle([
        # Header row
        ('BACKGROUND',   (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING',(0, 0), (-1, 0), 6),
        ('TOPPADDING',   (0, 0), (-1, 0), 6),
        # Body rows
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        ('TOPPADDING',   (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 1), (-1, -1), 5),
        # Alternating rows
        *[('BACKGROUND', (0, i), (-1, i), TABLE_ALT_BG)
          for i in range(2, len(data), 2)],
        # Grid
        ('GRID',         (0, 0), (-1, -1), 0.4, TABLE_BORDER),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ])
    t.setStyle(style)
    return t


# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------

def build_document():
    doc = NumberedDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2.5*cm,
        rightMargin=2.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm,
    )

    s = build_styles()
    story = []

    # -----------------------------------------------------------------------
    # TITLE PAGE
    # -----------------------------------------------------------------------
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph(
        "Misattribution Machine: AI-Driven Detection of Archival Misattribution",
        s['title']
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(hr(width=1.5, color='#1a1a1a'))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        "Technical Documentation — Exhibition System",
        s['subtitle']
    ))
    story.append(Spacer(1, 2.5*cm))
    story.append(Paragraph("Teona Yamanidze", s['meta']))
    story.append(Paragraph("University of Melbourne", s['meta']))
    story.append(Paragraph("May 2026", s['meta']))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # SECTION 1 — PROJECT OVERVIEW
    # -----------------------------------------------------------------------
    story.append(Paragraph("1. Project Overview", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "The Misattribution Machine is an exhibition system designed to detect and visualise the "
        "propagation of misattribution errors across digital archives and AI language models. The "
        "project analyses how incorrect nationality labels assigned to five artists — Kazimir "
        "Malevich, Alexandra Exter, Vera Pagava, David Kakabadze, and Sergei Parajanov — originate "
        "in archival authority records and are subsequently reproduced by major AI systems including "
        "Claude, GPT-4o, and LLAMA.",
        s['body']
    ))
    story.append(Paragraph(
        "The system comprises three principal components:",
        s['body']
    ))
    story.append(Paragraph(
        "(1) A dataset analysis pipeline processing 659 archival records;",
        s['bullet']
    ))
    story.append(Paragraph(
        "(2) A real-time AI misattribution detection tool using the Claude API; and",
        s['bullet']
    ))
    story.append(Paragraph(
        "(3) A 12-screen LED exhibition installation rendered in p5.js.",
        s['bullet']
    ))

    # -----------------------------------------------------------------------
    # SECTION 2 — DATASET ANALYSIS
    # -----------------------------------------------------------------------
    story.append(Paragraph("2. Dataset Analysis", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "Two datasets were processed to characterise the nature and scale of misattribution across "
        "institutional records.",
        s['body']
    ))

    # Parajanov dataset table
    story.append(Paragraph("2.1  Parajanov Bibliographic Dataset", s['subsection']))
    story.append(Paragraph(
        "305 records were analysed from bibliographic sources relating to Sergei Parajanov. "
        "The misattribution breakdown is as follows:",
        s['body']
    ))
    pj_headers = ['Misattribution Type', 'Record Count', 'Percentage']
    pj_rows = [
        ['Wrong nationality label', '218', '71.5%'],
        ['Omission of national identity', '54', '17.7%'],
        ['Spelling / name variants', '33', '10.8%'],
        ['Total', '305', '100%'],
    ]
    story.append(data_table(pj_headers, pj_rows, col_widths=[9*cm, 3.5*cm, 3.5*cm]))
    story.append(Spacer(1, 0.3*cm))

    # Artworks dataset table
    story.append(Paragraph("2.2  Artworks Dataset (Malevich, Exter, Pagava, Kakabadze)", s['subsection']))
    story.append(Paragraph(
        "354 records were analysed across the four visual artists. The breakdown by artist and "
        "misattribution type is presented below:",
        s['body']
    ))
    art_headers = ['Artist', 'Total Records', 'Wrong Label', 'Omission', 'Spelling / Structural']
    art_rows = [
        ['Kazimir Malevich', '272', '195', '61', '16'],
        ['Alexandra Exter',   '44',  '38',  '4',  '2'],
        ['Vera Pagava',        '19',  '19',  '—',  '—'],
        ['David Kakabadze',    '19',  '—',   '—',  '19 (structural)'],
        ['Subtotal',          '354', '252', '65',  '37'],
    ]
    story.append(data_table(art_headers, art_rows, col_widths=[4.5*cm, 3*cm, 2.5*cm, 2.5*cm, 3.5*cm]))
    story.append(Spacer(1, 0.3*cm))

    # Combined totals
    story.append(Paragraph("2.3  Combined Dataset Summary", s['subsection']))
    tot_headers = ['Metric', 'Value']
    tot_rows = [
        ['Total records', '659'],
        ['Artists covered', '5'],
        ['Records containing at least one misattribution', '~94%'],
    ]
    story.append(data_table(tot_headers, tot_rows, col_widths=[10*cm, 6*cm]))
    story.append(Spacer(1, 0.4*cm))

    # Artist profiles
    story.append(Paragraph("2.4  Artist Profiles and Misattribution Context", s['subsection']))
    artists = [
        ("Kazimir Malevich",
         "Born in Kyiv, 1879. Routinely labelled 'Russian avant-garde' or 'Soviet artist' in major "
         "archives including the Library of Congress, WorldCat, and MoMA, erasing his Ukrainian origin."),
        ("Alexandra Exter",
         "Born in Kyiv; trained at the Kyiv School of Art. Labelled 'Russian' across most institutional "
         "records, with no reference to her Ukrainian formation."),
        ("Vera Pagava",
         "Born in Tbilisi, Georgia. Labelled 'Empire Russe' in archival records — a framing that "
         "subsumes and erases Georgian identity entirely."),
        ("David Kakabadze",
         "Born in Kutaisi/Tbilisi, Georgia. Absorbed into the Société Anonyme 'Russian avant-garde' "
         "canon without acknowledgement of Georgian nationality."),
        ("Sergei Parajanov",
         "Soviet-Armenian filmmaker, Georgian-born. Birth name: Sarkis Hovsepi Parajanov. Labelled "
         "'Soviet' in most records, with both national and ethnic identity omitted."),
    ]
    for name, desc in artists:
        story.append(Paragraph(f"<b>{name}.</b>  {desc}", s['bullet']))
        story.append(Spacer(1, 0.15*cm))

    # -----------------------------------------------------------------------
    # SECTION 3 — PROPAGATION CHAIN
    # -----------------------------------------------------------------------
    story.append(Paragraph("3. Propagation Chain", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "Misattribution propagates through a hierarchical chain of institutions. An absence or error "
        "in a Library of Congress authority record is adopted as authoritative by downstream "
        "institutions, which in turn supply training data to AI language models. The models then "
        "reproduce and amplify the original error at scale.",
        s['body']
    ))
    prop_headers = ['Tier', 'Institution / System', 'Role in Chain']
    prop_rows = [
        ['Tier 0', 'Library of Congress', 'Authority records — original source'],
        ['Tier 1', 'WorldCat / OCLC', 'Aggregation and redistribution'],
        ['Tier 2', 'National libraries (Trove/NLA);\nMuseum databases (MoMA, NGA, NGV)',
                   'Institutional adoption of authority labels'],
        ['Tier 3', 'AI language models (Claude, GPT-4o, LLAMA);\nWeb knowledge graphs (Google Knowledge)',
                   'Reproduction and amplification of error'],
    ]
    story.append(data_table(prop_headers, prop_rows, col_widths=[1.8*cm, 6*cm, 8.2*cm]))

    # -----------------------------------------------------------------------
    # SECTION 4 — AI DETECTION SYSTEM
    # -----------------------------------------------------------------------
    story.append(Paragraph("4. AI Detection System", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "The detection tool queries AI language models about an artist's nationality and compares "
        "the response against the Record of Truth derived from the dataset.",
        s['body']
    ))

    story.append(Paragraph("4.1  Technical Implementation", s['subsection']))
    tech_headers = ['Component', 'Detail']
    tech_rows = [
        ['Language',         'Python 3.9+'],
        ['Primary API',      'Anthropic Claude API (claude-opus-4-5)'],
        ['Multi-model',      'Claude (Anthropic), GPT-4o (OpenAI API), LLAMA (Ollama, local)'],
        ['Detection method', 'Keyword matching against correct and incorrect nationality terms'],
        ['Image queries',    'Vision queries supported via artwork image URLs'],
    ]
    story.append(data_table(tech_headers, tech_rows, col_widths=[5*cm, 11*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("4.2  Server Routes", s['subsection']))
    story.append(Paragraph(
        "The HTTP server is implemented using the Python standard-library HTTP server (no external "
        "frameworks). The following API routes are exposed:",
        s['body']
    ))
    route_headers = ['Route', 'Method', 'Description']
    route_rows = [
        ['/api/query',    'GET', 'Single model query with misattribution assessment'],
        ['/api/compare',  'GET', 'All three models compared side by side'],
        ['/api/detect',   'GET', 'Misattribution detection for a given image URL'],
        ['/api/artworks', 'GET', 'Full dataset records (filterable by artist)'],
        ['/api/stats',    'GET', 'Dataset summary statistics'],
        ['/api/images',   'GET', 'Image manifest and status'],
    ]
    story.append(data_table(route_headers, route_rows, col_widths=[4*cm, 2.5*cm, 9.5*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("4.3  Source Files", s['subsection']))
    file_headers = ['File', 'Purpose']
    file_rows = [
        ['server/server.py',          'Main HTTP server'],
        ['server/multi_llm.py',       'Multi-model comparison (Claude + GPT-4o + LLAMA)'],
        ['server/claude_detector.py', 'Standalone CLI detection tool'],
        ['server/image_pipeline.py',  'Artwork image management'],
    ]
    story.append(data_table(file_headers, file_rows, col_widths=[7*cm, 9*cm]))

    # -----------------------------------------------------------------------
    # SECTION 5 — EXHIBITION SYSTEM
    # -----------------------------------------------------------------------
    story.append(Paragraph("5. Exhibition System", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "The exhibition is designed for a 12-screen LED installation configured as a 4-column by "
        "3-row grid. Each screen is a separate browser window displaying one panel of a continuous "
        "full-canvas animation rendered in p5.js.",
        s['body']
    ))

    story.append(Paragraph("5.1  Visual Language", s['subsection']))
    story.append(Paragraph(
        "The artwork is rendered as a cloud of 1,800 luminous particles, each positioned at a pixel "
        "sampled from the source artwork image. Nearby particles are connected by fine threads. "
        "The visual language operates across two opposing states:",
        s['body']
    ))
    story.append(Paragraph(
        "Truth state:  particles correctly positioned; threads form the real image clearly; warm "
        "cream luminosity on pure black background.",
        s['bullet']
    ))
    story.append(Paragraph(
        "Misattribution state:  particles displaced by a noise force field; threads tangled; "
        "cold blue-white colouration indicating corrupted data.",
        s['bullet']
    ))

    story.append(Paragraph("5.2  Phase Cycle", s['subsection']))
    story.append(Paragraph(
        "The animation cycles through eight phases automatically, with a total duration of "
        "approximately 35 seconds per artist:",
        s['body']
    ))
    phase_headers = ['Phase', 'Duration', 'Description']
    phase_rows = [
        ['1. PRISTINE',      '3.5 s', 'Particles coalesce from void. Artwork emerges as constellation of light.'],
        ['2. LABEL APPLY',   '3.5 s', 'Thin archival rectangle descends over the image.'],
        ['3. CORRUPT',       '4.5 s', 'Noise force field tears particles from correct positions. Threads tangle.'],
        ['4. PROPAGATE',     '5.0 s', 'Particle streams cross screen boundaries. Archive network activates.'],
        ['5. MACHINE GAZE',  '4.5 s', 'Cold scanner light sweeps. AI systems read the corrupted data.'],
        ['6. INTERVENTION',  '3.5 s', 'Warm light sweeps in. Spring force reclaims particles.'],
        ['7. TRUTH',         '6.0 s', 'Particles lock to correct positions. Threads form the real image clearly.'],
        ['8. FADE',          '2.0 s', 'Dissolves. Next artist begins.'],
    ]
    story.append(data_table(phase_headers, phase_rows, col_widths=[3.5*cm, 2*cm, 10.5*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("5.3  Screen Synchronisation", s['subsection']))
    story.append(Paragraph(
        "Screen synchronisation is achieved via the browser LocalStorage API. Screen 1 (the leader) "
        "writes phase state every 500 milliseconds. All other screens read the shared state and "
        "align their animation phase accordingly. No server-side coordination is required.",
        s['body']
    ))

    story.append(Paragraph("5.4  Screen URLs", s['subsection']))
    story.append(Paragraph(
        "Each screen is loaded with URL parameters specifying its position in the grid "
        "(screen index, column count, row count):",
        s['body']
    ))
    screen_headers = ['Screen', 'URL']
    screen_rows = [
        [f'Screen {i}', f'http://localhost:8000/index.html?screen={i}&cols=4&rows=3']
        for i in range(1, 13)
    ]
    screen_rows += [
        ['Single screen preview', 'http://localhost:8000/index.html'],
        ['Curator controller',    'http://localhost:8000/exhibition.html'],
    ]
    story.append(data_table(screen_headers, screen_rows, col_widths=[4*cm, 12*cm]))

    # -----------------------------------------------------------------------
    # SECTION 6 — VISITOR KIOSK
    # -----------------------------------------------------------------------
    story.append(Paragraph("6. Visitor Kiosk", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "The kiosk interface (kiosk.html) is a visitor touch-screen component. Visitors select an "
        "artist; the system queries three AI models in parallel and displays their responses "
        "alongside the Record of Truth derived from the dataset.",
        s['body']
    ))
    story.append(Paragraph(
        "URL:  http://localhost:8000/kiosk.html",
        s['code']
    ))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph("6.1  Layout", s['subsection']))
    story.append(Paragraph(
        "The kiosk displays four columns: Claude | GPT-4o | LLAMA | Record of Truth. "
        "Each AI response is revealed via a typewriter animation. A consensus bar "
        "indicates the degree of agreement or disagreement between the three models. "
        "Artist selector buttons allow navigation between Malevich, Exter, Pagava, "
        "Kakabadze, and Parajanov.",
        s['body']
    ))

    story.append(Paragraph("6.2  Operating Modes", s['subsection']))
    mode_headers = ['Mode', 'Requirement', 'Behaviour']
    mode_rows = [
        ['Demo mode', 'None (no API keys required)',
         'Operates using pre-written responses that demonstrate typical misattribution patterns from the dataset.'],
        ['Live mode', 'ANTHROPIC_API_KEY environment variable',
         'Queries Claude API in real time; GPT-4o and LLAMA also require their respective keys/services.'],
    ]
    story.append(data_table(mode_headers, mode_rows, col_widths=[3*cm, 4.5*cm, 8.5*cm]))

    # -----------------------------------------------------------------------
    # SECTION 7 — TECHNICAL REQUIREMENTS
    # -----------------------------------------------------------------------
    story.append(Paragraph("7. Technical Requirements", s['section']))
    story.append(section_rule())

    story.append(Paragraph("7.1  Dependencies", s['subsection']))
    dep_headers = ['Requirement', 'Detail']
    dep_rows = [
        ['Python', '3.9 or higher'],
        ['Python packages', 'anthropic, openai, openpyxl, gdown'],
        ['Environment variable', 'ANTHROPIC_API_KEY (required for live AI detection)'],
        ['Browser', 'Chrome or Firefox (recommended)'],
    ]
    story.append(data_table(dep_headers, dep_rows, col_widths=[5*cm, 11*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("7.2  Installation and Start", s['subsection']))
    story.append(Paragraph("Install dependencies:", s['body']))
    story.append(Paragraph("pip install anthropic openai openpyxl gdown", s['code']))
    story.append(Spacer(1, 0.15*cm))
    story.append(Paragraph("Start the server:", s['body']))
    story.append(Paragraph('export ANTHROPIC_API_KEY="your-key-here"', s['code']))
    story.append(Paragraph("python3 server/server.py", s['code']))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("7.3  Repository", s['subsection']))
    repo_headers = ['Field', 'Value']
    repo_rows = [
        ['Repository', 'github.com/yamanidzet/Teona-Yamanidze'],
        ['Branch',     'claude/analyze-art-datasets-fvjZt'],
    ]
    story.append(data_table(repo_headers, repo_rows, col_widths=[4*cm, 12*cm]))

    # -----------------------------------------------------------------------
    # SECTION 8 — VISUAL REFERENCES
    # -----------------------------------------------------------------------
    story.append(Paragraph("8. Visual References", s['section']))
    story.append(section_rule())
    story.append(Paragraph(
        "The visual aesthetic of the exhibition draws from the following precedents and principles:",
        s['body']
    ))
    story.append(Paragraph(
        "Memo Akten, The Networked Condition — particle and thread systems that form recognisable "
        "figures on a black ground.",
        s['bullet']
    ))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        "Mario Klingemann — painterly dissolution of image into data; the boundary between "
        "representation and information.",
        s['bullet']
    ))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        "Pure black background with luminous warm-cream threads (clean / truth state); "
        "cold blue-white threads (corrupted / misattributed state).",
        s['bullet']
    ))
    story.append(Spacer(1, 0.1*cm))
    story.append(Paragraph(
        "Motion blur trail achieved via semi-transparent frame accumulation, lending each frame "
        "a painterly depth consistent with the archival subject matter.",
        s['bullet']
    ))

    # -----------------------------------------------------------------------
    # Build
    # -----------------------------------------------------------------------
    doc.build(story)
    print(f"PDF generated: {OUTPUT_PATH}")


if __name__ == '__main__':
    build_document()
