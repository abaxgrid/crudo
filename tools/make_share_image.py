#!/usr/bin/env python3
"""Make assets/share.jpg (1200x630), the preview image WhatsApp and other apps show for the play link."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = lambda n, s: ImageFont.truetype(os.path.join(root, "tools", "fonts", n), s)
scene = next(os.path.join(root, "assets", f) for f in os.listdir(os.path.join(root, "assets")) if f.startswith("scene."))
W, H = 1200, 630
AMBER, FG, MUTED, BG = (232, 169, 59), (239, 231, 218), (190, 178, 160), (20, 17, 14)

img = Image.open(scene).convert("RGB")
s = max(W / img.width, H / img.height)
img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
x0 = (img.width - W) // 2
img = img.crop((x0, (img.height - H) // 2, x0 + W, (img.height - H) // 2 + H))

# dark fade from the left so the text reads over the camp
shade = Image.new("L", (W, H))
for x in range(W):
    a = max(0, min(235, int(235 * (1 - (x - 470) / 380)))) if x > 470 else 235
    ImageDraw.Draw(shade).line([(x, 0), (x, H)], fill=a)
img = Image.composite(Image.new("RGB", (W, H), BG), img, shade)

d = ImageDraw.Draw(img)
d.text((64, 70), "CRUDO", font=F("barlow-condensed-latin-700-normal.woff", 168), fill=AMBER)
d.text((70, 262), "Barrels of Venezuela", font=F("ibm-plex-sans-latin-600-normal.woff", 40), fill=FG)
body = F("ibm-plex-sans-latin-500-normal.woff", 26)
lines = ["Run an oil company, one quarter at a time.",
         "Drill, upgrade, ship and sell Orinoco crude",
         "past storms, sanctions and investors."]
for i, t in enumerate(lines):
    d.text((70, 336 + i * 40), t, font=body, fill=MUTED)
bf, label = F("ibm-plex-sans-latin-600-normal.woff", 24), "PLAY FREE IN YOUR BROWSER"
tw = d.textlength(label, font=bf)
d.rounded_rectangle((70, 494, 70 + tw + 52, 560), radius=10, fill=AMBER)
d.text((96, 509), label, font=bf, fill=BG)

out = os.path.join(root, "assets", "share.jpg")
img.save(out, "JPEG", quality=84, optimize=True, progressive=True)
print(out, os.path.getsize(out) // 1024, "KB")
