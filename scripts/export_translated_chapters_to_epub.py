#!/usr/bin/env python3
"""Export translated Markdown chapters into a clean EPUB 3 file."""

from __future__ import annotations

import argparse
import html
import json
import posixpath
import re
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET


EPUB_DIR = "EPUB"
TEXT_DIR = f"{EPUB_DIR}/text"
FOOTNOTE_RE = re.compile(r"^\[\^([^\]]+)\]:\s*(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ORDERED_LIST_RE = re.compile(r"^\d+\.\s+(.+?)\s*$")
UNORDERED_LIST_RE = re.compile(r"^[-*+]\s+(.+?)\s*$")
RAW_BR_RE = re.compile(r"&lt;br\s*/?&gt;", re.IGNORECASE)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Chapter:
    source: Path
    stem: str
    title: str
    xhtml_name: str
    xhtml_path: str
    xhtml: str


def slugify(value: str, fallback: str) -> str:
    plain = strip_markdown(value).lower()
    plain = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return plain or fallback


def strip_markdown(value: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\*\*([^*]+)\*\*", r"\1", value)
    value = re.sub(r"\*([^*]+)\*", r"\1", value)
    value = re.sub(r"\[\^([^\]]+)\]", "", value)
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", value).strip()


def escape_xml(value: str) -> str:
    return html.escape(value, quote=True)


def parse_footnotes(lines: list[str]) -> tuple[list[str], dict[str, str]]:
    body: list[str] = []
    footnotes: dict[str, str] = {}
    active_id: str | None = None

    for line in lines:
        match = FOOTNOTE_RE.match(line)
        if match:
            active_id = match.group(1)
            if active_id in footnotes:
                raise ValueError(f"Duplicate footnote definition: {active_id}")
            footnotes[active_id] = match.group(2).strip()
            continue

        if active_id and (line.startswith("    ") or line.startswith("\t")):
            continuation = line.strip()
            if continuation:
                footnotes[active_id] = f"{footnotes[active_id]} {continuation}".strip()
            continue

        if line.strip():
            active_id = None
        body.append(line)

    return body, footnotes


class MarkdownToXhtml:
    def __init__(self, chapter_id: str, footnotes: dict[str, str]) -> None:
        self.chapter_id = chapter_id
        self.footnotes = footnotes
        self.used_heading_ids: set[str] = set()
        self.reference_counts: dict[str, int] = {}

    def render(self, lines: list[str]) -> str:
        blocks: list[str] = []
        index = 0

        while index < len(lines):
            line = lines[index]
            stripped = line.strip()
            if not stripped:
                index += 1
                continue

            heading = HEADING_RE.match(stripped)
            if heading:
                level = len(heading.group(1))
                text = heading.group(2)
                heading_id = self.unique_heading_id(slugify(text, f"h{index + 1}"))
                blocks.append(
                    f'<h{level} id="{heading_id}">{self.render_inline(text)}</h{level}>'
                )
                index += 1
                continue

            if stripped.startswith(">"):
                quote_lines: list[str] = []
                while index < len(lines) and lines[index].strip().startswith(">"):
                    quote_lines.append(re.sub(r"^\s*>\s?", "", lines[index].rstrip()))
                    index += 1
                blocks.append(self.render_blockquote(quote_lines))
                continue

            ordered = ORDERED_LIST_RE.match(stripped)
            unordered = UNORDERED_LIST_RE.match(stripped)
            if ordered or unordered:
                list_type = "ol" if ordered else "ul"
                pattern = ORDERED_LIST_RE if ordered else UNORDERED_LIST_RE
                items: list[str] = []
                while index < len(lines):
                    item_match = pattern.match(lines[index].strip())
                    if item_match:
                        items.append(item_match.group(1))
                        index += 1
                        continue

                    if not lines[index].strip():
                        next_index = index + 1
                        while next_index < len(lines) and not lines[next_index].strip():
                            next_index += 1
                        if next_index < len(lines) and pattern.match(lines[next_index].strip()):
                            index = next_index
                            continue

                        break

                    break
                rendered_items = "".join(
                    f"<li>{self.render_inline(item)}</li>" for item in items
                )
                blocks.append(f"<{list_type}>{rendered_items}</{list_type}>")
                continue

            paragraph_lines: list[str] = []
            while index < len(lines):
                candidate = lines[index]
                candidate_stripped = candidate.strip()
                if not candidate_stripped:
                    break
                if (
                    HEADING_RE.match(candidate_stripped)
                    or candidate_stripped.startswith(">")
                    or ORDERED_LIST_RE.match(candidate_stripped)
                    or UNORDERED_LIST_RE.match(candidate_stripped)
                ):
                    break
                paragraph_lines.append(candidate_stripped)
                index += 1

            if paragraph_lines:
                paragraph = " ".join(paragraph_lines)
                blocks.append(f"<p>{self.render_inline(paragraph)}</p>")
            else:
                index += 1

        if self.footnotes:
            blocks.append(self.render_footnotes())

        return "\n".join(blocks)

    def render_blockquote(self, quote_lines: list[str]) -> str:
        paragraphs: list[list[str]] = [[]]
        for line in quote_lines:
            if line.strip():
                paragraphs[-1].append(line)
            elif paragraphs[-1]:
                paragraphs.append([])

        rendered = []
        for paragraph in paragraphs:
            if not paragraph:
                continue
            joined_parts = []
            for line_index, line in enumerate(paragraph):
                joined_parts.append(self.render_inline(line))
                if line_index < len(paragraph) - 1:
                    separator = "\n" if re.search(r"<br\s*/?>\s*$", line, re.IGNORECASE) else "<br />\n"
                    joined_parts.append(separator)
            joined = "".join(joined_parts)
            rendered.append(f"<p>{joined}</p>")
        return f"<blockquote>{''.join(rendered)}</blockquote>"

    def render_footnotes(self) -> str:
        items = []
        # Rendering notes can introduce additional references to earlier notes.
        rendered_notes = {key: self.render_inline(value) for key, value in self.footnotes.items()}
        for note_id, note_text in self.footnotes.items():
            note_anchor = self.footnote_id(note_id)
            ref_anchor = self.footnote_ref_id(note_id)
            number_attribute = f' value="{note_id}"' if note_id.isdigit() else ''
            label = '' if note_id.isdigit() else f'<span class="note-label">{self.footnote_label(note_id)}</span> '
            if not note_id.isdigit():
                number_attribute = ' class="editorial-note"'
            backlinks = ' '.join(
                f'<a href="#{ref_anchor}{"-" + str(index) if index > 1 else ""}" '
                f'aria-label="Back to reference {index}">&#8617;{index if self.reference_counts[note_id] > 1 else ""}</a>'
                for index in range(1, self.reference_counts.get(note_id, 0) + 1)
            )
            items.append(
                f'<li id="{note_anchor}" epub:type="footnote"'
                f'{number_attribute}><p>{label}{rendered_notes[note_id]} '
                f'{backlinks}</p></li>'
            )
        return (
            '<section class="footnotes" epub:type="footnotes">'
            "<h2>Notes</h2>"
            f"<ol>{''.join(items)}</ol>"
            "</section>"
        )

    def unique_heading_id(self, base_id: str) -> str:
        candidate = base_id
        suffix = 2
        while candidate in self.used_heading_ids:
            candidate = f"{base_id}-{suffix}"
            suffix += 1
        self.used_heading_ids.add(candidate)
        return candidate

    def footnote_id(self, note_id: str) -> str:
        return f"fn-{self.chapter_id}-{slugify(note_id, note_id)}"

    def footnote_ref_id(self, note_id: str) -> str:
        return f"fnref-{self.chapter_id}-{slugify(note_id, note_id)}"

    def footnote_label(self, note_id: str) -> str:
        if note_id.isdigit():
            return note_id
        named_notes = [key for key in self.footnotes if not key.isdigit()]
        index = named_notes.index(note_id)
        return ('†', '‡', '§', '‖')[index] if index < 4 else f'E{index + 1}'

    def render_inline(self, text: str) -> str:
        parts = re.split(r"(`[^`]*`)", text)
        rendered: list[str] = []
        for part in parts:
            if not part:
                continue
            if part.startswith("`") and part.endswith("`") and len(part) >= 2:
                rendered.append(f"<code>{escape_xml(part[1:-1])}</code>")
            else:
                rendered.append(self.render_non_code(part))
        return "".join(rendered)

    def render_non_code(self, text: str) -> str:
        escaped = escape_xml(text)
        escaped = RAW_BR_RE.sub("<br />", escaped)
        escaped = re.sub(
            r"\[\^([^\]]+)\]",
            lambda match: self.render_footnote_ref(match.group(1)),
            escaped,
        )
        escaped = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            lambda match: (
                f'<a href="{escape_xml(html.unescape(match.group(2)))}">'
                f"{self.render_inline(html.unescape(match.group(1)))}</a>"
            ),
            escaped,
        )
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)
        return escaped

    def render_footnote_ref(self, note_id: str) -> str:
        note_anchor = self.footnote_id(note_id)
        ref_anchor = self.footnote_ref_id(note_id)
        if note_id not in self.footnotes:
            raise ValueError(f"Undefined footnote {note_id} in {self.chapter_id}")
        self.reference_counts[note_id] = self.reference_counts.get(note_id, 0) + 1
        if self.reference_counts[note_id] > 1:
            ref_anchor += f'-{self.reference_counts[note_id]}'
        return (
            f'<a id="{ref_anchor}" epub:type="noteref" href="#{note_anchor}" '
            f'class="noteref">[{escape_xml(self.footnote_label(note_id))}]</a>'
        )


def chapter_title(source: Path, lines: list[str]) -> str:
    for line in lines:
        match = HEADING_RE.match(line.strip())
        if match:
            text = strip_markdown(match.group(2))
            return text or source.stem
    return source.stem


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"(\d+)", path.stem)
    if match:
        return int(match.group(1)), path.name
    return sys.maxsize, path.name


def discover_chapters(input_dir: Path) -> list[Path]:
    chapters = sorted(input_dir.glob("*.md"), key=chapter_sort_key)
    if not chapters:
        raise ValueError(f"No translated .md chapters found in {input_dir}")
    return chapters


def render_chapter(source: Path) -> Chapter:
    raw_lines = source.read_text(encoding="utf-8-sig").splitlines()
    body_lines, footnotes = parse_footnotes(raw_lines)
    title = chapter_title(source, body_lines)
    chapter_id = slugify(source.stem, source.stem)
    body = MarkdownToXhtml(chapter_id, footnotes).render(body_lines)
    xhtml_name = f"{source.stem}.xhtml"
    xhtml_path = f"{TEXT_DIR}/{xhtml_name}"
    document_title = escape_xml(title)
    xhtml = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head>
  <meta charset="utf-8" />
  <title>{document_title}</title>
  <link rel="stylesheet" type="text/css" href="../styles.css" />
</head>
<body>
<section epub:type="chapter" id="{chapter_id}">
{body}
</section>
</body>
</html>
"""
    return Chapter(source, source.stem, title, xhtml_name, xhtml_path, xhtml)


def nav_document(chapters: list[Chapter], title: str, language: str, cover: bool = False) -> str:
    items = "\n".join(
        f'      <li><a href="text/{chapter.xhtml_name}">{escape_xml(chapter.title)}</a></li>'
        for chapter in chapters
    )
    landmarks = []
    if cover:
        landmarks.append('<li><a epub:type="cover" href="text/cover.xhtml">Cover</a></li>')
    title_page = next((c for c in chapters if c.stem == 'chapter-0001'), chapters[0])
    main_text = next((c for c in chapters if c.stem == 'chapter-0003'), chapters[0])
    landmarks.extend([
        f'<li><a epub:type="titlepage" href="text/{title_page.xhtml_name}">Title page</a></li>',
        '<li><a epub:type="toc" href="nav.xhtml#toc">Contents</a></li>',
        f'<li><a epub:type="bodymatter" href="text/{main_text.xhtml_name}">Main text</a></li>',
    ])
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{escape_xml(language)}" xml:lang="{escape_xml(language)}">
<head>
  <meta charset="utf-8" />
  <title>Contents</title>
  <link rel="stylesheet" type="text/css" href="styles.css" />
</head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{escape_xml(title)}</h1>
    <ol>
{items}
    </ol>
  </nav>
  <nav epub:type="landmarks" id="landmarks" hidden="hidden">
    <h2>Landmarks</h2>
    <ol>
      {chr(10).join(landmarks)}
    </ol>
  </nav>
</body>
</html>
"""


def package_document(args: argparse.Namespace, chapters: list[Chapter], modified: str) -> str:
    manifest_items = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="style" href="styles.css" media-type="text/css"/>',
    ]
    spine_items = []
    if args.cover:
        manifest_items.extend([
            '<item id="cover-image" href="images/cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
            '<item id="cover-page" href="text/cover.xhtml" media-type="application/xhtml+xml"/>',
        ])
        spine_items.append('<itemref idref="cover-page"/>')
    for index, chapter in enumerate(chapters, 1):
        item_id = chapter.stem
        manifest_items.append(
            f'<item id="{item_id}" href="text/{chapter.xhtml_name}" '
            'media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{item_id}"/>')
        if chapter.stem == 'edition-and-credits':
            spine_items.append('<itemref idref="nav"/>')

    subjects = "\n".join(
        f"    <dc:subject>{escape_xml(subject)}</dc:subject>"
        for subject in args.subject
    )
    contributors = "\n".join(
        f'    <dc:contributor id="contributor-{index}">{escape_xml(contributor)}</dc:contributor>\n'
        f'    <meta refines="#contributor-{index}" property="role">AI assistance</meta>'
        for index, contributor in enumerate(args.contributor, 1)
    )
    translator_metadata = ''
    if args.translator:
        translator_metadata = (
            f'<dc:contributor id="translator">{escape_xml(args.translator)}</dc:contributor>\n'
            '<meta refines="#translator" property="role" scheme="marc:relators">trl</meta>'
        )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="{escape_xml(args.language)}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{escape_xml(args.identifier)}</dc:identifier>
    <dc:title>{escape_xml(args.title)}</dc:title>
    <dc:creator id="author">{escape_xml(args.creator)}</dc:creator>
    <meta refines="#author" property="role" scheme="marc:relators">aut</meta>
{translator_metadata}
{contributors}
    <dc:language>{escape_xml(args.language)}</dc:language>
    <dc:publisher>{escape_xml(args.publisher)}</dc:publisher>
    <dc:date>{escape_xml(args.date)}</dc:date>
{subjects}
    <dc:description>{escape_xml(args.description)}</dc:description>
    <dc:source>{escape_xml(args.source)}</dc:source>
    <dc:rights>{escape_xml(args.rights)}</dc:rights>
    <meta property="schema:bookEdition">First English release, v{escape_xml(args.release_version)}</meta>
    <meta property="dcterms:modified">{escape_xml(modified)}</meta>
  </metadata>
  <manifest>
    {chr(10).join(manifest_items)}
  </manifest>
  <spine>
    {chr(10).join(spine_items)}
  </spine>
</package>
"""


def container_document() -> str:
    return """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""


def stylesheet() -> str:
    return """body {
  font-family: serif;
  line-height: 1.45;
  margin: 5%;
}

h1, h2, h3, h4, h5, h6 {
  line-height: 1.2;
  margin: 1.6em 0 0.7em;
}

p {
  margin: 0 0 1em;
}

blockquote {
  margin: 1.2em 1.5em;
}

blockquote p {
  margin-bottom: 0.6em;
}

code {
  font-family: serif;
  font-style: italic;
}

ol, ul {
  margin: 1em 0 1em 2em;
  padding: 0;
}

li {
  margin: 0.35em 0;
}

.footnotes {
  border-top: 1px solid #777;
  margin-top: 2em;
  padding-top: 1em;
  font-size: 0.9em;
}

.noteref {
  font-size: 0.8em;
  vertical-align: super;
  text-decoration: none;
}

.editorial-note {
  list-style-type: none;
}

.note-label {
  font-weight: bold;
}
"""


def write_epub(args: argparse.Namespace, chapters: list[Chapter]) -> None:
    modified = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.output, "w", compression=zipfile.ZIP_DEFLATED) as epub:
        epub.writestr(
            zipfile.ZipInfo("mimetype"),
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        epub.writestr("META-INF/container.xml", container_document())
        epub.writestr(f"{EPUB_DIR}/content.opf", package_document(args, chapters, modified))
        epub.writestr(f"{EPUB_DIR}/nav.xhtml", nav_document(chapters, args.title, args.language, bool(args.cover)))
        epub.writestr(f"{EPUB_DIR}/styles.css", stylesheet())
        if args.cover:
            epub.write(args.cover, f'{EPUB_DIR}/images/cover.jpg')
            epub.writestr(f'{TEXT_DIR}/cover.xhtml', cover_document(args.title))
        for chapter in chapters:
            epub.writestr(chapter.xhtml_path, chapter.xhtml)


def cover_document(title: str) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="en" xml:lang="en">
<head><title>Cover</title><style>html,body{{margin:0;padding:0;text-align:center}} img{{display:block;width:100%;height:auto;margin:auto}}</style></head>
<body epub:type="cover"><img src="../images/cover.jpg" alt="Cover: {escape_xml(title)}, by Arthur Schopenhauer; Contemporary English translation, with a painted portrait of the author blending into a midnight teal background."/></body>
</html>'''


def validate_epub(path: Path) -> None:
    with zipfile.ZipFile(path) as epub:
        names = epub.namelist()
        if not names or names[0] != "mimetype":
            raise ValueError("EPUB mimetype must be the first archive entry.")
        if epub.read("mimetype") != b"application/epub+zip":
            raise ValueError("EPUB mimetype entry is invalid.")

        markdown_artifacts = [name for name in names if name.lower().endswith(".md")]
        if markdown_artifacts:
            joined = ", ".join(markdown_artifacts)
            raise ValueError(f"Markdown artifacts found inside EPUB: {joined}")

        required = {"META-INF/container.xml", f"{EPUB_DIR}/content.opf", f"{EPUB_DIR}/nav.xhtml"}
        missing = sorted(required.difference(names))
        if missing:
            raise ValueError(f"Missing required EPUB files: {', '.join(missing)}")

        documents = {}
        identifiers = {}
        for name in names:
            if name.endswith((".xhtml", ".opf", ".xml")):
                documents[name] = ET.fromstring(epub.read(name))
                ids = [element.get('id') for element in documents[name].iter() if element.get('id')]
                if len(ids) != len(set(ids)):
                    raise ValueError(f'Duplicate IDs in {name}')
                identifiers[name] = set(ids)
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        for name, root in documents.items():
            for element in root.iter():
                for attribute in ('href', 'src'):
                    link = element.get(attribute)
                    if not link:
                        continue
                    url = urlsplit(link)
                    if url.scheme or url.netloc:
                        continue
                    target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
                    if target not in names:
                        raise ValueError(f'Broken link in {name}: {link}')
                    if url.fragment and unquote(url.fragment) not in identifiers.get(target, set()):
                        raise ValueError(f'Broken fragment in {name}: {link}')
                refines = element.get('refines')
                if refines and refines.removeprefix('#') not in identifiers[name]:
                    raise ValueError(f'Unknown metadata refinement: {refines}')
        ns = {'opf': 'http://www.idpf.org/2007/opf', 'x': 'http://www.w3.org/1999/xhtml'}
        package = documents[f'{EPUB_DIR}/content.opf']
        manifest = package.findall('opf:manifest/opf:item', ns)
        by_id = {item.get('id'): item for item in manifest}
        for item in package.findall('opf:spine/opf:itemref', ns):
            if item.get('idref') not in by_id:
                raise ValueError(f'Unknown spine item: {item.get("idref")}')
        cover_images = [item for item in manifest if 'cover-image' in item.get('properties', '').split()]
        if len(cover_images) > 1:
            raise ValueError('Multiple cover images')
        # Every footnote destination is marked and links back to each reference.
        epub_type = '{http://www.idpf.org/2007/ops}type'
        for name, root in documents.items():
            if not name.endswith('.xhtml'):
                continue
            by_anchor = {element.get('id'): element for element in root.iter() if element.get('id')}
            for element in root.iter():
                if element.get(epub_type) == 'noteref':
                    note = by_anchor[element.get('href').removeprefix('#')]
                    if note.get(epub_type) != 'footnote':
                        raise ValueError(f'Unmarked footnote in {name}')
                    if not any(link.get('href') == '#' + element.get('id') for link in note.iter()):
                        raise ValueError(f'Missing footnote return link in {name}')


def normalize_identifier(identifier: str | None) -> str:
    if identifier:
        return identifier
    return f"urn:uuid:{uuid.uuid4()}"


def normalize_output(path: Path) -> Path:
    if path.suffix.lower() != ".epub":
        return path.with_suffix(".epub")
    return path


def parse_args() -> argparse.Namespace:
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument('--metadata-file', type=Path, default=PROJECT_ROOT / 'release.json')
    options, _ = preliminary.parse_known_args()
    configuration = json.loads(options.metadata_file.read_text(encoding='utf-8')) if options.metadata_file.exists() else {}
    parser = argparse.ArgumentParser(
        description="Export translated Markdown chapters into an EPUB 3 file."
    )
    parser.add_argument('--metadata-file', type=Path, default=options.metadata_file, help='Release metadata JSON; CLI flags override its values.')
    parser.add_argument('--cover', type=Path, help='JPEG cover image.')
    parser.add_argument('--credits', type=Path, help='Edition-and-credits Markdown page.')
    parser.add_argument('--translator', default='Ratanajaya', help='Translator metadata with MARC trl role.')
    parser.add_argument('--rights', default='', help='Rights and license statement.')
    parser.add_argument('--release-version', default='1.0.0', help='Edition version.')
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("english-translation"),
        help="Folder containing translated chapter-*.md files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/the-world-as-will-and-representation-volume-i.epub"),
        help="Output EPUB path.",
    )
    parser.add_argument(
        "--title",
        default="The World as Will and Representation, Volume I",
        help="EPUB title metadata.",
    )
    parser.add_argument("--creator", default="Arthur Schopenhauer", help="Author metadata.")
    parser.add_argument(
        "--contributor",
        action="append",
        default=[
            "OpenAI GPT-5.5",
            "OpenAI GPT-6 Sol",
        ],
        help="Contributor metadata. May be provided more than once.",
    )
    parser.add_argument("--language", default="en", help="EPUB language code.")
    parser.add_argument(
        "--publisher",
        default="Schopenhauer Translation Project",
        help="Publisher metadata.",
    )
    parser.add_argument(
        "--identifier",
        help="Unique EPUB identifier. Defaults to a generated urn:uuid value.",
    )
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Publication/export date metadata in YYYY-MM-DD form.",
    )
    parser.add_argument(
        "--subject",
        action="append",
        default=["Philosophy", "German philosophy", "Metaphysics"],
        help="Subject metadata. May be provided more than once.",
    )
    parser.add_argument(
        "--description",
        default=(
            "Modern English translation of Arthur Schopenhauer's "
            "The World as Will and Representation, Volume I, by Ratanajaya, "
            "with AI assistance from OpenAI's GPT-5.5 and GPT-6 Sol."
        ),
        help="Description metadata.",
    )
    parser.add_argument(
        "--source",
        default="Translated chapters from english-translation Markdown files.",
        help="Source metadata.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip archive and XML validation after writing the EPUB.",
    )
    for key in ('cover', 'credits'):
        if configuration.get(key):
            configuration[key] = options.metadata_file.resolve().parent / configuration[key]
    parser.set_defaults(**configuration)
    args = parser.parse_args()
    args.output = normalize_output(args.output)
    args.identifier = normalize_identifier(args.identifier)
    return args


def main() -> int:
    args = parse_args()
    try:
        chapter_paths = discover_chapters(args.input_dir)
        chapters = [render_chapter(path) for path in chapter_paths]
        if args.credits:
            credits = render_chapter(args.credits)
            chapters.insert(1, credits)
        write_epub(args, chapters)
        if not args.no_validate:
            validate_epub(args.output)
    except Exception as error:
        print(f"EPUB export failed: {error}", file=sys.stderr)
        return 1

    print(f"Exported {len(chapter_paths)} content files"
          f'{" plus edition-and-credits page" if args.credits else ""} to {args.output}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
