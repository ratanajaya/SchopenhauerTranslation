#!/usr/bin/env python3
"""Convert XHTML files extracted from an EPUB into Markdown files."""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


BLOCK_TAGS = {"div", "h1", "h2", "h3", "h4", "h5", "h6", "p", "section"}
SKIP_TAGS = {"head", "link", "meta", "script", "style", "title"}


def local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text)


def tidy_inline(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" ?<br>\n ?", "<br>\n", text)
    return text.strip()


def code_span(text: str) -> str:
    text = text.strip()
    if not text:
        return ""
    if "`" not in text:
        return f"`{text}`"
    return f"`` {text} ``"


def render_inline(
    node: ET.Element,
    footnotes: list[str],
    include_page_anchors: bool,
) -> str:
    tag = local_name(node.tag)
    classes = set((node.attrib.get("class") or "").split())

    if tag == "br":
        return "<br>\n" + normalize_text(node.tail)

    if tag == "a":
        text = render_children(node, footnotes, include_page_anchors)
        href = node.attrib.get("href")
        anchor_id = node.attrib.get("id")
        if href and text:
            rendered = f"[{text}]({href})"
        elif include_page_anchors and anchor_id:
            rendered = f'<a id="{anchor_id}"></a>'
        else:
            rendered = text
        return rendered + normalize_text(node.tail)

    if tag == "span" and "footnote" in classes:
        note = tidy_inline(render_children(node, footnotes, include_page_anchors))
        if note:
            footnotes.append(note)
            rendered = f"[^{len(footnotes)}]"
        else:
            rendered = ""
        return rendered + normalize_text(node.tail)

    text = render_children(node, footnotes, include_page_anchors)
    if tag == "span":
        if "tt" in classes:
            text = code_span(text)
        elif "spaced" in classes:
            text = f"*{text.strip()}*" if text.strip() else ""
    elif tag in {"em", "i"}:
        text = f"*{text.strip()}*" if text.strip() else ""
    elif tag in {"strong", "b"}:
        text = f"**{text.strip()}**" if text.strip() else ""
    elif tag == "sup":
        text = f"^{text.strip()}^" if text.strip() else ""
    elif tag == "sub":
        text = f"~{text.strip()}~" if text.strip() else ""

    return text + normalize_text(node.tail)


def render_children(
    node: ET.Element,
    footnotes: list[str],
    include_page_anchors: bool,
) -> str:
    parts = [normalize_text(node.text)]
    for child in node:
        tag = local_name(child.tag)
        if tag in SKIP_TAGS:
            parts.append(normalize_text(child.tail))
        elif tag in BLOCK_TAGS:
            parts.append(render_block(child, footnotes, include_page_anchors))
            parts.append(normalize_text(child.tail))
        else:
            parts.append(render_inline(child, footnotes, include_page_anchors))
    return "".join(parts)


def render_block(
    node: ET.Element,
    footnotes: list[str],
    include_page_anchors: bool,
) -> str:
    tag = local_name(node.tag)
    classes = set((node.attrib.get("class") or "").split())
    text = tidy_inline(render_children(node, footnotes, include_page_anchors))

    if not text:
        return ""

    if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(tag[1])
        return f"{'#' * level} {text}"

    if tag == "div" and "motto" in classes:
        return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())

    return text


def find_body(root: ET.Element) -> ET.Element:
    for element in root.iter():
        if local_name(element.tag) == "body":
            return element
    return root


def convert_file(source: Path, destination: Path, include_page_anchors: bool) -> None:
    parser = ET.XMLParser(encoding="utf-8")
    root = ET.parse(source, parser=parser).getroot()
    body = find_body(root)
    footnotes: list[str] = []
    blocks: list[str] = []

    for child in body:
        tag = local_name(child.tag)
        if tag in SKIP_TAGS:
            continue
        if tag in BLOCK_TAGS:
            rendered = render_block(child, footnotes, include_page_anchors)
        else:
            rendered = tidy_inline(render_inline(child, footnotes, include_page_anchors))
        if rendered:
            blocks.append(rendered)

    if footnotes:
        blocks.append("\n".join(f"[^{index}]: {note}" for index, note in enumerate(footnotes, 1)))

    markdown = "\n\n".join(blocks).strip() + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(markdown, encoding="utf-8")


def default_output_dir(input_dir: Path) -> Path:
    return input_dir.with_name(f"{input_dir.name}-md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert EPUB-extracted .xhtml files to .md files."
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        default="original-epub-extract",
        type=Path,
        help="Folder containing .xhtml files. Defaults to original-epub-extract.",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        type=Path,
        help="Folder for .md files. Defaults to a sibling folder ending in -md.",
    )
    parser.add_argument(
        "--include-page-anchors",
        action="store_true",
        help="Preserve empty page anchors as raw HTML anchors in the Markdown.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir or default_output_dir(input_dir)

    if not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}", file=sys.stderr)
        return 1

    sources = sorted(input_dir.rglob("*.xhtml"))
    if not sources:
        print(f"No .xhtml files found in {input_dir}", file=sys.stderr)
        return 1

    for source in sources:
        relative = source.relative_to(input_dir).with_suffix(".md")
        convert_file(source, output_dir / relative, args.include_page_anchors)

    print(f"Converted {len(sources)} files to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
