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
NAME = "Nishit DB"
GITHUB_USER = "Crossbow2560"
DOB = date(2006, 7, 8)
OUTPUT_PATH = "assets/profile.svg"

# (key, value) rows shown under the name. Age and GitHub rows are added
# automatically after these.
INFO = [
    ("OS", "Omarchy, Android, Windows"),
    ("University", "PES University, B.Tech CSE"),
    ("Interests", "Hardware and software"),
    ("Languages", "Python, Javascript, C"),
    ("Frameworks", "React, Next.js, Fastify, Express, Socket.IO"),
    ("Tools", "Docker, Prisma, Vite, Tailwind CSS"),
]

# (name, detail). Add or replace entries as projects are ready.
PROJECTS = [
    ("DBase", "dbase.nishit-db.com"),
    ("Cabo", "cabo.nishit-db.com"),
    ("More", "coming soon"),
]

# Layout, in SVG units
GAP = 36  # space between portrait and info
INFO_WIDTH = 520
LINE_H = 22
FONT_SIZE = 14
PAD = 12
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
            "Repos": str(profile["public_repos"]),
            "Followers": str(profile["followers"]),
            "Stars": str(stars),
        }
    except Exception as exc:  # the card should still build if the API is down
        print(f"GitHub stats unavailable: {exc}")
        return {"Repos": "n/a", "Followers": "n/a", "Stars": "n/a"}


def row(y: float, key: str, value: str) -> str:
    return (
        f'<text x="0" y="{y:g}"><tspan class="k">{escape(key)}</tspan>'
        f'<tspan class="d">: </tspan><tspan class="v">{escape(value)}</tspan></text>'
    )


def heading(y: float, title: str) -> str:
    return f'<text x="0" y="{y:g}" class="h">{escape(title)}</text>'


def build() -> str:
    today = datetime.now(timezone.utc).date()
    years, months, days = age_ymd(DOB, today)
    age = f"{plural(years, 'year')}, {plural(months, 'month')}, {plural(days, 'day')}"
    stats = github_stats(GITHUB_USER)

    art, art_w, art_h = ascii_portrait.portrait_fragment()

    lines: list[str] = []
    y = FONT_SIZE
    lines.append(f'<text x="0" y="{y}" class="name">{escape(NAME)}</text>')
    y += LINE_H * 0.6
    lines.append(f'<text x="0" y="{y:g}" class="d">{"-" * 34}</text>')
    y += LINE_H
    lines.append(row(y, "Age", age))
    for key, value in INFO:
        y += LINE_H
        lines.append(row(y, key, value))

    y += LINE_H * 1.6
    lines.append(heading(y, "Projects"))
    for name, detail in PROJECTS:
        y += LINE_H
        lines.append(row(y, name, detail))

    y += LINE_H * 1.6
    lines.append(heading(y, "GitHub"))
    gh = "  ".join(f"{k} {v}" for k, v in stats.items())
    y += LINE_H
    lines.append(row(y, "Stats", gh))
    y += LINE_H
    lines.append(row(y, "Updated", today.isoformat() + " (UTC)"))

    info_h = y + PAD
    height = max(art_h, round(info_h)) + 2 * PAD
    width = PAD + art_w + GAP + INFO_WIDTH + PAD
    info_y = PAD + max(0, (height - 2 * PAD - info_h) / 2)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img" '
        f'aria-label="{escape(NAME)} profile card">\n'
        "<style>\n"
        "  .k{fill:#0969da;font-weight:600} .v{fill:#1f2328} .d{fill:#6e7781}\n"
        "  .h{fill:#0969da;font-weight:700;text-decoration:underline}\n"
        "  .name{fill:#1f2328;font-weight:700;font-size:20px}\n"
        "  @media (prefers-color-scheme: dark){\n"
        "    .k,.h{fill:#58a6ff} .v,.name{fill:#e6edf3} .d{fill:#8b949e}\n"
        "  }\n"
        "</style>\n"
        f'<g transform="translate({PAD} {PAD})" font-family="ui-monospace, SFMono-Regular, '
        f'Menlo, Consolas, monospace" font-size="{ascii_portrait.FONT_SIZE}">\n{art}\n</g>\n'
        f'<g transform="translate({PAD + art_w + GAP} {info_y:g})" font-family="ui-monospace, '
        f'SFMono-Regular, Menlo, Consolas, monospace" font-size="{FONT_SIZE}">\n'
        + "\n".join(lines)
        + "\n</g>\n</svg>\n"
    )


if __name__ == "__main__":
    Path(OUTPUT_PATH).write_text(build(), encoding="utf-8")
