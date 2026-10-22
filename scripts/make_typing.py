#!/usr/bin/env python3
"""
Self-hosted typing animation  ->  assets/typing.svg

Edit the LINES below, commit the change on github.com, and the workflow
regenerates the animation automatically. No external service involved.
"""
import os
from html import escape

LINES = [
    "B.Tech CSE — AI & Data Science",
    "C | C++ | Python | JavaScript",
    "Building projects & grinding DSA",
    "Open to internships & collaboration",
]

OUT = os.environ.get("TYPING_OUT", "assets/typing.svg")
W, H = 880, 52
FS = 20
CW = FS * 0.6                 # monospace glyph width
TYPE_S, HOLD_S, GAP_S = 1.6, 1.7, 0.3
FONT = "'Fira Code','DejaVu Sans Mono','Courier New',monospace"
COLOR = "#58A6FF"


def build():
    P = TYPE_S + HOLD_S + GAP_S
    T = P * len(LINES)
    defs, texts, cursor = "", "", []

    for i, line in enumerate(LINES):
        n = len(line)
        full = n * CW
        x0 = (W - full) / 2
        s = i * P / T
        ty = TYPE_S / T
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

        # without animation support, only the first line stays visible
        base_w = full if i == 0 else 0
        defs += (f'<clipPath id="c{i}"><rect x="{x0:.1f}" y="6" width="{base_w:.1f}" height="40">'
                 f'<animate attributeName="width" dur="{T:.2f}s" repeatCount="indefinite" '
                 f'calcMode="discrete" keyTimes="{kt}" values="{vals}"/></rect></clipPath>')
        texts += (f'<text x="{x0:.1f}" y="33" font-family="{FONT}" font-size="{FS}" font-weight="600" '
                  f'fill="{COLOR}" clip-path="url(#c{i})" xml:space="preserve">{escape(line)}</text>')

        cursor += [(s + ty * k / n, x0 + k * CW) for k in range(0, n + 1)]

    cursor.append((1.0, cursor[-1][1]))
    ckt = ";".join(f"{t:.5f}" for t, _ in cursor)
    cvals = ";".join(f"{x:.1f}" for _, x in cursor)
    first_x = cursor[0][1]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(' | '.join(LINES))}">
  <defs>{defs}</defs>
  {texts}
  <rect x="{first_x:.1f}" y="12" width="2.5" height="28" rx="1" fill="{COLOR}">
    <animate attributeName="x" dur="{T:.2f}s" repeatCount="indefinite" calcMode="discrete" keyTimes="{ckt}" values="{cvals}"/>
    <animate attributeName="opacity" dur="1s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.5" values="1;0"/>
  </rect>
</svg>
"""


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"wrote {OUT} ({len(LINES)} lines)")
