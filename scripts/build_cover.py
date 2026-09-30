"""Compose the cover from a historical photo; retain editable SVG typography."""
from pathlib import Path
import base64
import html
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'cover'
ASSETS.mkdir(parents=True, exist_ok=True)
(ROOT / '.release-cache').mkdir(exist_ok=True)
PHOTO = ASSETS / 'schopenhauer-schaefer-1859.jpg'
PAGE = 'https://commons.wikimedia.org/wiki/File:Arthur_Schopenhauer_by_J_Sch%C3%A4fer,_1859.jpg'
if not PHOTO.exists():
    req = urllib.request.Request(PAGE, headers={'User-Agent': 'SchopenhauerTranslation/1.0'})
    page = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')
    urls = re.findall(r'href="([^"]+)"', page)
    url = next(html.unescape(u) for u in urls if 'upload.wikimedia.org' in u and '/thumb/' not in u and u.endswith('.jpg'))
    request = urllib.request.Request(url, headers={'User-Agent': 'SchopenhauerTranslation/1.0'})
    PHOTO.write_bytes(urllib.request.urlopen(request, timeout=30).read())

# All coordinates are shared between the editable vector master and JPEG export.
texts = [
    (120, 130, 'ARTHUR SCHOPENHAUER', 40, False),
    (120, 260, 'The World', 122, True),
    (120, 395, 'as Will and', 122, True),
    (120, 530, 'Representation', 122, True),
    (120, 700, 'VOLUME I', 44, False),
    (120, 2200, 'English translation by', 38, False),
    (120, 2260, 'Ratanajaya', 62, True),
]
image = Image.new('RGB', (1600, 2400), 'white')
portrait = Image.open(PHOTO).convert('RGB')
image.paste(ImageOps.fit(portrait, (1360, 1280), centering=(0.5, 0.08)), (120, 850))
draw = ImageDraw.Draw(image)
svg_text = []
for x, y, text, size, bold in texts:
    font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf', size)
    if draw.textlength(text, font=font) > 1360:
        raise ValueError(f'Text exceeds cover width: {text}')
    draw.text((x, y), text, fill='#111111', font=font, anchor='lt')
    # Pillow's lt anchor is the ink top. SVG uses a baseline; font ascent maps it.
    bbox = font.getbbox(text)
    baseline = y + font.getmetrics()[0] - bbox[1]
    svg_text.append(f'<text x="{x}" y="{baseline}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="#111111">{html.escape(text)}</text>')

data = base64.b64encode(PHOTO.read_bytes()).decode('ascii')
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2400" viewBox="0 0 1600 2400">
<title>The World as Will and Representation, Volume I</title>
<rect width="1600" height="2400" fill="white"/>
<defs><clipPath id="portrait"><rect x="120" y="850" width="1360" height="1280"/></clipPath></defs>
<image x="120" y="{850 - (1360 / portrait.width * portrait.height - 1280) * .08}" width="1360" height="{1360 / portrait.width * portrait.height}" href="data:image/jpeg;base64,{data}" clip-path="url(#portrait)"/>
{chr(10).join(svg_text)}
</svg>'''
(ASSETS / 'cover.svg').write_text(svg, encoding='utf-8')
image.save(ASSETS / 'cover.jpg', quality=95, subsampling=0, optimize=True)
image.resize((320, 480), Image.Resampling.LANCZOS).save(ROOT / '.release-cache' / 'cover-thumbnail.jpg', quality=95)
print('Cover: 1600 x 2400 px; SVG master and JPEG generated.')
