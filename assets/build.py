"""Builds the profile SVGs.

    pip install fonttools brotli
    python assets/build.py                  # hero and stack, into this folder
    python assets/build.py activity DIR     # the activity panel, into DIR

GitHub renders SVGs as images that cannot load anything, so everything is embedded: Plus Jakarta
Sans (SIL OFL, vendored in assets/fonts) and stack icons from skillicons.dev (downloaded once to
~/.cache). Edit the content below and re-run; don't hand-edit the SVGs (glyphs are subset per file).

Every panel has a wide version and a "-mobile" one drawn for a phone-width column. The README
picks between them with <picture media="(max-width: 700px)">.

The activity panel is not kept in this folder. .github/workflows/activity.yml builds it once a day
and publishes it to the "output" branch, so the main branch's history stays yours.
"""
import base64
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request
from functools import lru_cache
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).parent
CACHE = Path.home() / ".cache" / "parothegreat-fonts"
FONT = HERE / "fonts" / "PlusJakartaSans[wght].ttf"
WEIGHTS = (400, 600, 800)

THEMES = {
    "dark": dict(PANEL="#111B2E", RULE="#26385A", INK="#E9EFF8", MUTED="#A3B3CC", FAINT="#7586A3",
                 BLUE="#5AA2FF"),
    "light": dict(PANEL="#F2F6FC", RULE="#D2DDEE", INK="#0F1B2D", MUTED="#4A5B74", FAINT="#7A8AA3",
                  BLUE="#1660D9"),
}


# ---------------------------------------------------------------- helpers

def fetch(url, name):
    path = CACHE / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req, timeout=30).read())
    return path


def font_css(text):
    css = []
    for weight in WEIGHTS:
        # recalcTimestamp=False keeps the output byte-identical between runs, so CI only commits real changes
        font = instancer.instantiateVariableFont(TTFont(FONT, recalcTimestamp=False), {"wght": weight})
        opts = subset.Options()
        opts.flavor, opts.layout_features, opts.name_IDs, opts.hinting = "woff2", ["kern"], [1, 2], False
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:'Jakarta';font-weight:{weight};"
                   f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(css)


def svg(w, h, title, body, theme=None):
    if theme:
        for k, v in THEMES[theme].items():
            body = body.replace("$" + k, v)
    text = "".join(sorted(set("".join(re.findall(r">([^<>]+)</text>", body)))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">\n'
            f"<title>{escape(title)}</title>\n<style>{font_css(text)}"
            "text{font-family:'Jakarta','Plus Jakarta Sans','Segoe UI',-apple-system,Helvetica,Arial,sans-serif}"
            f"</style>\n{body}\n</svg>\n")


def t(x, y, s, size, weight=400, fill="$INK", anchor=None, extra=""):
    a = f' text-anchor="{anchor}"' if anchor else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}"{a}{extra}>{escape(s)}</text>'


def lines(x, y, rows, size, weight=400, fill="$INK", lh=1.4, **kw):
    return "".join(t(x, y + i * size * lh, row, size, weight, fill, **kw) for i, row in enumerate(rows))


_icon_n = 0


def skill_icon(name, theme, x, y, size=48):
    """Embed a skillicons.dev icon, with its ids made unique inside the parent SVG."""
    global _icon_n
    _icon_n += 1
    raw = fetch(f"https://skillicons.dev/icons?i={name}&theme={theme}", f"icons/{name}-{theme}.svg").read_text()
    assert "undefined" not in raw, f"skillicons has no icon named {name!r}"
    p = f"i{_icon_n}_"
    raw = re.sub(r'id="([^"]+)"', lambda m: f'id="{p}{m[1]}"', raw)
    raw = re.sub(r'url\(#([^)]+)\)', lambda m: f"url(#{p}{m[1]})", raw)
    raw = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}{m[1]}"', raw)
    return re.sub(r"<svg[^>]*>", f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 256 256">', raw, count=1)


# ---------------------------------------------------------------- hero (one file per width, works on both themes)

NAME = "Alvaro Prayogo"
MOTTO = "Infrastructure only becomes useful when it's understandable, observable, and defensible."


def hero_bg(w, h, circles):
    return ('<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
            '<stop stop-color="#0A2557"/><stop offset="1" stop-color="#1450B8"/></linearGradient>'
            f'<clipPath id="card"><rect width="{w}" height="{h}" rx="16"/></clipPath></defs>'
            f'<rect width="{w}" height="{h}" rx="16" fill="url(#bg)"/><g clip-path="url(#card)" fill="#FFFFFF">'
            + "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" opacity="{o}"/>' for cx, cy, r, o in circles) + "</g>")


def hero():
    return 1200, 264, "\n".join([
        hero_bg(1200, 264, [(1120, 30, 250, ".04"), (1160, 264, 160, ".05")]),
        t(64, 118, NAME, 64, 800, "#FFFFFF", extra=' letter-spacing="-1.5"'),
        '<rect x="66" y="152" width="44" height="3" rx="1.5" fill="#A9CBFF"/>',
        t(66, 202, MOTTO, 20, 400, "#FFFFFF", extra=' opacity=".9"'),
    ])


def hero_mobile():
    motto = wrap(MOTTO, 17, 400, 424)
    h = 158 + len(motto) * 24 + 16
    return 480, h, "\n".join([
        hero_bg(480, h, [(450, 10, 150, ".04"), (470, h, 100, ".05")]),
        t(27, 84, NAME, 47, 800, "#FFFFFF", extra=' letter-spacing="-1.1"'),
        '<rect x="28" y="112" width="36" height="3" rx="1.5" fill="#A9CBFF"/>',
        lines(28, 158, motto, 17, 400, "#FFFFFF", lh=24 / 17, extra=' opacity=".9"'),
    ])


# ---------------------------------------------------------------- text metrics

@lru_cache
def _metrics_font(weight):
    return instancer.instantiateVariableFont(TTFont(FONT), {"wght": weight})


def tw(s, size, weight):
    """Rendered width of s, so boxes are sized from the real font instead of guessed."""
    f = _metrics_font(weight)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in s) * size / f["head"].unitsPerEm


def wrap(s, size, weight, max_w):
    """Greedy line breaks measured with the real font."""
    rows, row = [], ""
    for word in s.split():
        trial = f"{row} {word}".strip()
        if row and tw(trial, size, weight) > max_w:
            rows.append(row)
            row = word
        else:
            row = trial
    return rows + [row]


# ---------------------------------------------------------------- stack

STACK = [  # label, skillicons ids, extra text
    ("Languages", ["go", "ts", "python", "rust", "bash"], ""),
    ("Web and data", ["nextjs", "react", "postgres", "mysql", "redis", "supabase"], "Gin"),
    ("Infrastructure", ["linux", "ubuntu", "docker", "nginx", "cloudflare", "git"], "Fedora, Podman, Caddy"),
    ("Observability", ["prometheus", "grafana"], "Node Exporter"),
    ("Networking", [], "MikroTik, TP-Link Omada, Ruijie, Cisco IOS, VLANs, DHCP, DNS"),
    ("Hardware", ["raspberrypi", "arduino"], "ESP32, NXP MCX"),
]


def stack(theme):
    row_h, top = 72, 20
    h = top * 2 + row_h * len(STACK)
    out = [f'<rect width="1200" height="{h}" rx="16" fill="$PANEL"/>']
    for r, (label, icons, extra) in enumerate(STACK):
        y = top + r * row_h
        if r:
            out.append(f'<line x1="40" y1="{y}" x2="1160" y2="{y}" stroke="$RULE"/>')
        out.append(t(44, y + 42, label, 17, 800))
        x = 250
        for name in icons:
            out.append(skill_icon(name, theme, x, y + 12))
            x += 60
        if extra:
            out.append(t(x + (14 if icons else 0), y + 42, extra, 16, 400, "$MUTED"))
    return h, "\n".join(out)


def stack_mobile(theme):
    out, y = [], 12
    for r, (label, icons, extra) in enumerate(STACK):
        if r:
            out.append(f'<line x1="24" y1="{y}" x2="456" y2="{y}" stroke="$RULE"/>')
        out.append(t(28, y + 34, label, 16.5, 800))
        y += 50
        x = 28
        for name in icons:
            out.append(skill_icon(name, theme, x, y, 46))
            x += 56
        if extra:
            beside = icons and x + 6 + tw(extra, 15.5, 400) <= 452
            if icons and not beside:
                y += 46 + 10
            rows = [extra] if beside else wrap(extra, 15.5, 400, 424)
            out.append(lines(x + 6 if beside else 28, y + (29 if beside else 16), rows, 15.5, 400, "$MUTED", lh=23 / 15.5))
            y += 46 if beside else len(rows) * 23
        else:
            y += 46
        y += 18
    h = y + 6
    return 480, h, f'<rect width="480" height="{h}" rx="16" fill="$PANEL"/>' + "\n".join(out)


# ---------------------------------------------------------------- activity (built by .github/workflows/activity.yml)

def fetch_activity(path):
    """Last year's public contribution calendar, as the profile page shows it."""
    query = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
             "weeks{contributionDays{date contributionCount}}}}}}")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": os.environ["GITHUB_LOGIN"]}}).encode(),
        headers={"Authorization": "bearer " + os.environ["GITHUB_TOKEN"], "User-Agent": "profile-readme-build"})
    reply = json.load(urllib.request.urlopen(req, timeout=30))
    assert "errors" not in reply, reply["errors"]
    weeks = reply["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    rows = [json.dumps([[d["date"], d["contributionCount"]] for d in w["contributionDays"]]) for w in weeks]
    path.write_text('{"weeks": [\n' + ",\n".join(rows) + "\n]}\n")


def activity_stats(path):
    weeks = json.loads(path.read_text())["weeks"]
    days = [n for w in weeks for _, n in w]
    longest = run = 0
    for n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    return dict(weeks=[(dt.date.fromisoformat(w[0][0]), sum(n for _, n in w)) for w in weeks],
                total=sum(days), active=sum(1 for n in days if n), longest=longest)


def nice_ticks(top, n=3):
    """Round axis steps (1, 2 or 5 times a power of ten) that cover top in about n intervals."""
    raw, mag = max(top, 1) / n, 1
    while mag * 10 <= raw:
        mag *= 10
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)
    return [step * i for i in range(int(-(-max(top, 1) // step)) + 1)]


def columns(weeks, x0, x1, y0, y1, gap=3, max_bar=24):
    """Weekly columns: rounded data-end, square on the baseline, hairline grid, the peak labelled."""
    ticks = nice_ticks(max(n for _, n in weeks))
    scale = (y1 - y0) / ticks[-1]
    pitch = (x1 - x0) / len(weeks)
    bw = min(max_bar, pitch - gap)
    out = []
    for v in ticks:
        y = y1 - v * scale
        out.append(f'<line x1="{x0}" y1="{y:g}" x2="{x1}" y2="{y:g}" stroke="$RULE"/>')
        out.append(t(x0 - 10, y + 4, f"{v:,}", 12, 400, "$FAINT", "end"))
    peak = max(range(len(weeks)), key=lambda i: weeks[i][1])
    last_label = -1e9
    for i, (day, n) in enumerate(weeks):
        x = x0 + i * pitch + (pitch - bw) / 2
        if n:
            hgt, rad = max(n * scale, 2), min(4, bw / 2, max(n * scale, 2))
            out.append(f'<path d="M{x:.1f} {y1}v{-(hgt - rad):.1f}q0 {-rad:g} {rad:g} {-rad:g}h{bw - 2 * rad:.1f}q{rad:g} 0 {rad:g} {rad:g}v{hgt - rad:.1f}z" fill="$BLUE"/>')
        if i == peak and n and n < ticks[-1] - 12 / scale:
            out.append(t(x + bw / 2, y1 - n * scale - 7, f"{n:,}", 12, 600, "$MUTED", "middle"))
        first = day + dt.timedelta(days=6)                      # label a month at the week it starts in
        if i and first.month != (weeks[i - 1][0] + dt.timedelta(days=6)).month and x - last_label > 44 and x < x1 - 24:
            out.append(t(x, y1 + 21, first.strftime("%b"), 12, 400, "$FAINT"))
            last_label = x
    return "".join(out)


def activity(a):
    out = ['<rect width="1200" height="284" rx="16" fill="$PANEL"/>',
           t(42, 104, f"{a['total']:,}", 60, 800, extra=' letter-spacing="-1.5"'),
           t(44, 136, "contributions in the last 12 months, by week", 16, 400, "$MUTED"),
           t(44, 200, f"{a['active']:,}", 22, 800), t(44, 221, "active days", 13, 400, "$FAINT"),
           t(176, 200, f"{a['longest']:,} day{'s' * (a['longest'] != 1)}", 22, 800), t(176, 221, "longest streak", 13, 400, "$FAINT"),
           columns(a["weeks"], 468, 1156, 48, 226)]
    return 1200, 284, "\n".join(out)


def activity_mobile(a):
    out = ['<rect width="480" height="360" rx="16" fill="$PANEL"/>',
           t(27, 76, f"{a['total']:,}", 50, 800, extra=' letter-spacing="-1.2"'),
           t(28, 104, "contributions in the last 12 months, by week", 15.5, 400, "$MUTED"),
           t(28, 152, f"{a['active']:,}", 20, 800), t(28, 172, "active days", 13, 400, "$FAINT"),
           t(160, 152, f"{a['longest']:,} day{'s' * (a['longest'] != 1)}", 20, 800), t(160, 172, "longest streak", 13, 400, "$FAINT"),
           columns(a["weeks"], 62, 452, 210, 312, gap=2.4)]
    return 480, 360, "\n".join(out)


# ---------------------------------------------------------------- build

def write(folder, name, title, panel, theme=None):
    w, h, body = panel
    (folder / f"{name}{'-' + theme if theme else ''}.svg").write_text(svg(w, h, title, body, theme))


def build_activity(folder):
    """With GITHUB_TOKEN and GITHUB_LOGIN set, fetches fresh numbers; otherwise redraws DIR/activity.json."""
    folder.mkdir(parents=True, exist_ok=True)
    if os.environ.get("GITHUB_LOGIN"):
        fetch_activity(folder / "activity.json")
    a = activity_stats(folder / "activity.json")
    title = f"{a['total']:,} contributions in the last 12 months, drawn as weekly columns."
    for theme in THEMES:
        write(folder, "activity", title, activity(a), theme)
        write(folder, "activity-mobile", title, activity_mobile(a), theme)


if __name__ == "__main__":
    if sys.argv[1:2] == ["activity"]:
        build_activity(Path(sys.argv[2]))
        sys.exit()
    for old in HERE.glob("*.svg"):
        old.unlink()
    write(HERE, "hero", f"{NAME}. {MOTTO}", hero())
    write(HERE, "hero-mobile", f"{NAME}. {MOTTO}", hero_mobile())
    for theme in THEMES:
        h, body = stack(theme)
        write(HERE, "stack", "Stack", (1200, h, body), theme)
        write(HERE, "stack-mobile", "Stack", stack_mobile(theme), theme)
    print("built", len(list(HERE.glob("*.svg"))), "svgs")
