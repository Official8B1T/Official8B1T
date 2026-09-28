# ─────────────────────────────────────────────────────
#   project · Official8B1T
#   module  · build.py — renders profile SVGs with embedded font subsets
#   author  · Jiří "8B1T" Lhotský
# ─────────────────────────────────────────────────────

import base64
import re
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / "assets"

# ── TOKENS · 8B1T Design System v2.1 ─────────────────────

VOID, CARBON, ASH = "#080808", "#161616", "#242424"
SIGNAL = "#FF0000"
BONE, PURE, SMOKE, OK = "#F5F2EF", "#FFFFFF", "#818181", "#1FB85C"

# GitHub dark card chrome, so panels sit flush with the profile's own sections
FRAME = "#3D444D"
RADIUS = 8.5  # ≈ GitHub's 6px once the 1200-wide panel scales into the README column

# ── FONTS ─────────────────────────────────────────────────

# NOTE · JetBrains Mono and Space Grotesk are SIL OFL 1.1 — embedding subsets in documents is permitted
# ASCII + Czech, so text edits never need a new subset
CHARSET = "".join(map(chr, range(32, 127))) + "ěščřžýáíéúůťďňĚŠČŘŽÝÁÍÉÚŮŤĎŇ·—→█°"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"  # woff2 only for modern UAs


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
        return r.read()


# inline a Google Fonts subset — SVG rendered via <img> must not load external resources
def font_face(family, weight, alias):
    q = urllib.parse.urlencode({"family": f"{family}:wght@{weight}", "text": CHARSET})
    css = fetch(f"https://fonts.googleapis.com/css2?{q}").decode()
    url = re.search(r"url\((https://[^)]+)\)", css).group(1)
    data = base64.b64encode(fetch(url)).decode()
    return f"@font-face{{font-family:{alias};font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2')}}"


FONTS = "".join([
    font_face("JetBrains Mono", 400, "M"),
    font_face("JetBrains Mono", 700, "M"),
    font_face("Space Grotesk", 700, "G"),
])

BASE_CSS = f"""{FONTS}
.m{{font-family:M,'JetBrains Mono',Consolas,monospace}}
.g{{font-family:G,'Space Grotesk',sans-serif;font-weight:700}}
.pulse{{animation:pulse 2.5s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:.65}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}"""

GLOW = """<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="{0}"/>
</filter>"""


def svg(w, h, css, defs, body, label):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{escape(label, {'"': "&quot;"})}">
<style>{css}</style>
<defs>{defs}<clipPath id="card"><rect width="{w}" height="{h}" rx="{RADIUS}"/></clipPath></defs>
<g clip-path="url(#card)">
{body}
</g>
<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{RADIUS}" fill="none" stroke="{FRAME}" vector-effect="non-scaling-stroke"/>
</svg>
"""


def crop_marks(w, h, inset=20, size=16):
    c = [(inset, inset, 1, 1), (w - inset, inset, -1, 1), (inset, h - inset, 1, -1), (w - inset, h - inset, -1, -1)]
    d = "".join(f"M{x} {y + size * sy}V{y}H{x + size * sx}" for x, y, sx, sy in c)
    return f'<path d="{d}" fill="none" stroke="{ASH}" stroke-width="2"/>'


# ── BANNER ────────────────────────────────────────────────

def banner():
    w, h = 1200, 400
    defs = GLOW.format(14)
    # the glow copy repeats the wordmark with only the "1" painted, so it aligns glyph for glyph
    mark = '<tspan fill-opacity="{o}">8B</tspan><tspan fill="{s}">1</tspan><tspan fill-opacity="{o}">T</tspan>'
    word = 'x="600" y="262" text-anchor="middle" font-size="210" letter-spacing="-6"'
    body = f"""<rect width="{w}" height="{h}" fill="{VOID}"/>
{crop_marks(w, h)}
<g class="m" font-size="14" letter-spacing="2.8" fill="{SMOKE}">
  <text x="56" y="62"><tspan fill="{SIGNAL}">//</tspan> JIŘÍ LHOTSKÝ</text>
  <text x="1144" y="62" text-anchor="end">PRAGUE · CZ</text>
  <text x="56" y="352" font-size="12">50.0755°N · 14.4378°E</text>
  <text x="1144" y="352" font-size="12" text-anchor="end">STATUS · ONLINE</text>
</g>
<circle class="pulse" cx="978" cy="348" r="4" fill="{OK}"/>
<text {word} fill="{SIGNAL}" filter="url(#glow)" class="g pulse">{mark.format(o=0, s=SIGNAL)}</text>
<text class="g" {word} fill="{PURE}">{mark.format(o=1, s=SIGNAL)}</text>
<rect class="pulse" x="577" y="292" width="46" height="2" fill="{SIGNAL}" filter="url(#glow)"/>
<rect x="577" y="292" width="46" height="2" fill="{SIGNAL}"/>
<text class="m" x="600" y="334" text-anchor="middle" font-size="16" letter-spacing="5" fill="{BONE}">SYSADMIN <tspan fill="{SIGNAL}">·</tspan> DEVOPS <tspan fill="{SIGNAL}">·</tspan> FREELANCER</text>"""
    return svg(w, h, BASE_CSS, defs, body, "8B1T — Jiří Lhotský · SysAdmin · DevOps · Freelancer · Prague")


# ── TERMINAL ──────────────────────────────────────────────

PROMPT = "C:\\8B1T> "


# one CV table row: when · what · kind · where, padded into monospace columns
def cv(when, what, kind, where):
    return ("out", [(f"{when:<13}", SMOKE), (f"{what:<26}", BONE), (f"{kind:<12}", SMOKE), (where, PURE)])


# NOTE · content mirrors the CV minus private details (phone, birth year, district, photo)
SCRIPT = [
    ("cmd", "whoami"),
    ("out", [('jiří "8b1t" lhotský', PURE), ("  ·  IT services  ·  Prague", SMOKE)]),
    ("gap",),
    ("cmd", "Get-Experience"),
    cv("2026 → now", "IT services", "freelance", "Raw Planet s.r.o."),
    cv("2026 → now", "IT services", "contract", "TechLines.cz s.r.o."),
    cv("2025 → now", "IT services", "contract", "VUMS LEGEND, spol. s r.o."),
    cv("2023 → 2025", "Process technician", "full-time", "Continental Automotive Czech Republic s.r.o."),
    cv("2021 → 2023", "Mechanic / electrician", "internship", "GREEN Center s.r.o."),
    ("gap",),
    ("cmd", "Get-Education"),
    cv("2019 → 2023", "Avionics technician", "maturita", "Secondary School of Civil Aviation, Prague"),
    cv("2025", "Python developer", "course", "ITnetwork · Django · SQLite · React"),
    cv("2025", "AI & big data specialist", "course", "ITnetwork · neural nets · PostgreSQL"),
    cv("2022", "English B2", "cert", "Cambridge FCE"),
    ("gap",),
    ("cmd", "Get-Skills | Format-Wide"),
    ("tags", "VIRT", ["ESXi", "iDRAC", "VMware", "Hyper-V", "VirtualBox", "Kubernetes", "Docker", "Podman", "Ceph", "Headlamp"]),
    ("tags", "OS", ["Windows Server", "Windows XP-11", "RHEL", "Rocky Linux", "CentOS", "Ubuntu", "Arch Linux",
                    "Kali Linux", "BlackArch", "BSD / Unix", "macOS", "Android", "iOS"]),
    ("tags", "SEC", ["FortiGate", "FortiAnalyzer", "FortiClient", "ESET Protect", "ESET Inspect", "Keeper", "Valimail", "Azure AD"]),
    ("tags", "OPS", ["Zabbix", "Veeam VBR", "Veeam One", "Synology NAS", "Patch My PC", "Apple Business", "HCL Domino", "HCL Notes"]),
    ("tags", "CODE", ["PowerShell", "Python", "JavaScript", "HTML / CSS", "Django", "React", "PostgreSQL", "SQLite"]),
    ("tags", "DEV", ["Git", "Gitea", "CVS", "Nexus", "Redmine", "Jira"]),
    ("tags", "AI", ["AI & big data", "Advanced AI via CLIs"]),
    ("tags", "MISC", ["SAP", "MS Office", "Photoshop", "Canva", "Video editing", "Photo editing"]),
    ("gap",),
    ("cmd", "Get-Language"),
    ("out", [("czech    ", BONE), ("excellent", SMOKE), ("   ·   ", SIGNAL), ("english  ", BONE), ("advanced (B2)", SMOKE)]),
    ("gap",),
    ("cmd", "Get-Strengths"),
    ("out", [("→ ", SIGNAL), ("problem solving · critical thinking · reliability · working under pressure", BONE)]),
    ("out", [("→ ", SIGNAL), ("teamwork · clear communication · leadership · always learning past my field", BONE)]),
    ("gap",),
    ("cmd", "Test-Connection 8b1t -Count 1"),
    ("out", [("[OK] ", OK), ("reply from Prague · time<1ms", BONE)]),
    ("gap",),
    ("prompt",),
]

FS, CW = 17, 17 * 0.6  # JetBrains Mono advance is exactly 0.6em
TAG_FS, TAG_LS, TAG_PAD = 14, 1.4, 10
X0, TOP = 32, 96


def terminal():
    w = 1200
    css = BASE_CSS + """
.s{animation:show .01s linear both}
@keyframes show{from{opacity:0}to{opacity:1}}
.cover{opacity:0;animation-name:type;animation-fill-mode:both}
@keyframes type{from{opacity:1;transform:translateX(0)}to{opacity:1;transform:translateX(var(--w))}}
.cur{opacity:0;animation-name:cur;animation-fill-mode:backwards}
@keyframes cur{from,to{opacity:1}}
.blink{animation:blink 1s step-end infinite}
@keyframes blink{50%{opacity:0}}"""
    prompt = f'<tspan fill="{SIGNAL}">{escape(PROMPT)}</tspan>'
    px = X0 + len(PROMPT) * CW
    rows, y, t = [], TOP, 0.4

    for kind, *arg in SCRIPT:
        if kind == "gap":
            y += 14
            continue
        if kind == "cmd":
            cmd = arg[0]
            dur = len(cmd) * 0.045
            # void cover slides right in steps, the cursor rides on its left edge = typing
            rows.append(f"""<g class="s" style="animation-delay:{t:.2f}s">
  <text class="m" x="{X0}" y="{y}" font-size="{FS}">{prompt}<tspan fill="{BONE}">{escape(cmd)}</tspan></text>
  <g class="cover" style="--w:{len(cmd) * CW:.1f}px;animation-duration:{dur:.2f}s;animation-timing-function:steps({len(cmd)},end);animation-delay:{t + 0.25:.2f}s">
    <rect x="{px:.1f}" y="{y - 18}" width="{len(cmd) * CW + 24:.1f}" height="24" fill="{VOID}"/>
    <rect class="cur" x="{px:.1f}" y="{y - 17}" width="{CW:.1f}" height="22" fill="{SIGNAL}" style="animation-duration:{dur + 0.45:.2f}s;animation-delay:{t:.2f}s"/>
  </g>
</g>""")
            t += dur + 0.5
            y += 32
        elif kind == "out":
            assert X0 + sum(len(s) for s, _ in arg[0]) * CW < w - X0, f"line overflows the window: {arg[0]}"
            spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in arg[0])
            rows.append(f'<text class="m s" x="{X0}" y="{y}" font-size="{FS}" style="animation-delay:{t:.2f}s" xml:space="preserve">{spans}</text>')
            t += 0.08
            y += 32
        elif kind == "tags":
            label, tags = arg
            left = X0 + 8 * CW
            parts, x = [f'<text x="{X0}" y="{y}" font-size="{FS}" fill="{SMOKE}">{label}</text>'], left
            for tag in tags:
                tag = tag.upper()
                tw = len(tag) * (TAG_FS * 0.6 + TAG_LS) - TAG_LS + 2 * TAG_PAD
                if x + tw > w - X0:  # wrap onto the next line under the same label
                    x, y = left, y + 34
                parts.append(f'<rect x="{x:.1f}" y="{y - 18}" width="{tw:.1f}" height="26" rx="4" fill="{CARBON}" stroke="{ASH}"/>'
                             f'<text x="{x + TAG_PAD:.1f}" y="{y}" font-size="{TAG_FS}" font-weight="700" letter-spacing="{TAG_LS}" fill="{SIGNAL}">{escape(tag)}</text>')
                x += tw + 8
            rows.append(f'<g class="m s" style="animation-delay:{t:.2f}s">{"".join(parts)}</g>')
            t += 0.12
            y += 38
        elif kind == "prompt":
            rows.append(f"""<g class="s" style="animation-delay:{t:.2f}s">
  <text class="m" x="{X0}" y="{y}" font-size="{FS}">{prompt}</text>
  <rect class="blink" x="{px:.1f}" y="{y - 17}" width="{CW:.1f}" height="22" fill="{SIGNAL}"/>
</g>""")
            y += 32

    h = y + 4
    body = f"""<rect width="{w}" height="{h}" fill="{VOID}"/>
<rect width="{w}" height="48" fill="{CARBON}"/>
<path d="M0 48.5H{w}" stroke="{FRAME}" vector-effect="non-scaling-stroke"/>
<rect x="24" y="19" width="10" height="10" fill="{ASH}"/><rect x="42" y="19" width="10" height="10" fill="{ASH}"/><rect x="60" y="19" width="10" height="10" fill="{SIGNAL}"/>
<text class="m" x="{w / 2}" y="29" text-anchor="middle" font-size="13" letter-spacing="1.3" fill="{SMOKE}">pwsh — official@8b1t: ~</text>
{chr(10).join(rows)}"""
    return svg(w, h, css, "", body, alt_terminal())


def alt_terminal():
    lines = []
    for kind, *arg in SCRIPT:
        if kind == "cmd":
            lines.append(f"{PROMPT}{arg[0]}")
        elif kind == "out":
            lines.append("".join(s for s, _ in arg[0]))
        elif kind == "tags":
            lines.append(f"{arg[0]}: {', '.join(arg[1])}")
    return " / ".join(lines)


# ── FOOTER ────────────────────────────────────────────────

EMAIL = "8b1t.biz@proton.me"


def footer():
    w, h = 1200, 164
    label = f"{EMAIL.upper()}  →"
    bw = len(label) * (17 * 0.6 + 2.5) - 2.5 + 64
    bx = (w - bw) / 2
    body = f"""<rect width="{w}" height="{h}" fill="{VOID}"/>
{crop_marks(w, h)}
<text class="m" x="600" y="46" text-anchor="middle" font-size="13" letter-spacing="3.9" fill="{SMOKE}"><tspan fill="{SIGNAL}">//</tspan> GET IN TOUCH</text>
<rect class="pulse" x="{bx:.1f}" y="68" width="{bw:.1f}" height="56" rx="4" fill="{SIGNAL}" filter="url(#glow)"/>
<rect x="{bx:.1f}" y="68" width="{bw:.1f}" height="56" rx="4" fill="{SIGNAL}"/>
<text class="m" x="600" y="102" text-anchor="middle" font-size="17" font-weight="700" letter-spacing="2.5" fill="{VOID}" xml:space="preserve">{label}</text>"""
    return svg(w, h, BASE_CSS, GLOW.format(12), body, f"Contact: {EMAIL}")


# ── MAIN ──────────────────────────────────────────────────

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, render in {"banner": banner, "terminal": terminal, "footer": footer}.items():
        (OUT / f"{name}.svg").write_text(render(), encoding="utf-8", newline="\n")
        print(f"{name}.svg  {(OUT / f'{name}.svg').stat().st_size // 1024} KB")
