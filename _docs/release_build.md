# Building the release

Run from the repository root with Python 3 and Pillow installed. The PDF
renderer additionally needs `reportlab` and `pypdf`; the build uses the active
Python if it has them, otherwise the installed Codex bundled Python runtime.
Use `python scripts/build_release.py --pdf-python PATH` to select another
Python executable explicitly:

```powershell
python -X utf8 scripts/build_release.py
python -X utf8 scripts/test_epub_exporter.py
python -X utf8 scripts/verify_release.py
```

The build writes exactly six files to `dist/`, verifies their checksums,
and retains the original portrait and editable artwork in `assets/cover/`.
The cover composer uses locally installed Georgia and Arial fonts at
`C:/Windows/Fonts/`. Font files are not part of the release. The retained
`assets/cover/schopenhauer-painted.png` is the AI-assisted artwork; rebuilding
does not regenerate it or call an image service. The composer creates both
the SVG and JPEG from the shared layout coordinates in `build_cover.py`;
change those coordinates to rebuild both consistently. The SVG also remains
independently editable; archive custom SVG edits before rerunning the composer.

`scripts/build_pdf.py` typesets the packaged EPUB into a 6 × 9-inch PDF.
It embeds locally installed Times New Roman (including italic and bold)
and Segoe UI Symbol fonts, checks glyph coverage including polytonic Greek,
and preserves content, external links, note references and return links.
Notes follow each source section. PDF bookmarks and a linked contents page
provide navigation, with printed page numbers beginning after the cover.
Font files are not redistributed separately. To build only the PDF, run:

```powershell
python -X utf8 scripts/build_pdf.py
```

This standalone command needs a Python environment with `reportlab` and
`pypdf`; `--font-dir` selects an alternative directory containing the required
font filenames. Regenerate `SHA256SUMS` through the release build after changes.
`scripts/verify_pdf.py`, run automatically by the release build, verifies
every paragraph, heading, and list item in source order, all 122 notes,
bookmark titles and pages, internal link destinations, embedded fonts,
profile links, page dimensions, and printed numbering. Its checked-in report
is `_docs/pdf-validation.json`. Run it with the same Python as the PDF renderer.

`release.json` is the checked-in publication metadata. It retains the book's
UUID, translation and AI credits, edition version, rights, and publication
date. Rebuilds of this edition keep September 30, 2026 (Asia/Bangkok); for a
new release, explicitly update the version and publication date. EPUB's
`dcterms:modified` records the actual UTC build time. ZIP timestamps also
change on rebuild, so a rebuilt EPUB has new checksums.

All existing exporter flags remain available. Additional inputs are
`--metadata-file`, `--cover`, `--credits`, `--translator`, `--rights`, and
`--release-version`. Scalar command-line flags override the configuration;
repeatable `--subject` and `--contributor` flags append, preserving the
exporter's prior behavior. The default exporter uses `release.json`.

To fetch the published collation witnesses and EPUBCheck into the ignored
cache, then validate (Java required):

```powershell
python -X utf8 scripts/fetch_release_references.py
java -jar .release-cache/epubcheck/epubcheck-5.4.0/epubcheck.jar dist/the-world-as-will-and-representation-volume-i.epub
```

EPUBCheck must report zero errors; review all warnings. The structural
verifier compares the full body and footnote text of all 74 input files with
the packaged XHTML, checks metadata, navigation, cover bytes, internal
references, and release checksums. It writes `release-validation.json`.
Reader inspection remains a separate visual check after changes.

Upload the six files in `dist/` to a GitHub release tagged **v1.0.0** and
paste `dist/RELEASE_NOTES.md` into its description. Publishing and uploading
are the repository owner's steps.
