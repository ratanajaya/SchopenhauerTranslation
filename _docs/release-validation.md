# Release validation — v1.0.0

Validated September 30, 2026 (Asia/Bangkok). Publication metadata and the
stable UUID are in [release.json](../release.json); reproducible build
instructions are in [release_build.md](release_build.md).

## Automated checks

- **EPUBCheck 5.4.0:** zero fatal errors, errors, warnings, or informational messages.
- **Exporter regression checks:** six passing checks, covering repeated and nested note references, return links, missing references, duplicate definitions, XML escaping in Markdown links, Greek line breaks, and preserved note numbering / editorial symbols.
- **Full content comparison:** all **74 existing content files**, **84 headings**, and **122 footnotes** included. Body and note text compared with every Markdown input after removing formatting and generated reference labels; original-language quotations remain present. Added edition-and-credits page brings the navigable content pages to 75, alongside the cover and contents.
- **Links and IDs:** unique document IDs; all internal resource links and fragments resolve; every footnote reference has a marked destination and return link. Nested references to earlier notes are included.
- **Metadata:** title, author (`aut`), translator (`trl`), two AI assistance contributors, publisher, language, subjects, source, rights, version, date, and unchanged UUID match the checked-in configuration.
- **Cover and navigation:** EPUB `cover-image` property; embedded JPEG byte-identical to the release cover; cover first in reading order; cover, title page, contents, and main-text landmarks; ordered contents links include all content files and credits.
- **Sources and package:** German extraction unchanged relative to Git HEAD. Exactly five upload files; four SHA-256 entries, each verified. Release license and notes match their checked-in sources. README is approximately 170 words, with a 320 px cover and valid local asset / editorial links.

[release-validation.json](release-validation.json) records content hashes,
counts, metadata check outcomes, and the final release-file checksums.

## Visual and reader checks

The actual packaged EPUB was opened with **EPUB.js 0.3.93** in Chromium,
at **375 px** and **900 px** reading widths. Inspected the cover, historical
title page, edition credits, contents, polytonic Greek in §16 and the Plato
epigraph, Homer's quotation in §51, the Kant appendix, and its Bruno and
editorial notes. Tested a contents link and both directions of a footnote
link. Greek characters, line breaks, headings, and notes are readable.
This is inspection in one reading engine, not a claim of testing every
commercial reader.

The reader check exposed a cover image shrinking under viewport-relative
height rules. The cover page now uses proportional image sizing without
those rules. Note lists retain the author's numeric labels, including
Bruno's note 2; editorial notes use dagger symbols instead of internal keys.

Inspected the 1600 × 2400 JPEG and its 320 × 480 thumbnail. Typography fits
the generous margins; the photograph retains the top of the hair and uses
the same crop in the embedded-image SVG. Inspected the README cover and
download links. The original photograph and attribution remain outside
`dist/`.

## Editorial disposition

Every earlier flagged review item has a sourced correction or explicit
explanation in [human_review_notes.md](human_review_notes.md). The expanded
Greek audit repairs additional extraction faults. Source omissions,
historical quotation variants, and the appendix's modality emendation are
identified in reader-facing notes. This is a modern reading edition with
targeted collation, not a newly established critical text.
