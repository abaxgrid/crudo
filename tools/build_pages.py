#!/usr/bin/env python3
"""Build the GitHub Pages version of CRUDO from the single-file claude.ai artifact.

Usage:  python3 tools/build_pages.py <artifact.html>

The artifact stays the source of truth. This script writes, next to it in the repo:
  index.html               the game, with the heavy embedded data moved out
  assets/scene.jpg         the start-screen image
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
m = once(r'const SCENE_IMG = "data:image/jpeg;base64,([A-Za-z0-9+/=]+)";', html)
with open(os.path.join(root, "assets", "scene.jpg"), "wb") as f:
    f.write(base64.b64decode(m.group(1)))
html = html[:m.start()] + 'const SCENE_IMG = "assets/scene.jpg";' + html[m.end():]

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

with open(os.path.join(root, "index.html"), "w", encoding="utf-8") as f:
    f.write(html)
print(f"index.html {len(html.encode())/1e6:.2f} MB, {len(sf)} instruments, {len(tracks)} tracks")
