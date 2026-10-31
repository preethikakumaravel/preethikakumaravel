"""
Pixel-art profile assets: hero banner, RPG player card, and section headers.

Usage:
    python gen_pixel.py --user YOUR_GITHUB_LOGIN --name PREETHS --player PREETHIKA
Set GITHUB_TOKEN for real stats (otherwise demo numbers). Standard library only.
"""
import argparse
import datetime
import json
import math
import os
import random
import urllib.request

from gen_graph import DARK, FONT, COLS, ROWS, fake_data, fetch_real, keyframes, name_mask

FONT = dict(FONT)
FONT.update({
    ":": ".|#|.|.|.|#|.",
    "/": "....#|...#.|...#.|..#..|.#...|.#...|#....",
    ">": "#...|.#..|..#.|...#|..#.|.#..|#...",
    "<": "...#|..#.|.#..|#...|.#..|..#.|...#",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "#": ".#.#.|.#.#.|#####|.#.#.|#####|.#.#.|.#.#.",
    "'": "#|#|.|.|.|.|.",
    ",": ".|.|.|.|.|#|#",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..",
    "*": ".....|#.#.#|.###.|#####|.###.|#.#.#|.....",
    "=": ".....|.....|#####|.....|#####|.....|.....",
    "%": "##..#|##..#|...#.|..#..|.#...|#..##|#..##",
    "♥": ".#.#.|#####|#####|#####|.###.|..#..|.....",
})

W = 840
GREEN, GREEN_DK, GOLD, INK, MUTED, PANEL = "#39d353", "#0e4429", "#ffd33d", "#e6edf3", "#8b949e", "#0d1117"


# ---------- pixel primitives ----------

def text_width(s, scale):
    glyphs = [FONT[c] for c in s.upper() if c in FONT]
    units = sum(len(g.split("|")[0]) for g in glyphs) + max(len(glyphs) - 1, 0)
    return units * scale


def text_path(s, x, y, scale):
    """Pixel text as one SVG path `d`, merging horizontal runs."""
    d = []
    for ch in s.upper():
        if ch not in FONT:
            continue
        rows = FONT[ch].split("|")
        for r, line in enumerate(rows):
            c = 0
            while c < len(line):
                if line[c] == "#":
                    run = 1
                    while c + run < len(line) and line[c + run] == "#":
                        run += 1
                    d.append(f"M{x + c * scale},{y + r * scale}h{run * scale}v{scale}h-{run * scale}z")
                    c += run
                else:
                    c += 1
        x += (len(rows[0]) + 1) * scale
    return "".join(d)


def text(s, x, y, scale, fill, extra=""):
    return f'<path d="{text_path(s, x, y, scale)}" fill="{fill}" {extra}/>'


def sprite(rows, palette, x, y, s, outline=None):
    """Render a char-grid sprite; optional 1-pixel outline around filled cells."""
    by_color = {}
    filled = {(c, r) for r, line in enumerate(rows) for c, ch in enumerate(line) if ch != "."}
    if outline:
        ring = {(c + dc, r + dr) for c, r in filled for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))} - filled
        by_color[outline] = [f"M{x + c * s},{y + r * s}h{s}v{s}h-{s}z" for c, r in ring]
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch != ".":
                by_color.setdefault(palette[ch], []).append(f"M{x + c * s},{y + r * s}h{s}v{s}h-{s}z")
    return "".join(f'<path d="{"".join(p)}" fill="{col}"/>' for col, p in by_color.items())


def svg(w, h, body, style=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'shape-rendering="crispEdges"><style>{style}'
            f'@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>{body}</svg>')


# ---------- the cat (black & white, purple headphones) ----------

CAT = [
    "...HHHHHHHH...",
    "..H........H..",
    ".HK........KH.",
    ".HKK......KKH.",
    "HHKKKKKKKKKKHH",
    "HHKWWKKKKWWKHH",
    "HHKWGWKKWGWKHH",
    "HHKWWWPPWWWKHH",
    "..KKWWWWWWKK..",
    "...KKKKKKKK...",
    "..KKWWWWWWKK.K",
    "..KKWWWWWWKKK.",
    "..KKKWWWWKKK..",
]
LEGS_A = ["..KK......KK.."]
LEGS_B = ["....KK..KK...."]
CAT_PAL = {"H": "#a371f7", "K": "#1e1e26", "W": "#f4f4f4", "G": GREEN, "P": "#ff7aa2"}
CAT_OUTLINE = "#c9d1d9"


def cat(x, y, s):
    body = sprite(CAT + [".............." ], CAT_PAL, x, y, s, outline=CAT_OUTLINE)
    a = sprite(["." * 14] * 13 + LEGS_A, CAT_PAL, x, y, s, outline=None)
    b = sprite(["." * 14] * 13 + LEGS_B, CAT_PAL, x, y, s, outline=None)
    return f'{body}<g class="legA">{a}</g><g class="legB">{b}</g>'


# ---------- hero ----------

def hero(name, player, subtitle):
    H = 300
    rnd = random.Random(42)
    parts = []
    # stepped sky bands
    for i, col in enumerate(["#070a14", "#0b1020", "#10172d", "#16203d", "#1c2950"]):
        parts.append(f'<rect x="0" y="{i * 50}" width="{W}" height="{50 if i < 4 else 60}" fill="{col}"/>')
    # stars
    for i in range(55):
        sx, sy, sz = rnd.randrange(0, W, 4), rnd.randrange(0, 200, 4), rnd.choice((2, 2, 4))
        parts.append(f'<rect x="{sx}" y="{sy}" width="{sz}" height="{sz}" fill="#fff" class="tw t{i % 3}"/>')
    # pixel moon
    mx, my, mr, g = 740, 56, 26, 4
    for yy in range(-mr, mr, g):
        for xx in range(-mr, mr, g):
            if xx * xx + yy * yy <= mr * mr:
                crater = (xx, yy) in {(-8, -4), (-4, -4), (8, 8), (12, 8), (4, -16)}
                shade = xx + yy > 14
                col = "#cdbf94" if crater else ("#e8dcb2" if shade else "#f7efd2")
                parts.append(f'<rect x="{mx + xx}" y="{my + yy}" width="{g}" height="{g}" fill="{col}"/>')
    # two mountain layers (random-walk silhouettes on an 8px grid)
    for col, base, rough in (("#1a2445", 200, 10), ("#222e57", 220, 8)):
        h = base
        for x in range(0, W, 8):
            h = max(base - 28, min(base + 16, h + rnd.choice((-rough, -8, 0, 0, 8, rough))))
            parts.append(f'<rect x="{x}" y="{h}" width="8" height="{252 - h}" fill="{col}"/>')
    # ground: grass + dirt with speckles
    parts.append(f'<rect x="0" y="252" width="{W}" height="8" fill="#3fb950"/>')
    parts.append(f'<rect x="0" y="260" width="{W}" height="4" fill="#238636"/>')
    parts.append(f'<rect x="0" y="264" width="{W}" height="{H - 264}" fill="#5c3a21"/>')
    for x in range(0, W, 8):
        if rnd.random() < 0.35:
            parts.append(f'<rect x="{x}" y="252" width="8" height="4" fill="#56d364"/>')
        if rnd.random() < 0.3:
            parts.append(f'<rect x="{x}" y="{rnd.randrange(268, H - 4, 4)}" width="4" height="4" fill="#7a4e2d"/>')
    # title: each letter bobs on its own beat
    s = 8
    tx = (W - text_width(name, s)) // 2
    for i, ch in enumerate(name.upper()):
        if ch not in FONT:
            continue
        g_ = (f'<g class="bob" style="animation-delay:{i * 0.12:.2f}s">'
              f'{text(ch, tx + s, 34 + s, s, GREEN_DK)}{text(ch, tx, 34, s, GREEN)}</g>')
        parts.append(g_)
        tx += text_width(ch, s) + s
    # subtitle lines
    for txt, y, col in ((f"PLAYER 1 : {player}", 120, INK), (subtitle, 142, MUTED)):
        parts.append(text(txt, (W - text_width(txt, 2)) // 2, y, 2, col))
    press = "> PRESS START"
    parts.append(text(press, (W - text_width(press, 3)) // 2, 178, 3, GOLD, 'class="blink"'))
    # walking cat
    parts.append(f'<g class="walk">{cat(0, 252 - 14 * 4, 4)}</g>')
    style = (
        ".tw{animation:tw 2.4s steps(1) infinite}.t1{animation-delay:.8s}.t2{animation-delay:1.6s}"
        "@keyframes tw{0%,60%{opacity:1}61%,100%{opacity:.25}}"
        ".bob{animation:bob 1.4s steps(1) infinite}"
        "@keyframes bob{0%,50%{transform:translateY(0)}51%,100%{transform:translateY(-8px)}}"
        ".blink{animation:bl 1.1s steps(1) infinite}@keyframes bl{0%,55%{opacity:1}56%,100%{opacity:0}}"
        f".walk{{animation:walk 14s linear infinite}}@keyframes walk{{from{{transform:translateX(-60px)}}to{{transform:translateX({W + 20}px)}}}}"
        ".legA{animation:la .36s steps(1) infinite}.legB{animation:la .36s steps(1) infinite reverse}"
        "@keyframes la{0%,49%{opacity:1}50%,100%{opacity:0}}"
    )
    return svg(W, H, "".join(parts), style)


# ---------- player card ----------

def pixel_frame(w, h, col):
    b, n = 4, 4  # border thickness, corner notch
    return (f'<rect x="{n}" y="0" width="{w - 2 * n}" height="{b}" fill="{col}"/>'
            f'<rect x="{n}" y="{h - b}" width="{w - 2 * n}" height="{b}" fill="{col}"/>'
            f'<rect x="0" y="{n}" width="{b}" height="{h - 2 * n}" fill="{col}"/>'
            f'<rect x="{w - b}" y="{n}" width="{b}" height="{h - 2 * n}" fill="{col}"/>'
            f'<rect x="{b}" y="{b}" width="{b}" height="{b}" fill="{col}"/>'
            f'<rect x="{w - 2 * b}" y="{b}" width="{b}" height="{b}" fill="{col}"/>'
            f'<rect x="{b}" y="{h - 2 * b}" width="{b}" height="{b}" fill="{col}"/>'
            f'<rect x="{w - 2 * b}" y="{h - 2 * b}" width="{b}" height="{b}" fill="{col}"/>')


def bar(x, y, frac, blocks, col, bs=12):
    on = round(frac * blocks)
    return "".join(
        f'<rect x="{x + i * (bs + 3)}" y="{y}" width="{bs}" height="{bs}" fill="{col if i < on else "#21262d"}"/>'
        for i in range(blocks)
    )


def player_card(stats, player):
    H = 270
    p = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PANEL}"/>', pixel_frame(W, H, GREEN)]
    xp = stats["total"]
    level = int(math.sqrt(xp / 2)) + 1
    lo, hi = 2 * (level - 1) ** 2, 2 * level ** 2
    rows = [
        ("PLAYER", player),
        ("LEVEL", f"{level}"),
        ("XP", f"{xp}"),
        ("QUESTS", f"{stats['repos']} REPOS"),
        ("STARS", f"{stats['stars']}"),
        ("STREAK", f"{stats['streak']} DAYS"),
    ]
    y = 36
    p.append(text("STATS", 40, y - 4, 3, GOLD))
    y += 36
    for label, value in rows:
        p.append(text(label, 40, y, 2, MUTED))
        p.append(text(value, 170, y, 2, INK))
        if label == "XP":
            p.append(bar(250, y, (xp - lo) / max(hi - lo, 1), 8, GREEN, 10))
        y += 28
    p.append(text("HP", 40, y, 2, MUTED))
    for i in range(5):  # hearts = hours of sleep, roughly
        p.append(text("♥", 170 + i * 16, y, 2, "#f85149" if i < 3 else "#30363d"))
    # skills column
    sx = 460
    p.append(text("SKILLS", sx, 32, 3, GOLD))
    langs = stats["langs"][:6]
    top = langs[0][1] if langs else 1
    for i, (lname, size, color) in enumerate(langs):
        ly = 72 + i * 34
        p.append(text(lname[:10], sx, ly, 2, INK))
        p.append(bar(sx + 140, ly - 1, size / top, 12, color or GREEN))
    p.append(f'<rect x="{sx - 30}" y="28" width="4" height="{H - 56}" fill="#21262d"/>')
    return svg(W, H, "".join(p))


def header(label, icon="*"):
    H = 44
    p = [text(icon, 0, 10, 3, GOLD), text(label, 30, 10, 3, GREEN)]
    x0 = 30 + text_width(label, 3) + 18
    p.append("".join(f'<rect x="{x}" y="22" width="6" height="6" fill="#30363d"/>' for x in range(x0, W, 14)))
    return svg(W, H, "".join(p))


def world_map(grid, total, name):
    """Contribution graph in a pixel frame; squares morph into the name and the cat hops on top."""
    cell, gap, px, top = 12, 3, 24, 92
    H = top + ROWS * (cell + gap) + 30
    on = name_mask(name)
    p = [f'<rect x="0" y="0" width="{W}" height="{H}" fill="{PANEL}"/>', pixel_frame(W, H, "#30363d")]
    p.append(text(f"XP LOG : {total} CONTRIBUTIONS", px, 20, 2, GOLD))
    for c in range(COLS):
        for r in range(ROWS):
            lvl = grid[c][r]
            if lvl is None:
                continue
            state = "on" if (c, r) in on else "off"
            p.append(f'<rect x="{px + c * (cell + gap)}" y="{top + r * (cell + gap)}" width="{cell}" height="{cell}" '
                     f'class="l{lvl}" style="animation-name:k{lvl}{state};animation-delay:{(c + r) * 0.035:.3f}s"/>')
    # cat lands on the first letter while the name is showing
    first = min(c for c, _ in on)
    p.append(f'<g class="perch">{cat(px + first * (cell + gap) - 8, top - 15 * 3, 3)}</g>')
    static = "".join(f".l{i}{{fill:{DARK[i]}}}" for i in range(5))
    style = (
        f"rect[class^=l]{{animation-duration:10s;animation-iteration-count:infinite;animation-fill-mode:both;"
        f"animation-timing-function:steps(1)}}{static}{keyframes(DARK)}"
        ".perch{opacity:0;animation:perch 10s steps(1) infinite}"
        "@keyframes perch{0%,44%{opacity:0;transform:translateY(-30px)}45%,47%{opacity:1;transform:translateY(-10px)}"
        "48%,70%{opacity:1;transform:translateY(0)}71%,100%{opacity:0;transform:translateY(0)}}"
        ".legA{animation:la .5s steps(1) infinite}.legB{animation:la .5s steps(1) infinite reverse}"
        "@keyframes la{0%,49%{opacity:1}50%,100%{opacity:0}}"
    )
    return svg(W, H, "".join(p), style)


# ---------- data ----------

def fetch_stats(user, token):
    query = """query($login:String!){user(login:$login){
      contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}
      repositories(ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC,first:100){totalCount nodes{stargazerCount
        languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    u = json.load(urllib.request.urlopen(req))["data"]["user"]
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    today = datetime.date.today().isoformat()
    streak = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            streak += 1
        elif d["date"] != today:  # an empty today doesn't break the streak yet
            break
    langs = {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            prev = langs.get(n, (0, e["node"]["color"]))
            langs[n] = (prev[0] + e["size"], e["node"]["color"])
    return {
        "total": cal["totalContributions"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "streak": streak,
        "langs": sorted(((n, s, c) for n, (s, c) in langs.items()), key=lambda t: -t[1]),
    }


DEMO = {"total": 19, "repos": 4, "stars": 1, "streak": 2,
        "langs": [("TypeScript", 900, "#3178c6"), ("HTML", 600, "#e34c26"), ("Python", 400, "#3572A5"),
                  ("CSS", 200, "#663399"), ("JavaScript", 120, "#f1e05a")]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--name", required=True, help="big title text")
    ap.add_argument("--player", required=True)
    ap.add_argument("--subtitle", default="CLASS : BUILDER  -  STATUS : CONFUSED BUT OKAY")
    ap.add_argument("--out", default="assets")
    a = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    stats = fetch_stats(a.user, token) if token else DEMO
    grid, total = fetch_real(a.user, token) if token else fake_data()
    os.makedirs(a.out, exist_ok=True)
    files = {
        "hero.svg": hero(a.name, a.player, a.subtitle),
        "player-card.svg": player_card(stats, a.player),
        "world-map.svg": world_map(grid, total, a.name),
        "h-stats.svg": header("PLAYER STATS", "♥"),
        "h-map.svg": header("WORLD MAP", ">"),
        "h-inventory.svg": header("INVENTORY", "+"),
        "h-quests.svg": header("QUEST LOG", "*"),
        "h-continue.svg": header("CONTINUE?", "?"),
    }
    for fname, content in files.items():
        with open(os.path.join(a.out, fname), "w", encoding="utf-8") as f:
            f.write(content)
    print(f"wrote {len(files)} files to {a.out}/ ({'real' if token else 'demo'} data)")


if __name__ == "__main__":
    main()
