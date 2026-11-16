"""Builds the profile SVGs.

    pip install fonttools brotli
    python assets/build.py                  # identity card and stack, into this folder
    python assets/build.py activity DIR     # the activity panel, into DIR

GitHub renders SVGs as images that cannot load anything, so the fonts are embedded: Plus Jakarta
Sans and JetBrains Mono (both SIL OFL, vendored in assets/fonts), subset to the glyphs each file
uses at each weight. The build needs no network and its output is byte-identical between runs.
Edit the content below and re-run; don't hand-edit the SVGs.

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
from html import escape, unescape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).parent
FONTS = {"sans": HERE / "fonts" / "PlusJakartaSans[wght].ttf", "mono": HERE / "fonts" / "JetBrainsMono[wght].ttf"}
STACKS = {"sans": "'Jakarta','Plus Jakarta Sans','Segoe UI',-apple-system,Helvetica,Arial,sans-serif",
          "mono": "'JBMono','JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"}

# GitHub's own surface, border and text colours, so the panels sit in the page instead of on it.
THEMES = {
    "dark": dict(SURFACE="#151B23", RULE="#30363D", GRID="#262C36", INK="#F0F6FC", MUTED="#9198A1", DATA="#37AD4B",
                 CHIP="#0D1117"),
    "light": dict(SURFACE="#F6F8FA", RULE="#D1D9E0", GRID="#E4E8EC", INK="#1F2328", MUTED="#59636E", DATA="#1A7F37",
                  CHIP="#FFFFFF"),
}
CARD = dict(SURFACE="#010409", RULE="#30363D", GRID="#FFFFFF", INK="#F0F6FC", MUTED="#9198A1", DATA="#3FB950")  # both themes


# ---------------------------------------------------------------- svg, text and fonts

@lru_cache
def instance(family, weight):
    return instancer.instantiateVariableFont(TTFont(FONTS[family]), {"wght": weight})


def font_face(family, weight, chars):
    # recalcTimestamp=False keeps the embedded font, and so the whole file, identical between runs
    font = instancer.instantiateVariableFont(TTFont(FONTS[family], recalcTimestamp=False), {"wght": weight})
    opts = subset.Options()
    opts.flavor, opts.layout_features, opts.name_IDs, opts.hinting = "woff2", ["kern"], [1, 2], False
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    name = STACKS[family].split(",")[0]
    return (f"@font-face{{font-family:{name};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{base64.b64encode(buf.getvalue()).decode()}) format('woff2')}}")


TEXT = re.compile(r'<text( class="m")?[^>]*? font-weight="(\d+)"[^>]*>([^<]*)</text>')


def svg(w, h, title, body, colors, css=""):
    for k, v in colors.items():
        body = body.replace("$" + k, v)
    used = {}                                   # (family, weight) -> the characters drawn with it
    for mono, weight, content in TEXT.findall(body):
        used.setdefault(("mono" if mono else "sans", int(weight)), set()).update(unescape(content))
    faces = "".join(font_face(family, weight, "".join(sorted(chars))) for (family, weight), chars in sorted(used.items()))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">\n'
            f"<title>{escape(title)}</title>\n<style>{faces}"
            f"text{{font-family:{STACKS['sans']}}}.m{{font-family:{STACKS['mono']}}}{css}</style>\n{body}\n</svg>\n")


def t(x, y, s, size, weight=400, fill="$INK", anchor=None, mono=False, ls=0):
    attrs = (' class="m"' if mono else "") + f' x="{x:g}" y="{y:g}" font-size="{size:g}" font-weight="{weight}" fill="{fill}"'
    attrs += (f' text-anchor="{anchor}"' if anchor else "") + (f' letter-spacing="{ls:g}"' if ls else "")
    return f"<text{attrs}>{escape(s)}</text>"


def label(x, y, s, anchor=None, size=12.5, fill="$MUTED"):
    """The small mono capitals that name things."""
    return t(x, y, s.upper(), size, 500, fill, anchor, mono=True, ls=round(size * .1, 2))


def tw(s, size, weight, mono=False, ls=0):
    """Rendered width of s, so layout comes from the real font instead of a guess."""
    f = instance("mono" if mono else "sans", weight)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in s) * size / f["head"].unitsPerEm + ls * len(s)


def panel(w, h, rx=12):
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{rx}" fill="$SURFACE" stroke="$RULE"/>'


# ---------------------------------------------------------------- identity card (one file per width, both themes)

NAME = "Alvaro Prayogo"
FIELD = "Infrastructure · Networking · Security"
SITE = "parothegreat.site"
MOTTO = [("Infrastructure only becomes useful when it's ", 0), ("understandable", 1), (", ", 0), ("observable", 1),
         (", and ", 0), ("defensible", 1), (".", 0)]          # 1 = the words that carry it
MOTTO_TEXT = "".join(s for s, _ in MOTTO)


def rich(x, y, segments, size, max_w, lh):
    """Mixed-emphasis text, wrapped by measuring each word. Returns the svg and the number of lines."""
    words, cur = [], []
    for text, strong in segments:
        for i, part in enumerate(text.split(" ")):
            if i and cur:
                words.append(cur)
                cur = []
            if part:
                cur.append((part, strong))
    words.append(cur)
    style = lambda strong: (600, "$INK") if strong else (400, "$MUTED")  # noqa: E731
    width = lambda word: sum(tw(p, size, style(s)[0]) for p, s in word)  # noqa: E731
    space, out, cx, row = tw(" ", size, 400), [], x, 0
    for word in words:
        if cx > x and cx + width(word) > x + max_w:
            cx, row = x, row + 1
        for piece, strong in word:
            out.append(t(round(cx, 1), y + row * lh, piece, size, *style(strong)))
            cx += tw(piece, size, style(strong)[0])
        cx += space
    return "".join(out), row + 1


def dots(w, h):
    """A faint measuring grid that fades in toward the far corner."""
    return ('<defs><pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
            '<circle cx="12" cy="12" r="1.1" fill="$GRID"/></pattern>'
            '<linearGradient id="fade" x1="0" y1="1" x2="1" y2="0"><stop offset=".35" stop-color="#FFFFFF" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#FFFFFF" stop-opacity=".34"/></linearGradient>'
            f'<mask id="m"><rect width="{w}" height="{h}" fill="url(#fade)"/></mask></defs>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="url(#dots)" mask="url(#m)"/>')


def card():
    motto, _ = rich(64, 264, MOTTO, 22, 1072, 32)
    return 1200, 324, "\n".join([
        panel(1200, 324, 16), dots(1200, 324),
        label(64, 64, FIELD), label(1136, 64, SITE, "end"),
        t(59, 184, NAME, 92, 800, ls=-3),
        '<rect x="64" y="212" width="48" height="3" rx="1.5" fill="$DATA"/>',
        motto,
    ])


def card_mobile():
    motto, rows = rich(28, 180, MOTTO, 17.5, 424, 26)
    h = 180 + (rows - 1) * 26 + 38
    return 480, h, "\n".join([
        panel(480, h, 16), dots(480, h),
        label(28, 48, FIELD, size=11.5),
        t(25, 112, NAME, 50, 800, ls=-1.5),
        '<rect x="28" y="134" width="40" height="3" rx="1.5" fill="$DATA"/>',
        motto,
    ])


# ---------------------------------------------------------------- stack

STACK = [
    ("Languages", ["Go", "TypeScript", "Python", "Rust", "Bash"]),
    ("Web & data", ["Next.js", "React", "PostgreSQL", "MySQL", "Redis", "Supabase", "Gin"]),
    ("Infrastructure", ["Linux", "Ubuntu", "Fedora", "Docker", "Podman", "Nginx", "Caddy", "Cloudflare", "Git"]),
    ("Observability", ["Prometheus", "Grafana", "Node Exporter"]),
    ("Networking", ["MikroTik", "TP-Link Omada", "Ruijie", "Cisco IOS", "VLANs", "DHCP", "DNS"]),
    ("Hardware", ["Raspberry Pi", "Arduino", "ESP32", "NXP MCX"]),
]
CHIP_H, CHIP_GAP = 30, 8


def chips(items, x0, x1, y):
    """Lays the items out as chips, wrapping at x1. Returns the svg and the y below the last row."""
    out, x = [], x0
    for item in items:
        w = round(tw(item, 13.5, 500, mono=True) + 24)
        if x > x0 and x + w > x1:
            x, y = x0, y + CHIP_H + CHIP_GAP
        out.append(f'<rect x="{x}.5" y="{y}.5" width="{w - 1}" height="{CHIP_H - 1}" rx="7" fill="$CHIP" stroke="$RULE"/>'
                   + t(x + 12, y + 20, item, 13.5, 500, mono=True))
        x += w + CHIP_GAP
    return "".join(out), y + CHIP_H


def stack():
    out, y = [], 26
    for i, (name, items) in enumerate(STACK):
        if i:
            out.append(f'<line x1="44" y1="{y}.5" x2="1156" y2="{y}.5" stroke="$GRID"/>')
            y += 17
        row, bottom = chips(items, 250, 1156, y)
        out += [label(44, y + 20, name), row]
        y = bottom + 16
    h = y + 10
    return 1200, h, panel(1200, h) + "\n".join(out)


def stack_mobile():
    out, y = [], 26
    for i, (name, items) in enumerate(STACK):
        if i:
            out.append(f'<line x1="28" y1="{y}.5" x2="452" y2="{y}.5" stroke="$GRID"/>')
            y += 22
        row, bottom = chips(items, 28, 452, y + 24)
        out += [label(28, y + 10, name, size=12), row]
        y = bottom + 20
    h = y + 6
    return 480, h, panel(480, h) + "\n".join(out)


# ---------------------------------------------------------------- activity (built by .github/workflows/activity.yml)

# Columns rise once when the image loads; people who ask for less motion get them in place.
GROW = (".b{transform-box:fill-box;transform-origin:50% 100%;animation:g .7s cubic-bezier(.2,.8,.2,1) both}"
        "@keyframes g{from{transform:scaleY(0)}}@media (prefers-reduced-motion:reduce){.b{animation:none}}")


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
    days = [(dt.date.fromisoformat(d), n) for w in weeks for d, n in w]
    longest = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    weekday = [0] * 7                                           # Monday first
    for day, n in days:
        weekday[day.weekday()] += n
    return dict(weeks=[(dt.date.fromisoformat(w[0][0]), sum(n for _, n in w)) for w in weeks], weekday=weekday,
                total=sum(n for _, n in days), active=sum(1 for _, n in days if n), longest=longest)


def nice_ticks(top, n=3):
    """Round axis steps (1, 2 or 5 times a power of ten) that cover top in about n intervals."""
    raw, mag = max(top, 1) / n, 1
    while mag * 10 <= raw:
        mag *= 10
    step = next(m * mag for m in (1, 2, 5, 10) if m * mag >= raw)
    return [step * i for i in range(int(-(-max(top, 1) // step)) + 1)]


def column(x, y1, w, h, order):
    """One column: rounded data-end, square on the baseline."""
    h = max(h, 2)
    r = min(4, w / 2, h)
    return (f'<path class="b" style="animation-delay:{order * 12}ms" d="M{x:.1f} {y1}v{-(h - r):.1f}q0 {-r:g} {r:g} {-r:g}'
            f'h{w - 2 * r:.1f}q{r:g} 0 {r:g} {r:g}v{h - r:.1f}z" fill="$DATA"/>')


def by_week(weeks, x0, x1, y0, y1, gap=3):
    """Weekly columns on a hairline grid, months along the bottom, the busiest week labelled."""
    ticks = nice_ticks(max(n for _, n in weeks))
    scale = (y1 - y0) / ticks[-1]
    pitch = (x1 - x0) / len(weeks)
    bw = min(24, pitch - gap)
    out = []
    for v in ticks:
        y = round(y1 - v * scale) + .5
        out.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="$GRID"/>')
        out.append(t(x0 - 10, y + 3.5, f"{v:,}", 11.5, 400, "$MUTED", "end", mono=True))
    peak = max(range(len(weeks)), key=lambda i: weeks[i][1])
    last_label = -1e9
    for i, (day, n) in enumerate(weeks):
        x = x0 + i * pitch + (pitch - bw) / 2
        if n:
            out.append(column(x, y1, bw, n * scale, i))
        if i == peak and n and n < ticks[-1] - 14 / scale:
            out.append(t(x + bw / 2, y1 - n * scale - 7, f"{n:,}", 11.5, 700, "$INK", "middle", mono=True))
        end = day + dt.timedelta(days=6)                        # name a month at the week it starts in
        if i and end.month != (weeks[i - 1][0] + dt.timedelta(days=6)).month and x - last_label > 46 and x < x1 - 26:
            out.append(label(x, y1 + 21, end.strftime("%b"), size=11.5))
            last_label = x
    return "".join(out)


def by_weekday(totals, x, y0, y1, bw, gap):
    """Seven columns, Monday first, with the busiest day's share of the year."""
    top, out = max(totals) or 1, []
    for i, n in enumerate(totals):
        bx = x + i * (bw + gap)
        out.append(f'<rect x="{bx}" y="{y1 - 1}" width="{bw}" height="1" fill="$GRID"/>')
        if n:
            out.append(column(bx, y1, bw, (y1 - y0) * n / top, 53 + i * 3))
        if i == totals.index(top) and n:
            out.append(t(bx + bw / 2, y0 - 7, f"{n / sum(totals):.0%}", 11.5, 700, "$INK", "middle", mono=True))
        out.append(label(bx + bw / 2, y1 + 19, "MTWTFSS"[i], "middle", 11.5))
    return "".join(out)


def figures(a, x, y, size, gap):
    days = f"{a['longest']:,} day{'s' * (a['longest'] != 1)}"
    return (t(x - 2, y, f"{a['total']:,}", size, 800, ls=round(-size * .028, 2))
            + t(x, y + 62, f"{a['active']:,}", 22, 800) + label(x, y + 82, "Active days", size=11.5)
            + t(x + gap, y + 62, days, 22, 800) + label(x + gap, y + 82, "Longest streak", size=11.5))


def activity(a):
    return 1200, 372, "\n".join([
        panel(1200, 372),
        label(44, 52, "Contributions · last 12 months"), label(1156, 52, "Per week", "end"),
        figures(a, 44, 124, 66, 150),
        label(44, 252, "By weekday", size=11.5), by_weekday(a["weekday"], 44, 280, 326, 24, 14),
        by_week(a["weeks"], 478, 1156, 78, 312)])


def activity_mobile(a):
    return 480, 548, "\n".join([
        panel(480, 548),
        label(28, 46, "Contributions · last 12 months", size=11.5),
        figures(a, 28, 106, 52, 138),
        label(28, 232, "Per week", size=11.5), by_week(a["weeks"], 62, 452, 252, 352, gap=2.4),
        label(28, 420, "By weekday", size=11.5), by_weekday(a["weekday"], 28, 462, 504, 24, 43)])


# ---------------------------------------------------------------- build

def write(folder, name, title, drawing, colors, css=""):
    w, h, body = drawing
    (folder / f"{name}.svg").write_text(svg(w, h, title, body, colors, css))


def build_activity(folder):
    """With GITHUB_TOKEN and GITHUB_LOGIN set, fetches fresh numbers; otherwise redraws DIR/activity.json."""
    folder.mkdir(parents=True, exist_ok=True)
    if os.environ.get("GITHUB_LOGIN"):
        fetch_activity(folder / "activity.json")
    a = activity_stats(folder / "activity.json")
    title = f"{a['total']:,} contributions in the last 12 months, by week and by weekday."
    for theme, colors in THEMES.items():
        write(folder, f"activity-{theme}", title, activity(a), colors, GROW)
        write(folder, f"activity-mobile-{theme}", title, activity_mobile(a), colors, GROW)


if __name__ == "__main__":
    if sys.argv[1:2] == ["activity"]:
        build_activity(Path(sys.argv[2]))
        sys.exit()
    for old in HERE.glob("*.svg"):
        old.unlink()
    write(HERE, "card", f"{NAME}. {FIELD}. {MOTTO_TEXT}", card(), CARD)
    write(HERE, "card-mobile", f"{NAME}. {FIELD}. {MOTTO_TEXT}", card_mobile(), CARD)
    for theme, colors in THEMES.items():
        write(HERE, f"stack-{theme}", "Stack", stack(), colors)
        write(HERE, f"stack-mobile-{theme}", "Stack", stack_mobile(), colors)
    print("built", len(list(HERE.glob("*.svg"))), "svgs")
