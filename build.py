# ─────────────────────────────────────────────────────
#   project · Official8B1T
#   module  · build.py — renders profile SVGs with embedded font subsets
#   author  · Jiří "8B1T" Lhotský
# ─────────────────────────────────────────────────────

import base64
import re
import textwrap
import urllib.parse
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).parent / "assets"

# ── TOKENS · Design\8B1T\8B1T.md v2.1 ─────────────────────

VOID, CARBON, ASH = "#080808", "#161616", "#242424"
SIGNAL = "#FF0000"
BONE, PURE, SMOKE = "#F5F2EF", "#FFFFFF", "#818181"

W = 1200
K = W / 846  # panel units per rendered px in GitHub's README column


def px(n):
    return round(n * K, 1)


R1, R2 = px(4), px(8)  # --r-1 buttons, --r-2 cards

# ── FONTS ─────────────────────────────────────────────────

# NOTE · JetBrains Mono is SIL OFL 1.1 — embedding subsets in documents is permitted
# ASCII + Czech, so text edits never need a new subset
CHARSET = "".join(map(chr, range(32, 127))) + "ěščřžýáíéúůťďňĚŠČŘŽÝÁÍÉÚŮŤĎŇ·—→"
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


BASE_CSS = f"""{font_face("JetBrains Mono", 400, "M")}{font_face("JetBrains Mono", 700, "M")}
.m{{font-family:M,'JetBrains Mono',Consolas,monospace}}
.pulse{{animation:pulse 2.5s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:.45}}50%{{opacity:.65}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}"""

HAIRLINE = f'stroke="{SMOKE}" stroke-width="1" vector-effect="non-scaling-stroke" fill="none"'


# card shell: clipped to --r-2, 1px --ash edge that stays 1px however the panel scales
def svg(h, css, defs, body, label):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" role="img" aria-label="{escape(label, {'"': "&quot;"})}">
<style>{css}</style>
<defs>{defs}<clipPath id="card"><rect width="{W}" height="{h}" rx="{R2}"/></clipPath></defs>
<g clip-path="url(#card)">
{body}
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{h - 1}" rx="{R2}" fill="none" stroke="{ASH}" vector-effect="non-scaling-stroke"/>
</svg>
"""


# ── TERMINAL · Windows Terminal running PowerShell ────────

PROMPT = "C:\\8B1T> "
FS, LH = 18, 26
CW = FS * 0.6  # JetBrains Mono advance is exactly 0.6em
X0 = px(16)
COLS = int((W - 2 * X0) // CW)  # console width in characters


# PowerShell-ish highlighting: commands --signal, parameters and operators --smoke, strings --bone
def cmd(line):
    parts = []
    for tok in re.findall(r"'[^']*'|\S+", line):
        color = SMOKE if tok == "|" or tok.startswith("-") else BONE if tok.startswith("'") else SIGNAL
        parts.append((tok, color))
    return [("cmd", parts)]


def out(text, color=BONE):
    return [("text", chunk, color, False) for chunk in textwrap.wrap(text, COLS)]


# wrap a comma list between items, never inside one ("Azure AD" stays whole)
def pack(text, width):
    lines = [""]
    for item in text.split(", "):
        joined = f"{lines[-1]}, {item}" if lines[-1] else item
        if len(joined) + 1 > width and lines[-1]:  # +1 keeps room for the trailing comma
            lines[-1] += ","
            lines.append(item)
        else:
            lines[-1] = joined
    assert all(len(line) <= width for line in lines), f"an item is wider than the column: {text}"
    return lines


# Format-Table -Wrap: autosized columns, headers + dashes, last column wraps under itself
def table(headers, rows):
    widths = [max(len(r[i]) for r in (headers, *rows)) for i in range(len(headers))]
    lead = sum(widths[:-1]) + len(widths) - 1
    line = lambda cells: " ".join(c.ljust(w) for c, w in zip(cells, widths)).rstrip()
    items = [("blank",), ("text", line(headers), SIGNAL, True), ("text", line(["-" * len(h) for h in headers]), SIGNAL, True)]
    for r in rows:
        for i, chunk in enumerate(pack(r[-1], COLS - lead)):
            items.append(("text", (line(r[:-1]) if i == 0 else "").ljust(lead) + chunk, BONE, False))
    return items + [("blank",)]


# NOTE · content mirrors the CV minus private details (phone, birth year, district, photo)
SCRIPT = [
    *out("PowerShell 7.6.6"), ("blank",),
    *cmd("whoami"),
    *out('Jiří "8B1T" Lhotský'), ("blank",),
    *cmd("Get-Experience"),
    *table(["Period", "Role", "Type", "Company"], [
        ["2026 → now", "IT services", "freelance", "Raw Planet s.r.o."],
        ["2026 → now", "IT services", "contract", "TechLines.cz s.r.o."],
        ["2025 → now", "IT services", "contract", "VUMS LEGEND, spol. s r.o."],
        ["2023 → 2025", "Process technician", "full-time", "Continental Automotive Czech Republic s.r.o."],
        ["2021 → 2023", "Mechanic / electrician", "internship", "GREEN Center s.r.o."],
    ]),
    *cmd("Get-Education"),
    *table(["Period", "Program", "Type", "Institution"], [
        ["2019 → 2023", "Avionics technician", "maturita", "Secondary School of Civil Aviation, Prague"],
        ["2025", "Python · Django · React", "course", "ITnetwork"],
        ["2025", "AI & big data specialist", "course", "ITnetwork"],
        ["2022", "English B2 (FCE)", "cert", "Cambridge English"],
    ]),
    *cmd("Get-Skills | Format-Table -Wrap"),
    *table(["Category", "Skills"], [
        ["Virtualization", "ESXi, iDRAC, VMware, Hyper-V, VirtualBox, Kubernetes, Docker, Podman, Ceph, Headlamp"],
        ["OS", "Windows Server, Windows XP-11, RHEL, Rocky Linux, CentOS, Ubuntu, Arch Linux, Kali Linux, "
               "BlackArch, BSD / Unix, macOS, Android, iOS"],
        ["Security", "FortiGate, FortiAnalyzer, FortiClient, ESET Protect, ESET Inspect, Keeper, Valimail, Azure AD"],
        ["Operations", "Zabbix, Veeam VBR, Veeam One, Synology NAS, Patch My PC, Apple Business, HCL Domino, HCL Notes"],
        ["Code", "PowerShell, Python, JavaScript, HTML / CSS, Django, React, PostgreSQL, SQLite"],
        ["DevOps", "Git, Gitea, CVS, Nexus, Redmine, Jira"],
        ["AI", "AI & big data, advanced AI via CLIs"],
        ["Other", "SAP, MS Office, Photoshop, Canva, video editing, photo editing"],
    ]),
    *cmd("Get-Language"),
    *table(["Language", "Level"], [["Czech", "Excellent"], ["English", "Advanced (B2)"]]),
    *cmd("Get-Strengths | Join-String -Separator ', '"),
    *out("Problem solving, Critical thinking, Reliability, Independence, Working under pressure, "
         "Teamwork, Clear communication, Leadership, Eagerness to learn"),
    ("blank",),
    ("prompt",),
]


# Windows Terminal tab strip: one active tab, new-tab + dropdown, caption buttons
def chrome(tb):
    tx, ty, tw = px(8), px(8), px(232)
    r, bottom = px(8), tb
    tab = f"M{tx} {bottom}V{ty + r}Q{tx} {ty} {tx + r} {ty}H{tx + tw - r}Q{tx + tw} {ty} {tx + tw} {ty + r}V{bottom}Z"
    cy = ty + (bottom - ty) / 2
    g = px(5)  # half glyph size

    def x_mark(cx, s):
        return f'<path d="M{cx - s} {cy - s}L{cx + s} {cy + s}M{cx + s} {cy - s}L{cx - s} {cy + s}" {HAIRLINE}/>'

    nx = tx + tw + px(20)
    caption = [W - px(23), W - px(69), W - px(115)]  # close · maximize · minimize, 46px buttons
    return f"""<rect width="{W}" height="{tb}" fill="{CARBON}"/>
<path d="{tab}" fill="{VOID}"/>
<text class="m" x="{tx + px(12)}" y="{cy + px(4)}" font-size="{px(12)}" font-weight="700" fill="{SIGNAL}">&gt;_</text>
<text class="m" x="{tx + px(36)}" y="{cy + px(4)}" font-size="{px(12)}" fill="{BONE}">PowerShell</text>
{x_mark(tx + tw - px(18), px(4))}
<path d="M{nx - g} {cy}H{nx + g}M{nx} {cy - g}V{cy + g}" {HAIRLINE}/>
<path d="M{nx + px(20)} {cy - px(2)}l{px(4)} {px(4)}l{px(4)} {-px(4)}" {HAIRLINE}/>
{x_mark(caption[0], g)}
<rect x="{caption[1] - g}" y="{cy - g}" width="{2 * g}" height="{2 * g}" {HAIRLINE}/>
<path d="M{caption[2] - g} {cy}H{caption[2] + g}" {HAIRLINE}/>"""


def terminal():
    css = BASE_CSS + """
.s{animation:show .01s linear both}
@keyframes show{from{opacity:0}to{opacity:1}}
.cover{opacity:0;animation-name:type;animation-fill-mode:both}
@keyframes type{from{opacity:1;transform:translateX(0)}99.9%{opacity:1;transform:translateX(var(--w))}to{opacity:0;transform:translateX(var(--w))}}
.cur{opacity:0;animation-name:cur;animation-fill-mode:backwards}
@keyframes cur{from,to{opacity:1}}
.blink{animation:blink 1s step-end infinite}
@keyframes blink{50%{opacity:0}}"""
    tb = px(40)
    prompt = f'<tspan fill="{BONE}">{escape(PROMPT)}</tspan>'
    px0 = X0 + len(PROMPT) * CW
    bar = f'width="{px(2)}" height="{FS + 4}" fill="{SIGNAL}"'  # Windows Terminal default bar cursor
    rows, y, t = [], tb + px(16) + FS, 0.3

    for kind, *arg in SCRIPT:
        if kind == "blank":
            y += LH
            continue
        if kind == "cmd":
            text = " ".join(s for s, _ in arg[0])
            spans = " ".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in arg[0])
            dur = len(text) * 0.04
            # a void cover slides right in steps and the cursor rides its left edge = typing
            rows.append(f"""<g class="s" style="animation-delay:{t:.2f}s">
  <text class="m" x="{X0}" y="{y}" font-size="{FS}" xml:space="preserve">{prompt}{spans}</text>
  <g class="cover" style="--w:{len(text) * CW:.1f}px;animation-duration:{dur:.2f}s;animation-timing-function:steps({len(text)},end);animation-delay:{t + 0.25:.2f}s">
    <rect x="{px0:.1f}" y="{y - FS}" width="{len(text) * CW + 24:.1f}" height="{FS + 8}" fill="{VOID}"/>
    <rect class="cur" x="{px0:.1f}" y="{y - FS + 1}" {bar} style="animation-duration:{dur + 0.45:.2f}s;animation-delay:{t:.2f}s"/>
  </g>
</g>""")
            t += dur + 0.45
        elif kind == "text":
            text, color, bold = arg
            assert len(text) <= COLS, f"line overflows the console: {text}"
            weight = ' font-weight="700"' if bold else ""
            rows.append(f'<text class="m s" x="{X0}" y="{y}" font-size="{FS}" fill="{color}"{weight} '
                        f'style="animation-delay:{t:.2f}s" xml:space="preserve">{escape(text)}</text>')
            t += 0.04
        elif kind == "prompt":
            rows.append(f"""<g class="s" style="animation-delay:{t:.2f}s">
  <text class="m" x="{X0}" y="{y}" font-size="{FS}" xml:space="preserve">{prompt}</text>
  <rect class="blink" x="{px0:.1f}" y="{y - FS + 1}" {bar}/>
</g>""")
        y += LH

    h = round(y - LH + px(16))
    body = f'<rect width="{W}" height="{h}" fill="{VOID}"/>\n{chrome(tb)}\n' + "\n".join(rows)
    return svg(h, css, "", body, alt_terminal())


def alt_terminal():
    lines = [PROMPT + " ".join(s for s, _ in a[0]) if k == "cmd" else a[0] for k, *a in SCRIPT if k in ("cmd", "text")]
    return " / ".join(lines)


# ── CONTACT · card + primary button ───────────────────────

EMAIL = "8b1t.biz@proton.me"


def contact():
    fs, ls = px(13), px(13) * 0.2
    label = f"{EMAIL.upper()}  →"
    bw = len(label) * (fs * 0.6 + ls) - ls + 2 * px(24)
    bh, bx = px(44), (W - bw) / 2
    top = px(32)
    by = top + px(12) + px(16)
    h = round(by + bh + px(32))
    body = f"""<rect width="{W}" height="{h}" fill="{CARBON}"/>
<text class="m" x="{W / 2}" y="{top + px(10)}" text-anchor="middle" font-size="{px(12)}" letter-spacing="{px(12) * 0.2:.1f}" fill="{SMOKE}"><tspan fill="{SIGNAL}">//</tspan> GET IN TOUCH</text>
<rect class="pulse" x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh}" rx="{R1}" fill="{SIGNAL}" filter="url(#glow)"/>
<rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh}" rx="{R1}" fill="{SIGNAL}"/>
<text class="m" x="{W / 2}" y="{by + bh / 2 + fs * 0.36:.1f}" text-anchor="middle" font-size="{fs}" font-weight="700" letter-spacing="{ls:.1f}" fill="{VOID}" xml:space="preserve">{label}</text>"""
    glow = f'<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{px(12)}"/></filter>'
    return svg(h, BASE_CSS, glow, body, f"Contact: {EMAIL}")


# ── MAIN ──────────────────────────────────────────────────

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, render in {"terminal": terminal, "contact": contact}.items():
        (OUT / f"{name}.svg").write_text(render(), encoding="utf-8", newline="\n")
        print(f"{name}.svg  {(OUT / f'{name}.svg').stat().st_size // 1024} KB")
