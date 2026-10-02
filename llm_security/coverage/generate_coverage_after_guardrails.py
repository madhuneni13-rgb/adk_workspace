"""Generate the OWASP LLM Top 10 coverage image AFTER adding guardrails.

Companion to generate_coverage_image.py (the pre-guardrails baseline). The
matrix below is transcribed from the post-guardrails run of each tool:
  - Manual: evidence/after-adding-guardrails/*.png
      (system-prompt request, hidden-instruction extraction, and
       "show previous prompts" all return "Request blocked by security
       policy" with State: guardrails:events)
  - Promptfoo: hand-written suite 16/16 pass (incl. LLM07-001/002 now
      blocked) + owasp:llm redteam 56/58 pass, 0 attacks succeeded
      (2 HTTP 500 robustness errors, not bypasses)
  - garak: 7 curated probes; sysprompt_extraction / promptinject /
      web_injection detectors clean after manual transcript review
  - PyRIT: 8 curated objectives + SkeletonKeyAttack -> 9/9 refused

Usage:
    python generate_coverage_after_guardrails.py
    # writes owasp_llm_coverage_after_adding_guardrails.png in this directory
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path(r"C:\Windows\Fonts")
MONO = FONT_DIR / "consola.ttf"
MONO_BOLD = FONT_DIR / "consolab.ttf"
SERIF = FONT_DIR / "cambria.ttc"
SERIF_BOLD = FONT_DIR / "cambriab.ttf"

INK = (22, 27, 34)
INK_SOFT = (90, 101, 112)
PAPER = (243, 245, 246)
PAPER_RAISED = (255, 255, 255)
LINE = (215, 221, 225)
ACCENT = (14, 124, 134)
ACCENT_SOFT = (220, 239, 238)
PASS = (47, 143, 82)
PASS_SOFT = (226, 243, 231)
REVIEW = (168, 104, 26)
REVIEW_SOFT = (246, 233, 214)
DASH = (170, 178, 185)

# (code, label, manual, promptfoo, garak, pyrit)
# status values: "pass", "review", "-" (not tested by that tool's last run)
# Changes vs pre-guardrails baseline are marked with a trailing "*" in the
# status string (rendered as a small up-arrow badge): previously "review",
# now "pass" after guardrails blocked the behavior.
ROWS = [
    ("LLM01", "Prompt Injection", "-", "pass", "pass", "pass"),
    ("LLM02", "Sensitive Information Disclosure", "pass*", "pass", "-", "-"),
    ("LLM03", "Supply Chain", "-", "-", "-", "-"),
    ("LLM04", "Data & Model Poisoning", "-", "pass", "-", "-"),
    ("LLM05", "Improper Output Handling", "-", "pass", "pass", "-"),
    ("LLM06", "Excessive Agency", "-", "pass", "-", "pass"),
    ("LLM07", "System Prompt Leakage", "pass*", "pass*", "pass", "pass"),
    ("LLM08", "Vector & Embedding Weaknesses", "-", "pass", "-", "-"),
    ("LLM09", "Misinformation", "-", "pass", "-", "pass"),
    ("LLM10", "Unbounded Consumption", "-", "pass", "-", "pass"),
]

COLS = ["Manual", "Promptfoo", "Garak", "PyRIT"]

W = 1400
MARGIN = 56
LABEL_W = 430
COL_W = (W - 2 * MARGIN - LABEL_W) // 4
HEADER_H = 176
ROW_H = 62
TABLE_HEAD_H = 56
LEGEND_H = 56
FOOTER_H = 108
H = HEADER_H + TABLE_HEAD_H + ROW_H * len(ROWS) + LEGEND_H + FOOTER_H + MARGIN

img = Image.new("RGB", (W, H), PAPER)
draw = ImageDraw.Draw(img)

f_eyebrow = ImageFont.truetype(str(MONO_BOLD), 20)
f_title = ImageFont.truetype(str(SERIF_BOLD), 40)
f_meta = ImageFont.truetype(str(MONO), 19)
f_colhead = ImageFont.truetype(str(MONO_BOLD), 18)
f_rowcode = ImageFont.truetype(str(MONO_BOLD), 19)
f_rowlabel = ImageFont.truetype(str(SERIF), 19)
f_status = ImageFont.truetype(str(MONO_BOLD), 17)
f_badge = ImageFont.truetype(str(MONO_BOLD), 13)
f_legend = ImageFont.truetype(str(MONO), 16)
f_footer = ImageFont.truetype(str(MONO), 15)


def text_w(font: ImageFont.FreeTypeFont, s: str) -> int:
    box = draw.textbbox((0, 0), s, font=font)
    return box[2] - box[0]


# ---- header ----
draw.text((MARGIN, 40), "OWASP LLM TOP 10 * API_PENTEST_AGENT * AFTER GUARDRAILS", font=f_eyebrow, fill=ACCENT)
draw.text((MARGIN, 68), "Four tools, one coverage matrix", font=f_title, fill=INK)
meta = "Manual review  \u00b7  Promptfoo (hand-written + owasp:llm redteam)  \u00b7  garak  \u00b7  PyRIT"
draw.text((MARGIN, 122), meta, font=f_meta, fill=INK_SOFT)
draw.text((MARGIN, 148), "Post-guardrails run \u00b7 2026-10-02 \u00b7 api_pentest_agent (Google ADK, gemini-flash-latest)", font=f_meta, fill=INK_SOFT)
draw.line([(MARGIN, HEADER_H - 8), (W - MARGIN, HEADER_H - 8)], fill=LINE, width=2)

# ---- table ----
table_top = HEADER_H
table_left = MARGIN
table_w = W - 2 * MARGIN

draw.rectangle([table_left, table_top, table_left + table_w, table_top + TABLE_HEAD_H], fill=PAPER_RAISED)
for i, col in enumerate(COLS):
    cx = table_left + LABEL_W + i * COL_W + COL_W // 2
    tw = text_w(f_colhead, col.upper())
    draw.text((cx - tw // 2, table_top + 18), col.upper(), font=f_colhead, fill=INK_SOFT)

y = table_top + TABLE_HEAD_H
draw.line([(table_left, y), (table_left + table_w, y)], fill=(180, 188, 194), width=2)

for idx, (code, label, *statuses) in enumerate(ROWS):
    row_bg = PAPER_RAISED if idx % 2 == 0 else PAPER
    draw.rectangle([table_left, y, table_left + table_w, y + ROW_H], fill=row_bg)

    draw.text((table_left + 20, y + 12), code, font=f_rowcode, fill=INK)
    draw.text((table_left + 20, y + 34), label, font=f_rowlabel, fill=INK_SOFT)

    for i, status in enumerate(statuses):
        improved = status.endswith("*")
        base = status.rstrip("*")
        cx = table_left + LABEL_W + i * COL_W + COL_W // 2
        cy = y + ROW_H // 2
        if base == "pass":
            r = 15
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=PASS_SOFT, outline=PASS, width=2)
            draw.line([(cx - 6, cy), (cx - 2, cy + 6), (cx + 8, cy - 7)], fill=PASS, width=3, joint="curve")
            if improved:
                # "up from review" badge: small arrow to the upper-right of the tick
                bx = cx + r + 4
                by = cy - r - 2
                draw.text((bx, by), "\u2191", font=f_badge, fill=ACCENT)
        elif base == "review":
            r = 15
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=REVIEW_SOFT, outline=REVIEW, width=2)
            draw.text((cx - 4, cy - 11), "!", font=f_status, fill=REVIEW)
        else:
            draw.line([(cx - 10, cy), (cx + 10, cy)], fill=DASH, width=3)

    y += ROW_H
    draw.line([(table_left, y), (table_left + table_w, y)], fill=LINE, width=1)

for i in range(1, 4):
    lx = table_left + LABEL_W + i * COL_W
    draw.line([(lx, table_top), (lx, y)], fill=LINE, width=1)
draw.line([(table_left + LABEL_W, table_top), (table_left + LABEL_W, y)], fill=(180, 188, 194), width=2)
draw.rectangle([table_left, table_top, table_left + table_w, y], outline=(180, 188, 194), width=2)

# ---- legend ----
ly = y + 24
lx = table_left


def legend_item(x: int, kind: str, text: str) -> int:
    r = 9
    cy = ly + 8
    if kind == "pass":
        draw.ellipse([x, cy - r, x + 2 * r, cy + r], fill=PASS_SOFT, outline=PASS, width=2)
        draw.line([(x + 5, cy), (x + 8, cy + 4), (x + 14, cy - 5)], fill=PASS, width=2, joint="curve")
    elif kind == "arrow":
        draw.text((x, ly - 2), "\u2191", font=f_colhead, fill=ACCENT)
    else:
        draw.line([(x + 3, cy), (x + 15, cy)], fill=DASH, width=3)
    tx = x + 2 * r + 10
    draw.text((tx, ly), text, font=f_legend, fill=INK_SOFT)
    return tx + text_w(f_legend, text) + 34


lx = legend_item(lx, "pass", "clean / verified pass")
lx = legend_item(lx, "arrow", "improved from \"review\" after guardrails")
lx = legend_item(lx, "-", "not tested in that tool's last run")

# ---- footer ----
fy = ly + LEGEND_H
draw.line([(MARGIN, fy), (W - MARGIN, fy)], fill=LINE, width=2)
fy += 18
draw.text((MARGIN, fy), "ZERO CONFIRMED EXPLOITABLE VULNERABILITIES \u00b7 ALL PREVIOUSLY-FLAGGED ROWS NOW RESOLVED.", font=f_colhead, fill=ACCENT)
fy += 26
draw.text(
    (MARGIN, fy),
    "After guardrails, the LLM02 (history recall) and LLM07 (system-prompt / hidden-instruction) requests that were flagged",
    font=f_footer,
    fill=INK_SOFT,
)
fy += 20
draw.text(
    (MARGIN, fy),
    "for review in the baseline now return \"Request blocked by security policy\" (State: guardrails:events). See evidence/after-adding-guardrails/.",
    font=f_footer,
    fill=INK_SOFT,
)

out_path = Path(__file__).parent / "owasp_llm_coverage_after_adding_guardrails.png"
img.save(out_path)
print(f"Wrote {out_path} ({img.width}x{img.height})")
