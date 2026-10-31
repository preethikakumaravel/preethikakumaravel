"""
Generate an animated SVG that looks like a GitHub contribution graph:
your real graph -> squares ripple into your NAME -> back to the real graph.

Usage:
    python gen_graph.py --user YOUR_GITHUB_LOGIN --name YOURNAME
Set GITHUB_TOKEN to pull your real contribution data (otherwise random demo data).
No dependencies beyond the standard library.
"""
import argparse
import json
import os
import random
import urllib.request

COLS, ROWS = 53, 7
CELL, GAP = 11, 3
PAD_X, PAD_TOP, PAD_BOTTOM = 34, 38, 30

LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]

# 5x7 pixel font
FONT = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.####",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": "#####|..#..|..#..|..#..|..#..|..#..|#####",
    "J": "..###|...#.|...#.|...#.|...#.|#..#.|.##..",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#",
    "N": "#...#|##..#|##..#|#.#.#|#..##|#..##|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|##.##|#...#",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "####.|....#|....#|.###.|....#|....#|####.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": ".###.|#....|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|....#|.###.",
    "-": ".....|.....|.....|.###.|.....|.....|.....",
    "!": "#|#|#|#|#|.|#",
    ".": ".|.|.|.|.|.|#",
    " ": "...|...|...|...|...|...|...",
}


def name_mask(text):
    """Return a set of (col, row) cells that spell `text`, centred in the grid."""
    glyphs = [FONT[ch].split("|") for ch in text.upper() if ch in FONT]
    width = sum(len(g[0]) for g in glyphs) + max(len(glyphs) - 1, 0)
    if width > COLS:
        raise SystemExit(f"'{text}' is {width} columns wide; max is {COLS}. Use a shorter name.")
    x = (COLS - width) // 2
    on = set()
    for g in glyphs:
        for r, line in enumerate(g):
            for c, px in enumerate(line):
                if px == "#":
                    on.add((x + c, r))
        x += len(g[0]) + 1
    return on


LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def fetch_real(user, token):
    query = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
        totalContributions weeks{contributionDays{weekday contributionLevel}}}}}}"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": user}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    grid = [[None] * ROWS for _ in range(COLS)]
    weeks = cal["weeks"][-COLS:]
    offset = COLS - len(weeks)
    for wi, week in enumerate(weeks):
        for day in week["contributionDays"]:
            grid[offset + wi][day["weekday"]] = LEVELS[day["contributionLevel"]]
    return grid, cal["totalContributions"]


def fake_data():
    rnd = random.Random(7)
    grid = [[rnd.choices([0, 1, 2, 3, 4], [35, 30, 18, 11, 6])[0] for _ in range(ROWS)] for _ in range(COLS)]
    return grid, sum(sum(col) for col in grid) * 2


def keyframes(palette):
    # 0-28% real graph, ripple into name, hold 38-72%, ripple back.
    out = []
    for lvl in range(5):
        for state, target in (("on", 4), ("off", 0)):
            out.append(
                f"@keyframes k{lvl}{state}{{0%,28%{{fill:{palette[lvl]}}}"
                f"38%,72%{{fill:{palette[target]}}}82%,100%{{fill:{palette[lvl]}}}}}"
            )
    return "".join(out)


def build_svg(grid, total, name, duration=10):
    on = name_mask(name)
    w = PAD_X + COLS * (CELL + GAP) + 6
    h = PAD_TOP + ROWS * (CELL + GAP) + PAD_BOTTOM
    rects = []
    for c in range(COLS):
        for r in range(ROWS):
            lvl = grid[c][r]
            if lvl is None:  # future days in the current week
                continue
            state = "on" if (c, r) in on else "off"
            x, y = PAD_X + c * (CELL + GAP), PAD_TOP + r * (CELL + GAP)
            # diagonal ripple: delay grows with column + row
            delay = (c + r) * 0.035
            rects.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'class="l{lvl}" style="animation-name:k{lvl}{state};animation-delay:{delay:.3f}s"/>'
            )
    day_labels = "".join(
        f'<text x="{PAD_X - 8}" y="{PAD_TOP + r * (CELL + GAP) + 9}" text-anchor="end">{d}</text>'
        for r, d in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    legend_x = w - 5 * (CELL + GAP) - 72
    legend = "".join(
        f'<rect x="{legend_x + 30 + i * (CELL + GAP)}" y="{h - 20}" width="{CELL}" height="{CELL}" rx="2" class="s{i}"/>'
        for i in range(5)
    )
    static = "".join(f".l{i},.s{i}{{fill:{LIGHT[i]}}}" for i in range(5))
    static_dark = "".join(f".l{i},.s{i}{{fill:{DARK[i]}}}" for i in range(5))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
<style>
text{{font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;fill:#57606a}}
.title{{font-size:14px;fill:#1f2328}}
rect{{animation-duration:{duration}s;animation-iteration-count:infinite;animation-timing-function:ease-in-out;animation-fill-mode:both}}
{static}{keyframes(LIGHT)}
@media (prefers-color-scheme:dark){{
text{{fill:#8b949e}}.title{{fill:#e6edf3}}
{static_dark}{keyframes(DARK)}
}}
@media (prefers-reduced-motion:reduce){{rect{{animation:none}}}}
</style>
<text x="{PAD_X}" y="20" class="title">{total:,} contributions in the last year</text>
{day_labels}
{''.join(rects)}
<text x="{legend_x}" y="{h - 11}">Less</text>{legend}<text x="{legend_x + 30 + 5 * (CELL + GAP) + 4}" y="{h - 11}">More</text>
</svg>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True, help="GitHub login")
    ap.add_argument("--name", required=True, help="text to spell (max ~8 letters)")
    ap.add_argument("--out", default="assets/contrib-name.svg")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    grid, total = fetch_real(args.user, token) if token else fake_data()
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(build_svg(grid, total, args.name))
    print(f"wrote {args.out} ({'real' if token else 'demo'} data)")


if __name__ == "__main__":
    main()
