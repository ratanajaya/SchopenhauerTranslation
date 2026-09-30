"""Compose editable book typography over the retained painted cover artwork."""
from pathlib import Path
import base64
import html
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'cover'
ART = ASSETS / 'schopenhauer-painted.png'
SIZE = (1600, 2400)
CREAM = '#f6e9ce'
COPPER = '#d5ae73'

# Shared typography coordinates keep the editable SVG and JPEG consistent.
# The artwork is full bleed, with no photo crop or portrait frame.
texts = [
    (130, 'ARTHUR SCHOPENHAUER', 43, 'arial.ttf', 'Arial, sans-serif', CREAM),
    (235, 'The World', 118, 'georgia.ttf', 'Georgia, serif', CREAM),
    (365, 'as Will and', 118, 'georgia.ttf', 'Georgia, serif', CREAM),
    (495, 'Representation', 118, 'georgia.ttf', 'Georgia, serif', CREAM),
    (625, 'VOLUME I', 30, 'arial.ttf', 'Arial, sans-serif', COPPER),
    (2240, 'Contemporary English translation', 47, 'arial.ttf', 'Arial, sans-serif', CREAM),
]

image = Image.open(ART).convert('RGB')
if image.width * SIZE[1] != image.height * SIZE[0]:
    raise ValueError('Cover artwork must have a 2:3 aspect ratio; do not crop it.')
image = image.resize(SIZE, Image.Resampling.LANCZOS)
draw = ImageDraw.Draw(image)
svg_text = []
for y, text, size, font_file, family, color in texts:
    font = ImageFont.truetype(str(Path('C:/Windows/Fonts') / font_file), size)
    width = draw.textlength(text, font=font)
    if width > SIZE[0] - 240:
        raise ValueError(f'Text exceeds cover width: {text}')
    x = (SIZE[0] - width) / 2
    draw.text((x, y), text, fill=color, font=font, anchor='lt')
    baseline = y + font.getmetrics()[0] - font.getbbox(text)[1]
    svg_text.append(f'<text x="{x}" y="{baseline}" font-family="{family}" font-size="{size}" fill="{color}">{html.escape(text)}</text>')

data = base64.b64encode(ART.read_bytes()).decode('ascii')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2400" viewBox="0 0 1600 2400">
<title>The World as Will and Representation, Volume I — Contemporary English translation</title>
<image x="0" y="0" width="1600" height="2400" href="data:image/png;base64,{data}"/>
{chr(10).join(svg_text)}
</svg>'''
(ASSETS / 'cover.svg').write_text(svg, encoding='utf-8')
image.save(ASSETS / 'cover.jpg', quality=95, subsampling=0, optimize=True)
(ROOT / '.release-cache').mkdir(exist_ok=True)
image.resize((320, 480), Image.Resampling.LANCZOS).save(ROOT / '.release-cache' / 'cover-thumbnail.jpg', quality=95)
print('Cover: 1600 x 2400 px; painted artwork with editable SVG typography and JPEG generated.')
