"""Normalize legacy PDF font encodings into real Unicode text."""
from reportlab.pdfbase import _fontdata, _glyphlist


def _symbol_private_use_map():
    mapping = {}
    glyphs = _fontdata.encodings["SymbolEncoding"]
    for code, glyph_name in enumerate(glyphs):
        if not glyph_name:
            continue
        point = _glyphlist._glyphname2unicode.get(glyph_name)
        if point is not None:
            mapping[0xF000 + code] = chr(point)
            continue
        points = _glyphlist._glyphname2unicodes.get(glyph_name)
        if points:
            mapping[0xF000 + code] = "".join(chr(value) for value in points)
    return mapping


SYMBOL_PRIVATE_USE_MAP = _symbol_private_use_map()


def normalize_legacy_symbols(value: str) -> str:
    """Convert characters such as Symbol-font U+F070 into Unicode π."""
    return str(value).translate(SYMBOL_PRIVATE_USE_MAP)
