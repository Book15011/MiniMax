"""Small dependency-free SVG charts for the scoring report (the shared venv has no plotting library).

Static images for a Markdown report: thin marks, a recessive grid, one y-axis per chart, a legend whenever there
are two or more series. Colours come from a validated data-viz palette (series 1-3 = blue, orange, aqua, which
stay distinguishable for colour-blind readers), with separate light and dark steps chosen by the viewer's
colour scheme. Text always uses the ink colours, never a series colour.
"""
from __future__ import annotations

import math
from html import escape

import numpy as np

STYLE = """<style>
svg{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--grid:#e4e3df;--axis:#a3a29d;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--none:#d6d5d0}
@media (prefers-color-scheme: dark){svg{--surface:#1a1a19;--ink:#ffffff;--ink2:#c3c2b7;--grid:#33332f;--axis:#6b6a65;--s1:#3987e5;--s2:#d95926;--s3:#199e70;--none:#4a4945}}
text{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:11px;fill:var(--ink2)}
.t{fill:var(--ink);font-size:14px;font-weight:600}.st{font-size:11.5px}.v{fill:var(--ink)}
.g{stroke:var(--grid);stroke-width:1}.ax{stroke:var(--axis);stroke-width:1}
.l1,.l2,.l3{fill:none;stroke-width:2;stroke-linejoin:round;stroke-linecap:round}
.l1{stroke:var(--s1)}.l2{stroke:var(--s2)}.l3{stroke:var(--s3)}
.f1{fill:var(--s1)}.f2{fill:var(--s2)}.f3{fill:var(--s3)}.f0{fill:var(--none)}
.ring{stroke:var(--surface);stroke-width:2}.bg{fill:var(--surface)}
</style>"""

SLOTS = {1: "s1", 2: "s2", 3: "s3"}


def nice_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    if not np.isfinite([lo, hi]).all() or hi <= lo:
        return [lo]
    raw = (hi - lo) / max(n, 1)
    mag = 10 ** math.floor(math.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    first = math.ceil(lo / step - 1e-9) * step
    return [round(first + k * step, 12) for k in range(int((hi - first) / step + 1e-9) + 1)]


def padded(lo: float, hi: float, pad: float = 0.06) -> tuple[float, float]:
    if hi <= lo:
        return lo - 1.0, hi + 1.0
    d = (hi - lo) * pad
    return lo - d, hi + d


def pct(x: float, digits: int = 0) -> str:
    return f"{x * 100:+.{digits}f}%" if x else "0%"


class Chart:
    def __init__(self, w: int, h: int, title: str, subtitle: str = ""):
        self.w, self.h, self.parts = w, h, []
        self.parts.append(f'<rect class="bg" width="{w}" height="{h}" rx="6"/>')
        self.text(16, 24, title, "t")
        if subtitle:
            self.text(16, 42, subtitle, "st")

    def text(self, x, y, s, cls="", anchor="start"):
        c = f' class="{cls}"' if cls else ""
        self.parts.append(f'<text x="{x:.1f}" y="{y:.1f}"{c} text-anchor="{anchor}">{escape(str(s))}</text>')

    def add(self, s: str):
        self.parts.append(s)

    def legend(self, items: list[tuple[str, int]], x: float, y: float):
        for label, slot in items:
            self.add(f'<rect x="{x:.1f}" y="{y - 8:.1f}" width="14" height="4" rx="2" class="f{slot}"/>')
            self.text(x + 19, y - 3, label)
            x += 26 + 6.5 * len(label)

    def axes(self, box, xr, yr, xfmt=str, yfmt=str, xticks=None, yticks=None, xlabel="", grid_x=False):
        x0, y0, x1, y1 = box
        sx = lambda v: x0 + (v - xr[0]) / (xr[1] - xr[0]) * (x1 - x0)
        sy = lambda v: y1 - (v - yr[0]) / (yr[1] - yr[0]) * (y1 - y0)
        for t in (yticks if yticks is not None else nice_ticks(*yr)):
            if yr[0] <= t <= yr[1]:
                self.add(f'<line class="g" x1="{x0}" x2="{x1}" y1="{sy(t):.1f}" y2="{sy(t):.1f}"/>')
                self.text(x0 - 6, sy(t) + 3.5, yfmt(t), anchor="end")
        for t in (xticks if xticks is not None else nice_ticks(*xr)):
            if xr[0] <= t <= xr[1]:
                if grid_x:
                    self.add(f'<line class="g" x1="{sx(t):.1f}" x2="{sx(t):.1f}" y1="{y0}" y2="{y1}"/>')
                self.text(sx(t), y1 + 15, xfmt(t), anchor="middle")
        self.add(f'<line class="ax" x1="{x0}" x2="{x1}" y1="{y1}" y2="{y1}"/>')
        if xlabel:
            self.text((x0 + x1) / 2, y1 + 31, xlabel, anchor="middle")
        return sx, sy

    def svg(self) -> str:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                f'viewBox="0 0 {self.w} {self.h}" role="img">{STYLE}' + "".join(self.parts) + "</svg>\n")


def polyline(sx, sy, xs, ys, slot: int) -> str:
    pts = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in zip(xs, ys) if np.isfinite(y))
    return f'<polyline class="l{slot}" points="{pts}"/>'


def lines(title: str, subtitle: str, x, series: list[tuple[str, np.ndarray, int]], xlabel: str, yfmt,
          xticks=None, w: int = 720, h: int = 300) -> str:
    c = Chart(w, h, title, subtitle)
    allv = np.concatenate([np.asarray(s[1], float) for s in series])
    lo, hi = padded(float(np.nanmin(np.append(allv, 0.0))), float(np.nanmax(np.append(allv, 0.0))))
    box = (70, 70, w - 110, h - 50)
    sx, sy = c.axes(box, (float(x[0]), float(x[-1])), (lo, hi), xfmt=lambda v: f"{v:g}", yfmt=yfmt,
                    xticks=xticks, xlabel=xlabel)
    for label, y, slot in series:
        c.add(polyline(sx, sy, x, y, slot))
        c.text(box[2] + 6, sy(float(y[-1])) + 4, label, "v")      # direct label at the line end
    if len(series) > 1:
        c.legend([(s[0], s[2]) for s in series], 70, 62)
    return c.svg()


def small_multiples(title: str, subtitle: str, panels: list[dict], legend: list[tuple[str, int]], cols: int = 5,
                    pw: int = 142, ph: int = 104) -> str:
    """panels: {"title", "x", "series": [(y, slot)]}; y values are returns (fractions) from the window start."""
    rows = math.ceil(len(panels) / cols)
    w, top = cols * (pw + 6) + 20, 76
    c = Chart(w, top + rows * (ph + 26) + 8, title, subtitle)
    c.legend(legend, 16, 62)
    for k, p in enumerate(panels):
        ox, oy = 14 + (k % cols) * (pw + 6), top + (k // cols) * (ph + 26)
        allv = np.concatenate([np.asarray(y, float) for y, _ in p["series"]] + [np.zeros(1)])
        lo, hi = padded(float(np.nanmin(allv)), float(np.nanmax(allv)), 0.08)
        box = (ox + 34, oy + 16, ox + pw, oy + ph)
        c.text(ox + 34, oy + 10, p["title"], "v")
        sx, sy = c.axes(box, (float(p["x"][0]), float(p["x"][-1])), (lo, hi), xfmt=lambda v: "",
                        yfmt=lambda v: f"{v * 100:.0f}%", xticks=[], yticks=nice_ticks(lo, hi, 3))
        for y, slot in p["series"]:
            c.add(polyline(sx, sy, p["x"], y, slot).replace("<polyline ", '<polyline style="stroke-width:1.5" '))
    return c.svg()


def histogram(title: str, subtitle: str, values, weights, edges, xlabel: str, xfmt, refs=(), w: int = 720,
              h: int = 290) -> str:
    """Weighted share of windows per bin (one series), with labelled reference lines [(label, x)]."""
    v, wt = np.asarray(values, float), np.asarray(weights, float)
    share = np.histogram(np.clip(v, edges[0], edges[-1]), bins=edges, weights=wt)[0] / wt.sum()
    c = Chart(w, h, title, subtitle)
    box = (70, 62, w - 30, h - 50)
    sx, sy = c.axes(box, (edges[0], edges[-1]), (0.0, float(share.max()) * 1.15 or 1.0), xfmt=xfmt,
                    yfmt=lambda t: f"{t * 100:.0f}%", xlabel=xlabel)
    for a, b, s in zip(edges[:-1], edges[1:], share):
        if s > 0:
            x0, x1 = sx(a) + 1, sx(b) - 1                      # 2 px surface gap between adjacent bars
            hgt = sy(0) - sy(s)
            r = min(4.0, (x1 - x0) / 2, hgt)
            c.add(f'<path class="f1" d="M{x0:.1f},{sy(0):.1f} V{sy(s) + r:.1f} Q{x0:.1f},{sy(s):.1f} {x0 + r:.1f},{sy(s):.1f} '
                  f'H{x1 - r:.1f} Q{x1:.1f},{sy(s):.1f} {x1:.1f},{sy(s) + r:.1f} V{sy(0):.1f} Z"/>')
    for k, (label, x) in enumerate(refs):
        if edges[0] <= x <= edges[-1]:
            c.add(f'<line class="ax" stroke-dasharray="4 3" x1="{sx(x):.1f}" x2="{sx(x):.1f}" y1="{box[1]}" y2="{box[3]}"/>')
            c.text(sx(x) + 4, box[1] + 10 + 13 * k, label, "v")
    return c.svg()


def dumbbell(title: str, subtitle: str, rows: list[tuple[str, float, float]], names: tuple[str, str],
             w: int = 720) -> str:
    """One row per window: model (slot 1) and reference (slot 2) on the same x scale, joined by a grey bar."""
    h = 92 + 19 * len(rows) + 40
    c = Chart(w, h, title, subtitle)
    c.legend([(names[0], 1), (names[1], 2)], 16, 62)
    allv = [x for _, a, b in rows for x in (a, b)] + [0.0]
    lo, hi = padded(min(allv), max(allv))
    box = (150, 80, w - 30, h - 46)
    sx, sy = c.axes(box, (lo, hi), (0, len(rows)), xfmt=lambda t: f"{t * 100:.0f}%", yfmt=lambda t: "", yticks=[],
                    xlabel="14-day return R", grid_x=True)
    c.add(f'<line class="ax" x1="{sx(0):.1f}" x2="{sx(0):.1f}" y1="{box[1]}" y2="{box[3]}"/>')
    for k, (label, a, b) in enumerate(rows):
        y = box[1] + 19 * k + 12
        c.text(box[0] - 8, y + 4, label, anchor="end")
        c.add(f'<line class="g" stroke-width="3" x1="{sx(min(a, b)):.1f}" x2="{sx(max(a, b)):.1f}" y1="{y}" y2="{y}"/>')
        c.add(f'<circle class="f2 ring" cx="{sx(b):.1f}" cy="{y}" r="4.5"/>')
        c.add(f'<circle class="f1 ring" cx="{sx(a):.1f}" cy="{y}" r="4.5"/>')
    return c.svg()


def _mix(a: str, b: str, t: float) -> str:
    pa, pb = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def heatmap(title: str, subtitle: str, med, cnt, rows: list[str], cols: list[str], limit: float,
            row_title: str, col_title: str, w: int = 520) -> str:
    """Diverging cells (red below 0, blue above, grey at 0), each labelled with its value and count."""
    cw, ch = 120, 64
    h = 96 + ch * len(rows) + 40
    c = Chart(w, h, title, subtitle)
    x0, y0 = 120, 84
    for j, col in enumerate(cols):
        c.text(x0 + cw * j + cw / 2, y0 - 8, col, anchor="middle")
    c.text(x0 + cw * len(cols) / 2, y0 + ch * len(rows) + 22, col_title, anchor="middle")
    c.text(16, y0 - 8, row_title)
    for i, r in enumerate(rows):
        c.text(x0 - 10, y0 + ch * i + ch / 2 + 4, r, anchor="end")
        for j, col in enumerate(cols):
            v, n = med[i][j], cnt[i][j]
            if v is None or not np.isfinite(v):
                fill, ink = "#d6d5d0", "#0b0b0b"
            else:
                t = min(abs(v) / limit, 1.0)
                fill = _mix("#f0efec", "#256abf" if v > 0 else "#d03b3b", t)
                ink = "#ffffff" if t > 0.55 else "#0b0b0b"
            x, y = x0 + cw * j, y0 + ch * i
            c.add(f'<rect x="{x + 1}" y="{y + 1}" width="{cw - 2}" height="{ch - 2}" rx="4" fill="{fill}"/>')
            label = "—" if v is None or not np.isfinite(v) else f"{v * 100:+.1f}%"
            c.add(f'<text x="{x + cw / 2}" y="{y + ch / 2}" text-anchor="middle" style="fill:{ink};font-size:13px;font-weight:600">{label}</text>')
            c.add(f'<text x="{x + cw / 2}" y="{y + ch / 2 + 16}" text-anchor="middle" style="fill:{ink}">n = {n}</text>')
    return c.svg()


def stacked_columns(title: str, subtitle: str, labels: list[str], stacks: list[tuple[str, np.ndarray, int]],
                    xlabel: str, w: int = 720, h: int = 300) -> str:
    """Columns of shares that add up to 1; stacks [(name, values, slot)], slot 0 = the neutral 'none' grey."""
    c = Chart(w, h, title, subtitle)
    box = (70, 70, w - 30, h - 50)
    n = len(labels)
    sx, sy = c.axes(box, (0, n), (0.0, 1.0), xfmt=lambda t: "", yfmt=lambda t: f"{t * 100:.0f}%", xticks=[],
                    yticks=[0, 0.25, 0.5, 0.75, 1.0], xlabel=xlabel)
    bw = (box[2] - box[0]) / n
    for k, lab in enumerate(labels):
        base = 0.0
        for _, vals, slot in stacks:
            v = float(vals[k])
            if v > 0:
                y_top, y_bot = sy(base + v), sy(base)
                c.add(f'<rect class="f{slot}" x="{box[0] + bw * k + 2:.1f}" y="{y_top + 1:.1f}" width="{bw - 4:.1f}" '
                      f'height="{max(y_bot - y_top - 2, 0.5):.1f}" rx="2"/>')   # 2 px surface gap between segments
            base += v
        c.text(box[0] + bw * k + bw / 2, box[3] + 15, lab, anchor="middle")
    c.legend([(s[0], s[2]) for s in stacks], 70, 62)
    return c.svg()
