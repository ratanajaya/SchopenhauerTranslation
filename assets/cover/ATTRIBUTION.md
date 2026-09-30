# Cover sources and artwork

Likeness reference: **Arthur Schopenhauer**, photographed by **J. Schäfer**, March 1859.
Source institution: Frankfurt am Main University Library, via
[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Arthur_Schopenhauer_by_J_Sch%C3%A4fer,_1859.jpg).

Commons identifies the photograph as public domain (Public Domain Mark 1.0).
The original JPEG is retained as `schopenhauer-schaefer-1859.jpg` for provenance.
It is not embedded in the revised cover.

`schopenhauer-painted.png` is an AI-assisted painted interpretation generated
with OpenAI's built-in image-generation tool on September 30, 2026, using the
historical photograph as a likeness reference. It is an illustration, not a
historical painting. The portrait and abstract backdrop form one full-bleed
image. The selected artwork is retained locally so builds need no image service.

Cover design by Ratanajaya; the artwork and layout are included in the CC BY 4.0
grant to the extent copyright applies. Typography: Georgia / Arial, rendered
using installed fonts; font files are not redistributed.

The editable `cover.svg` embeds the painted artwork with editable typography.
`build_cover.py` composes the same layout as a JPEG at 1600 × 2400 pixels.
The cover reads “Contemporary English translation” and has no translator name.

## Generation prompt

See [generation-prompt.txt](generation-prompt.txt) for the exact final prompt.
The built-in tool was used, not the CLI fallback.
