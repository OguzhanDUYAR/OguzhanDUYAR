#!/usr/bin/env python3
"""Generate theme-aware, factual GitHub profile SVGs from public REST data.

Uses only the Python standard library. Any API failure preserves the last valid
assets (the GitHub Actions job stops without committing partial output).
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from html import escape
import json
import math
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

USER = "OguzhanDUYAR"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
API = "https://api.github.com"
COLORS = {
    "Python": "#3572A5", "R": "#198CE7", "Shell": "#89e051", "C++": "#f34b7d",
    "C": "#555555", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "HTML": "#e34c26", "CSS": "#663399", "Java": "#b07219", "Rust": "#dea584",
    "Go": "#00ADD8", "GDScript": "#355570", "Jupyter Notebook": "#DA5B0B",
    "PHP": "#4F5D95", "Lua": "#000080", "Kotlin": "#A97BFF", "Dockerfile": "#384d54",
    "Makefile": "#427819", "PowerShell": "#012456", "Swift": "#F05138", "Ruby": "#701516",
}
THEMES = {
    "dark": {"bg": "#090f1e", "card": "#111b2d", "border": "#2a3c56", "text": "#ecf4ff",
             "muted": "#9bb0cc", "accent": "#37d9cf", "secondary": "#90a3ff", "track": "#243148"},
    "light": {"bg": "#f7fbff", "card": "#ffffff", "border": "#cedbe9", "text": "#17283e",
              "muted": "#536981", "accent": "#007f8a", "secondary": "#5c4dcf", "track": "#e6edf5"},
}


def e(value: object) -> str:
    return escape(str(value), quote=True)


def api_get(path: str, token: str | None) -> object:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "oguzhanduyar-profile-dashboard",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(API + path, headers=headers)
    try:
        with urlopen(req, timeout=20) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"GitHub API request failed for {path}: {exc}") from exc


def fetch_public_data(token: str | None) -> dict:
    user = api_get(f"/users/{USER}", token)
    if not isinstance(user, dict) or "public_repos" not in user:
        raise ValueError("Unexpected user API response")
    repositories = []
    # Page until exhausted. Stop at 20 pages to avoid an infinite loop on bad responses.
    for page in range(1, 21):
        batch = api_get(f"/users/{USER}/repos?type=owner&per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise ValueError("Unexpected repositories API response")
        repositories.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise RuntimeError("Repository pagination hit safety limit")

    # The /users/{user}/repos endpoint returns public repositories; however,
    # defensively exclude private and repos not owned by the requested user.
    repositories = [r for r in repositories if
                    not r.get("private", False) and
                    r.get("owner", {}).get("login", "").lower() == USER.lower()]
    if len(repositories) != int(user["public_repos"]):
        raise RuntimeError("Incomplete repository enumeration; refusing to publish partial metrics")
    return {"user": user, "repositories": repositories}


def iso_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def summarize(data: dict, now: datetime) -> dict:
    user = data["user"]
    repos = data["repositories"]
    source = [r for r in repos if not r.get("fork") and r.get("name", "").lower() != USER.lower()]
    recent = sorted((r for r in source if r.get("pushed_at")),
                    key=lambda r: r["pushed_at"], reverse=True)
    cutoff = now.timestamp() - 90 * 24 * 3600
    active_90d = sum(bool(iso_time(r.get("pushed_at")) and iso_time(r["pushed_at"]).timestamp() >= cutoff)
                     for r in source)
    # Language counts are number of primary-language repositories, NOT skill level or lines of code.
    langs = Counter(str(r["language"]) for r in source if r.get("language"))
    return {
        "repos": len(repos), "source_repos": len(source),
        "followers": int(user.get("followers", 0)),
        "stars": sum(int(r.get("stargazers_count", 0)) for r in repos),
        "forks": sum(int(r.get("forks_count", 0)) for r in repos),
        "active_90d": active_90d,
        "languages": langs,
        "recent": recent[:5],
        "updated": now.strftime("%d %b %Y · %H:%M UTC"),
    }


def svg_start(width: int, height: int, title: str, description: str, theme: str) -> str:
    c = THEMES[theme]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
<title id="title">{e(title)}</title><desc id="desc">{e(description)}</desc>
<defs>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{c['accent']}"/><stop offset="1" stop-color="{c['secondary']}"/></linearGradient>
  <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="{c['border']}" stroke-opacity=".24" stroke-width="1"/></pattern>
</defs>
<rect width="{width}" height="{height}" rx="22" fill="{c['bg']}"/>
<rect width="{width}" height="{height}" rx="22" fill="url(#grid)"/>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="21" fill="none" stroke="{c['border']}"/>
<g font-family="Inter,Segoe UI,Arial,sans-serif">'''


def t(x: float, y: float, value: object, color: str, size: int = 18,
      weight: int = 500, anchor: str = "start", extra: str = "") -> str:
    return (f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}" {extra}>{e(value)}</text>')


def truncate(s: str, maxlen: int) -> str:
    return s if len(s) <= maxlen else s[:maxlen - 1].rstrip() + "…"


def telemetry(summary: dict | None, theme: str) -> str:
    c = THEMES[theme]
    w, h = 1160, 300
    parts = [svg_start(w, h, "Open-source telemetry", "Daily snapshot of public GitHub repositories", theme)]
    parts += [f'<rect x="28" y="29" width="6" height="33" rx="3" fill="url(#accent)"/>',
              t(50, 54, "OPEN-SOURCE TELEMETRY", c["text"], 25, 800),
              t(1130, 51, "PUBLIC DATA  /  UTC", c["muted"], 13, 700, "end")]
    metrics = [("PUBLIC REPOS", "repos", "All visible repositories"),
               ("STARS EARNED", "stars", "Across public repositories"),
               ("FOLLOWERS", "followers", "GitHub followers"),
               ("ACTIVE / 90D", "active_90d", "Pushed in last 90 days")]
    for i, (label, key, detail) in enumerate(metrics):
        x, y, cw, ch = 28 + i * 282, 93, 259, 146
        parts += [f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="16" fill="{c["card"]}" stroke="{c["border"]}"/>',
                  f'<rect x="{x+18}" y="{y+17}" width="23" height="3" rx="1.5" fill="url(#accent)"/>',
                  t(x+18, y+47, label, c["muted"], 13, 700),
                  t(x+18, y+105, f'{summary[key]:,}' if summary else "--", c["text"], 48, 800),
                  t(x+18, y+130, detail, c["muted"], 12)]
    caption = f'Last refresh: {summary["updated"]}  •  Forks included in total repositories and stars' if summary else 'Automatic figures appear after the first GitHub Actions run'
    parts += [t(29, 274, caption, c["muted"], 13), '</g></svg>']
    return ''.join(parts)


def language_svg(summary: dict | None, theme: str) -> str:
    c = THEMES[theme]
    w, h = 1160, 333
    parts = [svg_start(w, h, "Repository language landscape", "Primary language count across public, non-fork repositories", theme),
             f'<rect x="28" y="29" width="6" height="33" rx="3" fill="url(#accent)"/>',
             t(50, 54, "LANGUAGE LANDSCAPE", c["text"], 24, 800),
             t(1130, 52, "BY REPOSITORY  /  NOT CODE VOLUME", c["muted"], 12, 700, "end")]
    counts = summary["languages"].most_common(8) if summary else []
    count = sum(summary["languages"].values()) if summary else 0
    if not counts:
        parts += [t(580, 185, "Language data will appear after the first scheduled refresh", c["muted"], 19, 500, "middle")]
    else:
        # Two columns of four languages, horizontal bars scaled to the number of repos.
        peak = max(v for _, v in counts)
        for index, (language, num) in enumerate(counts):
            col, row = index // 4, index % 4
            x, y = 34 + col * 570, 95 + row * 53
            color = COLORS.get(language, c["secondary"])
            pct = 100 * num / count
            parts += [f'<circle cx="{x+8}" cy="{y-6}" r="6" fill="{color}"/>',
                      t(x+24, y, truncate(language, 22), c["text"], 17, 650),
                      t(x+508, y, f"{num}  /  {pct:.0f}%", c["muted"], 15, 600, "end"),
                      f'<rect x="{x+24}" y="{y+12}" width="480" height="9" rx="4.5" fill="{c["track"]}"/>',
                      f'<rect x="{x+24}" y="{y+12}" width="{max(7,480*num/peak):.1f}" height="9" rx="4.5" fill="{color}"/>']
    footer = (f'{count} repositories with a detected primary language · excludes forks and the profile repository'
              if summary else 'Data source: public GitHub REST API; no manual percentages')
    parts += [t(31, 313, footer, c["muted"], 12), '</g></svg>']
    return ''.join(parts)


def activity_svg(summary: dict | None, theme: str) -> str:
    c = THEMES[theme]
    w, h = 1160, 365
    parts = [svg_start(w, h, "Recently pushed repositories", "Most recently pushed public source repositories", theme),
             f'<rect x="28" y="29" width="6" height="33" rx="3" fill="url(#accent)"/>',
             t(50, 54, "RECENT REPOSITORY PULSE", c["text"], 24, 800),
             t(1130, 52, "LAST PUSH  /  UTC", c["muted"], 12, 700, "end")]
    recent = summary["recent"] if summary else []
    if not recent:
        parts += [t(580, 189, "The latest public repository updates will appear here", c["muted"], 19, 500, "middle")]
    else:
        for i, r in enumerate(recent):
            y = 85 + i * 49
            pushed = iso_time(r.get("pushed_at"))
            stamp = pushed.strftime("%d %b %Y") if pushed else "Unknown"
            desc = truncate(r.get("description") or "Public repository", 74)
            parts += [f'<rect x="28" y="{y}" width="1104" height="44" rx="10" fill="{c["card"]}" stroke="{c["border"]}"/>',
                      f'<circle cx="48" cy="{y+22}" r="5" fill="{c["accent"]}"/>',
                      t(65, y+20, truncate(r.get("name", "Repository"), 29), c["text"], 15, 700),
                      t(405, y+20, desc, c["muted"], 13),
                      t(1115, y+26, stamp, c["secondary"], 14, 600, "end")]
    parts += [t(31, 349, 'Source: GitHub repository pushed_at field · excludes forks and the profile repository', c["muted"], 12), '</g></svg>']
    return ''.join(parts)


def placeholder_card(title: str, theme: str, height: int = 210) -> str:
    c = THEMES[theme]
    return (svg_start(1160, height, title, "Awaiting first GitHub Actions refresh", theme) +
            t(580, 80, title, c['text'], 27, 800, 'middle') +
            t(580, 126, 'AUTOMATICALLY GENERATED ON FIRST WORKFLOW RUN', c['muted'], 18, 500, 'middle') +
            t(580, 163, 'Actions → Refresh profile visuals → Run workflow', c['secondary'], 16, 500, 'middle') +
            '</g></svg>')


def write_pair(name: str, render, summary: dict | None) -> None:
    for theme in THEMES:
        path = OUT / f"{name}-{theme}.svg"
        path.write_text(render(summary, theme), encoding="utf-8")
        print(f"Wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--placeholder", action="store_true", help="Write honest placeholders, without network")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.placeholder:
        summary = None
    else:
        now = datetime.now(timezone.utc)
        summary = summarize(fetch_public_data(os.environ.get("GH_TOKEN")), now)
    write_pair("telemetry", telemetry, summary)
    write_pair("languages", language_svg, summary)
    write_pair("activity", activity_svg, summary)
    if args.placeholder:
        for theme in THEMES:
            for label, name in [("GITHUB CONTRIBUTION STATS", "stats"), ("CONTRIBUTION SNAKE", "snake")]:
                (OUT / f"{name}-{theme}.svg").write_text(placeholder_card(label, theme), encoding="utf-8")


if __name__ == "__main__":
    main()
