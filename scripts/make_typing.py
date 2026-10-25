#!/usr/bin/env python3
"""
Self-hosted banners  ->  assets/header.svg, typing.svg, about.svg and tech-stack.svg

Edit the text in the two settings blocks below, commit the change on github.com,
and the workflow regenerates both images automatically. No external service involved.
"""
import hashlib
import json
import math
import os
import re
import sys
import urllib.error
import urllib.request
import random
from html import escape

# ───────────────────────── 1. HEADER BANNER ─────────────────────────
GREETING = "I'm"
NAME = "MD ARSHAD RAZA"
TAGLINE = "AI and Data Science Student"

# ───────────────────────── 2. TYPING LINES ─────────────────────────
LINES = [
    "B.Tech CSE student, AI and Data Science",
    "C, C++, Python and MySQL",
    "Building projects and solving DSA problems",
    "Open to internships and collaboration",
]

# ───────────────────────── 3. ABOUT CARD (terminal window) ─────────────────────────
# Pick a preset: "tokyo-night", "github-dark", "dracula" or "monokai".
THEME = "tokyo-night"
# Override any single color you like, for example {"key": "#FF6AC1", "string": "#FFD866"}.
# Color names: bg, bar, border, title, key, string, punct, dash, text, prompt, dot1, dot2, dot3
CUSTOM_COLORS = {}

WINDOW_TITLE = "about.yml"
ABOUT = [                       # (key, value)   value can be text, a list, or ("inline", [..])
    ("name", "MD ARSHAD RAZA"),
    ("role", "B.Tech CSE (AI & Data Science)"),
    ("university", "SISTec Gandhi Nagar"),
    ("graduating", "2029"),
    ("location", "India"),
    ("", None),                 # blank line
    ("focused_on", [
        "Data Structures & Algorithms in C++",
        "Frontend fundamentals, then React",
        "Python for Machine Learning",
    ]),
    ("", None),
    ("building", "TIMMY"),
    ("open_to", ("inline", ["internships", "open source", "team projects"])),
    ("reach_me", "arshadraza.work@gmail.com"),
]

# ───────────────────────── 4. TECH STACK (scrolling logos) ─────────────────────────
TECH_TITLE = "Tech Stack"
TECH_STATUS = "actively learning"        # small green label, top right. Use "" to hide it
# Use icon names from https://devicon.dev (lowercase), e.g. "python", "docker", "typescript", "postgresql".
TECH_ROW1 = ["c", "cplusplus", "python", "javascript", "html5", "css3", "mysql"]
TECH_ROW2 = ["git", "github", "vscode", "react", "nodejs", "tailwindcss", "mongodb"]
TECH_LABELS = {                           # optional nicer display names (default: the icon name)
    "c": "C", "cplusplus": "C++", "javascript": "JavaScript", "html5": "HTML5", "css3": "CSS3",
    "mysql": "MySQL", "github": "GitHub", "vscode": "VS Code", "nodejs": "Node.js",
    "tailwindcss": "Tailwind", "mongodb": "MongoDB", "postgresql": "PostgreSQL", "typescript": "TypeScript",
}

# ───────────────────────── safety net ─────────────────────────
# If a setting above is accidentally deleted or has the wrong type while editing,
# the script prints a warning and uses these defaults, so one bad edit never breaks your profile.
_DEFAULTS = {
    "GREETING": "I'm",
    "NAME": "MD ARSHAD RAZA",
    "TAGLINE": "AI and Data Science Student",
    "CHIPS": [("India", "info"), ("B.Tech CSE · AI & Data Science", "info"), ("Open to internships", "status")],
    "LINES": ["B.Tech CSE student, AI and Data Science", "C, C++, Python and JavaScript",
              "Building projects and solving DSA problems", "Open to internships and collaboration"],
    "THEME": "tokyo-night",
    "CUSTOM_COLORS": {},
    "WINDOW_TITLE": "about.yml",
    "ABOUT": [("name", "MD ARSHAD RAZA"), ("role", "B.Tech CSE (AI & Data Science)"),
              ("university", "SISTec Gandhi Nagar"), ("graduating", "2029"), ("location", "India"),
              ("", None),
              ("focused_on", ["Data Structures & Algorithms in C++", "Frontend fundamentals, then React", "Python for Machine Learning"]),
              ("", None),
              ("building", "TIMMY"),
              ("open_to", ("inline", ["internships", "open source", "team projects"])),
              ("reach_me", "arshadraza.work@gmail.com ]")],
    "TECH_TITLE": "Tech Stack",
    "TECH_STATUS": "actively learning",
    "TECH_ROW1": ["c", "cplusplus", "python", "javascript", "html5", "css3", "mysql"],
    "TECH_ROW2": ["git", "github", "vscode", "react", "nodejs", "tailwindcss", "mongodb"],
    "TECH_LABELS": {"c": "C", "cplusplus": "C++", "javascript": "JavaScript", "html5": "HTML5", "css3": "CSS3",
                    "mysql": "MySQL", "github": "GitHub", "vscode": "VS Code", "nodejs": "Node.js",
                    "tailwindcss": "Tailwind", "mongodb": "MongoDB"},
}
for _name, _default in _DEFAULTS.items():
    _value = globals().get(_name)
    if _value is None or not isinstance(_value, type(_default)):
        print(f"WARNING: setting {_name} is missing or has the wrong type. Using the default. "
              f"Check the settings at the top of scripts/make_typing.py.")
        globals()[_name] = _default

HEADER_OUT = os.environ.get("HEADER_OUT", "assets/header.svg")
TYPING_OUT = os.environ.get("TYPING_OUT", "assets/typing.svg")
ABOUT_OUT = os.environ.get("ABOUT_OUT", "assets/about.svg")
TECH_OUT = os.environ.get("TECH_OUT", "assets/tech-stack.svg")
FONT = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"


# ───────────────────────── header ─────────────────────────
def wave(W, H, amp, wl, y0, phase=0.0):
    total = wl * (math.ceil(W / wl) + 1)       # cover the width plus one scroll step
    pts = [f"{x},{y0 + amp * math.sin(2 * math.pi * x / wl + phase):.1f}" for x in range(0, total + 1, 8)]
    return f"M0,{H} L" + " L".join(pts) + f" L{total},{H} Z"


def wave_layer(W, H, amp, wl, y0, color, op, dur, phase=0.0):
    return (f'<g opacity="{op}"><animateTransform attributeName="transform" type="translate" '
            f'from="0,0" to="-{wl},0" dur="{dur}s" repeatCount="indefinite"/>'
            f'<path d="{wave(W, H, amp, wl, y0, phase)}" fill="{color}"/></g>')


def build_header():
    W, H = 1000, 260
    random.seed(7)
    stars = ""
    for _ in range(44):
        x, y = random.uniform(10, W - 10), random.uniform(10, H - 90)
        r = random.choice([0.9, 1.1, 1.4, 1.8])
        op = round(random.uniform(0.25, 0.8), 2)
        dur, beg = round(random.uniform(2.2, 5.0), 2), round(random.uniform(0, 4), 2)
        stars += (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="#fff" opacity="{op}">'
                  f'<animate attributeName="opacity" values="{op};0.05;{op}" dur="{dur}s" '
                  f'begin="{beg}s" repeatCount="indefinite"/></circle>')

    # chips, centred as a row
    PH, GAP = 28, 10
    widths = [int(len(t) * 6.9 + 42) for t, _ in CHIPS]
    x = (W - (sum(widths) + GAP * (len(CHIPS) - 1))) / 2
    chips = ""
    for (text, style), w in zip(CHIPS, widths):
        if style == "status":
            fill, stroke, color, dot = "#3FB950", "#3FB950", "#3FB950", "#3FB950"
            body = f'<rect width="{w}" height="{PH}" rx="14" fill="{fill}" fill-opacity="0.14" stroke="{stroke}" stroke-opacity="0.6"/>'
            pulse = '<animate attributeName="opacity" values="1;0.25;1" dur="2s" repeatCount="indefinite"/>'
        else:
            color, dot = "#C9D1D9", "#58A6FF"
            body = f'<rect width="{w}" height="{PH}" rx="14" fill="#FFFFFF" fill-opacity="0.06" stroke="#FFFFFF" stroke-opacity="0.18"/>'
            pulse = ""
        chips += (f'<g transform="translate({x:.1f},180)">{body}'
                  f'<circle cx="16" cy="{PH/2}" r="3.5" fill="{dot}">{pulse}</circle>'
                  f'<text x="28" y="18.5" font-family="{FONT}" font-size="12.5" font-weight="600" fill="{color}">{escape(text)}</text></g>')
        x += w + GAP

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(NAME)}. {escape(TAGLINE)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0D1117"/><stop offset="0.5" stop-color="#132244"/><stop offset="1" stop-color="#241943"/>
    </linearGradient>
    <linearGradient id="nameGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#58A6FF"/><stop offset="0.5" stop-color="#A5D6FF"/><stop offset="1" stop-color="#BC8CFF"/>
      <animateTransform attributeName="gradientTransform" type="translate" values="-0.35 0; 0.35 0; -0.35 0" dur="8s" repeatCount="indefinite"/>
    </linearGradient>
    <filter id="glow" x="-30%" y="-40%" width="160%" height="180%">
      <feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <circle cx="150" cy="80" r="115" fill="#58A6FF" opacity="0.07"><animate attributeName="r" values="115;136;115" dur="9s" repeatCount="indefinite"/></circle>
  <circle cx="880" cy="190" r="135" fill="#BC8CFF" opacity="0.07"><animate attributeName="r" values="135;155;135" dur="11s" repeatCount="indefinite"/></circle>
  {stars}

  {wave_layer(W, H, 10, 320, H-34, "#58A6FF", 0.20, 9)}
  {wave_layer(W, H, 13, 260, H-22, "#BC8CFF", 0.22, 13, 1.1)}
  {wave_layer(W, H, 8, 200, H-12, "#58A6FF", 0.30, 7, 2.3)}

  <text x="{W/2}" y="72" text-anchor="middle" font-family="{FONT}" font-size="19" fill="#8B949E">{escape(GREETING)}
    <animate attributeName="opacity" from="0" to="1" dur="0.9s" fill="freeze"/></text>
  <text x="{W/2}" y="128" text-anchor="middle" font-family="{FONT}" font-size="58" font-weight="800" fill="url(#nameGrad)" filter="url(#glow)">{escape(NAME)}
    <animate attributeName="opacity" from="0" to="1" dur="1.1s" begin="0.2s" fill="freeze"/></text>
  <text x="{W/2}" y="158" text-anchor="middle" font-family="{FONT}" font-size="19" font-weight="500" fill="#E6EDF3">{escape(TAGLINE)}
    <animate attributeName="opacity" from="0" to="1" dur="1s" begin="0.5s" fill="freeze"/></text>
  {chips}
</svg>
"""


# ───────────────────────── typing ─────────────────────────
TW, TH, FS = 880, 52, 20
CW = FS * 0.6
TYPE_S, HOLD_S, GAP_S = 1.6, 1.7, 0.3
MONO = "'Fira Code','DejaVu Sans Mono','Courier New',monospace"
COLOR = "#58A6FF"


def build_typing():
    P = TYPE_S + HOLD_S + GAP_S
    T = P * len(LINES)
    defs, texts, cursor = "", "", []
    for i, line in enumerate(LINES):
        n = len(line)
        full = n * CW
        x0 = (TW - full) / 2
        s, ty = i * P / T, TYPE_S / T
        e = (i * P + TYPE_S + HOLD_S) / T
        pairs = [(0.0, 0.0)]
        if s > 0:
            pairs.append((s, 0.0))
        pairs += [(s + ty * k / n, k * CW) for k in range(1, n + 1)]
        pairs.append((e, 0.0))
        if e < 1:
            pairs.append((1.0, 0.0))
        kt = ";".join(f"{t:.5f}" for t, _ in pairs)
        vals = ";".join(f"{v:.1f}" for _, v in pairs)
        base_w = full if i == 0 else 0      # no-animation fallback shows line 1 only
        defs += (f'<clipPath id="c{i}"><rect x="{x0:.1f}" y="6" width="{base_w:.1f}" height="40">'
                 f'<animate attributeName="width" dur="{T:.2f}s" repeatCount="indefinite" '
                 f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        texts += (f'<text x="{x0:.1f}" y="33" font-family="{MONO}" font-size="{FS}" font-weight="600" '
                  f'fill="{COLOR}" clip-path="url(#c{i})" xml:space="preserve">{escape(line)}</text>')
        cursor += [(s + ty * k / n, x0 + k * CW) for k in range(0, n + 1)]
    cursor.append((1.0, cursor[-1][1]))
    ckt = ";".join(f"{t:.5f}" for t, _ in cursor)
    cvals = ";".join(f"{x:.1f}" for _, x in cursor)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{TW}" height="{TH}" viewBox="0 0 {TW} {TH}" role="img" aria-label="{escape(' | '.join(LINES))}">
  <defs>{defs}</defs>
  {texts}
  <rect x="{cursor[0][1]:.1f}" y="12" width="2.5" height="28" rx="1" fill="{COLOR}">
    <animate attributeName="x" dur="{T:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{ckt}" values="{cvals}"/>
    <animate attributeName="opacity" dur="1s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.5" values="1;0"/>
  </rect>
</svg>
"""


# ───────────────────────── about card ─────────────────────────
THEMES = {
    "tokyo-night": dict(bg="#1a1b26", bar="#16161e", border="#292e42", title="#565f89", key="#7aa2f7",
                        string="#9ece6a", punct="#565f89", dash="#ff9e64", text="#c0caf5", prompt="#9ece6a",
                        dot1="#f7768e", dot2="#e0af68", dot3="#9ece6a"),
    "github-dark": dict(bg="#0D1117", bar="#161B22", border="#30363D", title="#8B949E", key="#79C0FF",
                        string="#A5D6FF", punct="#8B949E", dash="#FF7B72", text="#C9D1D9", prompt="#3FB950",
                        dot1="#FF5F56", dot2="#FFBD2E", dot3="#27C93F"),
    "dracula": dict(bg="#282a36", bar="#21222c", border="#44475a", title="#6272a4", key="#bd93f9",
                    string="#f1fa8c", punct="#6272a4", dash="#ff79c6", text="#f8f8f2", prompt="#50fa7b",
                    dot1="#ff5555", dot2="#f1fa8c", dot3="#50fa7b"),
    "monokai": dict(bg="#272822", bar="#1e1f1c", border="#3e3d32", title="#75715e", key="#a6e22e",
                    string="#e6db74", punct="#75715e", dash="#f92672", text="#f8f8f2", prompt="#a6e22e",
                    dot1="#f92672", dot2="#e6db74", dot3="#a6e22e"),
}


def build_about():
    th = dict(THEMES.get(THEME, THEMES["tokyo-night"]))
    th.update(CUSTOM_COLORS)
    FS, LH = 14, 25
    CW = FS * 0.6
    PADX = 30

    def q(v):                                   # YAML-style quoting for odd-looking values
        return f'"{v}"' if v.startswith("[") or ": " in v else v

    scalar_keys = [k for k, v in ABOUT if k and not isinstance(v, list)]
    vcol = max(len(k) for k in scalar_keys) + 2

    rows = [[(0, "$ ", "prompt", True), (2, "cat " + WINDOW_TITLE, "text", False)]]
    for key, val in ABOUT:
        if not key:
            rows.append([])
        elif isinstance(val, str):
            rows.append([(0, key, "key", True), (len(key), ":", "punct", False), (vcol, q(val), "string", True)])
        elif isinstance(val, tuple):            # inline list
            row, col = [(0, key, "key", True), (len(key), ":", "punct", False), (vcol, "[", "punct", True)], vcol + 1
            for j, item in enumerate(val[1]):
                row.append((col, item, "string", False)); col += len(item)
                if j < len(val[1]) - 1:
                    row.append((col, ", ", "punct", False)); col += 2
            row.append((col, "]", "punct", False))
            rows.append(row)
        else:                                   # block list
            rows.append([(0, key, "key", True), (len(key), ":", "punct", False)])
            for item in val:
                rows.append([(2, "-", "dash", True), (4, item, "string", True)])
    rows.append([(0, "$ ", "prompt", True)])

    maxcol = max((c + len(t) for r in rows for c, t, *_ in r), default=20)
    W = max(560, int(PADX * 2 + maxcol * CW + 24))
    first_y = 44 + 36
    H = int(first_y + (len(rows) - 1) * LH + 30)

    body = ""
    for i, row in enumerate(rows):
        if not row:
            continue
        y = first_y + i * LH
        spans = "".join(
            f'<tspan {f"x=\"{PADX + c * CW:.1f}\" " if ab else ""}fill="{th[col]}">{escape(t)}</tspan>'
            for c, t, col, ab in row)
        body += (f'<text y="{y}" font-family="{MONO}" font-size="{FS}" xml:space="preserve">{spans}'
                 f'<animate attributeName="opacity" from="0" to="1" dur="0.4s" begin="{i*0.12:.2f}s" fill="freeze"/></text>')
    cy = first_y + (len(rows) - 1) * LH
    cursor = (f'<rect x="{PADX + 2 * CW + 2:.1f}" y="{cy - 14}" width="{CW:.1f}" height="18" fill="{th["text"]}" opacity="0.8">'
              f'<animate attributeName="opacity" values="0.8;0;0.8" dur="1.1s" repeatCount="indefinite"/></rect>')

    label = "; ".join(f"{k}: {v}" for k, v in ABOUT if k and isinstance(v, str))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(label)}">
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="14" fill="{th['bg']}" stroke="{th['border']}"/>
  <rect x="0.5" y="0.5" width="{W-1}" height="44" rx="14" fill="{th['bar']}"/>
  <rect x="0.5" y="30" width="{W-1}" height="14.5" fill="{th['bar']}"/>
  <line x1="0.5" y1="44.5" x2="{W-0.5}" y2="44.5" stroke="{th['border']}"/>
  <circle cx="26" cy="22" r="6" fill="{th['dot1']}"/><circle cx="46" cy="22" r="6" fill="{th['dot2']}"/><circle cx="66" cy="22" r="6" fill="{th['dot3']}"/>
  <text x="{W/2}" y="26.5" text-anchor="middle" font-family="{FONT}" font-size="12.5" fill="{th['title']}">{escape(WINDOW_TITLE)}</text>
  {body}
  {cursor}
</svg>
"""


# ───────────────────────── tech stack ─────────────────────────
DEVICON = "https://raw.githubusercontent.com/devicons/devicon/master/icons/{n}/{n}-{v}.svg"
VARIANTS = ("original", "plain", "original-wordmark", "plain-wordmark")
DARK_ICONS = {"github", "express", "flask", "nextjs", "markdown"}     # recolored so they show on a dark card
ITEM_W, CARD, ICON = 120, 84, 46


def _fetch_icon(name):
    """Return the icon's SVG text, None if devicon has no such name, or raise RuntimeError on network trouble."""
    for v in VARIANTS:
        try:
            with urllib.request.urlopen(DEVICON.format(n=name, v=v), timeout=20) as r:
                text = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise RuntimeError(f"HTTP {e.code} while fetching '{name}'")
        except Exception as e:
            raise RuntimeError(f"network problem while fetching '{name}': {e}")
        if "<svg" in text and "<style" not in text:
            return text
    return None


def _prepare_icon(name, raw):
    vb = re.search(r'viewBox="([^"]+)"', raw)
    vx, vy, vw, vh = [float(x) for x in vb.group(1).replace(",", " ").split()] if vb else (0.0, 0.0, 128.0, 128.0)
    inner = re.sub(r"^.*?<svg[^>]*>", "", raw, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner.strip(), flags=re.S)
    for i in sorted(set(re.findall(r'id="([^"]+)"', inner)), key=len, reverse=True):     # keep ids unique per icon
        new = f"{name}-{i}"
        inner = (inner.replace(f'id="{i}"', f'id="{new}"').replace(f"url(#{i})", f"url(#{new})")
                      .replace(f'href="#{i}"', f'href="#{new}"'))
    if name in DARK_ICONS:
        inner = re.sub(r'fill="#[0-9A-Fa-f]{3,6}"', 'fill="#E6EDF3"', inner)
        inner = f'<g fill="#E6EDF3">{inner}</g>'
    s = ICON / max(vw, vh)
    tx, ty = (ICON - vw * s) / 2, (ICON - vh * s) / 2
    return f'<g id="tech-{name}"><g transform="translate({tx:.2f},{ty:.2f}) scale({s:.5f}) translate({-vx},{-vy})">{inner}</g></g>'


def _tech_row(names, y, speed, direction, W):
    set_w = ITEM_W * len(names)
    copies = math.ceil(W / set_w) + 1
    items = ""
    for c in range(copies):
        for idx, n in enumerate(names):
            cx = c * set_w + idx * ITEM_W + ITEM_W / 2
            label = escape(TECH_LABELS.get(n, n[:1].upper() + n[1:]))
            items += f"""
    <g transform="translate({cx},0)"><g>
      <animateTransform attributeName="transform" type="translate" values="0,0; 0,-5; 0,0" dur="3.2s" begin="{idx*0.28:.2f}s" repeatCount="indefinite"/>
      <rect x="{-CARD/2}" y="0" width="{CARD}" height="{CARD}" rx="18" fill="#161B22" stroke="#30363D"/>
      <use href="#tech-{n}" xlink:href="#tech-{n}" x="{-ICON/2}" y="{(CARD-ICON)/2 - 5}"/>
      <text x="0" y="{CARD-12}" text-anchor="middle" font-family="{FONT}" font-size="10" font-weight="600" fill="#8B949E">{label}</text>
    </g></g>"""
    start, end = (0, -set_w) if direction < 0 else (-set_w, 0)
    return (f'<g transform="translate(0,{y})" mask="url(#fade)"><g>'
            f'<animateTransform attributeName="transform" type="translate" from="{start},0" to="{end},0" dur="{set_w/speed:.1f}s" repeatCount="indefinite"/>'
            f'{items}</g></g>')


def _tech_hash():
    cfg = json.dumps([TECH_TITLE, TECH_STATUS, TECH_ROW1, TECH_ROW2, TECH_LABELS, "v2"], sort_keys=True)
    return hashlib.sha1(cfg.encode()).hexdigest()[:12]


def ensure_techstack():
    """Rebuild assets/tech-stack.svg only when the settings above changed (it downloads logos from devicon)."""
    h = _tech_hash()
    if os.path.exists(TECH_OUT) and f"techstack-config:{h}" in open(TECH_OUT, encoding="utf-8").read():
        print("tech stack unchanged, skipped")
        return
    names = list(dict.fromkeys(TECH_ROW1 + TECH_ROW2))
    icons = {}
    try:
        for n in names:
            raw = _fetch_icon(n)
            if raw is None:
                print(f"WARNING: devicon has no icon named '{n}', skipping it (see https://devicon.dev)")
                continue
            icons[n] = _prepare_icon(n, raw)
    except RuntimeError as e:
        print("WARNING: tech stack not updated this run:", e)
        return
    row1 = [n for n in TECH_ROW1 if n in icons]
    row2 = [n for n in TECH_ROW2 if n in icons]
    W, H = 880, 260
    rows = ""
    if row1:
        rows += _tech_row(row1, 72, 32, -1, W)
    if row2:
        rows += _tech_row(row2, 168, 28, +1, W)
    status = ""
    if TECH_STATUS:
        status = (f'<circle cx="{W-38}" cy="33" r="4" fill="#3FB950"><animate attributeName="opacity" values="1;0.25;1" dur="2s" repeatCount="indefinite"/></circle>'
                  f'<text x="{W-50}" y="37" text-anchor="end" font-family="{FONT}" font-size="11" fill="#8B949E">{escape(TECH_STATUS)}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(TECH_TITLE)}: {escape(', '.join(row1 + row2))}">
  <!-- techstack-config:{h} -->
  <defs>
    {''.join(icons.values())}
    <linearGradient id="fadeGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#000"/><stop offset="0.06" stop-color="#fff"/><stop offset="0.94" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient>
    <mask id="fade"><rect x="0" y="0" width="{W}" height="{H}" fill="url(#fadeGrad)"/></mask>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#58A6FF"/><stop offset="1" stop-color="#BC8CFF"/></linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="#0D1117" stroke="#21262D"/>
  <text x="28" y="38" font-family="{FONT}" font-size="15" font-weight="700" fill="#E6EDF3">{escape(TECH_TITLE)}</text>
  <rect x="28" y="48" width="46" height="3" rx="1.5" fill="url(#accent)"/>
  {status}
  {rows}
</svg>
"""
    os.makedirs(os.path.dirname(TECH_OUT) or ".", exist_ok=True)
    with open(TECH_OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {TECH_OUT} ({len(icons)} logos)")


if __name__ == "__main__":
    failures = 0
    for label, path, build in (("header", HEADER_OUT, build_header),
                               ("typing animation", TYPING_OUT, build_typing),
                               ("about card", ABOUT_OUT, build_about)):
        try:
            svg = build()
        except Exception as e:      # one broken setting must not stop the other images
            failures += 1
            print(f"ERROR: could not build the {label}: {e!r}. Keeping the previous image. "
                  f"Check the settings at the top of scripts/make_typing.py.")
            continue
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote", path)
    try:
        ensure_techstack()
    except Exception as e:
        failures += 1
        print(f"ERROR: could not build the tech stack: {e!r}. Keeping the previous image.")
    sys.exit(1 if failures else 0)
