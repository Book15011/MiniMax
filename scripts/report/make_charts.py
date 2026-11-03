"""Draw the README charts (docs/assets/charts/<name>.light.svg and .dark.svg) from docs/assets/data/.

Standard library only, so anyone with the repo can redraw them:

    python3 scripts/report/make_charts.py
"""
from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from xml.sax.saxutils import escape

DATA = "docs/assets/data"
OUT = "docs/assets/charts"
FONT = "system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"

LIGHT = dict(surface="#fcfcfb", ink="#0b0b0b", ink2="#52514e", muted="#6f6d68", grid="#e1e0d9", axis="#c3c2b7",
             border="#e1e0d9", other="#b4b2a9", s1="#2a78d6", s2="#eb6834", s3="#1baf7a", neg="#e34948", name="light")
DARK = dict(surface="#1a1a19", ink="#f0efec", ink2="#c3c2b7", muted="#a3a29a", grid="#2c2c2a", axis="#383835",
            border="#2c2c2a", other="#5f5e58", s1="#3987e5", s2="#d95926", s3="#199e70", neg="#e66767", name="dark")


def read(name: str) -> list[dict]:
    with open(os.path.join(DATA, name), newline="") as f:
        return list(csv.DictReader(f))


def pct(v: float, digits: int = 1) -> str:
    s = f"{abs(v) * 100:.{digits}f}%"
    return ("−" if v < 0 else "+") + s


class Svg:
    def __init__(self, t: dict, w: int, h: int, title: str, sub: str, source: str, desc: str):
        self.t, self.w, self.h = t, w, h
        self.title, self.desc = title, desc
        self.p = [f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8" fill="{t["surface"]}" stroke="{t["border"]}"/>']
        self.text(24, 32, title, 17, "ink", weight=600)
        self.text(24, 53, sub, 12.5, "ink2")
        self.text(24, h - 14, source, 11, "muted")

    def text(self, x, y, s, size=12, color="ink2", anchor="start", weight=None, tabular=False):
        w = f' font-weight="{weight}"' if weight else ""
        n = ' style="font-variant-numeric:tabular-nums"' if tabular else ""
        self.p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{self.t[color]}" text-anchor="{anchor}"{w}{n}>{escape(str(s))}</text>')

    def line(self, x1, y1, x2, y2, color="grid", width=1):
        self.p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{self.t[color]}" stroke-width="{width}"/>')

    def poly(self, pts, color, width=2):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        self.p.append(f'<polyline points="{d}" fill="none" stroke="{self.t[color]}" stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"/>')

    def dot(self, x, y, color, r=4):
        self.p.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{self.t[color]}" stroke="{self.t["surface"]}" stroke-width="2"/>')

    def hbar(self, x0, x1, y, h, color, r=4, both=False):
        """A horizontal bar, rounded at its data end (x1), or at both ends for a range."""
        sign = 1 if x1 >= x0 else -1
        r = min(r, abs(x1 - x0), h / 2)
        r0 = r if both else 0
        d = (f"M{x0 + sign * r0:.1f},{y:.1f} L{x1 - sign * r:.1f},{y:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} "
             f"L{x1:.1f},{y + h - r:.1f} Q{x1:.1f},{y + h:.1f} {x1 - sign * r:.1f},{y + h:.1f} L{x0 + sign * r0:.1f},{y + h:.1f} ")
        d += f"Q{x0:.1f},{y + h:.1f} {x0:.1f},{y + h - r0:.1f} L{x0:.1f},{y + r0:.1f} Q{x0:.1f},{y:.1f} {x0 + sign * r0:.1f},{y:.1f} Z" if both else "Z"
        self.p.append(f'<path d="{d}" fill="{self.t[color]}"/>')

    def vbar(self, x, y0, y1, w, color, r=0):
        """A vertical segment from y0 (lower on screen) up to y1; r rounds its top."""
        r = min(r, abs(y0 - y1), w / 2)
        d = (f"M{x:.1f},{y0:.1f} L{x:.1f},{y1 + r:.1f} Q{x:.1f},{y1:.1f} {x + r:.1f},{y1:.1f} L{x + w - r:.1f},{y1:.1f} "
             f"Q{x + w:.1f},{y1:.1f} {x + w:.1f},{y1 + r:.1f} L{x + w:.1f},{y0:.1f} Z")
        self.p.append(f'<path d="{d}" fill="{self.t[color]}"/>')

    def legend(self, y, items, x=24):
        """items: (kind, color, label), kind one of line | bar | tick | dot."""
        for kind, color, label in items:
            if kind == "line":
                self.line(x, y - 4, x + 18, y - 4, color, 2.5)
                x += 24
            elif kind == "bar":
                self.hbar(x, x + 18, y - 9, 10, color, r=4, both=True)
                x += 24
            elif kind == "tick":
                self.line(x + 2, y - 11, x + 2, y + 1, color, 2.5)
                x += 10
            else:
                self.dot(x + 5, y - 4, color)
                x += 16
            self.text(x, y, label, 12, "ink2")
            x += 7.0 * len(label) + 20

    def render(self) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
                f'role="img" aria-labelledby="t d" font-family="{FONT}"><title id="t">{escape(self.title)}</title><desc id="d">{escape(self.desc)}</desc>')
        return head + "".join(self.p) + "</svg>\n"


def round_paper(t: dict) -> Svg:
    rows = read("paper_round.csv")
    summary = {r["label"]: r for r in read("paper_round_summary.csv")}
    labels = [k for k in rows[0] if k != "bar"]
    launch, btc = "Launch model (e20v45)", "BTC hold"
    others = [k for k in labels if k not in (launch, btc)]
    rets = [float(summary[k]["return"]) for k in others]
    r_l, r_b = float(summary[launch]["return"]), float(summary[btc]["return"])
    w, h = 860, 440
    x0, x1, y0, y1 = 58, 700, 370, 92
    times = [datetime.fromisoformat(r["bar"]) for r in rows]
    tmin, tmax = times[0], times[-1]
    lo, hi = -25.0, 5.0
    X = lambda d: x0 + (d - tmin).total_seconds() / (tmax - tmin).total_seconds() * (x1 - x0)
    Y = lambda v: y0 - (v - lo) / (hi - lo) * (y0 - y1)
    days = (tmax - tmin).total_seconds() / 86400
    s = Svg(t, w, h, f"The launch model lost {abs(r_l) * 100:.1f}% in the round's first {days:.0f} days, while BTC lost {abs(r_b) * 100:.1f}%",
            "Paper bots on live Roostoo quotes, rebased to 0% at the round start (Oct 4, 12:00 UTC). Not the competition account.",
            "Source: data/live*/logs, docs/assets/data/paper_round.csv. Logs end Oct 15, 10:00 UTC, three days before the round closed.",
            f"Line chart of return during the round. Launch model {pct(r_l)}, BTC hold {pct(r_b)}, {len(others)} other paper bots {pct(max(rets))} to {pct(min(rets))}.")
    s.legend(78, [("line", "s1", "Launch model"), ("line", "s2", "BTC hold"),
                  ("line", "other", f"{len(others)} other paper models ({pct(max(rets))} to {pct(min(rets))})")])
    for v in range(-25, 6, 5):
        s.line(x0, Y(v), x1, Y(v), "axis" if v == 0 else "grid")
        s.text(x0 - 10, Y(v) + 4, f"{v:+d}%".replace("-", "−") if v else "0%", 12, "muted", "end", tabular=True)
    for day in (5, 7, 9, 11, 13, 15):
        d = datetime(2026, 10, day, tzinfo=timezone.utc)
        s.line(X(d), y0, X(d), y0 + 5, "axis")
        s.text(X(d), y0 + 21, f"Oct {day}", 12, "muted", "middle", tabular=True)
    for k in others:
        s.poly([(X(d), Y(float(r[k]) - 100)) for d, r in zip(times, rows) if r[k]], "other", 1.25)
    for k, c in ((btc, "s2"), (launch, "s1")):
        pts = [(X(d), Y(float(r[k]) - 100)) for d, r in zip(times, rows) if r[k]]
        s.poly(pts, c, 2)
        s.dot(*pts[-1], c)
    for k, r, name in ((launch, r_l, "Launch model"), (btc, r_b, "BTC hold")):
        y = Y(r * 100)
        s.text(x1 + 12, y - 2, name, 12.5, "ink", weight=600)
        s.text(x1 + 12, y + 14, pct(r), 12.5, "ink2", tabular=True)
    return s


def backtest_range(t: dict) -> Svg:
    rows = {r["model"]: r for r in read("backtest_distribution.csv")}
    groups = [("Our models", "s1", ["book_e20combo_brk_cash", "pol_switch_vt_tl_e20v45", "baitoey_vt_mom", "book_orch"]),
              ("Simple benchmarks", "other", ["team_btc_hold", "team_rot_ew", "team_rot_iv", "team_ew_daily", "team_mom_ss25", "team_trend_2"])]
    w, h = 860, 472
    x0, x1 = 212, 640
    top = 112
    lo, hi = -50.0, 30.0
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    n = next(iter(rows.values()))["windows"]
    live, btc = rows["book_e20combo_brk_cash"], rows["team_btc_hold"]
    s = Svg(t, w, h, "Backtest: a shallower worst case than BTC, but a lower typical return",
            f"14-day return from cash over {int(n):,} daily-start windows, June 2020 to September 2026, after fees, spread and a 1-hour fill delay.",
            "Source: results/scoring (score.json and window tables), docs/assets/data/backtest_distribution.csv.",
            f"Range chart. Final live model median {pct(float(live['median']))}, worst {pct(float(live['worst']))}. BTC hold median {pct(float(btc['median']))}, worst {pct(float(btc['worst']))}.")
    s.legend(78, [("bar", "s1", "10th to 90th percentile"), ("tick", "ink", "Median"), ("dot", "s1", "Worst window")])
    y = top
    bottom = h - 56
    for v in range(-50, 31, 10):
        s.line(X(v), top - 10, X(v), bottom, "axis" if v == 0 else "grid")
        s.text(X(v), bottom + 18, f"{v:+d}%".replace("-", "−") if v else "0%", 12, "muted", "middle", tabular=True)
    for x, label in ((712, "Median"), (776, "Worst"), (836, "Up %")):
        s.text(x, top - 2, label, 11.5, "muted", "end")
    for gname, color, models in groups:
        s.text(24, y + 13, gname, 12, "muted", weight=600)
        y += 22
        for m in models:
            r = rows[m]
            s.text(24, y + 12, r["label"], 12.5, "ink" if color == "s1" else "ink2")
            s.hbar(X(float(r["p10"]) * 100), X(float(r["p90"]) * 100), y + 3, 10, color, r=4, both=True)
            mx = X(float(r["median"]) * 100)
            s.line(mx, y, mx, y + 16, "ink", 2.5)
            s.dot(X(float(r["worst"]) * 100), y + 8, color)
            s.text(712, y + 12, pct(float(r["median"])), 12, "ink2", "end", tabular=True)
            s.text(776, y + 12, pct(float(r["worst"])), 12, "ink2", "end", tabular=True)
            s.text(836, y + 12, f'{float(r["share_positive"]) * 100:.0f}%', 12, "ink2", "end", tabular=True)
            y += 26
        y += 8
    return s


def backtest_hist(t: dict) -> Svg:
    rows = read("backtest_histogram.csv")
    meta = {r["label"]: r for r in read("paper_round_summary.csv")}
    ret = float(meta["Launch model (e20v45)"]["return"]) * 100
    total = sum(int(r["windows"]) for r in rows)
    worse_exact = int(read("backtest_histogram_meta.csv")[0]["windows_worse_than_round"])
    w, h = 860, 400
    x0, x1, y0, y1 = 58, 836, 330, 104
    lo, hi = float(rows[0]["bin_low"]), float(rows[-1]["bin_high"])
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    top = max(int(r["windows"]) for r in rows)
    cap = (top // 100 + 1) * 100
    Y = lambda v: y0 - v / cap * (y0 - y1)
    share = worse_exact / total
    s = Svg(t, w, h, f"Only {share * 100:.0f}% of backtest windows lost more than the paper bot did in this round",
            f"Launch model: 14-day returns across {total:,} backtest windows, against {pct(ret / 100)} for its paper bot after 11 days of the round.",
            "Source: docs/assets/data/backtest_histogram.csv. The last bin holds every window at or above its lower edge.",
            f"Histogram of backtest returns. {worse_exact} of {total} windows were worse than {pct(ret / 100)}.")
    s.legend(78, [("bar", "s1", "Windows that did better than the round"), ("bar", "neg", "Windows that did worse")])
    for v in range(0, cap + 1, 100):
        s.line(x0, Y(v), x1, Y(v), "axis" if v == 0 else "grid")
        s.text(x0 - 10, Y(v) + 4, v, 12, "muted", "end", tabular=True)
    for r in rows:
        a, b, n = float(r["bin_low"]), float(r["bin_high"]), int(r["windows"])
        if n:
            s.vbar(X(a) + 1, y0, Y(n), min(24, X(b) - X(a) - 2), "neg" if b <= ret + 1e-9 else "s1", r=3)
    for v in range(int(lo), int(hi) + 1, 10):
        s.line(X(v), y0, X(v), y0 + 5, "axis")
        s.text(X(v), y0 + 21, f"{v:+d}%".replace("-", "−") if v else "0%", 12, "muted", "middle", tabular=True)
    s.line(X(ret), y0, X(ret), y1 + 18, "ink", 1.5)
    s.text(X(ret) + 6, y1 + 26, f"Round so far {pct(ret / 100)}", 12.5, "ink", weight=600)
    return s


def leaderboard(t: dict) -> Svg:
    rows = read("leaderboard.csv")[:21]
    live = {"pol_switch_vt_tl_e20v45": "launch", "book_e20combo_brk_cash": "final live"}
    h = 112 + 24 * len(rows) + 48
    w = 860
    x0, x1 = 252, 790
    X = lambda v: x0 + v / 0.7 * (x1 - x0)
    total = len(read("leaderboard.csv"))
    s = Svg(t, w, h, "The models that went live were not the top scorers",
            f"Scoring v2 headline: weighted share of 14-day windows that clear three return bars. Higher is better. Top {len(rows)} of {total} runs.",
            "Source: results/scoring/registry*.jsonl, docs/assets/data/leaderboard.csv. Same scoring tool version for every row.",
            "Bar chart of headline scores. " + "; ".join(f"{r['model']} {float(r['headline_ret']):.3f}" for r in rows[:6]))
    s.legend(78, [("bar", "s1", "Went live"), ("bar", "other", "Did not go live")])
    y0 = 100
    bottom = y0 + 24 * len(rows)
    for i in range(8):
        v = i / 10
        s.line(X(v), y0 - 4, X(v), bottom, "axis" if i == 0 else "grid")
        s.text(X(v), bottom + 18, f"{v:.1f}", 12, "muted", "middle", tabular=True)
    for i, r in enumerate(rows):
        y = y0 + 24 * i
        v = float(r["headline_ret"])
        name = r["model"] + (f" ({live[r['model']]})" if r["model"] in live else "") + (" (benchmark)" if r["author"] == "team" else "")
        s.text(x0 - 10, y + 15, name, 12, "ink" if r["model"] in live else "ink2", "end", weight=600 if r["model"] in live else None)
        s.hbar(X(0), X(v), y + 5, 14, "s1" if r["model"] in live else "other")
        s.text(X(v) + 8, y + 16, f"{v:.3f}", 12, "ink" if r["model"] in live else "ink2", tabular=True)
    return s


def scalp(t: dict) -> Svg:
    rows = read("scalp_fill_rules.csv")
    w, h = 860, 392
    x0, x1 = 356, 820
    lo, hi = -32.0, 12.0
    X = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    s = Svg(t, w, h, "The scalping edge came from an assumed fill rule; real fills removed it",
            "Sleeve profit or loss per day on $60k. Replay on Oct 5-7 quotes; measured rules on Oct 8-13 quotes, with the live account's fill behaviour.",
            "Source: deploy/SLEEVE.md, research/book/roostoo_fills/README.md, docs/assets/data/scalp_fill_rules.csv.",
            "Bar chart. " + "; ".join(f"{r['label']} {float(r['per_day_pct']):+.1f}% a day" for r in rows))
    s.legend(78, [("bar", "s1", "Gain"), ("bar", "neg", "Loss")])
    top, bottom = 100, h - 56
    for v in (-30, -20, -10, 0, 10):
        s.line(X(v), top, X(v), bottom, "axis" if v == 0 else "grid")
        s.text(X(v), bottom + 18, f"{v:+d}%".replace("-", "−") if v else "0%", 12, "muted", "middle", tabular=True)
    y = top
    group = None
    for r in rows:
        if r["group"] != group:
            group = r["group"]
            s.text(24, y + 15, group, 12, "muted", weight=600)
            y += 24
        v = float(r["per_day_pct"])
        s.text(24, y + 14, r["label"], 12.5, "ink2")
        s.hbar(X(0), X(v), y + 4, 13, "s1" if v > 0 else "neg")
        text = f"{v:+.1f}%".replace("-", "−")
        s.text(X(v) + (8 if v > 0 else -8), y + 15, text, 12, "ink", "start" if v > 0 else "end", tabular=True)
        y += 26
    return s


def activity(t: dict) -> Svg:
    rows = read("commits_by_day.csv")
    who = [("Book", "s1"), ("Pol", "s2"), ("Baitoey", "s3")]
    totals = [sum(int(r[k]) for k, _ in who) for r in rows]
    w, h = 860, 360
    x0, x1, y0, y1 = 58, 836, 290, 100
    cap = (max(totals) // 25 + 1) * 25
    Y = lambda v: y0 - v / cap * (y0 - y1)
    step = (x1 - x0) / len(rows)
    s = Svg(t, w, h, f"{sum(totals)} commits over {len(rows)} days of work, most of them during the round",
            "Commits per day on feature branches, without merges. The round started on Oct 4.",
            "Source: git log, docs/assets/data/commits_by_day.csv.",
            f"Stacked columns of commits per day. Busiest day {rows[totals.index(max(totals))]['date']} with {max(totals)} commits.")
    s.legend(78, [("bar", c, k) for k, c in who])
    for v in range(0, cap + 1, 25):
        s.line(x0, Y(v), x1, Y(v), "axis" if v == 0 else "grid")
        s.text(x0 - 10, Y(v) + 4, v, 12, "muted", "end", tabular=True)
    bw = min(24, step - 8)
    for i, r in enumerate(rows):
        x = x0 + step * i + (step - bw) / 2
        base = 0
        present = [(k, c) for k, c in who if int(r[k])]
        for j, (k, c) in enumerate(present):
            n = int(r[k])
            top = Y(base + n)
            bottom = Y(base) - (2 if base else 0)
            s.vbar(x, bottom, min(top, bottom), bw, c, r=4 if j == len(present) - 1 else 0)
            base += n
        d = datetime.strptime(r["date"], "%Y-%m-%d")
        if i % 2 == 0:
            s.text(x + bw / 2, y0 + 21, d.strftime("%b ") + str(d.day), 12, "muted", "middle", tabular=True)
    i = totals.index(max(totals))
    s.text(x0 + step * i + step / 2, Y(totals[i]) - 8, totals[i], 12.5, "ink", "middle", weight=600, tabular=True)
    return s


CHARTS = {"round_paper": round_paper, "backtest_range": backtest_range, "backtest_hist": backtest_hist,
          "leaderboard": leaderboard, "scalp_fill_rules": scalp, "activity": activity}


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for name, draw in CHARTS.items():
        for t in (LIGHT, DARK):
            with open(os.path.join(OUT, f"{name}.{t['name']}.svg"), "w", encoding="utf-8") as f:
                f.write(draw(t).render())
    print(f"{len(CHARTS)} charts in {OUT}")


if __name__ == "__main__":
    main()
