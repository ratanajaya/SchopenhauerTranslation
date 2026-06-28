#!/usr/bin/env python3
"""Export translated Markdown chapters into a clean EPUB 3 file."""

from __future__ import annotations

import argparse
import html
import re
import sys
import uuid
import zipfile
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from xml.etree import ElementTree as ET


EPUB_DIR = "EPUB"
TEXT_DIR = f"{EPUB_DIR}/text"
FOOTNOTE_RE = re.compile(r"^\[\^([^\]]+)\]:\s*(.*)$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ORDERED_LIST_RE = re.compile(r"^\d+\.\s+(.+?)\s*$")
UNORDERED_LIST_RE = re.compile(r"^[-*+]\s+(.+?)\s*$")
RAW_BR_RE = re.compile(r"&lt;br\s*/?&gt;", re.IGNORECASE)


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
        for note_id, note_text in self.footnotes.items():
            note_anchor = self.footnote_id(note_id)
            ref_anchor = self.footnote_ref_id(note_id)
            items.append(
                f'<li id="{note_anchor}"><p>{self.render_inline(note_text)} '
                f'<a href="#{ref_anchor}" aria-label="Back to text">&#8617;</a></p></li>'
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
                f'<a href="{escape_xml(match.group(2))}">'
                f"{self.render_inline(match.group(1))}</a>"
            ),
            escaped,
        )
        escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)
        return escaped

    def render_footnote_ref(self, note_id: str) -> str:
        note_anchor = self.footnote_id(note_id)
        ref_anchor = self.footnote_ref_id(note_id)
        return (
            f'<a id="{ref_anchor}" epub:type="noteref" href="#{note_anchor}" '
            f'class="noteref">[{escape_xml(note_id)}]</a>'
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


def nav_document(chapters: list[Chapter], title: str, language: str) -> str:
    items = "\n".join(
        f'      <li><a href="text/{chapter.xhtml_name}">{escape_xml(chapter.title)}</a></li>'
        for chapter in chapters
    )
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
      <li><a epub:type="bodymatter" href="text/{chapters[0].xhtml_name}">Start</a></li>
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
    for index, chapter in enumerate(chapters, 1):
        item_id = f"chapter-{index:04d}"
        manifest_items.append(
            f'<item id="{item_id}" href="text/{chapter.xhtml_name}" '
            'media-type="application/xhtml+xml"/>'
        )
        spine_items.append(f'<itemref idref="{item_id}"/>')

    subjects = "\n".join(
        f"    <dc:subject>{escape_xml(subject)}</dc:subject>"
        for subject in args.subject
    )
    contributors = "\n".join(
        f"    <dc:contributor>{escape_xml(contributor)}</dc:contributor>"
        for contributor in args.contributor
    )

    return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="{escape_xml(args.language)}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{escape_xml(args.identifier)}</dc:identifier>
    <dc:title>{escape_xml(args.title)}</dc:title>
    <dc:creator>{escape_xml(args.creator)}</dc:creator>
{contributors}
    <dc:language>{escape_xml(args.language)}</dc:language>
    <dc:publisher>{escape_xml(args.publisher)}</dc:publisher>
    <dc:date>{escape_xml(args.date)}</dc:date>
{subjects}
    <dc:description>{escape_xml(args.description)}</dc:description>
    <dc:source>{escape_xml(args.source)}</dc:source>
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
"""


def write_epub(args: argparse.Namespace, chapters: list[Chapter]) -> None:
    modified = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(args.output, "w") as epub:
        epub.writestr(
            zipfile.ZipInfo("mimetype"),
            "application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
        )
        epub.writestr("META-INF/container.xml", container_document())
        epub.writestr(f"{EPUB_DIR}/content.opf", package_document(args, chapters, modified))
        epub.writestr(f"{EPUB_DIR}/nav.xhtml", nav_document(chapters, args.title, args.language))
        epub.writestr(f"{EPUB_DIR}/styles.css", stylesheet())
        for chapter in chapters:
            epub.writestr(chapter.xhtml_path, chapter.xhtml)


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

        for name in names:
            if name.endswith((".xhtml", ".opf", ".xml")):
                ET.fromstring(epub.read(name))


def normalize_identifier(identifier: str | None) -> str:
    if identifier:
        return identifier
    return f"urn:uuid:{uuid.uuid4()}"


def normalize_output(path: Path) -> Path:
    if path.suffix.lower() != ".epub":
        return path.with_suffix(".epub")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export translated Markdown chapters into an EPUB 3 file."
    )
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
        default=["Schopenhauer Translation Project"],
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
            "In-progress modern English translation of Arthur Schopenhauer's "
            "The World as Will and Representation, Volume I."
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
    args = parser.parse_args()
    args.output = normalize_output(args.output)
    args.identifier = normalize_identifier(args.identifier)
    return args


def main() -> int:
    args = parse_args()
    try:
        chapter_paths = discover_chapters(args.input_dir)
        chapters = [render_chapter(path) for path in chapter_paths]
        write_epub(args, chapters)
        if not args.no_validate:
            validate_epub(args.output)
    except Exception as error:
        print(f"EPUB export failed: {error}", file=sys.stderr)
        return 1

    print(f"Exported {len(chapters)} translated chapters to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
