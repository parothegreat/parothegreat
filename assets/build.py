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


# ---------------------------------------------------------------- Klaro

ARROW = '<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="$FAINT"/></marker>'


def box(label, cx, cy, w):
    return (f'<rect x="{cx - w / 2:g}" y="{cy - 18}" width="{w}" height="36" rx="8" fill="$BOX" stroke="$RULE"/>'
            + t(cx, cy + 5, label, 14, 600, anchor="middle"))


def klaro():
    out = [f"<defs>{ARROW}</defs>", '<rect width="1200" height="320" rx="16" fill="$PANEL"/>',
           t(44, 84, "Klaro", 36, 800, extra=' letter-spacing="-.5"'),
           t(44, 116, "CTO  ·  In development", 16, 600, "$BLUE")]
    for i, line in enumerate(["A German-learning platform. I lead engineering end to end:",
                              "the architecture, the Go API and Next.js app, TOTP-based",
                              "auth, and the containerised infrastructure it runs on."]):
        out.append(t(44, 164 + i * 26, line, 16.5, 400, "$MUTED"))
    out.append(t(44, 272, "Go, Next.js, PostgreSQL, Supabase Auth, Caddy, Podman", 14.5, 600, "$FAINT"))

    out.append('<rect x="770" y="66" width="408" height="150" rx="12" fill="none" stroke="$RULE" stroke-dasharray="5 5"/>')
    out.append(t(788, 92, "Podman on a VPS", 13, 600, "$FAINT"))
    line = 'fill="none" stroke="$FAINT" stroke-width="1.6"'
    out += [f'<path d="M745 120H762V160H780" {line} marker-end="url(#a)"/>', f'<path d="M745 200H762V160" {line}/>',
            f'<path d="M878 160H894V110H912" {line} marker-end="url(#a)"/>',
            f'<path d="M878 160H894V180H912" {line} marker-end="url(#a)"/>',
            f'<path d="M970 128V160" {line} marker-end="url(#a)"/>',
            f'<path d="M1026 180H1043" {line} marker-end="url(#a)"/>',
            f'<path d="M970 198V250H1043" {line} marker-end="url(#a)"/>']
    out += [box("Learners", 690, 120, 110), box("Studio", 690, 200, 110), box("Caddy", 830, 160, 96),
            box("Next.js", 970, 110, 112), box("Go API", 970, 180, 112),
            box("PostgreSQL", 1105, 180, 120), box("Supabase Auth", 1105, 250, 120)]
    out.append(t(636, 292, "Simplified architecture", 13, 400, "$FAINT"))
    return "\n".join(out)


# ---------------------------------------------------------------- project cards

CARDS = [  # id, title, two lines, stack, has public repo
    ("cloud", "Self-hosted cloud & monitoring",
     ["Nextcloud on Ubuntu, reached through Cloudflare Tunnel", "with no open ports. Prometheus and Grafana watch the hosts."],
     "Ubuntu, Nextcloud, Nginx, Cloudflare Tunnel, Prometheus, Grafana", False),
    ("recon", "Nodebuntu Recon Agent",
     ["An LLM-driven agent for authorized recon and server", "monitoring that only runs allowlisted commands."],
     "Go, subfinder, httpx, nuclei, katana", True),
    ("rfid", "RFID door access",
     ["Prototype server-room access: an ESP32 reads the card,", "a Go service verifies it, then drives the lock and alerts."],
     "ESP32-C6, MFRC522, Go, MariaDB, Telegram Bot API", False),
    ("claude-hud", "claude-hud",
     ["A desk display for Claude Code. An ESP32-C3 drives a", "128×64 OLED showing agent state and rate limits."],
     "Rust, ESP32-C3, OLED", True),
]


def card(title, lines, stack, linked):
    out = ['<rect width="580" height="210" rx="16" fill="$PANEL"/>', t(32, 62, title, 24, 800, extra=' letter-spacing="-.3"')]
    if linked:
        out.append('<path d="M534 40h12v12M546 40l-14 14" fill="none" stroke="$BLUE" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>')
    for i, line in enumerate(lines):
        out.append(t(32, 102 + i * 25, line, 16, 400, "$MUTED"))
    out.append(t(32, 176, stack, 14, 600, "$FAINT"))
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
        (HERE / f"klaro-{theme}.svg").write_text(svg(1200, 320, "Klaro: German-learning platform", klaro(), theme))
        for cid, title, lines, stack_text, linked in CARDS:
            (HERE / f"card-{cid}-{theme}.svg").write_text(
                svg(580, 210, f"{title}: {' '.join(lines)}", card(title, lines, stack_text, linked), theme))
        h, body = stack(theme)
        (HERE / f"stack-{theme}.svg").write_text(svg(1200, h, "Stack", body, theme))
    print("built", len(list(HERE.glob("*.svg"))), "svgs")
