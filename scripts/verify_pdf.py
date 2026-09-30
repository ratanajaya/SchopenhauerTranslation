"""Verify PDF content, embedded fonts, navigation, and page dimensions."""
from pathlib import Path
import json
import re
import zipfile
from xml.etree import ElementTree as ET
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
STEM = 'the-world-as-will-and-representation-volume-i'
NS = {'x': 'http://www.w3.org/1999/xhtml', 'opf': 'http://www.idpf.org/2007/opf'}


def compact(text):
    return ''.join(text.split())


def verify():
    path = ROOT / 'dist' / (STEM + '.pdf')
    reader = PdfReader(path)
    metadata = json.loads((ROOT / 'release.json').read_text(encoding='utf8'))
    assert reader.metadata.title == metadata['title']
    assert reader.metadata.author == metadata['creator']
    page_ids = {p.indirect_reference.idnum for p in reader.pages}
    links = []
    fonts = set()
    text_pages = []
    for index, page in enumerate(reader.pages):
        assert list(page.mediabox) == [0, 0, 432, 648], ('page size', index + 1)
        for font_ref in page['/Resources'].get('/Font', {}).values():
            font = font_ref.get_object()
            name = str(font['/BaseFont'])
            if 'TimesNewRoman' in name or 'SegoeUISymbol' in name:
                assert '/FontFile2' in font['/FontDescriptor'], ('font not embedded', name)
                assert '/ToUnicode' in font, ('missing Unicode mapping', name)
                fonts.add(name.split('+')[-1])
        for annotation_ref in page.get('/Annots', []):
            annotation = annotation_ref.get_object()
            if annotation.get('/Subtype') != '/Link':
                continue
            links.append(annotation)
            rectangle = list(map(float, annotation['/Rect']))
            assert 0 <= rectangle[0] <= rectangle[2] <= 432
            assert 0 <= rectangle[1] <= rectangle[3] <= 648
            destination = annotation.get('/Dest')
            if destination:
                assert destination[0].idnum in page_ids, 'Invalid internal link destination'
        if index:
            text = page.extract_text() or ''
            text = re.sub(r'^THE WORLD AS WILL AND REPRESENTATION\n', '', text)
            footer, separator, text = text.partition('\n')
            assert separator and footer.strip() == str(index), ('page number', index + 1)
            assert text.strip(), ('blank text page', index + 1)
            text_pages.append(text)
    assert {'TimesNewRomanPSMT', 'TimesNewRomanPS-ItalicMT',
            'TimesNewRomanPS-BoldMT', 'SegoeUISymbol'} <= fonts, fonts
    assert len(reader.pages[0].images) == 1, 'Cover image missing'
    assert not reader.pages[0].extract_text().strip(), 'Unexpected cover text overlay'
    uris = [a['/A']['/URI'] for a in links if a.get('/A', {}).get('/S') == '/URI']
    assert uris.count('https://github.com/ratanajaya') == 2, 'Translator profile links missing'
    text = compact(''.join(text_pages))
    cursor = 0
    blocks = 0
    notes = 0
    source_links = 0
    with zipfile.ZipFile(ROOT / 'dist' / (STEM + '.epub')) as archive:
        package = ET.fromstring(archive.read('EPUB/content.opf'))
        manifest = {e.get('id'): e.get('href') for e in package.findall('opf:manifest/opf:item', NS)}
        paths = [manifest[e.get('idref')] for e in package.findall('opf:spine/opf:itemref', NS)
                 if e.get('idref') not in ('cover-page', 'nav')]
        assert len(paths) == len(reader.outline) == 75
        section_pages = json.loads((ROOT / '.release-cache/pdf-build.json').read_text())['section_pages']
        for source, bookmark in zip(paths, reader.outline):
            document = ET.fromstring(archive.read('EPUB/' + source))
            assert bookmark.title == document.find('x:head/x:title', NS).text
            assert reader.get_destination_page_number(bookmark) + 1 == section_pages[Path(source).stem]
            source_links += len(document.findall('.//x:a', NS))
            for element in document.find('x:body/x:section', NS).iter():
                kind = element.tag.rsplit('}', 1)[-1]
                if element.get('{http://www.idpf.org/2007/ops}type') == 'footnote':
                    notes += 1
                # List items with inline children are not wrapped in paragraphs.
                leaf_item = kind == 'li' and not any(
                    child.tag.rsplit('}', 1)[-1] in ('p', 'blockquote', 'ol', 'ul') for child in element)
                if kind in ('p', 'h1', 'h2', 'h4') or leaf_item:
                    expected = compact(''.join(element.itertext()))
                    found = text.find(expected, cursor)
                    assert found >= 0, ('Missing or reordered content', source, expected[:120])
                    cursor = found + len(expected)
                    blocks += 1
    assert notes == 122
    assert len(links) >= source_links + 75, 'Missing content or contents links'
    report = {'pages': len(reader.pages), 'page_size_inches': [6, 9],
              'content_sections': len(paths), 'verified_text_blocks_in_source_order': blocks,
              'notes': notes, 'bookmarks': len(reader.outline), 'link_annotations': len(links),
              'embedded_fonts': sorted(fonts),
              'checks': ['all paragraph, heading, and list text preserved in source order',
                         'all 122 source notes present', '75 bookmarks match source titles and pages',
                         'valid internal link destinations and link rectangles',
                         'both translator GitHub links', 'embedded fonts and Unicode mappings',
                         'full-page cover', 'consistent page dimensions and printed numbering']}
    (ROOT / '_docs/pdf-validation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf8', newline='\n')
    print(f'PASS PDF: {len(reader.pages)} pages; {blocks} text blocks, {notes} notes, '
          f'75 bookmarks, {len(links)} link annotations; embedded fonts verified.')


if __name__ == '__main__':
    verify()
