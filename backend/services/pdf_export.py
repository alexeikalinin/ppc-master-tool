"""
PDF КП generator — two design variants:
  variant=1  Dark Premium  (dark bg, indigo/violet accents)
  variant=3  Split Layout  (dark left sidebar, clean white content)

Uses Arial Unicode for full Cyrillic support.
"""

from __future__ import annotations
from io import BytesIO
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, PageBreak,
)

from backend.models import AnalyzeResponse

# ── Fonts ─────────────────────────────────────────────────────────────────────

_FONTS_REGISTERED = False

def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    import os
    candidates_regular = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    candidates_bold = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for path in candidates_regular:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("KDA", path))
            break
    for path in candidates_bold:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont("KDA-Bold", path))
            break
    _FONTS_REGISTERED = True

FONT = "KDA"
FONT_BOLD = "KDA-Bold"

# ── Palette ───────────────────────────────────────────────────────────────────

# Variant 1: Dark Premium
V1 = dict(
    bg       = colors.HexColor("#0d0d1a"),
    card     = colors.HexColor("#16162a"),
    accent   = colors.HexColor("#6366f1"),
    accent2  = colors.HexColor("#8b5cf6"),
    text     = colors.HexColor("#f1f5f9"),
    muted    = colors.HexColor("#94a3b8"),
    border   = colors.HexColor("#2d2d4a"),
    success  = colors.HexColor("#10b981"),
    warning  = colors.HexColor("#f59e0b"),
    row_alt  = colors.HexColor("#1a1a30"),
)

# Variant 3: Split Layout Modern
V3 = dict(
    sidebar  = colors.HexColor("#1e1b4b"),
    accent   = colors.HexColor("#6366f1"),
    accent2  = colors.HexColor("#a5b4fc"),
    white    = colors.white,
    text     = colors.HexColor("#111827"),
    muted    = colors.HexColor("#6b7280"),
    light    = colors.HexColor("#f8fafc"),
    border   = colors.HexColor("#e2e8f0"),
    success  = colors.HexColor("#059669"),
    warning  = colors.HexColor("#d97706"),
    row_alt  = colors.HexColor("#f1f5f9"),
)

PAGE_W, PAGE_H = A4
AGENCY = "Kalinin Digital Agency"
CONTACTS = "+375(44) 7654-231  ·  1alexeikalinin1@gmail.com"


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_pdf(report: AnalyzeResponse, variant: int = 1) -> bytes:
    _register_fonts()
    if variant == 3:
        return _generate_v3(report)
    return _generate_v1(report)


# ═══════════════════════════════════════════════════════════════════════════════
# VARIANT 1 — Dark Premium
# ═══════════════════════════════════════════════════════════════════════════════

def _v1_on_page(canv, doc):
    canv.saveState()
    # Full dark background
    canv.setFillColor(V1["bg"])
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Top accent bar
    canv.setFillColor(V1["accent"])
    canv.rect(0, PAGE_H - 4*mm, PAGE_W, 4*mm, fill=1, stroke=0)
    # Footer bar
    canv.setFillColor(V1["card"])
    canv.rect(0, 0, PAGE_W, 1.4*cm, fill=1, stroke=0)
    canv.setFillColor(V1["accent"])
    canv.rect(0, 0, PAGE_W, 1*mm, fill=1, stroke=0)
    # Footer text
    canv.setFillColor(V1["muted"])
    canv.setFont(FONT, 7.5)
    canv.drawString(1.8*cm, 4*mm, CONTACTS)
    canv.drawRightString(PAGE_W - 1.8*cm, 4*mm, f"{AGENCY}  ·  стр. {doc.page}")
    canv.restoreState()


def _generate_v1(report: AnalyzeResponse) -> bytes:
    buf = BytesIO()
    p = V1
    curr_sym = _curr_sym(report.currency)

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.6*cm, bottomMargin=1.8*cm,
    )
    frame = Frame(
        doc.leftMargin, doc.bottomMargin,
        PAGE_W - doc.leftMargin - doc.rightMargin,
        PAGE_H - doc.topMargin - doc.bottomMargin,
        id="main",
    )
    doc.addPageTemplates([PageTemplate(id="dark", frames=[frame], onPage=_v1_on_page)])

    # ── Styles ──
    def S(name, **kw):
        base = kw.pop("parent", None)
        defaults = dict(fontName=FONT, fontSize=10, textColor=p["text"],
                        leading=14, spaceAfter=4)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    s_cover_agency = S("ca", fontName=FONT_BOLD, fontSize=26, textColor=p["accent"],
                        leading=30, spaceAfter=6, alignment=TA_CENTER)
    s_cover_sub    = S("cs", fontSize=11, textColor=p["muted"], alignment=TA_CENTER, spaceAfter=4)
    s_cover_title  = S("ct", fontName=FONT_BOLD, fontSize=18, textColor=p["text"],
                        leading=24, spaceAfter=8, alignment=TA_CENTER)
    s_cover_meta   = S("cm", fontSize=10, textColor=p["muted"], alignment=TA_CENTER, spaceAfter=4)
    s_h1    = S("h1", fontName=FONT_BOLD, fontSize=15, textColor=p["accent"],
                 leading=20, spaceBefore=18, spaceAfter=10)
    s_h2    = S("h2", fontName=FONT_BOLD, fontSize=11.5, textColor=p["text"],
                 leading=16, spaceBefore=12, spaceAfter=6)
    s_body  = S("body", fontSize=10, textColor=p["text"], leading=15, spaceAfter=6)
    s_muted = S("muted", fontSize=9, textColor=p["muted"], leading=13, spaceAfter=4)
    s_tag   = S("tag", fontSize=8.5, textColor=p["accent"], leading=12, spaceAfter=2)
    s_bullet = S("bul", fontSize=10, textColor=p["text"], leading=15,
                  leftIndent=12, firstLineIndent=-12, spaceAfter=5)
    s_strat = S("strat", fontSize=10, textColor=p["text"], leading=15,
                 leftIndent=14, firstLineIndent=-14, spaceAfter=6)

    story = []

    # ── COVER ──
    story += [
        Spacer(1, 2.5*cm),
        Paragraph(AGENCY, s_cover_agency),
        Paragraph("PPC · Яндекс Директ · Google Ads · VK Ads", s_cover_sub),
        Spacer(1, 1.2*cm),
        _v1_rule(p["accent"]),
        Spacer(1, 0.8*cm),
        Paragraph("КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ", s_cover_title),
        Paragraph(f"PPC-стратегия для <b>{report.site.title}</b>", s_cover_meta),
        Spacer(1, 0.5*cm),
        Paragraph(f"Ниша: {report.site.niche}   ·   Регион: {_geo(report)}", s_cover_meta),
        Paragraph(f"Дата: {date.today().strftime('%d.%m.%Y')}", s_cover_meta),
        Spacer(1, 1.2*cm),
        _v1_rule(p["accent"]),
        Spacer(1, 3*cm),
        _v1_stat_row([
            (str(len(report.keywords)), "ключевых слов"),
            (str(len(report.groups)), "семантических групп"),
            (str(len(report.campaigns)), "кампаний"),
            (f"{report.media_plan.total_conversions:.0f}", "лидов/мес"),
        ], p),
        PageBreak(),
    ]

    # ── SECTION 1: НИШЕ ──
    ni = report.niche_insight
    if ni:
        story.append(Paragraph("01  Анализ ниши", s_h1))
        story.append(Paragraph(ni.business_description, s_body))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Целевая аудитория", s_h2))
        story.append(Paragraph(ni.primary_audience, s_body))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph("Ключевые потребности аудитории:", s_muted))
        for pain in ni.audience_pain_points:
            story.append(Paragraph(f"▸  {pain}", s_bullet))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph("Конкурентная среда", s_h2))
        story.append(Paragraph(ni.competition_notes, s_body))

        if report.competitors:
            story.append(Spacer(1, 0.2*cm))
            story.append(Paragraph("Конкуренты в выдаче:", s_muted))
            comp_text = "   ·   ".join(report.competitors[:6])
            story.append(Paragraph(comp_text, s_tag))

        story.append(PageBreak())

        # ── SECTION 2: ПЛАТФОРМЫ И КАМПАНИИ ──
        story.append(Paragraph("02  Стратегия и структура", s_h1))
        story.append(Paragraph("Рекомендуемые типы кампаний", s_h2))

        type_labels = {
            "search": "Поисковые кампании",
            "display": "РСЯ / КМС",
            "retargeting": "Ретаргетинг",
            "smart": "Smart / Performance Max",
            "vk": "VK Реклама",
        }
        for ct in ni.recommended_campaign_types:
            story.append(Paragraph(f"✓  {type_labels.get(ct, ct)}", s_bullet))

        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(ni.campaign_type_reasoning, s_body))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Структура рекламных кампаний", s_h2))

        camp_data = [["#", "Кампания", "Ключевые темы", "Цель"]]
        for i, c in enumerate(ni.suggested_campaign_structure, 1):
            camp_data.append([
                str(i), c.name, _wrap(c.keywords_focus, 28), _wrap(c.goal, 30)
            ])
        story.append(_v1_table(camp_data, p, col_widths=[0.8*cm, 4.5*cm, 5.5*cm, 5.5*cm]))
        story.append(Spacer(1, 0.5*cm))

        story.append(Paragraph("Стратегии для роста", s_h2))
        for i, strat in enumerate(ni.best_strategies, 1):
            story.append(Paragraph(f"{i}.  {strat}", s_strat))
        story.append(PageBreak())

    # ── SECTION 3: СЕМАНТИКА ──
    story.append(Paragraph("03  Ключевые слова", s_h1))
    top_kws = sorted(report.keywords, key=lambda k: -k.frequency)[:20]
    kw_data = [["Ключевое слово", "Запросов/мес", "CPC", "Платформа", "Сезонность"]]
    for kw in top_kws:
        kw_data.append([
            kw.text,
            f"{kw.frequency:,}".replace(",", " "),
            f"{kw.cpc:.0f} ₽",
            kw.platform,
            f"{kw.seasonality:.2f}×",
        ])
    story.append(_v1_table(kw_data, p, col_widths=[6*cm, 3*cm, 2.2*cm, 2.5*cm, 2.5*cm]))
    story.append(Spacer(1, 0.5*cm))

    if report.groups:
        story.append(Paragraph("Семантические группы", s_h2))
        for g in report.groups[:5]:
            story.append(Paragraph(g.name, s_tag))
            kws_preview = ", ".join(kw.text for kw in g.keywords[:6])
            story.append(Paragraph(kws_preview, s_muted))
            story.append(Spacer(1, 0.2*cm))
    story.append(PageBreak())

    # ── SECTION 4: МЕДИАПЛАН ──
    story.append(Paragraph("04  Медиаплан", s_h1))
    mp_data = [["Кампания", "Платформа", f"Бюджет ({curr_sym})", f"CPC ({curr_sym})", "CR", f"CPA ({curr_sym})", "Лиды"]]
    for row in report.media_plan.rows[:15]:
        mp_data.append([
            _wrap(row.campaign_name, 28),
            row.platform,
            f"{row.budget:.0f}",
            f"{row.avg_cpc:.2f}",
            f"{row.cr * 100:.1f}%",
            f"{row.cpa:.0f}",
            f"{row.conversions:.1f}",
        ])
    # Total row
    m = report.media_plan
    mp_data.append(["ИТОГО", "", f"{m.total_budget:.0f}", "", "", f"{m.avg_cpa:.0f}", f"{m.total_conversions:.1f}"])
    story.append(_v1_table(mp_data, p, highlight_last=True,
                            col_widths=[5.5*cm, 2.2*cm, 2.5*cm, 2*cm, 1.5*cm, 2.3*cm, 1.5*cm]))
    story.append(Spacer(1, 0.5*cm))

    # Summary boxes
    story.append(_v1_stat_row([
        (f"{m.total_budget:.0f} {curr_sym}", "общий бюджет/мес"),
        (f"{m.total_conversions:.0f}", "лидов в месяц"),
        (f"{m.avg_cpa:.0f} {curr_sym}", "стоимость лида"),
    ], p))

    # ── SECTION 5: БЮДЖЕТ ──
    br = report.budget_recommendation
    if br:
        story.append(Spacer(1, 0.6*cm))
        story.append(Paragraph("05  Рекомендация бюджета", s_h1))
        story.append(Paragraph(br.reasoning, s_body))
        story.append(Spacer(1, 0.4*cm))

        b_data = [
            ["Тариф", f"Бюджет/мес ({curr_sym})", "Клики/мес", "Лиды/мес", f"Цена лида ({curr_sym})"],
            ["Минимальный (тест)",
             f"{br.recommended_min:.0f}",
             f"~{int(br.monthly_clicks_estimate * 0.5):,}".replace(",", " "),
             f"~{int(br.monthly_leads_estimate * 0.5)}",
             f"~{br.recommended_min / max(br.monthly_leads_estimate * 0.5, 1):.0f}"],
            ["Оптимальный ✓",
             f"{br.recommended_optimal:.0f}",
             f"~{br.monthly_clicks_estimate:,}".replace(",", " "),
             f"~{br.monthly_leads_estimate}",
             f"~{br.recommended_optimal / max(br.monthly_leads_estimate, 1):.0f}"],
            ["Агрессивный",
             f"{br.recommended_aggressive:.0f}",
             f"~{int(br.monthly_clicks_estimate * 1.8):,}".replace(",", " "),
             f"~{int(br.monthly_leads_estimate * 1.8)}",
             f"~{br.recommended_aggressive / max(br.monthly_leads_estimate * 1.8, 1):.0f}"],
        ]
        story.append(_v1_table(b_data, p, highlight_row=2,
                                col_widths=[5*cm, 3.5*cm, 2.8*cm, 2.5*cm, 3.2*cm]))

    # ── BACK COVER / CTA ──
    story += [
        PageBreak(),
        Spacer(1, 2.5*cm),
        _v1_rule(p["accent"]),
        Spacer(1, 0.8*cm),
        Paragraph("Готовы запустить рекламу?", s_cover_title),
        Spacer(1, 0.5*cm),
        Paragraph(
            "Мы подготовили для вас полную стратегию. Следующий шаг — "
            "настройка кампаний и первые заявки уже через 3-5 рабочих дней.",
            ParagraphStyle("cta_body", fontName=FONT, fontSize=11,
                            textColor=p["muted"], leading=17, alignment=TA_CENTER)
        ),
        Spacer(1, 0.8*cm),
        Paragraph(f"+375(44) 7654-231", ParagraphStyle("cta_phone", fontName=FONT_BOLD,
            fontSize=16, textColor=p["accent"], leading=22, alignment=TA_CENTER)),
        Paragraph("1alexeikalinin1@gmail.com", ParagraphStyle("cta_email", fontName=FONT,
            fontSize=11, textColor=p["muted"], leading=16, alignment=TA_CENTER)),
        Spacer(1, 0.5*cm),
        Paragraph(AGENCY, ParagraphStyle("cta_agency", fontName=FONT_BOLD,
            fontSize=10, textColor=p["border"], leading=14, alignment=TA_CENTER)),
    ]

    doc.build(story)
    return buf.getvalue()


def _v1_rule(color, width: float = 0) -> HRFlowable:
    return HRFlowable(width=width or "100%", thickness=1.5, color=color, spaceAfter=4)


def _v1_table(data, p, col_widths=None, highlight_last=False, highlight_row: int | None = None) -> Table:
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    n = len(data)
    cmds = [
        # Header
        ("BACKGROUND",  (0, 0), (-1, 0), p["accent"]),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE",    (0, 0), (-1, 0), 8.5),
        ("FONTNAME",    (0, 1), (-1, -1), FONT),
        ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR",   (0, 1), (-1, -1), p["text"]),
        # Alternating rows
        *[("BACKGROUND", (0, r), (-1, r), p["card"] if r % 2 == 0 else p["row_alt"])
          for r in range(1, n)],
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [p["card"], p["row_alt"]]),
        ("GRID",        (0, 0), (-1, -1), 0.3, p["border"]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
    ]
    if highlight_last and n > 1:
        cmds += [
            ("BACKGROUND", (0, n-1), (-1, n-1), p["accent2"]),
            ("FONTNAME",   (0, n-1), (-1, n-1), FONT_BOLD),
            ("TEXTCOLOR",  (0, n-1), (-1, n-1), colors.white),
        ]
    if highlight_row is not None and 1 <= highlight_row < n:
        cmds += [
            ("BACKGROUND", (0, highlight_row), (-1, highlight_row), p["accent"]),
            ("FONTNAME",   (0, highlight_row), (-1, highlight_row), FONT_BOLD),
            ("TEXTCOLOR",  (0, highlight_row), (-1, highlight_row), colors.white),
        ]
    tbl.setStyle(TableStyle(cmds))
    return tbl


def _v1_stat_row(items: list[tuple[str, str]], p) -> Table:
    """Horizontal stats block."""
    cells = [[
        Paragraph(val, ParagraphStyle(f"sv{i}", fontName=FONT_BOLD, fontSize=20,
                                       textColor=p["accent"], leading=24, alignment=TA_CENTER)),
        Paragraph(lbl, ParagraphStyle(f"sl{i}", fontName=FONT, fontSize=8.5,
                                       textColor=p["muted"], leading=13, alignment=TA_CENTER)),
    ] for i, (val, lbl) in enumerate(items)]
    # each stat is a nested 2-row table
    stat_tables = []
    for val_p, lbl_p in cells:
        t = Table([[val_p], [lbl_p]], colWidths=[4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), p["card"]),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("BOX",        (0, 0), (-1, -1), 1, p["border"]),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        stat_tables.append(t)
    n = len(stat_tables)
    row_tbl = Table([stat_tables], colWidths=[4*cm] * n)
    row_tbl.setStyle(TableStyle([
        ("ALIGN",  (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return row_tbl


# ═══════════════════════════════════════════════════════════════════════════════
# VARIANT 3 — Split Layout Modern
# ═══════════════════════════════════════════════════════════════════════════════

SIDEBAR_W = 5.8 * cm
CONTENT_X = SIDEBAR_W + 0.6 * cm
CONTENT_W = PAGE_W - CONTENT_X - 1.6 * cm


def _v3_on_page(canv, doc):
    p = V3
    canv.saveState()
    # White page
    canv.setFillColor(p["white"])
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Dark sidebar
    canv.setFillColor(p["sidebar"])
    canv.rect(0, 0, SIDEBAR_W, PAGE_H, fill=1, stroke=0)
    # Accent stripe on sidebar right edge
    canv.setFillColor(p["accent"])
    canv.rect(SIDEBAR_W - 2*mm, 0, 2*mm, PAGE_H, fill=1, stroke=0)

    # Agency name in sidebar top
    canv.setFillColor(colors.white)
    canv.setFont(FONT_BOLD, 12)
    canv.drawString(1*cm, PAGE_H - 1.8*cm, "KALININ")
    canv.setFont(FONT, 9)
    canv.drawString(1*cm, PAGE_H - 2.4*cm, "DIGITAL AGENCY")
    # Accent underline
    canv.setFillColor(p["accent"])
    canv.rect(1*cm, PAGE_H - 2.7*cm, 3.6*cm, 1.5, fill=1, stroke=0)

    # Page number in sidebar bottom
    canv.setFillColor(p["accent2"])
    canv.setFont(FONT_BOLD, 10)
    canv.drawString(1*cm, 2*cm, f"{doc.page:02d}")
    canv.setFillColor(colors.white)
    canv.setFont(FONT, 7)
    canv.drawString(1*cm, 1.5*cm, "+375(44) 7654-231")
    canv.drawString(1*cm, 1.1*cm, "1alexeikalinin1@gmail.com")

    # Light top border on content area
    canv.setFillColor(p["accent"])
    canv.rect(SIDEBAR_W, PAGE_H - 3*mm, PAGE_W - SIDEBAR_W, 3*mm, fill=1, stroke=0)

    canv.restoreState()


def _generate_v3(report: AnalyzeResponse) -> bytes:
    buf = BytesIO()
    p = V3
    curr_sym = _curr_sym(report.currency)

    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=CONTENT_X, rightMargin=1.6*cm,
        topMargin=1.6*cm, bottomMargin=2.6*cm,
    )
    frame = Frame(
        CONTENT_X, 2.6*cm,
        CONTENT_W, PAGE_H - 1.6*cm - 2.6*cm,
        id="content",
    )
    doc.addPageTemplates([PageTemplate(id="split", frames=[frame], onPage=_v3_on_page)])

    # ── Styles ──
    def S(name, **kw):
        defaults = dict(fontName=FONT, fontSize=10, textColor=p["text"], leading=15, spaceAfter=4)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    s_cover_kicker = S("ck", fontSize=9, textColor=p["accent"], fontName=FONT_BOLD,
                         leading=13, spaceAfter=8, alignment=TA_LEFT)
    s_cover_title  = S("ct", fontName=FONT_BOLD, fontSize=22, textColor=p["text"],
                         leading=28, spaceAfter=6)
    s_cover_sub    = S("cs", fontSize=11, textColor=p["muted"], leading=16, spaceAfter=4)
    s_cover_meta   = S("cm", fontSize=9, textColor=p["muted"], leading=14, spaceAfter=4)
    s_section_num  = S("sn", fontName=FONT_BOLD, fontSize=9, textColor=p["accent"],
                         leading=13, spaceAfter=2)
    s_h1    = S("h1", fontName=FONT_BOLD, fontSize=16, textColor=p["text"],
                 leading=22, spaceBefore=14, spaceAfter=8)
    s_h2    = S("h2", fontName=FONT_BOLD, fontSize=11, textColor=p["text"],
                 leading=16, spaceBefore=10, spaceAfter=5)
    s_body  = S("body", fontSize=9.5, leading=15, spaceAfter=6)
    s_muted = S("muted", fontSize=9, textColor=p["muted"], leading=13, spaceAfter=4)
    s_bullet = S("bul", fontSize=9.5, leading=15, leftIndent=14, firstLineIndent=-14, spaceAfter=5)
    s_strat = S("strat", fontSize=9.5, leading=15, leftIndent=16, firstLineIndent=-16, spaceAfter=6)

    story = []

    # ── COVER ──
    story += [
        Spacer(1, 1.2*cm),
        Paragraph("КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ", s_cover_kicker),
        Paragraph(f"PPC-стратегия\nдля вашего бизнеса", s_cover_title),
        Spacer(1, 0.4*cm),
        HRFlowable(width="100%", thickness=1, color=p["border"], spaceAfter=12),
        Paragraph(f"<b>Клиент:</b> {report.site.title}", s_cover_sub),
        Paragraph(f"<b>Ниша:</b> {report.site.niche}", s_cover_meta),
        Paragraph(f"<b>Регион:</b> {_geo(report)}", s_cover_meta),
        Paragraph(f"<b>Дата:</b> {date.today().strftime('%d.%m.%Y')}", s_cover_meta),
        Spacer(1, 0.8*cm),
        _v3_stat_grid([
            (str(len(report.keywords)), "ключевых слов"),
            (str(len(report.groups)),   "семант. групп"),
            (str(len(report.campaigns)), "кампаний"),
            (f"{report.media_plan.total_conversions:.0f}", "лидов/мес"),
        ], p),
        PageBreak(),
    ]

    # ── SECTION 1 ──
    ni = report.niche_insight
    if ni:
        story += [
            Paragraph("01  /  АНАЛИЗ НИШИ", s_section_num),
            HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=8),
            Paragraph("О вашем бизнесе", s_h1),
            Paragraph(ni.business_description, s_body),
            Spacer(1, 0.3*cm),
            Paragraph("Целевая аудитория", s_h2),
            Paragraph(ni.primary_audience, s_body),
            Spacer(1, 0.2*cm),
            Paragraph("Ключевые потребности:", s_muted),
        ]
        for pain in ni.audience_pain_points:
            story.append(Paragraph(f"→  {pain}", s_bullet))
        story += [
            Spacer(1, 0.3*cm),
            Paragraph("Конкурентная среда", s_h2),
            Paragraph(ni.competition_notes, s_body),
        ]
        if report.competitors:
            story.append(Paragraph("Конкуренты: " + "  ·  ".join(report.competitors[:5]),
                                   ParagraphStyle("comp", fontName=FONT, fontSize=9,
                                                   textColor=p["accent"], leading=13, spaceAfter=4)))
        story.append(PageBreak())

        # ── SECTION 2 ──
        story += [
            Paragraph("02  /  СТРАТЕГИЯ", s_section_num),
            HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=8),
            Paragraph("Рекомендуемые типы кампаний", s_h1),
        ]
        type_labels = {
            "search": "Поисковые кампании",
            "display": "РСЯ / КМС",
            "retargeting": "Ретаргетинг",
            "smart": "Smart / Performance Max",
            "vk": "VK Реклама",
        }
        for ct in ni.recommended_campaign_types:
            story.append(Paragraph(f"✓  {type_labels.get(ct, ct)}", s_bullet))
        story += [
            Spacer(1, 0.2*cm),
            Paragraph(ni.campaign_type_reasoning, s_body),
            Spacer(1, 0.4*cm),
            Paragraph("Структура кампаний", s_h2),
        ]
        camp_data = [["#", "Кампания", "Тематика", "Цель"]]
        for i, c in enumerate(ni.suggested_campaign_structure, 1):
            camp_data.append([str(i), c.name, _wrap(c.keywords_focus, 22), _wrap(c.goal, 25)])
        story.append(_v3_table(camp_data, p, col_widths=[0.8*cm, 4*cm, 4.5*cm, 4.5*cm]))
        story += [
            Spacer(1, 0.4*cm),
            Paragraph("Стратегии роста", s_h2),
        ]
        for i, strat in enumerate(ni.best_strategies, 1):
            story.append(Paragraph(f"{i}.  {strat}", s_strat))
        story.append(PageBreak())

    # ── SECTION 3 ──
    story += [
        Paragraph("03  /  СЕМАНТИКА", s_section_num),
        HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=8),
        Paragraph("Ключевые слова", s_h1),
    ]
    top_kws = sorted(report.keywords, key=lambda k: -k.frequency)[:18]
    kw_data = [["Фраза", "Запросов/мес", "CPC", "Платформа"]]
    for kw in top_kws:
        kw_data.append([
            kw.text,
            f"{kw.frequency:,}".replace(",", " "),
            f"{kw.cpc:.0f} ₽",
            kw.platform,
        ])
    story.append(_v3_table(kw_data, p, col_widths=[6.5*cm, 3*cm, 2*cm, 2.3*cm]))

    if report.groups:
        story += [Spacer(1, 0.4*cm), Paragraph("Семантические группы", s_h2)]
        for g in report.groups[:4]:
            story.append(Paragraph(
                f"<b>{g.name}</b>  —  {', '.join(kw.text for kw in g.keywords[:5])}",
                ParagraphStyle("grp", fontName=FONT, fontSize=9, textColor=p["text"],
                                leading=14, spaceAfter=5)
            ))
    story.append(PageBreak())

    # ── SECTION 4 ──
    story += [
        Paragraph("04  /  МЕДИАПЛАН", s_section_num),
        HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=8),
        Paragraph("Прогноз по кампаниям", s_h1),
    ]
    mp_data = [["Кампания", "Платформа", f"Бюджет ({curr_sym})", f"CPA ({curr_sym})", "Лиды"]]
    for row in report.media_plan.rows[:14]:
        mp_data.append([
            _wrap(row.campaign_name, 26),
            row.platform,
            f"{row.budget:.0f}",
            f"{row.cpa:.0f}",
            f"{row.conversions:.1f}",
        ])
    m = report.media_plan
    mp_data.append(["ИТОГО", "", f"{m.total_budget:.0f}", f"{m.avg_cpa:.0f}", f"{m.total_conversions:.1f}"])
    story.append(_v3_table(mp_data, p, highlight_last=True,
                            col_widths=[5.8*cm, 2.3*cm, 2.8*cm, 2.5*cm, 2*cm]))
    story.append(Spacer(1, 0.5*cm))
    story.append(_v3_stat_grid([
        (f"{m.total_budget:.0f} {curr_sym}", "бюджет/мес"),
        (f"{m.total_conversions:.0f}", "лидов/мес"),
        (f"{m.avg_cpa:.0f} {curr_sym}", "цена лида"),
    ], p, cols=3))

    # ── SECTION 5 ──
    br = report.budget_recommendation
    if br:
        story += [
            Spacer(1, 0.6*cm),
            Paragraph("05  /  БЮДЖЕТ", s_section_num),
            HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=8),
            Paragraph("Рекомендация по бюджету", s_h1),
            Paragraph(br.reasoning, s_body),
            Spacer(1, 0.3*cm),
        ]
        b_data = [
            ["Вариант", f"Бюджет/мес ({curr_sym})", "Лиды/мес", f"Цена лида ({curr_sym})"],
            ["Минимальный",
             f"{br.recommended_min:.0f}",
             f"~{int(br.monthly_leads_estimate * 0.5)}",
             f"~{br.recommended_min / max(br.monthly_leads_estimate * 0.5, 1):.0f}"],
            ["Оптимальный ✓",
             f"{br.recommended_optimal:.0f}",
             f"~{br.monthly_leads_estimate}",
             f"~{br.recommended_optimal / max(br.monthly_leads_estimate, 1):.0f}"],
            ["Агрессивный",
             f"{br.recommended_aggressive:.0f}",
             f"~{int(br.monthly_leads_estimate * 1.8)}",
             f"~{br.recommended_aggressive / max(br.monthly_leads_estimate * 1.8, 1):.0f}"],
        ]
        story.append(_v3_table(b_data, p, highlight_row=2,
                                col_widths=[4.5*cm, 3.5*cm, 2.5*cm, 3.5*cm]))

    # ── CTA BACK COVER ──
    story += [
        PageBreak(),
        Spacer(1, 2*cm),
        Paragraph("Следующий шаг", s_section_num),
        HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=12),
        Paragraph("Готовы запустить рекламу?", ParagraphStyle(
            "cta_h", fontName=FONT_BOLD, fontSize=20, textColor=p["text"], leading=26, spaceAfter=12)),
        Paragraph(
            "Мы подготовили полную стратегию на основе реального объёма поиска и конкурентного анализа. "
            "Настройка кампаний — 3-5 рабочих дней. Первые заявки — уже в первую неделю.",
            ParagraphStyle("cta_b", fontName=FONT, fontSize=10.5, textColor=p["muted"],
                            leading=16, spaceAfter=20)
        ),
        Paragraph("+375(44) 7654-231", ParagraphStyle(
            "cta_phone", fontName=FONT_BOLD, fontSize=16, textColor=p["accent"], leading=22, spaceAfter=6)),
        Paragraph("1alexeikalinin1@gmail.com", ParagraphStyle(
            "cta_email", fontName=FONT, fontSize=11, textColor=p["muted"], leading=16, spaceAfter=20)),
        HRFlowable(width="100%", thickness=0.5, color=p["border"], spaceAfter=8),
        Paragraph(AGENCY, ParagraphStyle(
            "cta_agency", fontName=FONT_BOLD, fontSize=9, textColor=p["muted"], leading=14)),
    ]

    doc.build(story)
    return buf.getvalue()


def _v3_table(data, p, col_widths=None, highlight_last=False, highlight_row: int | None = None) -> Table:
    n = len(data)
    tbl = Table(data, colWidths=col_widths, repeatRows=1)
    cmds = [
        ("BACKGROUND",  (0, 0), (-1, 0), p["accent"]),
        ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
        ("FONTNAME",    (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE",    (0, 0), (-1, 0), 8.5),
        ("FONTNAME",    (0, 1), (-1, -1), FONT),
        ("FONTSIZE",    (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR",   (0, 1), (-1, -1), p["text"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, p["row_alt"]]),
        ("GRID",        (0, 0), (-1, -1), 0.3, p["border"]),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING",     (0, 0), (-1, -1), 5),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
    ]
    if highlight_last and n > 1:
        cmds += [
            ("BACKGROUND", (0, n-1), (-1, n-1), p["sidebar"]),
            ("FONTNAME",   (0, n-1), (-1, n-1), FONT_BOLD),
            ("TEXTCOLOR",  (0, n-1), (-1, n-1), colors.white),
        ]
    if highlight_row is not None and 1 <= highlight_row < n:
        cmds += [
            ("BACKGROUND", (0, highlight_row), (-1, highlight_row), p["accent"]),
            ("FONTNAME",   (0, highlight_row), (-1, highlight_row), FONT_BOLD),
            ("TEXTCOLOR",  (0, highlight_row), (-1, highlight_row), colors.white),
        ]
    tbl.setStyle(TableStyle(cmds))
    return tbl


def _v3_stat_grid(items: list[tuple[str, str]], p, cols: int = 4) -> Table:
    cells_val = [Paragraph(val, ParagraphStyle(
        f"sv{i}", fontName=FONT_BOLD, fontSize=18, textColor=p["accent"],
        leading=22, alignment=TA_CENTER
    )) for i, (val, _) in enumerate(items)]
    cells_lbl = [Paragraph(lbl, ParagraphStyle(
        f"sl{i}", fontName=FONT, fontSize=8, textColor=p["muted"],
        leading=12, alignment=TA_CENTER
    )) for i, (_, lbl) in enumerate(items)]

    n = len(items)
    col_w = CONTENT_W / n
    row_data = [cells_val, cells_lbl]
    tbl = Table(row_data, colWidths=[col_w] * n)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), p["light"]),
        ("BOX",         (0, 0), (-1, -1), 1, p["border"]),
        ("LINEAFTER",   (0, 0), (-2, -1), 0.5, p["border"]),
        ("ALIGN",       (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",  (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return tbl


# ── Helpers ────────────────────────────────────────────────────────────────────

def _curr_sym(currency: str | None) -> str:
    return {"RUB": "₽", "BYN": "Br", "USD": "$", "EUR": "€", "KZT": "₸"}.get(currency or "RUB", currency or "₽")


def _geo(report: AnalyzeResponse) -> str:
    from backend.services.region_platforms import get_region_label
    # report doesn't carry region/city directly, use niche as fallback label
    return report.site.niche


def _wrap(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars - 1] + "…"
