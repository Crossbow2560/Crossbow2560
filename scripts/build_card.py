"""Build assets/profile.svg: ASCII portrait on the left, profile info on the right.

Run by the GitHub Actions workflow. Age and GitHub stats are computed at build
time, so they stay current whenever the workflow runs.
"""

import json
import os
import urllib.request
from datetime import date, datetime, timezone
from html import escape
from pathlib import Path

import ascii_portrait

# ---- Profile data (edit these) ---------------------------------------------
NAME = "NISHIT DB"
GITHUB_USER = "Crossbow2560"
DOB = date(2006, 7, 8)
OUTPUT_PATH = "assets/profile.svg"

# Sections of (label, value) rows. Age and the GitHub section are added
# automatically.
SYSTEM = [
    ("OS", "Omarchy (Arch Linux), Hyprland"),
    ("UNIVERSITY", "PES University, B.Tech CSE (sophomore)"),
    ("INTERESTS", "Hardware and software"),
]
STACK = [
    ("LANGUAGES", "TypeScript, Rust, Python"),
    ("FRAMEWORKS", "React, Next.js, Fastify, Express, Socket.IO"),
    ("TOOLS", "Docker, Prisma, Vite, Tailwind CSS"),
]
# (name, detail). Add or replace entries as projects are ready.
PROJECTS = [
    ("DBASE", "dbase.nishit-db.com"),
    ("CABO", "cabo.nishit-db.com"),
    ("NEXT", "coming soon"),
]

# Palette: near-black with one accent.
BG, ACCENT = "#0a0d14", "#5b9dff"
TEXT, DIM, LINE = "#d3dbe8", "#5d6b82", "#1c2433"

# Layout, in SVG units
PAD = 28
GAP = 24
INFO_WIDTH = 500
VALUE_X = 112  # x of the value column
LINE_H = 21
FONT_SIZE = 13
# ----------------------------------------------------------------------------


def age_ymd(dob: date, today: date) -> tuple[int, int, int]:
    years = today.year - dob.year
    months = today.month - dob.month
    days = today.day - dob.day
    if days < 0:
        months -= 1
        prev_month_end = today.replace(day=1).toordinal() - 1
        days += date.fromordinal(prev_month_end).day
    if months < 0:
        years -= 1
        months += 12
    return years, months, days


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def github_stats(user: str) -> dict[str, str]:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-card"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def get(url: str):
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:
            return json.load(r)

    try:
        profile = get(f"https://api.github.com/users/{user}")
        repos = get(f"https://api.github.com/users/{user}/repos?per_page=100&type=owner")
        stars = sum(r["stargazers_count"] for r in repos if not r["fork"])
        return {
            "REPOS": str(profile["public_repos"]),
            "FOLLOWERS": str(profile["followers"]),
            "STARS": str(stars),
        }
    except Exception as exc:  # the card should still build if the API is down
        print(f"GitHub stats unavailable: {exc}")
        return {"REPOS": "n/a", "FOLLOWERS": "n/a", "STARS": "n/a"}


def row(y: float, key: str, value: str, value_fill: str = TEXT) -> str:
    return (
        f'<text x="0" y="{y:g}" fill="{ACCENT}" font-weight="700">{escape(key)}</text>'
        f'<text x="{VALUE_X}" y="{y:g}" fill="{value_fill}">{escape(value)}</text>'
    )


def heading(y: float, title: str) -> str:
    return (
        f'<text x="0" y="{y:g}" fill="{DIM}" letter-spacing="1.5">[ {escape(title)} ]</text>'
        f'<rect x="0" y="{y + 8:g}" width="{INFO_WIDTH}" height="1" fill="{LINE}"/>'
        f'<rect x="0" y="{y + 8:g}" width="28" height="1" fill="{ACCENT}"/>'
    )


def build() -> str:
    today = datetime.now(timezone.utc).date()
    years, months, days = age_ymd(DOB, today)
    age = f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"
    stats = github_stats(GITHUB_USER)

    art, art_w, art_h = ascii_portrait.portrait_fragment()

    lines: list[str] = []
    y = 24
    lines.append(f'<text x="0" y="{y}" fill="#e8f1ef" font-size="24" font-weight="800" '
                 f'letter-spacing="2">{escape(NAME)}<tspan fill="{ACCENT}" class="cursor">_</tspan></text>')
    y += LINE_H * 1.4

    lines.append(heading(y, "SYSTEM"))
    y += LINE_H * 1.2
    lines.append(row(y, "AGE", age, ACCENT))
    for key, value in SYSTEM:
        y += LINE_H
        lines.append(row(y, key, value))

    y += LINE_H * 1.6
    lines.append(heading(y, "STACK"))
    y += LINE_H * 1.2
    for i, (key, value) in enumerate(STACK):
        if i:
            y += LINE_H
        lines.append(row(y, key, value))

    y += LINE_H * 1.6
    lines.append(heading(y, "PROJECTS"))
    y += LINE_H * 1.2
    for i, (key, value) in enumerate(PROJECTS):
        if i:
            y += LINE_H
        lines.append(row(y, key, value, DIM if key == "NEXT" else TEXT))

    y += LINE_H * 1.6
    lines.append(heading(y, "GITHUB"))
    y += LINE_H * 1.2
    lines.append(row(y, "STATS", "  |  ".join(f"{k} {v}" for k, v in stats.items())))
    y += LINE_H
    lines.append(row(y, "SYNC", f"{today.isoformat()} UTC", DIM))

    info_h = y + 10
    body_h = max(art_h, round(info_h)) + 24
    width = PAD + art_w + 24 + GAP + INFO_WIDTH + PAD
    height = body_h + 2 * PAD

    top = PAD
    art_panel_w = art_w + 24
    info_x = PAD + art_panel_w + GAP
    art_y = top + (body_h - art_h) / 2
    info_y = top + (body_h - info_h) / 2 + 6

    mono = 'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"'
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" '
        f'aria-label="{escape(NAME)} profile card">\n'
        "<defs>\n"
        '  <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        f'<path d="M24 0H0V24" fill="none" stroke="{LINE}" stroke-width="0.6"/></pattern>\n'
        '  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        '<rect width="4" height="1" fill="#fff" opacity="0.025"/></pattern>\n'
        "</defs>\n"
        "<style>.cursor{animation:blink 1.2s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}</style>\n"
        f'<rect width="{width}" height="{height}" fill="{BG}"/>\n'
        f'<rect width="{width}" height="{height}" fill="url(#grid)" opacity="0.5"/>\n'
        f'<rect width="{width}" height="{height}" fill="url(#scan)"/>\n'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="none" '
        f'stroke="{LINE}"/>\n'
        # portrait panel
        f'<rect x="{PAD}" y="{top}" width="{art_panel_w}" height="{body_h}" fill="#000" '
        f'fill-opacity="0.35" stroke="{LINE}"/>\n'
        f'<g transform="translate({PAD + 12} {art_y:g})" {mono} '
        f'font-size="{ascii_portrait.FONT_SIZE}">\n{art}\n</g>\n'
        # info panel
        f'<rect x="{info_x - 14}" y="{top}" width="{INFO_WIDTH + 28}" height="{body_h}" '
        f'fill="#000" fill-opacity="0.35" stroke="{LINE}"/>\n'
        f'<g transform="translate({info_x} {info_y:g})" {mono} font-size="{FONT_SIZE}">\n'
        + "\n".join(lines)
        + "\n</g>\n</svg>\n"
    )


if __name__ == "__main__":
    Path(OUTPUT_PATH).write_text(build(), encoding="utf-8")
