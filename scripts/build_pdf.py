"""Typeset the release EPUB as a linked 6 x 9 inch PDF reading edition.

Requires reportlab and pypdf. The EPUB is the content source, so the two
formats share prose, notes, credits, and navigation. Notes remain at the
end of their source section, with links in both directions.
"""
from pathlib import Path
import argparse
import html
import json
import re
import zipfile
from xml.etree import ElementTree as ET

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, HRFlowable, PageBreak, PageTemplate,
    Paragraph, Spacer, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STEM = 'the-world-as-will-and-representation-volume-i'
NS = {'x': 'http://www.w3.org/1999/xhtml', 'opf': 'http://www.idpf.org/2007/opf'}
WIDTH, HEIGHT = 432, 648
MARGIN = 48
INK = colors.HexColor('#202b2d')
TEAL = colors.HexColor('#244e54')


def tag(element):
    return element.tag.rsplit('}', 1)[-1]


def anchor(path, fragment=''):
    return Path(path).stem + ('--' + fragment if fragment else '')


def register_fonts(font_dir, documents):
    for name, filename in [('Book', 'times.ttf'), ('BookItalic', 'timesi.ttf'),
                           ('BookBold', 'timesbd.ttf'), ('BookBoldItalic', 'timesbi.ttf'),
                           ('Symbols', 'seguisym.ttf')]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily('Book', normal='Book', bold='BookBold',
                                  italic='BookItalic', boldItalic='BookBoldItalic')
    characters = set(''.join(''.join(d.itertext()) for d in documents))
    # The actual content is checked before typesetting, including polytonic Greek.
    for name in ['Book', 'BookItalic', 'BookBold', 'BookBoldItalic']:
        coverage = pdfmetrics.getFont(name).face.charToGlyph
        missing = [c for c in characters if ord(c) > 31 and c != '↩' and ord(c) not in coverage]
        if missing:
            raise ValueError(f'{name} lacks glyphs: {sorted(missing)}')
    if ord('↩') not in pdfmetrics.getFont('Symbols').face.charToGlyph:
        raise ValueError('Symbol font lacks the note return arrow.')


def inline(element, path):
    """Translate only the EPUB's supported inline markup to PDF paragraph markup."""
    result = html.escape(element.text or '')
    for child in element:
        kind = tag(child)
        content = inline(child, path)
        if child.get('id'):
            content = f'<a name="{anchor(path, child.get("id"))}"/>' + content
        if kind == 'br':
            content = '<br/>'
        elif kind in ('em', 'strong'):
            wrapper = 'i' if kind == 'em' else 'b'
            content = f'<{wrapper}>{content}</{wrapper}>'
        elif kind == 'a':
            href = child.get('href', '')
            if child.get('aria-label', '').startswith('Back to'):
                content = '<font name="Symbols">↩</font>'
            if href.startswith('#'):
                href = '#' + anchor(path, href[1:])
            elif not re.match(r'https?://', href):
                target, _, fragment = href.partition('#')
                href = '#' + anchor(target, fragment)
            content = f'<a href="{html.escape(href, quote=True)}" color="#244e54">{content}</a>'
            if child.get('class') == 'noteref':
                content = f'<super>{content}</super>'
        elif kind not in ('span', 'code'):
            raise ValueError(f'Unsupported inline element: {kind}')
        result += content + html.escape(child.tail or '')
    return result


class Cover(Flowable):
    def __init__(self, path):
        super().__init__()
        self.path = str(path)
        self.width, self.height = 1, 1

    def draw(self):
        # Draw in page coordinates, outside the text frame, without cropping.
        self.canv.saveState()
        self.canv.resetTransforms()
        self.canv.drawImage(self.path, 0, 0, width=WIDTH, height=HEIGHT)
        self.canv.restoreState()


class BookDocument(BaseDocTemplate):
    def __init__(self, path, metadata):
        super().__init__(str(path), pagesize=(WIDTH, HEIGHT),
                         title=metadata['title'], author=metadata['creator'],
                         subject=metadata['description'], creator='SchopenhauerTranslation PDF build',
                         leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=48, bottomMargin=46, pageCompression=1)
        frame = Frame(MARGIN, 46, WIDTH - 2 * MARGIN, HEIGHT - 94,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id='book', frames=frame, onPage=self.furniture))
        self.section_pages = {}

    def furniture(self, canvas, document):
        if document.page == 1:
            return
        canvas.saveState()
        canvas.setFont('Book', 8)
        canvas.setFillColor(colors.HexColor('#6a7373'))
        if document.page > 2:
            canvas.drawCentredString(WIDTH / 2, HEIGHT - 27, 'THE WORLD AS WILL AND REPRESENTATION')
        canvas.drawCentredString(WIDTH / 2, 24, str(document.page - 1))
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if hasattr(flowable, 'outline_key'):
            key, title = flowable.outline_key, flowable.getPlainText()
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0, closed=False)
            self.notify('TOCEntry', (0, title, self.page - 1, key))
            self.section_pages[key] = self.page


def styles():
    base = dict(fontName='Book', fontSize=10.5, leading=14.5, textColor=INK,
                allowWidows=0, allowOrphans=0, splitLongWords=0)
    body = ParagraphStyle('body', alignment=TA_JUSTIFY, firstLineIndent=12, spaceAfter=5, **base)
    return {
        'body': body,
        'front': ParagraphStyle('front', parent=body, alignment=0, firstLineIndent=0, spaceAfter=8),
        'title': ParagraphStyle('title', parent=body, alignment=TA_CENTER, firstLineIndent=0,
                                fontSize=10.5, leading=14, spaceAfter=10),
        'quote': ParagraphStyle('quote', parent=body, firstLineIndent=0,
                                leftIndent=16, rightIndent=12, spaceBefore=6, spaceAfter=9),
        'note': ParagraphStyle('note', parent=body, firstLineIndent=0,
                               fontSize=9, leading=12, spaceAfter=7),
        'h1': ParagraphStyle('h1', parent=body, fontName='BookBold', firstLineIndent=0,
                             fontSize=19, leading=24, textColor=TEAL, spaceAfter=16, keepWithNext=True),
        'h2': ParagraphStyle('h2', parent=body, fontName='BookBold', firstLineIndent=0,
                             fontSize=14, leading=18, spaceBefore=12, spaceAfter=9, keepWithNext=True),
        'h4': ParagraphStyle('h4', parent=body, fontName='BookBold', firstLineIndent=0,
                             fontSize=11, leading=14.5, spaceBefore=10, spaceAfter=6, keepWithNext=True),
        'toc': ParagraphStyle('toc', fontName='Book', fontSize=10, leading=14,
                              textColor=INK, spaceBefore=0, leftIndent=0, firstLineIndent=0),
    }


def convert_blocks(container, path, style_set, context='body'):
    items = []
    for element in container:
        kind = tag(element)
        if kind in ('h1', 'h2', 'h4', 'p'):
            style = style_set[kind] if kind.startswith('h') else style_set[context]
            if context == 'title' and kind.startswith('h'):
                style = ParagraphStyle('title-' + kind, parent=style, alignment=TA_CENTER,
                                       fontSize=17 if kind == 'h1' else 14, leading=20)
            content = inline(element, path)
            if element.get('id'):
                content = f'<a name="{anchor(path, element.get("id"))}"/>' + content
            items.append(Paragraph(content, style))
        elif kind == 'blockquote':
            items.extend(convert_blocks(element, path, style_set, 'quote'))
        elif kind == 'section':
            if element.get('class') == 'footnotes':
                items += [Spacer(1, 10), HRFlowable(width='30%', color=TEAL, spaceAfter=8)]
                items.append(Paragraph('Notes', style_set['h4']))
            items.extend(convert_blocks(element, path, style_set, context))
        elif kind in ('ol', 'ul'):
            for index, item in enumerate(element, 1):
                note = item.get('{http://www.idpf.org/2007/ops}type') == 'footnote'
                item_context = 'note' if note else context
                if any(tag(child) in ('p', 'blockquote', 'ol', 'ul') for child in item):
                    blocks = convert_blocks(item, path, style_set, item_context)
                else:
                    blocks = [Paragraph(inline(item, path), style_set[item_context])]
                if not blocks:
                    raise ValueError('Empty list item')
                label = item.get('value', str(index)) if kind == 'ol' else '•'
                if item.get('class') == 'editorial-note':
                    label = ''  # The source already includes its dagger label.
                prefix = f'<b>{label}.</b> ' if label else ''
                if item.get('id'):
                    prefix = f'<a name="{anchor(path, item.get("id"))}"/>' + prefix
                blocks[0] = Paragraph(prefix + blocks[0].text, blocks[0].style)
                items.extend(blocks)
        else:
            raise ValueError(f'Unsupported block element: {kind}')
    return items


def build(epub, output, font_dir):
    metadata = json.loads((ROOT / 'release.json').read_text(encoding='utf8'))
    with zipfile.ZipFile(epub) as archive:
        package = ET.fromstring(archive.read('EPUB/content.opf'))
        manifest = {e.get('id'): e.get('href') for e in package.findall('opf:manifest/opf:item', NS)}
        paths = [manifest[e.get('idref')] for e in package.findall('opf:spine/opf:itemref', NS)
                 if e.get('idref') not in ('cover-page', 'nav')]
        documents = [ET.fromstring(archive.read('EPUB/' + path)) for path in paths]
    register_fonts(font_dir, documents)
    style_set = styles()
    story = [Cover(ROOT / metadata['cover']), PageBreak()]
    toc = TableOfContents()
    toc.levelStyles = [style_set['toc']]
    toc.dotsMinLevel = 0
    toc.tableStyle = TableStyle([('LEFTPADDING', (0, 0), (-1, -1), 0),
                                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                ('TOPPADDING', (0, 0), (-1, -1), 2),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 2)])
    for index, (path, document) in enumerate(zip(paths, documents)):
        if index:
            story.append(PageBreak())
        section = document.find('x:body/x:section', NS)
        context = 'title' if index == 0 else 'front' if index == 1 else 'body'
        # The source section itself is also an internal-link target.
        blocks = convert_blocks(section, path, style_set, context)
        blocks[0].text = f'<a name="{anchor(path)}"/>' + blocks[0].text
        # Reparse because Paragraph parses markup in its constructor.
        blocks[0] = Paragraph(blocks[0].text, blocks[0].style)
        blocks[0].outline_key = anchor(path)
        story.extend(blocks)
        if index == 1:
            story += [PageBreak(), Paragraph('Contents', style_set['h1']), toc]
    output.parent.mkdir(exist_ok=True, parents=True)
    doc = BookDocument(output, metadata)
    doc.multiBuild(story)
    reader = PdfReader(output)
    if len(doc.section_pages) != 75:
        raise ValueError(f'Expected 75 sections, got {len(doc.section_pages)}')
    report = {'pages': len(reader.pages), 'page_size_inches': [6, 9],
              'sections': len(doc.section_pages), 'section_pages': doc.section_pages,
              'notes': 'Linked notes at the end of each source section',
              'fonts': ['Times New Roman (regular, italic, bold, bold italic)', 'Segoe UI Symbol'],
              'source_epub': epub.name}
    (ROOT / '.release-cache').mkdir(exist_ok=True)
    (ROOT / '.release-cache/pdf-build.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(f'PDF: {len(reader.pages)} pages, 75 bookmarked sections, embedded fonts and linked notes: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--epub', type=Path, default=ROOT / 'dist' / (STEM + '.epub'))
    parser.add_argument('--output', type=Path, default=ROOT / 'dist' / (STEM + '.pdf'))
    parser.add_argument('--font-dir', type=Path, default=Path('C:/Windows/Fonts'))
    args = parser.parse_args()
    build(args.epub, args.output, args.font_dir)
