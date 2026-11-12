"""도면 그리기 도구: A3 시트, 표제란, 투상도 렌더(은선 제거), 치수선, 풍선 번호."""
import glob
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import Arc, Circle, Polygon, Rectangle  # noqa: E402

DATE = "2026-11-12"
PROJECT = "볼 크레이터 두께 측정기"
TOTAL_SHEETS = 6


# ── 한글 글꼴 ───────────────────────────────────────────────

def _setup_font():
    cands = []
    try:
        import importlib.util
        spec = importlib.util.find_spec("koreanize_matplotlib")
        if spec and spec.submodule_search_locations:
            cands += glob.glob(os.path.join(list(spec.submodule_search_locations)[0], "fonts", "NanumGothic.ttf"))
    except Exception:
        pass
    cands += glob.glob("/usr/share/fonts/**/NanumGothic*.ttf", recursive=True)
    cands += glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True)
    cands += ["C:/Windows/Fonts/malgun.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc"]
    for c in cands:
        if os.path.exists(c):
            font_manager.fontManager.addfont(c)
            for extra in glob.glob(os.path.join(os.path.dirname(c), "NanumGothic*.ttf")):
                font_manager.fontManager.addfont(extra)
            name = font_manager.FontProperties(fname=c).get_name()
            plt.rcParams["font.family"] = [name, "DejaVu Sans"]
            return name
    raise RuntimeError("한글 글꼴을 찾지 못했습니다. pip install koreanize-matplotlib 로 나눔고딕을 설치하세요.")


FONT = _setup_font()
plt.rcParams["lines.scale_dashes"] = False
plt.rcParams["hatch.linewidth"] = 0.4
plt.rcParams["pdf.fonttype"] = 42

LW = dict(outline=1.3, thin=0.5, hidden=0.6, center=0.45, dim=0.45, border=1.6, cut=1.2)
LS = dict(outline="-", thin="-", hidden=(0, (5, 2.5)), center=(0, (16, 3, 2, 3)), dim="-",
          border="-", cut=(0, (16, 3, 2, 3)))
FS_DIM, FS_NOTE, FS_LABEL, FS_TITLE = 7.5, 8, 9.5, 15


# ── 은선 제거 렌더러 (z-버퍼) ───────────────────────────────

def view_axes(front_dir, which):
    """3각법. front_dir = 정면도에서 보는 사람이 바라보는 방향."""
    d_f = np.array(front_dir, float)
    z = np.array([0, 0, 1.0])
    r = np.cross(d_f, z)
    if which == "front":
        return d_f, r, z
    if which == "top":
        return -z, r, d_f
    if which == "right":
        d = -r
        return d, np.cross(d, z), z
    if which == "bottom":
        return z, r, -d_f
    raise ValueError(which)


def zrender(meshes, d, r, up, win, ppm, ss=2, mode="line", colors=None, cut=None,
            hatch=None, solid=(), edge_mm=0.3, depth_jump=0.4, paper_ppm=None, hatch_mm=2.0):
    """meshes: [(이름, trimesh)]. win = (u0, u1, v0, v1) 모델 mm. ppm = 출력 px/모델 mm.

    mode="line": 흰 면 + 검은 윤곽선 (도면용). mode="shaded": 색 + 윤곽선 (그림용).
    cut = 단면 평면의 깊이 값 (d 방향). hatch = {이름: 각도} 단면 해칭할 부품.
    paper_ppm = 종이 mm 당 px (선 굵기와 해칭 간격을 종이 기준으로 맞춤).
    """
    if paper_ppm is None:
        paper_ppm = ppm
    u0, u1, v0, v1 = win
    k = ppm * ss
    W, H = int(round((u1 - u0) * k)), int(round((v1 - v0) * k))
    zbuf = np.full((H, W), np.inf, np.float32)
    ids = np.full((H, W), -1, np.int16)
    nbuf = np.zeros((H, W, 3), np.float16)
    cutm = np.zeros((H, W), bool)
    rgb = np.ones((H, W, 3), np.float32) if mode == "shaded" else None
    light = -d * 0.55 + up * 0.65 + r * 0.35
    light /= np.linalg.norm(light)
    names = []
    for pid, (name, tm) in enumerate(meshes):
        names.append(name)
        V = tm.vertices
        px = (V @ r - u0) * k
        py = (v1 - V @ up) * k
        pz = V @ d
        fn = tm.face_normals
        col = np.array((colors or {}).get(name, (0.75, 0.75, 0.75)), np.float32)
        is_hatch = hatch is not None and name in hatch or name in solid
        for f, n in zip(tm.faces, fn):
            nd = float(n @ d)
            if nd > 1e-6:
                continue
            x, y, zz = px[f], py[f], pz[f]
            x0, x1 = int(max(0, math.floor(x.min()))), int(min(W - 1, math.ceil(x.max())))
            y0, y1 = int(max(0, math.floor(y.min()))), int(min(H - 1, math.ceil(y.max())))
            if x1 < x0 or y1 < y0:
                continue
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-5) & (w1 >= -1e-5) & (w2 >= -1e-5)
            if not inside.any():
                continue
            depth = (w0 * zz[0] + w1 * zz[1] + w2 * zz[2]).astype(np.float32)
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (depth < sub - 1e-4)
            if not upd.any():
                continue
            sub[upd] = depth[upd]
            ids[y0:y1 + 1, x0:x1 + 1][upd] = pid
            nbuf[y0:y1 + 1, x0:x1 + 1][upd] = n
            is_cut = is_hatch and cut is not None and nd < -0.999 and abs(float(zz.mean()) - cut) < 0.05
            cutm[y0:y1 + 1, x0:x1 + 1][upd] = is_cut
            if rgb is not None:
                shade = 0.38 + 0.62 * max(0.0, float(n @ light))
                rgb[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(col * shade, 0, 1)

    edge = np.zeros((H, W), bool)
    nb = nbuf.astype(np.float32)
    for ax in (0, 1):
        i1 = np.roll(ids, 1, axis=ax)
        edge |= ids != i1
        z1 = np.roll(zbuf, 1, axis=ax)
        both = np.isfinite(zbuf) & np.isfinite(z1)
        dz = np.zeros_like(zbuf)
        dz[both] = np.abs(zbuf[both] - z1[both])
        edge |= both & (dz > depth_jump)
        n1 = np.roll(nb, 1, axis=ax)
        edge |= (ids >= 0) & (i1 >= 0) & ((nb * n1).sum(-1) < 0.85)
    edge[0, :] = edge[:, 0] = False
    rad = max(1, int(round(edge_mm * paper_ppm * ss / 2)))
    e = edge.copy()
    for ax in (0, 1):
        acc = e.copy()
        for s in range(1, rad + 1):
            acc |= np.roll(e, s, axis=ax) | np.roll(e, -s, axis=ax)
        e = acc

    if mode == "line":
        img = np.ones((H, W), np.float32)
        if hatch is not None or solid:
            yy, xx = np.mgrid[0:H, 0:W]
            sp = hatch_mm * paper_ppm * ss
            lw = 0.25 * paper_ppm * ss
            for pid, name in enumerate(names):
                m = cutm & (ids == pid)
                if not m.any():
                    continue
                if name in solid:
                    img[m] = 0.15
                    continue
                ang = math.radians(hatch.get(name, 45))
                t = (xx * math.cos(ang) + yy * math.sin(ang)) % sp
                img[m & (t < lw)] = 0.0
        img[e] = 0.0
        out = img
    else:
        out = rgb
        out[e] = out[e] * 0.2
    if ss > 1:
        Hs, Ws = H // ss, W // ss
        out = out[:Hs * ss, :Ws * ss]
        if out.ndim == 2:
            out = out.reshape(Hs, ss, Ws, ss).mean(axis=(1, 3))
        else:
            out = out.reshape(Hs, ss, Ws, ss, 3).mean(axis=(1, 3))
    return out


# ── 시트 ────────────────────────────────────────────────────

class Sheet:
    def __init__(self, title, number, scale, sheet_no, material="", qty=""):
        self.fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 420)
        ax.set_ylim(0, 297)
        ax.set_aspect("equal")
        ax.axis("off")
        self.ax = ax
        self.rect(10, 410, 10, 287, "border")
        for x in (210,):
            self.line([(x, 287), (x, 292)], "thin")
            self.line([(x, 5), (x, 10)], "thin")
        for y in (148.5,):
            self.line([(5, y), (10, y)], "thin")
            self.line([(410, y), (415, y)], "thin")
        self._title_block(title, number, scale, sheet_no, material, qty)

    # 기본 그리기 (종이 mm 좌표)
    def line(self, pts, kind="outline", color="k", z=3):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=color, lw=LW[kind], ls=LS[kind], solid_capstyle="butt",
                     dash_capstyle="butt", zorder=z)

    def rect(self, x0, x1, y0, y1, kind="outline", fill=None, z=3):
        self.ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=fill is not None,
                                    facecolor=fill or "none", edgecolor="k", lw=LW[kind],
                                    ls=LS[kind], zorder=z))

    def text(self, x, y, s, size=FS_NOTE, ha="left", va="baseline", rot=0, weight="normal", z=6, color="k",
             box=False):
        bbox = dict(facecolor="white", edgecolor="none", pad=0.6) if box else None
        return self.ax.text(x, y, s, fontsize=size, ha=ha, va=va, rotation=rot, weight=weight,
                            zorder=z, color=color, rotation_mode="anchor", bbox=bbox, linespacing=1.15)

    def _title_block(self, title, number, scale, sheet_no, material, qty):
        x0, y0 = 230, 10
        self.rect(x0, 410, y0, 50, "outline", fill="white", z=2)
        rows = [  # (y, [(폭, 글, 제목칸?)])
            (40, [(20, "도면명", 1), (110, title, 0), (20, "척도", 1), (30, scale, 0)]),
            (30, [(20, "도면번호", 1), (110, number, 0), (20, "투상법", 1), (30, "3각법", 0)]),
            (20, [(20, "작품명", 1), (110, PROJECT, 0), (20, "단위", 1), (30, "mm", 0)]),
            (10, [(20, "작성", 1), (40, "", 0), (20, "작성일", 1), (50, DATE, 0), (20, "장", 1),
                  (30, f"{sheet_no} / {TOTAL_SHEETS}", 0)]),
        ]
        for y, cells in rows:
            self.line([(x0, y + 10), (410, y + 10)], "thin")
            x = x0
            for w, s, head in cells:
                if x > x0:
                    self.line([(x, y), (x, y + 10)], "thin")
                big = (s == title)
                self.text(x + (w / 2 if head else 3), y + 5, s, size=(12 if big else (7.5 if head else 8.5)),
                          ha="center" if head else "left", va="center", weight="bold" if big else "normal")
                x += w
        if material or qty:
            self.rect(x0, 410, 50, 58, "thin", fill="white", z=2)
            self.text(x0 + 3, 54, f"재질: {material}", size=8, va="center")
            self.text(x0 + 120, 54, f"수량: {qty}", size=8, va="center")

    def notes(self, x, y, title, lines, size=FS_NOTE, lh=4.6, width=None):
        self.text(x, y, title, size=size + 1.5, weight="bold")
        yy = y - lh - 1
        for s in lines:
            self.text(x, yy, s, size=size)
            yy -= lh
        return yy

    def table(self, x, y, cols, rows, rh=5.0, size=7.2, head_fill="#e8e8e8"):
        """x, y = 왼쪽 위. cols = [(제목, 폭, 정렬)]."""
        W = sum(c[1] for c in cols)
        n = len(rows) + 1
        self.rect(x, x + W, y - n * rh, y, "outline", z=4)
        self.ax.add_patch(Rectangle((x, y - rh), W, rh, facecolor=head_fill, edgecolor="none", zorder=1))
        for i in range(1, n):
            self.line([(x, y - i * rh), (x + W, y - i * rh)], "thin", z=4)
        cx = x
        for ci, (head, w, al) in enumerate(cols):
            if ci:
                self.line([(cx, y), (cx, y - n * rh)], "thin", z=4)
            self.text(cx + w / 2, y - rh / 2, head, size=size, ha="center", va="center", weight="bold")
            for ri, row in enumerate(rows):
                s = str(row[ci])
                tx = cx + (w / 2 if al == "c" else (2 if al == "l" else w - 2))
                self.text(tx, y - (ri + 1.5) * rh, s, size=size, ha={"c": "center", "l": "left", "r": "right"}[al],
                          va="center")
            cx += w
        return y - n * rh

    def image(self, img, x0, x1, y0, y1, z=1, cmap="gray"):
        self.ax.imshow(img, extent=(x0, x1, y0, y1), cmap=cmap if img.ndim == 2 else None,
                       vmin=0, vmax=1, interpolation="lanczos", zorder=z, aspect="auto")

    def save(self, pdf, png_path=None, dpi=150):
        if pdf is not None:
            pdf.savefig(self.fig)
        if png_path:
            self.fig.savefig(png_path, dpi=dpi)
        plt.close(self.fig)


# ── 투상도 ──────────────────────────────────────────────────

class View:
    """모델 좌표 → 종이 좌표. (u, v) = (점·r, 점·up), 종이 = 기준점 + s × (u - u_ref, v - v_ref)."""

    def __init__(self, sheet, front_dir, which, ref3, paper_xy, scale):
        self.sh = sheet
        self.d, self.r, self.up = view_axes(front_dir, which)
        ref = np.array(ref3, float)
        self.u_ref, self.v_ref = float(ref @ self.r), float(ref @ self.up)
        self.px, self.py = paper_xy
        self.s = scale

    def uv(self, P):
        P = np.array(P, float)
        return float(P @ self.r), float(P @ self.up)

    def paper_uv(self, u, v):
        return self.px + self.s * (u - self.u_ref), self.py + self.s * (v - self.v_ref)

    def P(self, P3):
        return self.paper_uv(*self.uv(P3))

    def render(self, meshes, win3_lo, win3_hi, dpi=400, pad=2.0, **kw):
        """모델의 상자 범위(두 꼭짓점)를 이 방향으로 렌더해 종이에 붙입니다."""
        corners = np.array([[a, b, c] for a in (win3_lo[0], win3_hi[0]) for b in (win3_lo[1], win3_hi[1])
                            for c in (win3_lo[2], win3_hi[2])], float)
        us, vs = corners @ self.r, corners @ self.up
        u0, u1 = us.min() - pad, us.max() + pad
        v0, v1 = vs.min() - pad, vs.max() + pad
        ppm = dpi / 25.4 * self.s
        img = zrender(meshes, self.d, self.r, self.up, (u0, u1, v0, v1), ppm, paper_ppm=dpi / 25.4, **kw)
        x0, y0 = self.paper_uv(u0, v0)
        x1, y1 = self.paper_uv(u1, v1)
        self.sh.image(img, x0, x1, y0, y1)
        return img

    # 선
    def line3(self, pts3, kind="outline"):
        self.sh.line([self.P(q) for q in pts3], kind)

    def line_uv(self, pts, kind="outline"):
        self.sh.line([self.paper_uv(u, v) for u, v in pts], kind)

    def circle_uv(self, u, v, r, kind="outline", fill=None):
        x, y = self.paper_uv(u, v)
        self.sh.ax.add_patch(Circle((x, y), r * self.s, fill=fill is not None, facecolor=fill or "none",
                                    edgecolor="k", lw=LW[kind], ls=LS[kind], zorder=3))

    def center_mark(self, P3, r, ext=2.0):
        u, v = self.uv(P3)
        e = r + ext / self.s
        self.line_uv([(u - e, v), (u + e, v)], "center")
        self.line_uv([(u, v - e), (u, v + e)], "center")

    def label(self, text, P3_below=None, dy=-7, x=None, y=None, size=FS_LABEL):
        if x is None:
            x, y0 = self.P(P3_below)
            y = y0 + dy
        self.sh.text(x, y, text, size=size, ha="center", va="top", weight="bold")


# ── 치수 ────────────────────────────────────────────────────

def fmt(v):
    v = abs(v)
    if abs(v - round(v)) < 0.005:
        return f"{int(round(v))}"
    if abs(v * 10 - round(v * 10)) < 0.01:
        return f"{v:.1f}"
    return f"{v:.2f}"


def arrow(sh, tip, direction, L=2.6, w=0.55, z=5):
    dx, dy = direction
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    bx, by = tip[0] - dx * L, tip[1] - dy * L
    pts = [tip, (bx - dy * w, by + dx * w), (bx + dy * w, by - dx * w)]
    sh.ax.add_patch(Polygon(pts, closed=True, facecolor="k", edgecolor="k", lw=0.2, zorder=z))


def _dim_line(sh, a, b, text, text_side=1, size=FS_DIM, outside=None, rot=None):
    (x1, y1), (x2, y2) = a, b
    L = math.hypot(x2 - x1, y2 - y1)
    if L < 1e-6:
        return
    ux, uy = (x2 - x1) / L, (y2 - y1) / L
    if outside is None:
        outside = L < 7
    sh.line([a, b], "dim", z=5)
    if outside:
        arrow(sh, a, (ux, uy))
        arrow(sh, b, (-ux, -uy))
        sh.line([(x1 - ux * 5, y1 - uy * 5), a], "dim", z=5)
        sh.line([b, (x2 + ux * 5, y2 + uy * 5)], "dim", z=5)
    else:
        arrow(sh, a, (-ux, -uy))
        arrow(sh, b, (ux, uy))
    ang = math.degrees(math.atan2(uy, ux)) if rot is None else rot
    if ang > 90.01 or ang < -89.99:
        ang -= 180 if ang > 0 else -180
    nx, ny = -uy, ux
    if ang != math.degrees(math.atan2(uy, ux)):
        nx, ny = -nx, -ny
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    off = 0.9
    sh.text(mx + nx * off * text_side, my + ny * off * text_side, text, size=size, ha="center",
            va="bottom" if text_side > 0 else "top", rot=ang)


def hdim(V, P1, P2, off, text=None, pre="", suf="", size=FS_DIM, outside=None, gap=1.0):
    """수평 치수 (뷰의 u 방향). off = 종이 mm. +면 위, -면 아래."""
    sh = V.sh
    (u1, v1), (u2, v2) = V.uv(P1), V.uv(P2)
    x1, y1 = V.paper_uv(u1, v1)
    x2, y2 = V.paper_uv(u2, v2)
    yd = (max(y1, y2) + off) if off > 0 else (min(y1, y2) + off)
    sgn = 1 if off > 0 else -1
    for x, y in ((x1, y1), (x2, y2)):
        if abs(yd - y) > gap:
            sh.line([(x, y + sgn * gap), (x, yd + sgn * 1.5)], "dim", z=5)
    t = text if text is not None else pre + fmt(u2 - u1) + suf
    a, b = sorted([(x1, yd), (x2, yd)])
    _dim_line(sh, a, b, t, 1, size, outside)


def vdim(V, P1, P2, off, text=None, pre="", suf="", size=FS_DIM, outside=None, gap=1.0):
    """수직 치수 (뷰의 v 방향). off = 종이 mm. +면 오른쪽, -면 왼쪽."""
    sh = V.sh
    (u1, v1), (u2, v2) = V.uv(P1), V.uv(P2)
    x1, y1 = V.paper_uv(u1, v1)
    x2, y2 = V.paper_uv(u2, v2)
    xd = (max(x1, x2) + off) if off > 0 else (min(x1, x2) + off)
    sgn = 1 if off > 0 else -1
    for x, y in ((x1, y1), (x2, y2)):
        if abs(xd - x) > gap:
            sh.line([(x + sgn * gap, y), (xd + sgn * 1.5, y)], "dim", z=5)
    t = text if text is not None else pre + fmt(v2 - v1) + suf
    a, b = sorted([(xd, y1), (xd, y2)], key=lambda q: q[1])
    _dim_line(sh, a, b, t, 1, size, outside, rot=90)


def adim(V, P1, P2, off, text=None, size=FS_DIM):
    """정렬 치수 (두 점을 잇는 방향). off = 종이 mm, 왼쪽 법선 방향."""
    sh = V.sh
    x1, y1 = V.P(P1)
    x2, y2 = V.P(P2)
    L = math.hypot(x2 - x1, y2 - y1)
    nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    a = (x1 + nx * off, y1 + ny * off)
    b = (x2 + nx * off, y2 + ny * off)
    s = 1 if off > 0 else -1
    if abs(off) > 1:
        sh.line([(x1 + nx * s, y1 + ny * s), (a[0] + nx * 1.5 * s, a[1] + ny * 1.5 * s)], "dim", z=5)
        sh.line([(x2 + nx * s, y2 + ny * s), (b[0] + nx * 1.5 * s, b[1] + ny * 1.5 * s)], "dim", z=5)
    t = text if text is not None else fmt(L / V.s)
    _dim_line(sh, a, b, t, 1, size)


def leader(V, P3, dx, dy, text, size=FS_DIM, dot=False, shoulder=3.0, ha=None, arrow_tip=True):
    """지시선. dx, dy = 종이 mm 오프셋."""
    sh = V.sh
    x, y = V.P(P3) if len(P3) == 3 else V.paper_uv(*P3)
    tx, ty = x + dx, y + dy
    sh.line([(x, y), (tx, ty)], "dim", z=5)
    if dot:
        sh.ax.add_patch(Circle((x, y), 0.6, facecolor="k", edgecolor="none", zorder=6))
    elif arrow_tip:
        arrow(sh, (x, y), (x - tx, y - ty))
    sgn = 1 if dx >= 0 else -1
    sh.line([(tx, ty), (tx + sgn * shoulder, ty)], "dim", z=5)
    sh.text(tx + sgn * (shoulder + 0.8), ty, text, size=size, ha=ha or ("left" if sgn > 0 else "right"),
            va="center")


def dia(V, P3, r, ang, text, L=10, size=FS_DIM):
    u, v = V.uv(P3)
    a = math.radians(ang)
    tip = (u + r * math.cos(a), v + r * math.sin(a))
    x, y = V.paper_uv(*tip)
    leader(V, tip, L * math.cos(a), L * math.sin(a), text, size=size)


def balloon(V, P3, dx, dy, num, r=3.6):
    sh = V.sh
    x, y = V.P(P3)
    bx, by = x + dx, y + dy
    L = math.hypot(dx, dy)
    ex, ey = bx - dx / L * r, by - dy / L * r
    sh.line([(x, y), (ex, ey)], "thin", z=7)
    sh.ax.add_patch(Circle((x, y), 0.7, facecolor="k", edgecolor="none", zorder=7))
    sh.ax.add_patch(Circle((bx, by), r, facecolor="white", edgecolor="k", lw=0.8, zorder=7))
    sh.text(bx, by, str(num), size=8.5, ha="center", va="center", weight="bold", z=8)


def curved_arrow(sh, center, radius, a0, a1, lw=0.9):
    """종이 좌표 원호 화살표 (a0 → a1 도, 반시계 +)."""
    cx, cy = center
    lo, hi = min(a0, a1), max(a0, a1)
    sh.ax.add_patch(Arc(center, 2 * radius, 2 * radius, theta1=lo, theta2=hi, lw=lw, color="k", zorder=6))
    t = math.radians(a1)
    tip = (cx + radius * math.cos(t), cy + radius * math.sin(t))
    sgn = 1 if a1 > a0 else -1
    tangent = (-math.sin(t) * sgn, math.cos(t) * sgn)
    arrow(sh, tip, tangent, L=2.4, w=0.8)
