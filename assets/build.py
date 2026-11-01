"""Builds the profile SVGs in this folder.

    pip install fonttools brotli
    python assets/build.py

Plus Jakarta Sans (SIL OFL) and stack icons from skillicons.dev are downloaded once to
~/.cache and embedded, because GitHub renders SVGs as images that cannot load anything.
Edit the content below and re-run; don't hand-edit the SVGs (glyphs are subset per file).
"""
import base64
import io
import re
import urllib.request
from functools import lru_cache
from html import escape
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).parent
CACHE = Path.home() / ".cache" / "parothegreat-fonts"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/plusjakartasans/PlusJakartaSans%5Bwght%5D.ttf"
WEIGHTS = (400, 600, 800)

THEMES = {
    "dark": dict(PANEL="#111B2E", BOX="#17243B", RULE="#26385A", INK="#E9EFF8", MUTED="#A3B3CC", FAINT="#7586A3",
                 BLUE="#5AA2FF"),
    "light": dict(PANEL="#F2F6FC", BOX="#FFFFFF", RULE="#D2DDEE", INK="#0F1B2D", MUTED="#4A5B74", FAINT="#7A8AA3",
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
        font = instancer.instantiateVariableFont(TTFont(fetch(FONT_URL, "jakarta.ttf")), {"wght": weight})
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


# ---------------------------------------------------------------- hero (one file, works on both themes)

MOTTO = "Infrastructure only becomes useful when it's understandable, observable, and defensible."


def hero():
    return "\n".join([
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#0A2557"/><stop offset="1" stop-color="#1450B8"/></linearGradient></defs>',
        '<rect width="1200" height="300" rx="16" fill="url(#bg)"/>',
        '<circle cx="1120" cy="40" r="260" fill="#FFFFFF" opacity=".04"/>',
        '<circle cx="1160" cy="300" r="170" fill="#FFFFFF" opacity=".05"/>',
        t(64, 128, "Alvaro Prayogo", 64, 800, "#FFFFFF", extra=' letter-spacing="-1.5"'),
        t(66, 170, "CTO at Klaro", 24, 600, "#A9CBFF"),
        '<rect x="66" y="204" width="44" height="3" rx="1.5" fill="#A9CBFF"/>',
        t(66, 246, MOTTO, 20, 400, "#FFFFFF", extra=' opacity=".9"'),
    ])


# ---------------------------------------------------------------- diagram kit (Klaro + cards)

GLYPHS = {  # 24x24 stroke icons for things skillicons doesn't have
    "users": '<circle cx="9" cy="8" r="3.2"/><path d="M3 19c0-3.3 2.7-6 6-6s6 2.7 6 6M15.5 5.2a3.2 3.2 0 0 1 0 6M17.5 13.4c2 .8 3.5 2.9 3.5 5.6"/>',
    "pen": '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16v4ZM13.5 6.5l4 4"/>',
    "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
    "image": '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="9.5" r="1.6"/><path d="m20.5 16-5-5-8.5 8.5"/>',
    "cloud": '<path d="M7 19h10.5a4.5 4.5 0 0 0 .6-8.96A6.5 6.5 0 0 0 5.6 8.6 5 5 0 0 0 7 19Z"/>',
    "send": '<path d="M21 3 10 14M21 3l-7 18-4-7-7-4 18-7Z"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4V5Z"/><path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01" stroke-width="2.6"/>',
    "shield": '<path d="M12 3 5 6v5c0 4.5 3 8.3 7 10 4-1.7 7-5.5 7-10V6l-7-3Z"/><path d="m9 12 2 2 4-4"/>',
    "terminal": '<rect x="3" y="4.5" width="18" height="15" rx="2"/><path d="m7 10 3 2.5L7 15M12.5 15H17"/>',
    "doc": '<path d="M6 3h8l4 4v14H6V3Z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "card": '<rect x="2" y="6" width="13" height="12" rx="2"/><path d="M5.5 10h4M5.5 14h6M18 9a4.5 4.5 0 0 1 0 6M20.5 6.5a8 8 0 0 1 0 11"/>',
    "chip": '<rect x="6" y="6" width="12" height="12" rx="1.5"/><rect x="9.5" y="9.5" width="5" height="5"/><path d="M9 2.5V6M15 2.5V6M9 18v3.5M15 18v3.5M2.5 9H6M2.5 15H6M18 9h3.5M18 15h3.5"/>',
    "display": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4M7 9h2M11 9h2M7 12h6"/>',
    "dashboard": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M7 16v-3M11 16v-5M15 16v-2"/>',
    "db": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v12c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"/>',
    "door": '<path d="M6 21V4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17M3.5 21h17"/><circle cx="14.5" cy="12.5" r=".6" stroke-width="2.4"/>',
}
TILE = {"dark": "#242938", "light": "#F4F2ED"}  # skillicons' neutral tile, so glyph tiles sit next to brand tiles


@lru_cache
def _metrics_font(weight):
    return instancer.instantiateVariableFont(TTFont(fetch(FONT_URL, "jakarta.ttf")), {"wght": weight})


def tw(s, size, weight):
    """Rendered width of s, so boxes are sized from the real font instead of guessed."""
    f = _metrics_font(weight)
    cmap, hmtx = f.getBestCmap(), f["hmtx"]
    return sum(hmtx[cmap[ord(c)]][0] for c in s) * size / f["head"].unitsPerEm


def icon(name, theme, x, y, size):
    if name in GLYPHS:
        k = size / 24
        return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="{size * .234:.1f}" fill="{TILE[theme]}"/>'
                f'<g transform="translate({x + size * .16:g} {y + size * .16:g}) scale({k * .68:.4f})" fill="none" stroke="$BLUE" '
                f'stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">{GLYPHS[name]}</g>')
    return skill_icon(name, theme, x, y, size)


class Node:
    def __init__(self, label, ico, x, cy, w, h, sub=None):
        self.label, self.ico, self.x, self.cy, self.w, self.h, self.sub = label, ico, x, cy, w, h, sub

    l = property(lambda n: n.x)
    r = property(lambda n: n.x + n.w)
    cx = property(lambda n: n.x + n.w / 2)
    top = property(lambda n: n.cy - n.h / 2)
    bot = property(lambda n: n.cy + n.h / 2)

    def draw(self, theme):
        big = self.sub is not None
        pad, size, size_t = (12, 32, 14.5) if big else (9, 26, 14)
        tx = self.x + pad + size + (11 if big else 9)
        assert tx + tw(self.label, size_t, 700) <= self.r - 6, f"label too long: {self.label}"
        out = [f'<rect x="{self.x:g}" y="{self.top:g}" width="{self.w}" height="{self.h}" rx="{11 if big else 10}" fill="$BOX" stroke="$RULE"/>',
               icon(self.ico, theme, self.x + pad, self.cy - size / 2, size)]
        if big:
            out += [t(tx, self.cy - 3, self.label, size_t, 700), t(tx, self.cy + 15, self.sub, 12.5, 400, "$FAINT")]
        else:
            out.append(t(tx, self.cy + 5, self.label, size_t, 700))
        return "".join(out)


def link(a, b, mx=None):
    """Path from node a to node b: straight when aligned, otherwise one elbow through the gap."""
    if a.cy == b.cy:
        x1, x2 = (a.r, b.l) if b.x > a.x else (a.l, b.r)
        return f"M{x1:g} {a.cy:g}H{x2:g}"
    if a.cx == b.cx:
        y1, y2 = (a.bot, b.top) if b.cy > a.cy else (a.top, b.bot)
        return f"M{a.cx:g} {y1:g}V{y2:g}"
    x1, x2 = (a.r, b.l) if b.x > a.x else (a.l, b.r)
    mx = (x1 + x2) / 2 if mx is None else mx
    return f"M{x1:g} {a.cy:g}H{mx:g}V{b.cy:g}H{x2:g}"


def flow(d, dur=1.4):
    """A wire with packets moving along it in the direction it was drawn."""
    return (f'<path d="{d}" fill="none" stroke="$RULE" stroke-width="2" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="$BLUE" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="4 10">'
            f'<animate attributeName="stroke-dashoffset" from="28" to="0" dur="{dur}s" repeatCount="indefinite"/></path>')


def zone(x, y, w, h, label, theme):
    """Dashed boundary with its label set into the line, like a fieldset legend."""
    lw = tw(label, 12, 700) + 16
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="none" stroke="$RULE" stroke-width="1.5" stroke-dasharray="6 6"/>'
            f'<rect x="{x + 18}" y="{y - 9}" width="{lw:.0f}" height="18" fill="$PANEL"/>'
            + t(x + 26, y + 4.5, label, 12, 700, "$FAINT", extra=' letter-spacing=".6"'))


def diagram(nodes, links, theme):
    return "\n".join([flow(d) for d in links] + [n.draw(theme) for n in nodes.values()])


# ---------------------------------------------------------------- Klaro

KLARO_H = 452


def klaro(theme):
    W, H = 176, 56
    c = [36, 268, 488, 708, 952]           # column x
    r = [244, 322, 400]                     # row centre y
    half = lambda i: (r[i] + r[i + 1]) / 2  # noqa: E731
    N = {k: Node(label, ico, c[col], y, W, H, sub) for k, label, ico, col, y, sub in [
        ("learn", "Learners", "users", 0, half(0), "Browser"),
        ("studio", "Studio", "pen", 0, half(1), "Authoring tool"),
        ("caddy", "Caddy", "lock", 1, r[1], "TLS · HTTP/3"),
        ("web", "Next.js", "nextjs", 2, r[0], "Web frontend"),
        ("api", "Go API", "go", 2, r[1], "REST · Podman"),
        ("media", "Media worker", "image", 2, r[2], "WebP · systemd"),
        ("pg", "PostgreSQL", "postgres", 3, r[1], "v18 · Podman"),
        ("auth", "Supabase Auth", "supabase", 4, r[0], "Identity"),
        ("r2", "Cloudflare R2", "cloudflare", 4, r[2], "Media storage"),
    ]}
    gap_api_pg = (N["api"].r + N["pg"].l) / 2
    links = [link(N["learn"], N["caddy"], 232), link(N["studio"], N["caddy"], 232),  # merge left of the VPS line
             link(N["caddy"], N["web"]), link(N["caddy"], N["api"]), link(N["web"], N["api"]),
             link(N["api"], N["pg"]),
             f'M{N["api"].r:g} {r[1]}H{gap_api_pg:g}V{r[0]}H{N["auth"].l:g}',     # over the empty slot above PostgreSQL
             link(N["media"], N["r2"]),
             f'M{N["media"].r:g} {r[2]}H{N["pg"].cx:g}V{N["pg"].bot:g}']

    title_w = tw("Klaro", 36, 800)
    out = [f'<rect width="1200" height="{KLARO_H}" rx="16" fill="$PANEL"/>',
           t(44, 82, "Klaro", 36, 800, extra=' letter-spacing="-.5"'),
           # status: a slow pulse, because it's the one thing on this page that is live
           f'<circle cx="{66 + title_w:g}" cy="70" r="9" fill="#F5A524" opacity=".25">'
           '<animate attributeName="r" values="5;10;5" dur="2.4s" repeatCount="indefinite"/>'
           '<animate attributeName="opacity" values=".35;0;.35" dur="2.4s" repeatCount="indefinite"/></circle>',
           f'<circle cx="{66 + title_w:g}" cy="70" r="4.5" fill="#F5A524"/>',
           t(80 + title_w, 75, "In development", 15, 600, "$MUTED"),
           t(44, 118, "CTO  ·  A German-learning platform. I lead engineering end to end, from the architecture to the servers it runs on.",
             16, 400, "$MUTED"),
           zone(c[1] - 16, 172, c[3] + W + 24 - (c[1] - 16), 268, "VPS", theme),
           zone(c[4] - 24, 172, W + 48, 268, "MANAGED", theme),
           diagram(N, links, theme)]
    return "\n".join(out)


# ---------------------------------------------------------------- project cards

CARD_W, CARD_H = 580, 268
COLS, ROWS, NODE_W = [32, 218, 404], [150, 214], 144

CARDS = [  # id, title, one line, nodes {key: (label, icon, col, row)}, links (from, to), repo
    ("cloud", "Self-hosted cloud & monitoring", "Private cloud with zero open ports, plus host monitoring.",
     {"cf": ("Tunnel", "cloudflare", 0, 0), "nginx": ("Nginx", "nginx", 1, 0), "nc": ("Nextcloud", "cloud", 2, 0),
      "host": ("Ubuntu host", "ubuntu", 0, 1), "prom": ("Prometheus", "prometheus", 1, 1), "graf": ("Grafana", "grafana", 2, 1)},
     [("cf", "nginx"), ("nginx", "nc"), ("host", "prom"), ("prom", "graf")], False),
    ("recon", "Nodebuntu Recon Agent", "Autonomous recon loop. Every command passes an allowlist.",
     {"tg": ("Telegram", "send", 0, 0), "go": ("Go agent", "go", 1, 0), "llm": ("LLM", "chat", 2, 0),
      "allow": ("Allowlist", "shield", 2, 1), "tools": ("Recon tools", "terminal", 1, 1), "rep": ("Report", "doc", 0, 1)},
     [("tg", "go"), ("go", "llm"), ("llm", "allow"), ("allow", "tools"), ("tools", "rep"), ("rep", "tg")], True),
    ("rfid", "RFID door access", "Server-room door with offline card checks and hourly sync.",
     {"card": ("MFRC522", "card", 0, 0), "esp": ("ESP32-C6", "chip", 1, 0), "lock": ("Relay lock", "door", 2, 0),
      "tg": ("Telegram", "send", 0, 1), "api": ("Go API", "go", 1, 1), "db": ("MariaDB", "db", 2, 1)},
     [("card", "esp"), ("esp", "lock"), ("tg", "api"), ("api", "esp"), ("api", "db")], False),
    ("claude-hud", "claude-hud", "Claude Code state and usage limits on a desk OLED, at 60 fps.",
     {"cc": ("Claude Code", "terminal", 0, 0), "br": ("Rust bridge", "rust", 1, 0), "esp": ("ESP32-C3", "chip", 2, 0),
      "dash": ("Dashboard", "dashboard", 1, 1), "oled": ("OLED 128×64", "display", 2, 1)},
     [("cc", "br"), ("br", "esp"), ("br", "dash"), ("esp", "oled")], True),
]


def card(title, line, nodes, links, linked, theme):
    N = {k: Node(label, ico, COLS[col], ROWS[row], NODE_W, 44) for k, (label, ico, col, row) in nodes.items()}
    out = [f'<rect width="{CARD_W}" height="{CARD_H}" rx="16" fill="$PANEL"/>',
           t(32, 58, title, 24, 800, extra=' letter-spacing="-.3"'),
           t(32, 88, line, 15, 400, "$MUTED"),
           diagram(N, [link(N[a], N[b]) for a, b in links], theme)]
    if linked:
        out.append('<path d="M534 38h12v12M546 38l-14 14" fill="none" stroke="$BLUE" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
    return "\n".join(out)


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


if __name__ == "__main__":
    for old in HERE.glob("*.svg"):
        old.unlink()
    (HERE / "hero.svg").write_text(svg(1200, 300, f"Alvaro Prayogo, CTO at Klaro. {MOTTO}", hero()))
    for theme in THEMES:
        (HERE / f"klaro-{theme}.svg").write_text(svg(1200, KLARO_H, "Klaro: German-learning platform", klaro(theme), theme))
        for cid, title, line, nodes, links, linked in CARDS:
            (HERE / f"card-{cid}-{theme}.svg").write_text(
                svg(CARD_W, CARD_H, f"{title}: {line}", card(title, line, nodes, links, linked, theme), theme))
        h, body = stack(theme)
        (HERE / f"stack-{theme}.svg").write_text(svg(1200, h, "Stack", body, theme))
    print("built", len(list(HERE.glob("*.svg"))), "svgs")
