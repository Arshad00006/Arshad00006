#!/usr/bin/env python3
"""
Generates assets/activity-radar.svg — a self-hosted recreation of GitHub's
"Activity overview" radar chart.

Usage:
    GH_TOKEN=xxx USERNAME=Arshad00006 python3 scripts/generate_radar.py
    python3 scripts/generate_radar.py --demo        # offline preview, sample data

No third-party packages required (standard library only).
"""
import json
import os
import sys
import urllib.request
from html import escape

OUT = os.environ.get("OUT_PATH", "assets/activity-radar.svg")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      commitContributionsByRepository(maxRepositories: 100) {
        repository { nameWithOwner }
      }
    }
  }
}
"""


def fetch(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "activity-radar-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload or not payload.get("data", {}).get("user"):
        sys.exit(f"GitHub API error: {payload.get('errors') or 'user not found'}")
    c = payload["data"]["user"]["contributionsCollection"]
    return {
        "commits": c["totalCommitContributions"],
        "issues": c["totalIssueContributions"],
        "prs": c["totalPullRequestContributions"],
        "reviews": c["totalPullRequestReviewContributions"],
        "repos": len(c["commitContributionsByRepository"]),
    }


def pct_label(p):
    if p == 0:
        return "0%"
    if p < 1:
        return "<1%"
    return f"{round(p)}%"


def build(login, d):
    W, H = 880, 340
    cx, cy, R = 650, 178, 104

    total = d["commits"] + d["issues"] + d["prs"] + d["reviews"]
    pcts = {k: (d[k] / total * 100 if total else 0) for k in ("commits", "issues", "prs", "reviews")}
    top = max(pcts.values()) or 1

    def radius(p):
        if p <= 0:
            return R * 0.05
        return R * (0.10 + 0.90 * p / top)

    r_rev = radius(pcts["reviews"])
    r_iss = radius(pcts["issues"])
    r_prs = radius(pcts["prs"])
    r_com = radius(pcts["commits"])

    # polygon points relative to centre (top, right, bottom, left)
    pts = [(0, -r_rev), (r_iss, 0), (0, r_prs), (-r_com, 0)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.5" fill="#0D1117" stroke="#58A6FF" stroke-width="2"/>'
        for x, y in pts
    )

    grid = ""
    for f in (0.25, 0.5, 0.75, 1.0):
        r = R * f
        grid += (
            f'<polygon points="{cx},{cy-r} {cx+r},{cy} {cx},{cy+r} {cx-r},{cy}" '
            f'fill="none" stroke="#30363D" stroke-width="1" stroke-dasharray="{"0" if f == 1 else "3 4"}"/>'
        )

    font = "'Segoe UI',Ubuntu,Helvetica,Arial,sans-serif"

    def axis_label(x, y, anchor, key, name):
        return (
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{font}" '
            f'font-size="17" font-weight="700" fill="#E6EDF3">{pct_label(pcts[key])}</text>'
            f'<text x="{x}" y="{y+17}" text-anchor="{anchor}" font-family="{font}" '
            f'font-size="12" fill="#8B949E">{name}</text>'
        )

    labels = (
        axis_label(cx, cy - R - 42, "middle", "reviews", "Code review")
        + axis_label(cx + R + 18, cy - 4, "start", "issues", "Issues")
        + axis_label(cx, cy + R + 28, "middle", "prs", "Pull requests")
        + axis_label(cx - R - 18, cy - 4, "end", "commits", "Commits")
    )

    rows = [
        ("Commits", "commits", "#58A6FF"),
        ("Pull requests", "prs", "#BC8CFF"),
        ("Issues", "issues", "#3FB950"),
        ("Code reviews", "reviews", "#F78166"),
    ]
    bar_w = 330
    row_svg = ""
    for i, (name, key, color) in enumerate(rows):
        y = 128 + i * 50
        w = max(4, bar_w * pcts[key] / 100)
        delay = 0.2 + i * 0.15
        row_svg += f"""
    <circle cx="38" cy="{y-4}" r="4" fill="{color}"/>
    <text x="52" y="{y}" font-family="{font}" font-size="13" font-weight="600" fill="#C9D1D9">{name}</text>
    <text x="{32+bar_w}" y="{y}" text-anchor="end" font-family="{font}" font-size="13" fill="#8B949E">{d[key]:,}</text>
    <rect x="32" y="{y+10}" width="{bar_w}" height="6" rx="3" fill="#161B22"/>
    <rect x="32" y="{y+10}" width="{w:.1f}" height="6" rx="3" fill="{color}">
      <animate attributeName="width" from="0" to="{w:.1f}" dur="1s" begin="{delay}s"
               fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1"/>
    </rect>"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"
     role="img" aria-label="Activity overview for {escape(login)}">
  <defs>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#58A6FF"/><stop offset="1" stop-color="#BC8CFF"/>
    </linearGradient>
    <radialGradient id="polyFill" cx="0.5" cy="0.5" r="0.7">
      <stop offset="0" stop-color="#58A6FF" stop-opacity="0.55"/>
      <stop offset="1" stop-color="#BC8CFF" stop-opacity="0.18"/>
    </radialGradient>
  </defs>

  <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="20" fill="#0D1117" stroke="#21262D"/>

  <text x="32" y="46" font-family="{font}" font-size="18" font-weight="700" fill="#E6EDF3">Activity Overview</text>
  <rect x="32" y="56" width="46" height="3" rx="1.5" fill="url(#accent)"/>
  <text x="32" y="82" font-family="{font}" font-size="12" fill="#8B949E">@{escape(login)} · last 12 months · {d['repos']} repositories</text>
  {row_svg}

  <line x1="410" y1="32" x2="410" y2="{H-32}" stroke="#21262D"/>

  <g>{grid}</g>
  <line x1="{cx}" y1="{cy-R}" x2="{cx}" y2="{cy+R}" stroke="#3FB950" stroke-opacity="0.55" stroke-width="1.5"/>
  <line x1="{cx-R}" y1="{cy}" x2="{cx+R}" y2="{cy}" stroke="#3FB950" stroke-opacity="0.55" stroke-width="1.5"/>

  <g transform="translate({cx},{cy})">
    <g>
      <animateTransform attributeName="transform" type="scale" from="0" to="1" dur="1.1s"
        begin="0.1s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines="0.2 0.8 0.2 1"/>
      <polygon points="{poly}" fill="url(#polyFill)" stroke="#58A6FF" stroke-width="2" stroke-linejoin="round"/>
      {dots}
    </g>
  </g>

  {labels}
</svg>
"""


def main():
    login = os.environ.get("USERNAME", "Arshad00006")
    if "--demo" in sys.argv:
        data = {"commits": 1240, "issues": 73, "prs": 131, "reviews": 15, "repos": 42}
    else:
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GH_TOKEN (or GITHUB_TOKEN) or pass --demo")
        data = fetch(login, token)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(login, data))
    print(f"wrote {OUT}  ->  {data}")


if __name__ == "__main__":
    main()
