"""Verify the packaged edition against its Markdown inputs and release config."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import html
import json
import re
import subprocess
import zipfile
from xml.etree import ElementTree as ET
from export_translated_chapters_to_epub import validate_epub, parse_footnotes

ROOT = Path(__file__).resolve().parents[1]
NS = {'x': 'http://www.w3.org/1999/xhtml', 'opf': 'http://www.idpf.org/2007/opf', 'dc': 'http://purl.org/dc/elements/1.1/'}
EPUB_TYPE = '{http://www.idpf.org/2007/ops}type'


def plain(text, markdown=True):
    text = re.sub(r'\[\^([^\]]+)\]', '', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'<br\s*/?>', '', text, flags=re.I)
    if markdown:
        text = re.sub(r'^\s*(?:#{1,6}\s+|>\s*|[-*+]\s+|\d+\.\s+)', '', text, flags=re.M)
    text = text.replace('`', '').replace('*', '')
    return ''.join(html.unescape(text).split())


def readable_text(element):
    # Omit the generated reference labels and return-arrow UI, retain their tails.
    return (element.text or '') + ''.join(
        ('' if child.get('class') == 'note-label' or (child.tag.endswith('a') and
         (child.get(EPUB_TYPE) == 'noteref' or child.get('aria-label', '').startswith('Back to')))
         else readable_text(child)) + (child.tail or '') for child in element)


def verify():
    configuration = json.loads((ROOT / 'release.json').read_text(encoding='utf8'))
    dist = ROOT / 'dist'
    path = dist / 'the-world-as-will-and-representation-volume-i.epub'
    validate_epub(path)
    sources = sorted((ROOT / 'english-translation').glob('chapter-*.md'))
    assert len(sources) == 74
    checked = []
    notes_total = 0
    headings_total = 0
    with zipfile.ZipFile(path) as archive:
        package = ET.fromstring(archive.read('EPUB/content.opf'))
        metadata = package.find('opf:metadata', NS)
        for field, key in [('title', 'title'), ('creator', 'creator'), ('language', 'language'), ('publisher', 'publisher'), ('identifier', 'identifier'), ('date', 'date'), ('source', 'source'), ('rights', 'rights'), ('description', 'description')]:
            assert metadata.find('dc:' + field, NS).text == configuration[key], field
        subjects = [e.text for e in metadata.findall('dc:subject', NS)]
        assert subjects == configuration['subject']
        contributors = metadata.findall('dc:contributor', NS)
        assert [e.text for e in contributors] == [configuration['translator']] + configuration['contributor']
        roles = {e.get('refines'): e.text for e in metadata.findall('opf:meta', NS) if e.get('property') == 'role'}
        assert roles == {'#author': 'aut', '#translator': 'trl', '#contributor-1': 'AI assistance', '#contributor-2': 'AI assistance'}
        assert metadata.find('opf:meta[@property="schema:bookEdition"]', NS).text == 'First English release, v' + configuration['release_version']
        manifest = {e.get('id'): e for e in package.findall('opf:manifest/opf:item', NS)}
        assert manifest['cover-image'].get('properties') == 'cover-image'
        assert archive.read('EPUB/images/cover.jpg') == (dist / 'cover.jpg').read_bytes()
        spine = [e.get('idref') for e in package.findall('opf:spine/opf:itemref', NS)]
        assert spine == ['cover-page', 'chapter-0001', 'edition-and-credits', 'nav'] + [p.stem for p in sources[1:]]
        nav = ET.fromstring(archive.read('EPUB/nav.xhtml'))
        landmarks = {a.get(EPUB_TYPE) for a in nav.findall('.//x:nav[@id="landmarks"]//x:a', NS)}
        assert landmarks == {'cover', 'titlepage', 'toc', 'bodymatter'}
        assert len(nav.findall('.//x:nav[@id="toc"]//x:a', NS)) == 75
        for source in sources:
            body, notes = parse_footnotes(source.read_text(encoding='utf-8-sig').splitlines())
            document = ET.fromstring(archive.read('EPUB/text/' + source.stem + '.xhtml'))
            section = document.find('x:body/x:section', NS)
            note_section = section.find('x:section[@class="footnotes"]', NS)
            if note_section is not None:
                assert len(note_section.findall('x:ol/x:li', NS)) == len(notes), source.name
                for note, item in zip(notes.values(), note_section.findall('x:ol/x:li', NS)):
                    assert plain(note) == plain(readable_text(item), markdown=False), ('footnote text', source.name)
                section.remove(note_section)
            assert plain('\n'.join(body)) == plain(readable_text(section), markdown=False), ('body text', source.name)
            source_headings = sum(bool(re.match(r'^#{1,6}\s+', line)) for line in body)
            output_headings = sum(element.tag.rsplit('}', 1)[-1] in ['h1','h2','h3','h4','h5','h6'] for element in section.iter())
            assert source_headings == output_headings, ('headings', source.name)
            headings_total += output_headings
            notes_total += len(notes)
            checked.append({'file': source.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'footnotes': len(notes), 'headings': output_headings})
    expected = {'the-world-as-will-and-representation-volume-i.epub', 'cover.jpg', 'RELEASE_NOTES.md', 'LICENSE.txt', 'SHA256SUMS'}
    assert set(p.name for p in dist.iterdir()) == expected
    checksums = {}
    for line in (dist / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert digest == hashlib.sha256((dist / name).read_bytes()).hexdigest(), name
        checksums[name] = digest
    assert len(checksums) == 4
    assert (dist / 'LICENSE.txt').read_bytes() == (ROOT / 'LICENSE.txt').read_bytes()
    assert (dist / 'RELEASE_NOTES.md').read_bytes() == (ROOT / '_docs/release_notes.md').read_bytes()
    readme = (ROOT / 'README.md').read_text(encoding='utf8')
    assert 'src="dist/cover.jpg" width="320"' in readme
    for link in re.findall(r'\]\(([^)]+)\)', readme):
        if not link.startswith('http'): assert (ROOT / link).is_file(), link
    assert 'https://github.com/ratanajaya/SchopenhauerTranslation/releases' in readme
    assert subprocess.check_output(['git','diff','--name-only','HEAD','--','original-epub-extract-md'],cwd=ROOT,text=True).strip() == '', 'German extraction changed'
    report = {'version': configuration['release_version'], 'publication_date_Asia_Bangkok': configuration['date'],
              'verified_at_Asia_Bangkok': datetime.now(timezone(timedelta(hours=7))).isoformat(timespec='seconds'),
              'content_files': len(checked), 'headings': headings_total, 'footnotes': notes_total,
              'checks': ['archive and XML structure', 'unique IDs', 'all internal links and fragments', 'footnote destinations and every return link', 'metadata and contributor roles', 'cover property and bytes', 'spine and navigation landmarks', 'complete body and footnote text against all 74 Markdown files', 'heading counts', 'unchanged German extraction', 'README local links', 'license consistency', 'exact release filenames', 'SHA256SUMS'],
              'release_checksums': checksums, 'content': checked}
    epubcheck_report = ROOT / '.release-cache/epubcheck-report.json'
    if epubcheck_report.exists() and epubcheck_report.stat().st_mtime >= path.stat().st_mtime:
        checker_result = json.loads(epubcheck_report.read_text(encoding='utf8'))
        checker = checker_result['checker']
        assert checker['filename'] == path.name
        assert checker['nFatal'] == checker['nError'] == checker['nWarning'] == 0
        assert not checker_result['messages']
        report['epubcheck'] = {key: checker[key] for key in ['checkerVersion', 'checkDate', 'nFatal', 'nError', 'nWarning']}
    else:
        report['epubcheck'] = {'status': 'No current EPUBCheck JSON report; run EPUBCheck separately.'}
    (ROOT / '_docs/release-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(f'PASS: {len(checked)} content files, {headings_total} headings, {notes_total} footnotes; release integrity verified.')


if __name__ == '__main__':
    verify()
