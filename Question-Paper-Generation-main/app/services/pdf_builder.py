"""Render validated papers, escaping source text and keeping marks aligned."""
from pathlib import Path
from io import BytesIO
import cv2
import numpy as np
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, CondPageBreak, Preformatted
from app.services.text_normalization import normalize_legacy_symbols

FONT_DIR = Path(reportlab.__file__).parent / "fonts"
REGULAR_FONT = next((path for path in (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
    FONT_DIR / "Vera.ttf",
) if path.is_file()))
BOLD_FONT = next((path for path in (
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    REGULAR_FONT,
) if path.is_file()))
pdfmetrics.registerFont(TTFont("PaperFont", str(REGULAR_FONT)))
pdfmetrics.registerFont(TTFont("PaperFont-Bold", str(BOLD_FONT)))
pdfmetrics.registerFontFamily("PaperFont", normal="PaperFont", bold="PaperFont-Bold", italic="PaperFont", boldItalic="PaperFont-Bold")


def text(value):
    value = normalize_legacy_symbols(value)
    supported = pdfmetrics.getFont("PaperFont").face.charToGlyph
    missing = sorted({c for c in value if ord(c) > 31 and ord(c) not in supported})
    if missing:
        codes = ", ".join(f"{c} (U+{ord(c):04X})" for c in missing[:6])
        raise ValueError(f"The PDF font cannot render these characters: {codes}. Replace them in the bank review with plain-text notation or use a source figure.")
    return escape(value).replace("\n", "<br/>")


class SourceExcerpt(Image):
    """Split tall source images only along whitespace, keeping glyphs intact."""
    def __init__(self, pixels, width):
        self.pixels = pixels
        ok, encoded = cv2.imencode('.png', pixels)
        if not ok:
            raise ValueError("Could not render the original question excerpt.")
        super().__init__(BytesIO(encoded.tobytes()), width=width, height=width*pixels.shape[0]/pixels.shape[1])
        self.hAlign = 'LEFT'

    def split(self, availWidth, availHeight):
        ratio = self.drawWidth/self.pixels.shape[1]
        limit = min(self.pixels.shape[0]-1, int(availHeight/ratio)-2)
        if limit < 40:
            return []
        gray = cv2.cvtColor(self.pixels, cv2.COLOR_BGR2GRAY)
        low = max(20,limit-int(90/ratio))
        cuts = [y for y in range(low,limit) if np.mean(gray[y]<210)<.005]
        if not cuts:
            return []
        cut=cuts[-1]
        return [SourceExcerpt(self.pixels[:cut],self.drawWidth),SourceExcerpt(self.pixels[cut:],self.drawWidth)]


def build_questionpaper_from_json(paper, output_path, asset_dir=None):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(output_path), pagesize=A4,
                            leftMargin=48, rightMargin=48, topMargin=45, bottomMargin=48)
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "PaperFont"
    normal = ParagraphStyle("PaperBody", parent=styles["Normal"], fontSize=10, leading=15, spaceAfter=5)
    title = ParagraphStyle("PaperTitle", parent=normal, fontSize=14, leading=19, alignment=TA_CENTER, spaceAfter=6)
    subtitle = ParagraphStyle("PaperSubtitle", parent=normal, fontSize=11, alignment=TA_CENTER)
    label = ParagraphStyle("PaperQuestion", parent=normal, spaceBefore=6)
    centered = ParagraphStyle("PaperOR", parent=normal, alignment=TA_CENTER, spaceBefore=5, spaceAfter=5)
    width = A4[0] - 96
    header = paper["header"]
    content = [Paragraph(f"<b>{text(header['institution'])}</b>", title),
               Paragraph(text(header["exam_name"]), subtitle), Spacer(1, 10)]
    details = Table([
        [Paragraph(f"<b>Subject:</b> {text(header['subject'])}", normal), Paragraph(f"<b>Date:</b> {text(header['date'] or 'Not specified')}", normal)],
        [Paragraph(f"<b>Duration:</b> {text(header['duration'])}", normal), Paragraph(f"<b>Total marks:</b> {paper['total_marks']}", normal)],
    ], colWidths=[width*.63, width*.37])
    details.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    content.extend([details, Spacer(1, 9), Paragraph("<b>Instructions</b>", normal),
                    Paragraph("Attempt ONE alternative from each unit. Each alternative carries the full unit marks.", normal)])
    if header.get("instructions"):
        content.append(Paragraph(text(header["instructions"]), normal))
    for unit in paper["units"]:
        for index, alternative in enumerate(unit["alternatives"]):
            content.append(CondPageBreak(110))
            if index:
                content.append(Paragraph("<b>OR</b>", centered))
            content.append(Paragraph(
                f"<b>Q{alternative['number']}. {text(unit['name'])}</b> — {unit['marks']} marks", label))
            for position, q in enumerate(alternative["questions"]):
                question = Paragraph(f"<b>({chr(97+position)})</b> {text(q['text']).replace('  ', '&#160;&#160;').replace('\t', '&#160;'*4)}", normal)
                marks = Paragraph(f"<b>[{q['marks']}]</b>", normal)
                row = Table([[question, marks]], colWidths=[width-45, 45], splitByRow=1, splitInRow=1)
                row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(0,0),12),
                                         ('RIGHTPADDING',(0,0),(-1,-1),0), ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
                content.append(row)
                for asset in q.get("assets", []):
                    if asset_dir is None or Path(asset).name != asset:
                        raise ValueError("A source figure is unavailable. Regenerate from the question bank.")
                    path = Path(asset_dir) / asset
                    if not path.is_file():
                        raise ValueError("A source figure is missing. Upload the source again.")
                    image = Image(str(path))
                    scale = min((width-30)/image.imageWidth, 240/image.imageHeight, 1)
                    image.drawWidth = image.imageWidth * scale
                    image.drawHeight = image.imageHeight * scale
                    image.hAlign = "LEFT"
                    content.extend([image, Spacer(1, 8)])

    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("PaperFont", 8)
        canvas.setFillColor(colors.HexColor("#555555"))
        canvas.drawRightString(A4[0]-48, 25, f"Page {document.page}")
        canvas.restoreState()

    doc.build(content, onFirstPage=footer, onLaterPages=footer)
