#!/usr/bin/env python3
"""Build the GitHub Pages version of CRUDO from the single-file claude.ai artifact.

Usage:  python3 tools/build_pages.py <artifact.html>

The artifact stays the source of truth. This script writes, next to it in the repo:
  index.html               the game, with the heavy embedded data moved out
  assets/scene.*           the start-screen image
  assets/kit3.glb          the 3D models, fetched when the 3D view first opens
  assets/sf/<name>.json    instrument samples, fetched only when music plays
  assets/music/<name>.mid  the soundtrack, as plain download links

Every patch is checked: if the game's code changes shape, the build stops
instead of publishing a broken page.
"""
import base64, json, os, re, sys

src = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(src, encoding="utf-8").read()

def once(pattern, text, flags=0):
    m = list(re.finditer(pattern, text, flags))
    if len(m) != 1:
        sys.exit(f"build stopped: expected one match for {pattern[:60]!r}, found {len(m)}")
    return m[0]

def replace_once(old, new, text):
    if text.count(old) != 1:
        sys.exit(f"build stopped: expected one occurrence of {old[:60]!r}, found {text.count(old)}")
    return text.replace(old, new)

os.makedirs(os.path.join(root, "assets", "sf"), exist_ok=True)
os.makedirs(os.path.join(root, "assets", "music"), exist_ok=True)

# 1. Instrument samples: one JSON file per instrument, loaded on demand.
m = once(r'const MIDI_SF=(\{.*?\});(?=/\*MIDI-DATA-END\*/|\s*$)', html, re.M)
sf = json.loads(m.group(1))
for name, notes in sf.items():
    with open(os.path.join(root, "assets", "sf", f"{name}.json"), "w") as f:
        json.dump(notes, f, separators=(",", ":"))
html = html[:m.start()] + "const MIDI_SF={};" + html[m.end():]
html = replace_once(
    "const set = MIDI_SF[name] || {}, out = {};",
    'const set = MIDI_SF[name] || await fetch("assets/sf/"+name+".json").then(r=>r.ok?r.json():{}).catch(()=>({})), out = {};',
    html)

# 2. Start-screen image: a real file instead of base64.
m = once(r'const SCENE_IMG = "data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)";', html)
ext = {"jpeg": "jpg"}.get(m.group(1), m.group(1))
for old in os.listdir(os.path.join(root, "assets")):
    if old.startswith("scene."):
        os.remove(os.path.join(root, "assets", old))
with open(os.path.join(root, "assets", f"scene.{ext}"), "wb") as f:
    f.write(base64.b64decode(m.group(2)))
html = html[:m.start()] + f'const SCENE_IMG = "assets/scene.{ext}";' + html[m.end():]

# 2b. 3D model kit (GLB): a separate file, fetched alongside three.js when the 3D view first opens.
kit = os.path.join(root, "assets", "kit3.glb")
m = re.search(r'window\.KIT3_B64="([A-Za-z0-9+/=]+)";', html)
if m:
    with open(kit, "wb") as f:
        f.write(base64.b64decode(m.group(1)))
    html = html[:m.start()] + html[m.end():]   # the rest of that line (the 2D icons) stays
    html = replace_once(
        "const bin = Uint8Array.from(atob(b64), c=>c.charCodeAt(0)), dv",
        "const bin = b64 instanceof Uint8Array ? b64 : Uint8Array.from(atob(b64), c=>c.charCodeAt(0)), dv",
        html)
    html = replace_once(
        "  function load(){\n    if (window.THREE) return Promise.resolve();",
        '  let kitP = null;\n'
        '  function kitLoad(){ return kitP || (kitP = window.KIT3_B64 ? Promise.resolve() : fetch("assets/kit3.glb").then(r=>r.ok ? r.arrayBuffer() : null)'
        '.then(b=>{ if (b) window.KIT3_B64 = new Uint8Array(b); }).catch(()=>{})); }\n'
        '  function load(){ return Promise.all([load3(), kitLoad()]); }\n'
        '  function load3(){\n    if (window.THREE) return Promise.resolve();',
        html)
elif os.path.exists(kit):
    os.remove(kit)

# 3. Soundtrack: write the .mid files and let the Credits buttons link to them
#    when claude.ai's download feature isn't there.
m = once(r'const MIDI_FILES=(\{.*?\});', html)
tracks = json.loads(m.group(1))
names = dict(re.findall(r'\["(\w+)","([^"]+)"\]', once(r'const MTRK = \[(.*?)\];', html).group(1)))
for key, b64 in tracks.items():
    slug = re.sub(r"\s+", "-", names.get(key, key).lower())
    with open(os.path.join(root, "assets", "music", f"crudo-{slug}.mid"), "wb") as f:
        f.write(base64.b64decode(b64))
html = replace_once(
    'if (!SHARE.dl){ if (msg) msg.textContent = es ? "Las descargas solo están disponibles al jugar en claude.ai." : "Downloads are available when you play this on claude.ai."; return; }',
    'if (!SHARE.dl){ const a = document.createElement("a"); a.href = `assets/music/crudo-${mName(k).toLowerCase().replace(/\\s+/g,"-")}.mid`; a.download = ""; document.body.appendChild(a); a.click(); a.remove(); if (msg) msg.textContent = es ? `${mName(k)} descargado.` : `${mName(k)} downloaded.`; return; }',
    html)

# 4. Link preview (WhatsApp, Facebook, X, LinkedIn, iMessage): title, summary and assets/share-sim.jpg.
cfg = json.load(open(os.path.join(root, "tools", "site_config.json")))
# Custom domain (e.g. playcrudo.com): set "domain" only once its DNS points at GitHub,
# otherwise GitHub would redirect visitors to an address that doesn't answer yet.
DOMAIN = cfg.get("domain", "").strip()
SITE = f"https://{DOMAIN}/" if DOMAIN else "https://dannysimgames.github.io/crudo/"
cname = os.path.join(root, "CNAME")
if DOMAIN:
    open(cname, "w").write(DOMAIN + "\n")
elif os.path.exists(cname):
    os.remove(cname)
TITLE = "CRUDO: Venezuela Oil Value Chain Simulator"
DESC = ("A business simulation of Venezuela's oil sector: drill, upgrade, ship and sell Orinoco crude "
        "through fiscal terms, sanctions and investor scrutiny, over 36 quarters. Runs in the browser, in English and Spanish.")
meta = f"""<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="CRUDO">
<meta property="og:url" content="{SITE}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:image" content="{SITE}assets/share-sim.jpg">
<meta property="og:image:secure_url" content="{SITE}assets/share-sim.jpg">
<meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="CRUDO: an oil camp on the Orinoco, with an upgrader, tanks and a tanker terminal">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
<meta name="twitter:image" content="{SITE}assets/share-sim.jpg">
"""
if not os.path.exists(os.path.join(root, "assets", "share-sim.jpg")):
    sys.exit("build stopped: assets/share-sim.jpg is missing (run tools/make_share_image.py)")
html = replace_once("<head><meta charset=utf8>", "<head><meta charset=utf8>" + meta, html)   # charset stays first

# 5. Leads and statistics (tools/site_config.json): only what is configured is added.
extra = ""
if cfg.get("goatcounter"):
    extra += f'<script data-goatcounter="https://{cfg["goatcounter"]}.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>\n'
if cfg.get("form_url"):
    js = open(os.path.join(root, "tools", "leads.js"), encoding="utf-8").read().replace("__FORM_URL__", cfg["form_url"])
    extra += "<script>" + js + "</script>\n"
if extra:
    i = html.rfind("</body>")
    html = (html[:i] + extra + html[i:]) if i >= 0 else html + extra

with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print(f"index.html {len(html.encode())/1e6:.2f} MB, {len(sf)} instruments, {len(tracks)} tracks")
