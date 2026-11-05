"""Source-region figure extraction used by the active parser."""
from uuid import uuid4
import pymupdf as fitz


def attach_pdf_figures(doc, questions, asset_dir, skip_pages=()):
    """Crop visible graphics in a question's source band. Teachers verify association."""
    for index, question in enumerate(questions):
        if not question["_start"]:
            continue
        first_page = question["source_page"] - 1
        following = questions[index+1] if index+1 < len(questions) else None
        last_page = following["source_page"] - 1 if following else len(doc)-1
        for page_index in range(first_page, last_page + 1):
            if page_index in skip_pages:
                continue
            page = doc[page_index]
            top = question["_start"][1] if page_index == first_page else 40
            bottom = following["_start"][1] if following and page_index == last_page else page.rect.height-35
            band = fitz.Rect(20, top, page.rect.width-20, bottom)
            if band.is_empty:
                continue
            rects = [fitz.Rect(info["bbox"]) for info in page.get_image_info()]
            rects.extend(d["rect"] for d in page.get_drawings())
            rects = [r & band for r in rects if r.intersects(band) and r.get_area() > 100]
            rects = [r for r in rects if r.width > 10 and r.height > 10]
            if not rects:
                continue
            region = fitz.Rect(rects[0])
            for rect in rects[1:]:
                region |= rect
            region = fitz.Rect(region.x0-6, region.y0-6, region.x1+6, region.y1+6) & band
            asset = str(uuid4()) + ".png"
            page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), clip=region, alpha=False).save(asset_dir / asset)
            question["assets"].append(asset)

