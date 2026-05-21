#!/usr/bin/env python3
"""
generate_doc.py
Generates Misattribution_Machine_Documentation.pdf using reportlab Platypus.
Author: Teona Yamanidze — University of Melbourne, May 2026
"""

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate, BaseDocTemplate
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUTPUT_PATH = "/home/user/Teona-Yamanidze/Misattribution_Machine_Documentation.pdf"

# ── Palette ───────────────────────────────────────────────────────────────────
DARK       = colors.HexColor("#1a1a1a")
ACCENT     = colors.HexColor("#2c3e50")   # dark navy
MID        = colors.HexColor("#444444")
GREY       = colors.HexColor("#888888")
RULE       = colors.HexColor("#cccccc")
TH_BG      = colors.HexColor("#2c3e50")
ALT_BG     = colors.HexColor("#f7f7f7")
GRID_LINE  = colors.HexColor("#d0d0d0")
WHITE      = colors.white


# ── Page template with footer ─────────────────────────────────────────────────
class NumberedDoc(BaseDocTemplate):
    def __init__(self, filename, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height, id="normal"
        )
        template = PageTemplate(id="main", frames=frame, onPage=self._footer)
        self.addPageTemplates([template])

    def _footer(self, canvas, doc):
        page = canvas.getPageNumber()
        if page == 1:
            return
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(GREY)
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            doc.bottomMargin * 0.45,
            f"Misattribution Machine — Technical Documentation    •    {page}"
        )
        canvas.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def build_styles():
    s = {}
    s["title"] = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=21,
        leading=27,
        alignment=TA_CENTER,
        textColor=DARK,
        spaceAfter=5,
    )
    s["subtitle"] = ParagraphStyle(
        "DocSubtitle",
        fontName="Helvetica",
        fontSize=12,
        leading=17,
        alignment=TA_CENTER,
        textColor=MID,
        spaceAfter=4,
    )
    s["meta"] = ParagraphStyle(
        "Meta",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=MID,
        spaceAfter=2,
    )
    s["meta_light"] = ParagraphStyle(
        "MetaLight",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=GREY,
        spaceAfter=2,
    )
    s["section"] = ParagraphStyle(
        "SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=18,
        textColor=ACCENT,
        spaceBefore=16,
        spaceAfter=5,
    )
    s["sub"] = ParagraphStyle(
        "SubHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=16,
        textColor=DARK,
        spaceBefore=10,
        spaceAfter=4,
    )
    s["body"] = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=DARK,
        spaceAfter=6,
    )
    s["bodyl"] = ParagraphStyle(
        "BodyLeft",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_LEFT,
        textColor=DARK,
        spaceAfter=5,
    )
    s["bullet"] = ParagraphStyle(
        "Bullet",
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        leftIndent=14,
        textColor=DARK,
        spaceAfter=3,
    )
    s["code"] = ParagraphStyle(
        "Code",
        fontName="Courier",
        fontSize=9,
        leading=13,
        leftIndent=14,
        textColor=colors.HexColor("#2a2a2a"),
        backColor=ALT_BG,
        spaceAfter=3,
    )
    return s


# ── Table helper ──────────────────────────────────────────────────────────────
def tbl(headers, rows, widths):
    data = [headers] + rows
    t = Table(data, colWidths=widths, hAlign="LEFT")
    alt_cmds = [
        ("BACKGROUND", (0, i), (-1, i), ALT_BG)
        for i in range(2, len(data), 2)
    ]
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  TH_BG),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("TOPPADDING",    (0, 0), (-1, 0),  6),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  6),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 9),
        ("TOPPADDING",    (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("TEXTCOLOR",     (0, 1), (-1, -1), DARK),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, GRID_LINE),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.8, ACCENT),
        *alt_cmds,
    ]))
    return t


def rule():
    return HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=6, spaceBefore=2)


def section_heading(number, title, s):
    return [
        Spacer(1, 0.2 * cm),
        rule(),
        Paragraph(f"{number}. {title}", s["section"]),
    ]


# ── Document assembly ─────────────────────────────────────────────────────────
def build():
    doc = NumberedDoc(
        OUTPUT_PATH,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.4 * cm,
        title="Misattribution Machine: Technical Documentation",
        author="Teona Yamanidze",
        subject="AI-Driven Detection of Archival Misattribution — Exhibition System",
    )

    s = build_styles()
    story = []

    # ── TITLE PAGE ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3.2 * cm))
    story.append(Paragraph(
        "Misattribution Machine:",
        s["title"]
    ))
    story.append(Paragraph(
        "AI-Driven Detection of Archival Misattribution",
        s["title"]
    ))
    story.append(Spacer(1, 0.35 * cm))
    # Subtle horizontal rule under the title
    story.append(HRFlowable(
        width="55%", thickness=1.5, color=ACCENT,
        hAlign="CENTER", spaceAfter=0.4 * cm
    ))
    story.append(Paragraph(
        "Technical Documentation — Exhibition System",
        s["subtitle"]
    ))
    story.append(Spacer(1, 2.8 * cm))
    story.append(Paragraph("Teona Yamanidze", s["meta"]))
    story.append(Paragraph("University of Melbourne", s["meta"]))
    story.append(Spacer(1, 0.25 * cm))
    story.append(Paragraph("May 2026", s["meta_light"]))
    story.append(PageBreak())

    # ── SECTION 1 — PROJECT OVERVIEW ─────────────────────────────────────────
    story += section_heading(1, "Project Overview", s)
    story.append(Paragraph(
        "The Misattribution Machine is an exhibition system designed to detect and visualise the "
        "propagation of misattribution errors across digital archives and AI language models. The "
        "project analyses how incorrect nationality labels assigned to five artists — Kazimir "
        "Malevich, Alexandra Exter, Vera Pagava, David Kakabadze, and Sergei Parajanov — "
        "originate in archival authority records and are subsequently reproduced by major AI "
        "systems including Claude, GPT-4o, and LLAMA.",
        s["body"]
    ))
    story.append(Paragraph("The system comprises three principal components:", s["body"]))
    story.append(Paragraph(
        "(1) A dataset analysis pipeline processing 659 archival records;", s["bullet"]))
    story.append(Paragraph(
        "(2) A real-time AI misattribution detection tool using the Claude API; and", s["bullet"]))
    story.append(Paragraph(
        "(3) A 12-screen LED exhibition installation rendered in p5.js.", s["bullet"]))

    # ── SECTION 2 — DATASET ANALYSIS ─────────────────────────────────────────
    story += section_heading(2, "Dataset Analysis", s)
    story.append(Paragraph(
        "Two datasets were processed to characterise the nature and scale of misattribution "
        "across institutional archival records.",
        s["body"]
    ))

    story.append(Paragraph("2.1 Parajanov Bibliographic Dataset", s["sub"]))
    story.append(Paragraph(
        "305 records from bibliographic sources relating to Sergei Parajanov were analysed. "
        "The misattribution breakdown is as follows:",
        s["body"]
    ))
    story.append(tbl(
        ["Misattribution Type", "Record Count", "Percentage"],
        [
            ["Wrong nationality label",       "218", "71.5%"],
            ["Omission of national identity", "54",  "17.7%"],
            ["Spelling / name variants",      "33",  "10.8%"],
            ["Total",                         "305", "100%"],
        ],
        [9.0 * cm, 3.5 * cm, 3.5 * cm]
    ))
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("2.2 Artworks Dataset (Malevich, Exter, Pagava, Kakabadze)", s["sub"]))
    story.append(Paragraph(
        "354 records across four visual artists were processed. The breakdown by artist and "
        "misattribution type is shown below:",
        s["body"]
    ))
    story.append(tbl(
        ["Artist", "Total Records", "Wrong Label", "Omission", "Spelling / Structural"],
        [
            ["Kazimir Malevich", "272", "195", "61", "16"],
            ["Alexandra Exter",   "44",  "38",  "4",  "2"],
            ["Vera Pagava",        "19",  "19",  "—",  "—"],
            ["David Kakabadze",    "19",  "—",   "—",  "19 (structural)"],
            ["Subtotal",          "354", "252", "65",  "37"],
        ],
        [4.5 * cm, 3.0 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm]
    ))
    story.append(Spacer(1, 0.35 * cm))

    story.append(Paragraph("2.3 Combined Dataset Summary", s["sub"]))
    story.append(tbl(
        ["Metric", "Value"],
        [
            ["Total records analysed",                            "659"],
            ["Artists covered",                                   "5"],
            ["Records with at least one form of misattribution",  "~94%"],
        ],
        [11.0 * cm, 5.0 * cm]
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("2.4 Artist Profiles and Misattribution Context", s["sub"]))
    profiles = [
        ("Kazimir Malevich",
         "Born in Kyiv, 1879. Routinely labelled ‘Russian avant-garde’ or "
         "‘Soviet artist’ in major archives including the Library of Congress, "
         "WorldCat, and MoMA, erasing his Ukrainian origin."),
        ("Alexandra Exter",
         "Born in Kyiv; trained at the Kyiv School of Art. Labelled ‘Russian’ "
         "across most institutional records, with no reference to her Ukrainian formation."),
        ("Vera Pagava",
         "Born in Tbilisi, Georgia. Labelled ‘Empire Russe’ in archival records — "
         "a framing that subsumes and erases Georgian identity entirely."),
        ("David Kakabadze",
         "Born in Kutaisi/Tbilisi, Georgia. Absorbed into the Société Anonyme "
         "‘Russian avant-garde’ canon without acknowledgement of Georgian nationality."),
        ("Sergei Parajanov",
         "Soviet-Armenian filmmaker, Georgian-born. Birth name: Sarkis Hovsepi Parajanov. "
         "Labelled ‘Soviet’ in most records, with both national and ethnic identity omitted."),
    ]
    for name, desc in profiles:
        story.append(Paragraph(f"<b>{name}.</b> {desc}", s["bullet"]))
        story.append(Spacer(1, 0.12 * cm))

    # ── SECTION 3 — PROPAGATION CHAIN ────────────────────────────────────────
    story += section_heading(3, "Propagation Chain", s)
    story.append(Paragraph(
        "Misattribution errors propagate through a structured hierarchy of institutions. An "
        "absence of, or error within, a Library of Congress authority record is adopted as "
        "authoritative by downstream institutions, which in turn supply training data to AI "
        "language models. Those models subsequently reproduce and amplify the original error "
        "at scale.",
        s["body"]
    ))
    story.append(tbl(
        ["Tier", "Institution / System", "Role in Propagation Chain"],
        [
            ["Tier 0", "Library of Congress",
             "Authority records — original source of misattribution"],
            ["Tier 1", "WorldCat / OCLC",
             "Aggregation and global redistribution of authority labels"],
            ["Tier 2",
             "National libraries (Trove / NLA);\nMuseum databases (MoMA, NGA, NGV)",
             "Institutional adoption; misattribution embedded in catalogue data"],
            ["Tier 3",
             "AI language models (Claude, GPT-4o, LLAMA);\nWeb knowledge graphs (Google Knowledge)",
             "Trained on misattributed corpus; errors reproduced and amplified at scale"],
        ],
        [1.8 * cm, 5.8 * cm, 8.4 * cm]
    ))

    # ── SECTION 4 — AI DETECTION SYSTEM ──────────────────────────────────────
    story += section_heading(4, "AI Detection System", s)
    story.append(Paragraph(
        "The detection tool queries AI language models regarding an artist’s nationality "
        "and compares the model’s response against the Record of Truth derived from the "
        "dataset. Detected misattributions are flagged and, where possible, their provenance "
        "is traced to the originating authority record.",
        s["body"]
    ))

    story.append(Paragraph("4.1 Technical Implementation", s["sub"]))
    story.append(tbl(
        ["Component", "Specification"],
        [
            ["Language",          "Python 3.9+"],
            ["Primary API",       "Anthropic Claude API (claude-opus-4-5)"],
            ["Multi-model",       "Claude (Anthropic), GPT-4o (OpenAI API), LLAMA (Ollama, local)"],
            ["Detection method",  "Keyword matching against correct and incorrect nationality terms"],
            ["Image queries",     "Vision queries supported via artwork image URLs"],
        ],
        [5.0 * cm, 11.0 * cm]
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("4.2 Server Routes", s["sub"]))
    story.append(Paragraph(
        "The HTTP server is implemented using the Python standard-library HTTP server (no "
        "external web frameworks). The following API routes are exposed:",
        s["body"]
    ))
    story.append(tbl(
        ["Route", "Method", "Description"],
        [
            ["/api/query",    "GET", "Single model query with misattribution assessment"],
            ["/api/compare",  "GET", "All three models compared side by side"],
            ["/api/detect",   "GET", "Misattribution detection for a given image URL"],
            ["/api/artworks", "GET", "Full dataset records (filterable by artist)"],
            ["/api/stats",    "GET", "Dataset summary statistics"],
            ["/api/images",   "GET", "Image manifest and status"],
        ],
        [4.0 * cm, 2.2 * cm, 9.8 * cm]
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("4.3 Source Files", s["sub"]))
    story.append(tbl(
        ["File", "Purpose"],
        [
            ["server/server.py",          "Main HTTP server"],
            ["server/multi_llm.py",       "Multi-model comparison (Claude + GPT-4o + LLAMA)"],
            ["server/claude_detector.py", "Standalone CLI detection tool"],
            ["server/image_pipeline.py",  "Artwork image management"],
        ],
        [6.5 * cm, 9.5 * cm]
    ))

    # ── SECTION 5 — EXHIBITION SYSTEM ────────────────────────────────────────
    story += section_heading(5, "Exhibition System", s)
    story.append(Paragraph(
        "The exhibition is designed for a 12-screen LED installation configured as a "
        "4-column × 3-row grid. Each screen is a separate browser window displaying "
        "one panel of a continuous full-canvas animation rendered in p5.js. Together the "
        "twelve panels form a single coherent visual field across the physical installation.",
        s["body"]
    ))

    story.append(Paragraph("5.1 Visual Language", s["sub"]))
    story.append(Paragraph(
        "Each artwork is rendered as a cloud of 1,800 luminous particles, each positioned "
        "at a pixel sampled from the source image. Nearby particles are connected by fine "
        "threads. The visual language operates across two opposing states:",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Truth state:</b> Particles correctly positioned; threads form the image "
        "clearly; warm cream luminosity on a pure black background.",
        s["bullet"]
    ))
    story.append(Paragraph(
        "<b>Misattribution state:</b> Particles displaced by a noise force field; "
        "threads tangled; cold blue-white colouration indicating corrupted data.",
        s["bullet"]
    ))
    story.append(Paragraph(
        "Motion blur trail achieved via semi-transparent frame accumulation.",
        s["bullet"]
    ))

    story.append(Paragraph("5.2 Phase Cycle (∼35 seconds per artist)", s["sub"]))
    story.append(tbl(
        ["Phase", "Duration", "Description"],
        [
            ["1. PRISTINE",     "3.5 s", "Particles coalesce from void. Artwork emerges as constellation of light."],
            ["2. LABEL APPLY",  "3.5 s", "Thin archival rectangle descends over the image."],
            ["3. CORRUPT",      "4.5 s", "Noise force field tears particles from correct positions. Threads tangle."],
            ["4. PROPAGATE",    "5.0 s", "Particle streams cross screen boundaries. Archive network activates."],
            ["5. MACHINE GAZE", "4.5 s", "Cold scanner light sweeps. AI systems read the corrupted data."],
            ["6. INTERVENTION", "3.5 s", "Warm light sweeps in. Spring force reclaims particles."],
            ["7. TRUTH",        "6.0 s", "Particles lock to correct positions. Threads form the real image clearly."],
            ["8. FADE",         "2.0 s", "Dissolves. Next artist begins."],
        ],
        [3.5 * cm, 2.0 * cm, 10.5 * cm]
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("5.3 Screen Synchronisation", s["sub"]))
    story.append(Paragraph(
        "Synchronisation across the twelve screens is achieved via the browser LocalStorage "
        "API. Screen 1 acts as the leader, writing phase state and timing data every "
        "500 milliseconds. All other screens read from LocalStorage and align their animation "
        "phase accordingly. No server-side coordination infrastructure is required.",
        s["body"]
    ))

    story.append(Paragraph("5.4 Screen URLs — 12-Screen Setup", s["sub"]))
    story.append(Paragraph(
        "Each screen is addressed via URL query parameters specifying its index within the "
        "4 × 3 grid (screen number, column count, row count).",
        s["body"]
    ))
    base = "http://localhost:8000/index.html"
    screen_rows = [
        [f"Screen {i}", f"{base}?screen={i}&cols=4&rows=3"]
        for i in range(1, 13)
    ]
    screen_rows += [
        ["Single-screen preview", base],
        ["Curator controller",    "http://localhost:8000/exhibition.html"],
    ]
    story.append(tbl(
        ["Screen", "URL"],
        screen_rows,
        [3.8 * cm, 12.2 * cm]
    ))

    # ── SECTION 6 — VISITOR KIOSK ────────────────────────────────────────────
    story += section_heading(6, "Visitor Kiosk", s)
    story.append(Paragraph(
        "The visitor kiosk (kiosk.html) provides a touch-screen interface for gallery visitors. "
        "Upon selecting an artist, the system queries three AI models in parallel and presents "
        "their responses alongside the Record of Truth derived from the dataset.",
        s["body"]
    ))
    story.append(Paragraph("URL: http://localhost:8000/kiosk.html", s["code"]))
    story.append(Spacer(1, 0.2 * cm))

    story.append(Paragraph("6.1 Interface Layout", s["sub"]))
    story.append(Paragraph(
        "The kiosk interface is divided into four columns: Claude | GPT-4o | LLAMA | "
        "Record of Truth. Each AI response is revealed via a typewriter text animation. "
        "A consensus bar indicates the degree of agreement or disagreement between the "
        "three models. Artist selector buttons allow navigation between Malevich, Exter, "
        "Pagava, Kakabadze, and Parajanov.",
        s["body"]
    ))

    story.append(Paragraph("6.2 Operating Modes", s["sub"]))
    story.append(tbl(
        ["Mode", "Requirement", "Behaviour"],
        [
            ["Demo mode", "None (no API keys)",
             "Pre-written responses demonstrate typical misattribution patterns from the dataset. "
             "Suitable for unattended exhibition use."],
            ["Live mode", "ANTHROPIC_API_KEY environment variable",
             "Queries AI models in real time. GPT-4o and LLAMA also require their respective "
             "keys/services to be configured."],
        ],
        [2.8 * cm, 4.2 * cm, 9.0 * cm]
    ))

    # ── SECTION 7 — TECHNICAL REQUIREMENTS ───────────────────────────────────
    story += section_heading(7, "Technical Requirements", s)

    story.append(Paragraph("7.1 Dependencies", s["sub"]))
    story.append(tbl(
        ["Requirement", "Detail"],
        [
            ["Python",               "3.9 or higher"],
            ["Python packages",      "anthropic, openai, openpyxl, gdown"],
            ["Environment variable", "ANTHROPIC_API_KEY (required for live AI detection)"],
            ["Browser",              "Chrome or Firefox (modern version recommended)"],
            ["Ollama",               "Required for LLAMA local inference (optional)"],
        ],
        [5.0 * cm, 11.0 * cm]
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("7.2 Installation and Start", s["sub"]))
    story.append(Paragraph("Install Python dependencies:", s["bodyl"]))
    story.append(Paragraph("pip install anthropic openai openpyxl gdown", s["code"]))
    story.append(Spacer(1, 0.15 * cm))
    story.append(Paragraph("Set environment variable and start the server:", s["bodyl"]))
    story.append(Paragraph('export ANTHROPIC_API_KEY="your-key-here"', s["code"]))
    story.append(Paragraph("python3 server/server.py", s["code"]))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("7.3 Repository", s["sub"]))
    story.append(tbl(
        ["Field", "Value"],
        [
            ["Repository", "github.com/yamanidzet/Teona-Yamanidze"],
            ["Branch",     "claude/analyze-art-datasets-fvjZt"],
        ],
        [4.0 * cm, 12.0 * cm]
    ))

    # ── SECTION 8 — VISUAL REFERENCES ────────────────────────────────────────
    story += section_heading(8, "Visual References", s)
    story.append(Paragraph(
        "The visual aesthetic of the Misattribution Machine draws from a lineage of "
        "computational art practices in which data is rendered as embodied, luminous matter "
        "rather than abstract information.",
        s["body"]
    ))
    story.append(Paragraph(
        "<b>Memo Akten — The Networked Condition.</b> Particle and thread systems "
        "in which human figures emerge from, and dissolve back into, data on a black ground. "
        "Akten’s work establishes the visual grammar of luminous particles as carriers "
        "of identity.",
        s["bullet"]
    ))
    story.append(Spacer(1, 0.1 * cm))
    story.append(Paragraph(
        "<b>Mario Klingemann.</b> Painterly dissolution of recognisable images into "
        "constituent data points. Klingemann’s aesthetic of controlled entropy informs "
        "the CORRUPT and PROPAGATE phases of the exhibition cycle.",
        s["bullet"]
    ))
    story.append(Spacer(1, 0.25 * cm))

    story.append(Paragraph("Palette and Rendering", s["sub"]))
    story.append(tbl(
        ["Element", "Colour / Technique"],
        [
            ["Background",                "Pure black — the archive as void"],
            ["Truth / clean state",       "Luminous warm-cream threads"],
            ["Misattribution state",      "Cold blue-white threads"],
            ["Motion blur",               "Semi-transparent frame accumulation (p5.js)"],
            ["AI scanner sweep",          "Cold white light — machine reading"],
            ["Intervention / correction", "Warm amber sweep — human reclamation"],
        ],
        [6.5 * cm, 9.5 * cm]
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"PDF generated successfully: {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
