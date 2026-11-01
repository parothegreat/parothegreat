"""Builds the profile SVGs in this folder (hero, featured card, project cards; light and dark).

    pip install fonttools brotli
    python assets/build.py

Fonts (Plus Jakarta Sans, JetBrains Mono; SIL OFL) are downloaded once to ~/.cache and
embedded as subsets, because GitHub renders SVGs as images that cannot load web fonts.
Edit the text below and re-run; don't hand-edit the SVGs (glyphs are subset per file).
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
FONT_URLS = {
    "jakarta": "https://github.com/google/fonts/raw/main/ofl/plusjakartasans/PlusJakartaSans%5Bwght%5D.ttf",
    "mono": "https://github.com/google/fonts/raw/main/ofl/jetbrainsmono/JetBrainsMono%5Bwght%5D.ttf",
}
FACES = [("Jakarta", "jakarta", 400), ("Jakarta", "jakarta", 600), ("Jakarta", "jakarta", 800), ("Mono", "mono", 500)]

THEMES = {
    "dark": dict(BG="#0F141B", CARD="#151B23", RULE="#2A313B", INK="#F0F3F6", MUTED="#9AA4B2", FAINT="#6B7685",
                 ACCENT="#3DD68C", SOFT="#173A2A", BLUE="#58A6FF", AMBER="#E3B341"),
    "light": dict(BG="#F6F8FA", CARD="#F6F8FA", RULE="#D8DEE4", INK="#1F2328", MUTED="#59636E", FAINT="#8C959F",
                  ACCENT="#0A7D4F", SOFT="#DDF4E7", BLUE="#0969DA", AMBER="#9A6700"),
}

ICONS = {  # 24x24 stroke icons
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
    "letters": '<path d="M4 19 9 5l5 14M6 14h6"/><path d="M15.5 9.5h4.5M17.75 9.5V19M15 19h5.5"/>',
    "rfid": '<rect x="2" y="6" width="13" height="12" rx="2"/><path d="M5.5 10h4M5.5 14h6M18 9a4.5 4.5 0 0 1 0 6M20.5 6.5a8 8 0 0 1 0 11"/>',
    "cloud": '<path d="M7 19h10.5a4.5 4.5 0 0 0 .6-8.96A6.5 6.5 0 0 0 5.6 8.6 5 5 0 0 0 7 19Z"/>',
    "display": '<rect x="3" y="4" width="18" height="13" rx="2"/><path d="M8 21h8M12 17v4M7 9h2M11 9h2M7 12h6"/>',
    "radar": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><path d="m12 12 6-6"/><circle cx="16" cy="9" r="1" fill="currentColor"/>',
}

STATUS = {"Active": "$ACCENT", "Maintained": "$BLUE", "Prototype": "$AMBER",
          "In development": "$AMBER", "Experimental": "$AMBER"}


def icon(name, x, y, color, size=24, width=1.8):
    s = size / 24
    return (f'<g transform="translate({x} {y}) scale({s:g})" fill="none" stroke="{color}" color="{color}" '
            f'stroke-width="{width / s:g}" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def font_file(key):
    path = CACHE / f"{key}.ttf"
    if not path.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(FONT_URLS[key], path)
    return path


def font_css(text):
    css = []
    for family, key, weight in FACES:
        font = instancer.instantiateVariableFont(TTFont(font_file(key)), {"wght": weight})
        opts = subset.Options()
        opts.flavor, opts.layout_features, opts.name_IDs = "woff2", ["kern"], [1, 2]
        opts.hinting = False
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        data = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:'{family}';font-weight:{weight};"
                   f"src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(css)


def svg(w, h, title, body, theme):
    for k, v in THEMES[theme].items():
        body = body.replace("$" + k, v)
    text = "".join(sorted(set("".join(re.findall(r">([^<>]+)</text>", body)))))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">\n'
            f'<title>{escape(title)}</title>\n<style>{font_css(text)}'
            ".sans{font-family:'Jakarta','Plus Jakarta Sans','Segoe UI',-apple-system,Helvetica,Arial,sans-serif}"
            ".mono{font-family:'Mono','JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
            f"</style>\n{body}\n</svg>\n")


def node(label, cx, cy, w, dot):
    return (f'<rect x="{cx - w / 2:g}" y="{cy - 18}" width="{w}" height="36" rx="9" fill="$BG" stroke="$RULE"/>'
            f'<circle cx="{cx - w / 2 + 16:g}" cy="{cy}" r="4" fill="{dot}"/>'
            f'<text x="{cx - w / 2 + 28:g}" y="{cy + 5}" class="sans" font-size="13" font-weight="600" fill="$INK">{escape(label)}</text>')


def flow(d):
    return (f'<path d="{d}" fill="none" stroke="$RULE" stroke-width="2"/>'
            f'<path d="{d}" fill="none" stroke="$ACCENT" stroke-width="2" stroke-linecap="round" stroke-dasharray="5 15">'
            '<animate attributeName="stroke-dashoffset" from="40" to="0" dur="1.6s" repeatCount="indefinite"/></path>')


# ---------------------------------------------------------------- hero

PATH = [("Industrial electronics", "Circuits, microcontrollers, embedded"),
        ("Infrastructure & security", "Linux, networks, containers, self-hosting"),
        ("CTO, Klaro", "Architecture, backend, infrastructure")]


def hero():
    out = ['<defs><radialGradient id="g" cx="980" cy="60" r="460" gradientUnits="userSpaceOnUse">'
           '<stop stop-color="$ACCENT" stop-opacity=".10"/><stop offset="1" stop-color="$ACCENT" stop-opacity="0"/>'
           '</radialGradient></defs>',
           '<rect width="1200" height="320" rx="16" fill="$BG"/><rect width="1200" height="320" rx="16" fill="url(#g)"/>',
           '<text x="66" y="90" class="mono" font-size="13" letter-spacing="2.5" fill="$ACCENT">CTO · KLARO</text>',
           '<text x="62" y="162" class="sans" font-size="66" font-weight="800" letter-spacing="-2" fill="$INK">Alvaro Prayogo</text>',
           '<text x="66" y="206" class="sans" font-size="22" font-weight="400" fill="$MUTED">I build, operate, and secure the systems a product runs on.</text>',
           icon("pin", 66, 239, "$FAINT", 18),
           '<text x="92" y="254" class="sans" font-size="15" font-weight="600" fill="$INK">Bekasi, Indonesia</text>']

    # career path: one straight line, the last stop is now
    x, top, step = 800, 84, 80
    out.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + 2 * step}" stroke="$RULE" stroke-width="2"/>')
    out.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + 2 * step}" stroke="$ACCENT" stroke-width="2" '
               f'stroke-dasharray="{2 * step}" stroke-dashoffset="0">'
               f'<animate attributeName="stroke-dashoffset" from="{2 * step}" to="0" dur="1.4s" fill="freeze"/></line>')
    for i, (title, sub) in enumerate(PATH):
        y = top + i * step
        now = i == len(PATH) - 1
        if now:
            out.append(f'<circle cx="{x}" cy="{y}" r="12" fill="$ACCENT" opacity=".18">'
                       '<animate attributeName="r" values="8;14;8" dur="2.4s" repeatCount="indefinite"/></circle>')
        out.append(f'<circle cx="{x}" cy="{y}" r="6" fill="{"$ACCENT" if now else "$BG"}" stroke="$ACCENT" stroke-width="2"/>')
        out.append(f'<text x="{x + 26}" y="{y + 1}" class="sans" font-size="17" font-weight="800" fill="$INK">{escape(title)}</text>')
        out.append(f'<text x="{x + 26}" y="{y + 22}" class="sans" font-size="13.5" font-weight="400" fill="$MUTED">{escape(sub)}</text>')
    return "\n".join(out)


# ---------------------------------------------------------------- featured: Klaro

def featured():
    out = ['<rect width="1200" height="300" rx="16" fill="$CARD"/>',
           '<rect x="32" y="32" width="48" height="48" rx="12" fill="$SOFT"/>',
           icon("letters", 44, 44, "$ACCENT", 24),
           '<text x="32" y="122" class="mono" font-size="12" letter-spacing="1.2" fill="$ACCENT">CTO</text>',
           f'<circle cx="80" cy="118" r="4" fill="{STATUS["In development"]}"/>',
           '<text x="92" y="122" class="mono" font-size="12.5" fill="$MUTED">In development</text>',
           '<text x="32" y="162" class="sans" font-size="34" font-weight="800" letter-spacing="-.8" fill="$INK">Klaro</text>']
    lines = ["A German-learning platform. I lead engineering end to",
             "end: the architecture, the Go API and Next.js app, TOTP",
             "auth, and the containerised infrastructure it runs on."]
    for i, line in enumerate(lines):
        out.append(f'<text x="32" y="{196 + i * 23}" class="sans" font-size="15.5" font-weight="400" fill="$MUTED">{escape(line)}</text>')
    out.append('<text x="32" y="274" class="mono" font-size="12" fill="$FAINT">Go · Next.js · PostgreSQL · Supabase Auth · Caddy · Podman</text>')

    # architecture (simplified)
    out.append('<rect x="766" y="62" width="414" height="148" rx="12" fill="none" stroke="$RULE" stroke-dasharray="4 5"/>')
    out.append('<text x="782" y="84" class="mono" font-size="10.5" letter-spacing="1.5" fill="$FAINT">PODMAN · VPS</text>')
    for d in ["M736 110H756V150H776", "M736 190H756V150", "M866 150H881V100H896", "M866 150H881V170H896",
              "M951 118V152", "M1006 170H1038", "M951 188V240H1038"]:
        out.append(flow(d))
    for args in [("Learners", 681, 110, 110, "$FAINT"), ("Studio", 681, 190, 110, "$FAINT"),
                 ("Caddy", 821, 150, 90, "$ACCENT"), ("Next.js", 951, 100, 110, "$BLUE"),
                 ("Go API", 951, 170, 110, "$BLUE"), ("PostgreSQL", 1104, 170, 132, "$AMBER"),
                 ("Supabase Auth", 1104, 240, 132, "$FAINT")]:
        out.append(node(*args))
    out.append('<text x="626" y="274" class="mono" font-size="11" letter-spacing="1.5" fill="$FAINT">PLATFORM ARCHITECTURE · SIMPLIFIED</text>')
    return "\n".join(out)


# ---------------------------------------------------------------- cards

CARDS = [  # id, icon, role, title, status, two description lines, stack
    ("cloud", "cloud", "Infrastructure", "Self-hosted Cloud & Monitoring", "Maintained",
     ["Nextcloud on Ubuntu behind Cloudflare Tunnel with", "no open ports. Prometheus and Grafana for hosts."],
     "Ubuntu · Nextcloud · Nginx · Prometheus · Grafana"),
    ("recon", "radar", "Security", "Nodebuntu Recon Agent", "Experimental",
     ["LLM-driven agent for authorized recon and server", "monitoring, limited to an allowlist of commands."],
     "Go · subfinder · httpx · nuclei · katana"),
    ("rfid", "rfid", "Embedded · Backend", "RFID Door Access", "Prototype",
     ["Server-room access control: ESP32 card reads,", "Go verification, relay lock and Telegram alerts."],
     "ESP32-C6 · MFRC522 · Go · MariaDB"),
    ("claude-hud", "display", "Embedded · Rust", "claude-hud", "Active",
     ["Desk display for Claude Code. An ESP32-C3 drives a", "128×64 OLED with agent state and rate limits."],
     "Rust · ESP32-C3 · OLED"),
]


def card(icon_name, role, title, status, lines, stack):
    out = ['<rect width="580" height="250" rx="16" fill="$CARD"/>',
           '<rect x="28" y="28" width="48" height="48" rx="12" fill="$SOFT"/>',
           icon(icon_name, 40, 40, "$ACCENT", 24),
           f'<circle cx="{552 - len(status) * 7.6 - 14:g}" cy="47" r="4" fill="{STATUS[status]}"/>',
           f'<text x="552" y="52" text-anchor="end" class="mono" font-size="12.5" fill="$MUTED">{status}</text>',
           f'<text x="28" y="114" class="mono" font-size="11.5" letter-spacing="1.2" fill="$ACCENT">{escape(role.upper())}</text>',
           f'<text x="28" y="146" class="sans" font-size="26" font-weight="800" letter-spacing="-.5" fill="$INK">{escape(title)}</text>']
    for i, line in enumerate(lines):
        out.append(f'<text x="28" y="{178 + i * 23}" class="sans" font-size="15.5" font-weight="400" fill="$MUTED">{escape(line)}</text>')
    out.append(f'<text x="28" y="226" class="mono" font-size="12" fill="$FAINT">{escape(stack)}</text>')
    return "\n".join(out)


if __name__ == "__main__":
    for old in HERE.glob("*.svg"):
        old.unlink()
    for theme in THEMES:
        (HERE / f"hero-{theme}.svg").write_text(svg(1200, 320, "Alvaro Prayogo, CTO at Klaro", hero(), theme))
        (HERE / f"klaro-{theme}.svg").write_text(svg(1200, 300, "Klaro: German-learning platform", featured(), theme))
        for cid, ic, role, title, status, lines, stack in CARDS:
            (HERE / f"card-{cid}-{theme}.svg").write_text(
                svg(580, 250, f"{title}: {' '.join(lines)}", card(ic, role, title, status, lines, stack), theme))
    print("built", len(list(HERE.glob("*.svg"))), "svgs")
