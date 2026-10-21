#!/usr/bin/env python3
"""
Generates three self-hosted profile cards from your real GitHub data:

    assets/trophies.svg          achievement trophies with Bronze → Diamond tiers
    assets/activity-graph.svg    smooth 31-day contribution line chart
    assets/projects/<repo>.svg   one card per pinned repo (falls back to recent repos)

It also rewrites the block between <!-- PROJECTS:START --> and <!-- PROJECTS:END -->
in README.md so each card links to its repository.

Usage:
    GH_TOKEN=xxx USERNAME=Arshad00006 python3 scripts/generate_cards.py
    python3 scripts/generate_cards.py --demo      # offline preview, sample data

Standard library only — no pip install needed.
"""
import datetime as dt
import json
import math
import os
import random
import re
import sys
import textwrap
import urllib.request
from html import escape

OUT_DIR = os.environ.get("OUT_DIR", "assets")
README = os.environ.get("README_PATH", "README.md")
FONT = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"

REPO_FIELDS = """
  name url description stargazerCount forkCount
  primaryLanguage { name color }
"""

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    issues { totalCount }
    pullRequests { totalCount }
    owned: repositories(first: 100, ownerAffiliation: OWNER, isFork: false) {
      totalCount
      nodes { stargazerCount }
    }
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { REPO_FIELDS } }
    }
    recent: repositories(first: 8, ownerAffiliation: OWNER, isFork: false,
                         orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes { REPO_FIELDS }
    }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
""".replace("REPO_FIELDS", REPO_FIELDS)


def esc(s):
    return escape(str(s), quote=True)


# ───────────────────────────── data ─────────────────────────────
def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-cards-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload or not payload.get("data", {}).get("user"):
        sys.exit(f"GitHub API error: {payload.get('errors') or 'user not found'}")

    u = payload["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = sorted(
        (d for w in cal["weeks"] for d in w["contributionDays"]), key=lambda d: d["date"]
    )
    created = dt.datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    years = (dt.datetime.now(dt.timezone.utc) - created).days // 365

    pins = [n for n in u["pinnedItems"]["nodes"] if n and n.get("name")]
    recent = [
        n for n in u["recent"]["nodes"]
        if n and n.get("name") and n["name"].lower() != login.lower()
    ][:6]

    return {
        "stars": sum(n["stargazerCount"] for n in u["owned"]["nodes"]),
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "followers": u["followers"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "repos": u["owned"]["totalCount"],
        "years": years,
        "days": [(d["date"], d["contributionCount"]) for d in days],
        "projects": pins or recent,
    }


def demo_data():
    random.seed(11)
    today = dt.date(2026, 10, 11)
    days = []
    for i in range(365):
        d = today - dt.timedelta(days=364 - i)
        days.append((d.isoformat(), random.choice([0, 0, 0, 1, 2, 3, 4, 6, 9])))
    return {
        "stars": 14, "commits": 312, "followers": 23, "prs": 9, "issues": 4,
        "repos": 18, "years": 2, "days": days,
        "projects": [
            {"name": "student-management-system", "url": "#",
             "description": "Console based student record manager with file handling and a MySQL backend for persistent storage.",
             "stargazerCount": 6, "forkCount": 2, "primaryLanguage": {"name": "C++", "color": "#f34b7d"}},
            {"name": "portfolio-website", "url": "#",
             "description": "Responsive personal portfolio built with plain HTML, CSS and JavaScript.",
             "stargazerCount": 3, "forkCount": 0, "primaryLanguage": {"name": "JavaScript", "color": "#f1e05a"}},
            {"name": "house-price-predictor", "url": "#",
             "description": "Linear regression model that predicts house prices from area, rooms and location.",
             "stargazerCount": 12, "forkCount": 4, "primaryLanguage": {"name": "Python", "color": "#3572A5"}},
            {"name": "dsa-practice", "url": "#", "description": None,
             "stargazerCount": 1, "forkCount": 0, "primaryLanguage": {"name": "C", "color": "#555555"}},
        ],
    }


# ───────────────────────────── trophies ─────────────────────────────
def ic_star(c):
    return f'<polygon points="12,2 14.9,8.6 22,9.3 16.6,14 18.2,21 12,17.3 5.8,21 7.4,14 2,9.3 9.1,8.6" fill="{c}"/>'

def ic_commit(c):
    return (f'<line x1="2" y1="12" x2="22" y2="12" stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
            f'<circle cx="12" cy="12" r="4.5" fill="#0D1117" stroke="{c}" stroke-width="2"/>')

def ic_user(c):
    return (f'<circle cx="12" cy="8" r="4" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"/>')

def ic_pr(c):
    return (f'<circle cx="6" cy="5" r="2.5" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<circle cx="6" cy="19" r="2.5" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<circle cx="18" cy="19" r="2.5" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<line x1="6" y1="7.5" x2="6" y2="16.5" stroke="{c}" stroke-width="2"/>'
            f'<path d="M18 16.5V10a3 3 0 0 0-3-3h-3" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"/>')

def ic_issue(c):
    return (f'<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<circle cx="12" cy="12" r="1.8" fill="{c}"/>')

def ic_repo(c):
    return (f'<rect x="5" y="3" width="14" height="18" rx="2" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<line x1="9" y1="8" x2="15" y2="8" stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
            f'<line x1="9" y1="12" x2="15" y2="12" stroke="{c}" stroke-width="2" stroke-linecap="round"/>')

def ic_clock(c):
    return (f'<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="2"/>'
            f'<path d="M12 7v5l3 2" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')


TROPHIES = [
    ("Stars", "stars", [1, 10, 50, 200], ic_star),
    ("Commits", "commits", [10, 100, 500, 1500], ic_commit),
    ("Followers", "followers", [1, 10, 50, 200], ic_user),
    ("Pull Requests", "prs", [1, 10, 50, 200], ic_pr),
    ("Issues", "issues", [1, 10, 50, 200], ic_issue),
    ("Repositories", "repos", [1, 5, 20, 50], ic_repo),
    ("Experience", "years", [1, 2, 4, 7], ic_clock),
]
TIERS = [("Bronze", "#CD7F32"), ("Silver", "#C0C8D4"), ("Gold", "#F2C94C"), ("Diamond", "#58D6FF")]
LOCKED = "#484F58"


def build_trophies(d):
    CW, CH, GAP, MX, TOP = 112, 172, 10, 18, 4
    W, H = 880, CH + TOP * 2
    cards = ""
    for i, (title, key, th, icon) in enumerate(TROPHIES):
        v = d[key]
        idx = sum(v >= t for t in th)          # 0 = locked, 4 = max
        name, color = ("Locked", LOCKED) if idx == 0 else TIERS[idx - 1]
        if idx == 0:
            frac = v / th[0]
        elif idx < 4:
            frac = (v - th[idx - 1]) / (th[idx] - th[idx - 1])
        else:
            frac = 1
        frac = max(0.0, min(1.0, frac))
        val = (f"{v} yr" if v == 1 else f"{v} yrs") if key == "years" else f"{v:,}"
        x = MX + i * (CW + GAP)
        cx = CW / 2
        icon_color = color if idx else "#6E7681"
        cards += f"""
  <g transform="translate({x},{TOP})">
    <animate attributeName="opacity" from="0" to="1" dur="0.6s" begin="{i*0.08:.2f}s" fill="freeze"/>
    <rect width="{CW}" height="{CH}" rx="14" fill="#161B22" stroke="{color}" stroke-opacity="{0.55 if idx else 0.35}"/>
    <circle cx="{cx}" cy="52" r="31" fill="{color}" fill-opacity="{0.13 if idx else 0.06}"/>
    <circle cx="{cx}" cy="52" r="31" fill="none" stroke="{color}" stroke-opacity="0.5" stroke-width="1.5"/>
    <g transform="translate({cx-14.4},{52-14.4}) scale(1.2)">{icon(icon_color)}</g>
    <text x="{cx}" y="106" text-anchor="middle" font-family="{FONT}" font-size="11" font-weight="600" fill="#8B949E">{esc(title)}</text>
    <text x="{cx}" y="128" text-anchor="middle" font-family="{FONT}" font-size="20" font-weight="800" fill="#E6EDF3">{esc(val)}</text>
    <rect x="16" y="138" width="{CW-32}" height="3" rx="1.5" fill="#21262D"/>
    <rect x="16" y="138" width="{(CW-32)*frac:.1f}" height="3" rx="1.5" fill="{color}"/>
    <rect x="{cx-30}" y="148" width="60" height="16" rx="8" fill="{color}" fill-opacity="0.15"/>
    <text x="{cx}" y="160" text-anchor="middle" font-family="{FONT}" font-size="10" font-weight="700" fill="{color}">{name.upper()}</text>
  </g>"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub trophies">{cards}
</svg>
"""


# ───────────────────────────── activity graph ─────────────────────────────
def nice_top(m):
    step = max(1, math.ceil(max(4, m) / 4))
    for n in (1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 250, 500, 1000):
        if n >= step:
            return n * 4
    return step * 4


def build_activity(d):
    W, H = 880, 320
    x0, x1, y0, y1 = 64, 840, 108, 262
    last = d["days"][-31:]
    dates = [dt.date.fromisoformat(a) for a, _ in last]
    vals = [b for _, b in last]
    n = len(vals)
    total, active = sum(vals), sum(1 for v in vals if v)
    top = nice_top(max(vals))

    def X(i):
        return x0 + i * (x1 - x0) / (n - 1)

    def Y(v):
        return y1 - (v / top) * (y1 - y0)

    pts = [(X(i), Y(v)) for i, v in enumerate(vals)]
    line = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        mx = (ax + bx) / 2
        line += f" C{mx:.1f},{ay:.1f} {mx:.1f},{by:.1f} {bx:.1f},{by:.1f}"
    area = f"{line} L{x1},{y1} L{x0},{y1} Z"

    grid = ""
    for k in range(5):
        v = top * k / 4
        y = Y(v)
        grid += (f'<line x1="{x0}" y1="{y:.1f}" x2="{x1}" y2="{y:.1f}" stroke="#21262D" '
                 f'stroke-dasharray="{"0" if k == 0 else "3 5"}"/>'
                 f'<text x="{x0-12}" y="{y+4:.1f}" text-anchor="end" font-family="{FONT}" font-size="11" fill="#6E7681">{int(v)}</text>')

    xlabels = ""
    for i in range(0, n, 5):
        xlabels += (f'<text x="{X(i):.1f}" y="{y1+24}" text-anchor="middle" font-family="{FONT}" '
                    f'font-size="11" fill="#6E7681">{dates[i]:%b} {dates[i].day}</text>')

    dots = "".join(
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="2.6" fill="#0D1117" stroke="#58A6FF" stroke-width="1.5"/>'
        for px, py in pts
    )

    peak_i = max(range(n), key=lambda i: vals[i])
    peak_note = ""
    if vals[peak_i] > 0:
        px, py = pts[peak_i]
        anchor = "end" if px > x1 - 60 else ("start" if px < x0 + 60 else "middle")
        peak_note = f"""
  <circle cx="{px:.1f}" cy="{py:.1f}" r="5.5" fill="#BC8CFF" stroke="#0D1117" stroke-width="2"/>
  <circle cx="{px:.1f}" cy="{py:.1f}" r="5.5" fill="none" stroke="#BC8CFF">
    <animate attributeName="r" values="5.5;13;5.5" dur="2.4s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.8;0;0.8" dur="2.4s" repeatCount="indefinite"/>
  </circle>
  <text x="{px:.1f}" y="{py-14:.1f}" text-anchor="{anchor}" font-family="{FONT}" font-size="12" font-weight="700" fill="#BC8CFF">{vals[peak_i]} on {dates[peak_i]:%b} {dates[peak_i].day}</text>"""

    empty = ""
    if total == 0:
        empty = (f'<text x="{(x0+x1)/2}" y="{(y0+y1)/2-10}" text-anchor="middle" font-family="{FONT}" '
                 f'font-size="14" fill="#8B949E">No contributions in the last 31 days — your first commit starts the line.</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Contribution activity, last 31 days">
  <defs>
    <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#58A6FF" stop-opacity="0.35"/>
      <stop offset="1" stop-color="#58A6FF" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#58A6FF"/><stop offset="1" stop-color="#BC8CFF"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#58A6FF"/><stop offset="1" stop-color="#BC8CFF"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="#0D1117" stroke="#21262D"/>

  <text x="32" y="46" font-family="{FONT}" font-size="18" font-weight="700" fill="#E6EDF3">Contribution Activity</text>
  <rect x="32" y="56" width="46" height="3" rx="1.5" fill="url(#accent)"/>
  <text x="32" y="84" font-family="{FONT}" font-size="12" fill="#8B949E">Last 31 days · {total:,} contributions · {active} active days</text>

  {grid}
  <path d="{area}" fill="url(#areaFill)">
    <animate attributeName="opacity" from="0" to="1" dur="1.4s" fill="freeze"/>
  </path>
  <path d="{line}" fill="none" stroke="url(#lineGrad)" stroke-width="2.5" stroke-linecap="round"
        stroke-linejoin="round" pathLength="1" stroke-dasharray="1">
    <animate attributeName="stroke-dashoffset" from="1" to="0" dur="1.6s" fill="freeze"/>
  </path>
  {dots}
  {peak_note}
  {xlabels}
  {empty}
</svg>
"""


# ───────────────────────────── project cards ─────────────────────────────
def project_card(r):
    W, H = 430, 140
    name = r["name"] if len(r["name"]) <= 30 else r["name"][:29] + "…"
    desc = (r.get("description") or "No description yet.").strip()
    lines = textwrap.wrap(desc, 56) or [""]
    if len(lines) > 2:
        lines = [lines[0], lines[1].rstrip()[:54] + "…"]
    desc_svg = "".join(
        f'<text x="24" y="{68 + i*19}" font-family="{FONT}" font-size="12.5" fill="#8B949E">{esc(l)}</text>'
        for i, l in enumerate(lines)
    )

    lang = r.get("primaryLanguage")
    fy = H - 20
    foot, x = "", 24
    if lang:
        foot += (f'<circle cx="{x+5}" cy="{fy-4}" r="5" fill="{esc(lang.get("color") or "#8B949E")}"/>'
                 f'<text x="{x+16}" y="{fy}" font-family="{FONT}" font-size="12" fill="#C9D1D9">{esc(lang["name"])}</text>')
        x += 16 + len(lang["name"]) * 7 + 22
    stars, forks = r.get("stargazerCount", 0), r.get("forkCount", 0)
    foot += (f'<g transform="translate({x},{fy-12}) scale(0.55)"><polygon points="12,2 14.9,8.6 22,9.3 16.6,14 18.2,21 12,17.3 5.8,21 7.4,14 2,9.3 9.1,8.6" fill="#8B949E"/></g>'
             f'<text x="{x+17}" y="{fy}" font-family="{FONT}" font-size="12" fill="#8B949E">{stars:,}</text>')
    x += 17 + len(str(stars)) * 7 + 18
    foot += (f'<g transform="translate({x},{fy-12}) scale(0.55)" fill="none" stroke="#8B949E" stroke-width="2.4" stroke-linecap="round">'
             f'<circle cx="6" cy="5" r="2.5"/><circle cx="18" cy="5" r="2.5"/><circle cx="12" cy="19" r="2.5"/>'
             f'<path d="M6 7.5v2a3 3 0 0 0 3 3h6a3 3 0 0 0 3-3v-2M12 12.5v4"/></g>'
             f'<text x="{x+17}" y="{fy}" font-family="{FONT}" font-size="12" fill="#8B949E">{forks:,}</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(r['name'])}">
  <defs><clipPath id="card"><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16"/></clipPath></defs>
  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="16" fill="#0D1117" stroke="#30363D"/>
  <rect x="0" y="0" width="4" height="{H}" fill="#58A6FF" clip-path="url(#card)"/>
  <g transform="translate(24,24) scale(0.78)">
    <rect x="5" y="3" width="14" height="18" rx="2" fill="none" stroke="#8B949E" stroke-width="2.2"/>
    <line x1="9" y1="8" x2="15" y2="8" stroke="#8B949E" stroke-width="2.2" stroke-linecap="round"/>
  </g>
  <text x="50" y="39" font-family="{FONT}" font-size="16" font-weight="700" fill="#58A6FF">{esc(name)}</text>
  {desc_svg}
  {foot}
</svg>
"""


def safe(name):
    return re.sub(r"[^A-Za-z0-9._-]", "-", name)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def update_readme(projects, login):
    if not os.path.exists(README):
        print(f"(skip) {README} not found")
        return
    if projects:
        cards = "\n".join(
            f'<a href="{esc(p["url"])}"><img width="49%" src="./assets/projects/{safe(p["name"])}.svg" alt="{esc(p["name"])}"/></a>'
            for p in projects
        )
        block = f'\n<div align="center">\n\n{cards}\n\n</div>\n'
    else:
        block = ("\n<div align=\"center\"><sub>📌 Create a repository (or pin one on your profile) "
                 "and it will appear here automatically.</sub></div>\n")
    text = open(README, encoding="utf-8").read()
    new, n = re.subn(
        r"(<!-- PROJECTS:START -->).*?(<!-- PROJECTS:END -->)",
        lambda m: f"{m.group(1)}{block}{m.group(2)}", text, flags=re.S,
    )
    if n == 0:
        print("WARNING: PROJECTS markers not found in README — project cards not linked")
        return
    if new != text:
        open(README, "w", encoding="utf-8").write(new)
    print("README project block updated")


def main():
    login = os.environ.get("USERNAME", "Arshad00006")
    demo = "--demo" in sys.argv
    if demo:
        data = demo_data()
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GH_TOKEN (or GITHUB_TOKEN) or pass --demo")
        data = fetch(login, token)

    write(os.path.join(OUT_DIR, "trophies.svg"), build_trophies(data))
    write(os.path.join(OUT_DIR, "activity-graph.svg"), build_activity(data))

    pdir = os.path.join(OUT_DIR, "projects")
    keep = set()
    for r in data["projects"]:
        fn = safe(r["name"]) + ".svg"
        keep.add(fn)
        write(os.path.join(pdir, fn), project_card(r))
    if os.path.isdir(pdir):
        for fn in os.listdir(pdir):
            if fn.endswith(".svg") and fn not in keep:
                os.remove(os.path.join(pdir, fn))

    if not demo:
        update_readme(data["projects"], login)

    print(f"wrote trophies, activity graph and {len(data['projects'])} project card(s) to {OUT_DIR}/")


if __name__ == "__main__":
    main()
