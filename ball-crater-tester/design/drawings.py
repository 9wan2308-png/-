"""도면 6장(A3)을 만듭니다: PDF 한 개 + 장별 PNG."""
import math
import os
import sys

import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle

import models as M
import params as p
from drafting import (FS_LABEL, Sheet, View, adim, arrow, balloon, curved_arrow, dia, fmt, hdim, leader, vdim,
                      zrender)

FRONT = (0, 1, 0)       # 조립도 정면 = 앞(-Y)에서 +Y 방향으로 봄
AXIAL = (1, 0, 0)       # 부품 정면 = 축 방향(-X)에서 +X 방향으로 봄
DPI = 400
YW = p.wall_y(p.D_REF)  # 기준 설정에서 홀더 벽 앞면 Y

_cache = {}


def mesh(name, factory):
    if name not in _cache:
        _cache[name] = [(name, M.to_trimesh(factory()))]
    return _cache[name]


def assembly_meshes():
    if "asm" not in _cache:
        _cache["asm"] = [(n, M.to_trimesh(m)) for n, m in M.assembly().items()]
    return _cache["asm"]


def section_meshes(x_cut):
    out = []
    for n, m in M.assembly().items():
        if n == "ball":                      # 구는 단면하지 않음
            out.append((n, M.to_trimesh(m)))
            continue
        t = m.trim_by_plane([-1, 0, 0], -x_cut)
        if not t.is_empty():
            out.append((n, M.to_trimesh(t)))
    return out


class IsoView:
    """등각 투상 그림 + 풍선용 좌표 변환."""

    def __init__(self, sheet, meshes, box, azim=-55, elev=28, dpi=300, colors=None, fill=1.04):
        self.sh = sheet
        az, el = math.radians(azim), math.radians(elev)
        self.d = -np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
        z = np.array([0, 0, 1.0])
        self.r = np.cross(self.d, z)
        self.r /= np.linalg.norm(self.r)
        self.up = np.cross(self.r, self.d)
        V = np.vstack([m.vertices for _, m in meshes])
        us, vs = V @ self.r, V @ self.up
        x0, x1, y0, y1 = box
        s = min((x1 - x0) / (np.ptp(us) * fill), (y1 - y0) / (np.ptp(vs) * fill))
        self.s = s
        self.cu, self.cv = (us.max() + us.min()) / 2, (vs.max() + vs.min()) / 2
        self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2
        hu, hv = (x1 - x0) / 2 / s, (y1 - y0) / 2 / s
        win = (self.cu - hu, self.cu + hu, self.cv - hv, self.cv + hv)
        img = zrender(meshes, self.d, self.r, self.up, win, dpi / 25.4 * s, ss=2, mode="shaded",
                      colors=colors or M.COLORS, paper_ppm=dpi / 25.4, edge_mm=0.22)
        sheet.image(img, x0, x1, y0, y1)

    def P(self, P3):
        P3 = np.array(P3, float)
        return self.cx + self.s * (P3 @ self.r - self.cu), self.cy + self.s * (P3 @ self.up - self.cv)


def label(sh, x, y, text):
    sh.text(x, y, text, size=FS_LABEL, ha="center", va="top", weight="bold")


# ═══════════════════════════════════════════════════════════
# 1장: 조립도
# ═══════════════════════════════════════════════════════════

BOM = [
    (1, "베이스판", "250×160×10, Ø5.5 관통 8곳 (BCT-02)", "1", "알루미늄 또는 아크릴 가공"),
    (2, "베어링 블록", "608ZZ 압입 (BCT-03)", "2", "3D 프린트"),
    (3, "모터 클램프", "Ø37 기어모터용 (BCT-03)", "1", "3D 프린트"),
    (4, "시료 홀더", "장공으로 앞뒤 11 조절 (BCT-04)", "1", "3D 프린트"),
    (5, "시료 캐리어", "40×40×6, 핀 2개 압입 (BCT-05)", "3", "3D 프린트 (여분 포함)"),
    (6, "연마제 받침", "50×52×22 (BCT-05)", "1", "3D 프린트"),
    (7, "간격 게이지", "14~24 계단 (BCT-05)", "1", "3D 프린트"),
    (8, "구동축", "Ø8 h6 연마봉, 길이 150 (BCT-02)", "1", "구입 후 절단"),
    (9, "베어링", "608ZZ (8×22×7)", "2", "구입"),
    (10, "축 고정 칼라", "내경 8, 외경 약 16", "2", "구입"),
    (11, "커플링", "6×8, Ø19×25", "1", "구입"),
    (12, "감속 DC 모터", "12V, JGB37-520 계열 (Ø37, 축 Ø6)", "1", "구입"),
    (13, "O링", "NBR 내경 7 × 굵기 3", "2", "구입 (여분 포함)"),
    (14, "쇠구슬", "크롬강 Ø30, 베어링볼 정밀 등급", "1", "구입 (여분 포함)"),
    (15, "평행핀", "Ø3×8", "2", "구입"),
    (16, "볼트·너트·와셔", "M5×25", "8", "구입"),
    (17, "볼트·너트", "M3×25 (클램프 조임)", "1", "구입"),
    (18, "고무발", "높이 12 이상, 접착식", "4", "구입"),
    (19, "심 와셔", "8×12×0.5 (칼라와 베어링 사이)", "2", "구입"),
]


def sheet1(pdf, outdir):
    sh = Sheet("조립도", "BCT-00", "1:2", 1)
    meshes = assembly_meshes()
    lo, hi = (-2, -2, -12), (252, 162, 87)
    s = 0.5
    F = View(sh, FRONT, "front", (0, 0, 0), (25, 132), s)
    T = View(sh, FRONT, "top", (0, 0, 0), (25, 192), s)
    R = View(sh, FRONT, "right", (0, 0, 0), (180, 132), s)
    for V in (F, T, R):
        V.render(meshes, lo, hi, dpi=DPI, pad=0)

    y, z = p.SHAFT_Y, p.SHAFT_Z
    bx, by, bz = p.ball_center()
    F.line3([(-4, y, z), (254, y, z)], "center")
    T.line3([(-4, y, 0), (254, y, 0)], "center")
    T.line3([(p.BALL_X, 40, 0), (p.BALL_X, p.BASE_W + 4, 0)], "center")
    R.center_mark((0, y, z), p.SHAFT_D / 2, 3)
    F.center_mark((bx, by, bz), p.BALL_D / 2, 2)
    # 단면 표시 A-A (정면도, X = 165): 화살표는 보는 방향(-X)
    xa, ya_lo = F.P((p.BALL_X, 0, -13))
    _, ya_hi = F.P((p.BALL_X, 0, 89))
    sh.line([(xa, ya_lo), (xa, ya_hi)], "center")
    for yy in (ya_lo - 1, ya_hi + 1):
        sh.line([(xa, yy - 2), (xa, yy + 2)], "cut")
        sh.line([(xa, yy), (xa - 4, yy)], "thin")
        arrow(sh, (xa - 6.5, yy), (-1, 0), L=2.6, w=0.7)
        sh.text(xa - 8, yy, "A", size=10, ha="right", va="center", weight="bold")

    hdim(F, (0, 0, -10), (p.BASE_L, 0, -10), -8)
    vdim(F, (0, 0, 0), (0, 0, z), -5)
    vdim(F, (p.BASE_L, 0, -10), (p.HD_X1, 0, p.HD_WALL_H), 5)
    vdim(T, (p.BASE_L, 0, 0), (p.BASE_L, p.BASE_W, 0), 5)
    vdim(T, (0, 0, 0), (0, y, 0), -5)
    hdim(T, (0, p.BASE_W, 0), (p.BALL_X, p.BASE_W, 0), 5, text="165 (공 위치)")
    hdim(R, (0, 0, -10), (0, p.BASE_W, -10), -8)
    hdim(R, (0, y, z), (0, by + p.BALL_D / 2, bz), 24, text=f"D = {fmt(p.D_REF)} (17~28 조절, BCT-01)")

    label(sh, F.P((125, 0, 0))[0], 118, "정면도 (1:2)")
    label(sh, T.P((125, 0, 0))[0], 189.5, "평면도 (1:2)")
    label(sh, R.P((0, 80, 0))[0], 118, "우측면도 (1:2)")

    iso = IsoView(sh, meshes, (262, 408, 168, 278))
    label(sh, 335, 283, "등각도 (척도 없음)")
    yw = YW
    for num, P3, (dx, dy) in [
        (1, (232, 18, 0), (6, -9)),
        (2, (p.BB_XA, p.SHAFT_Y - 20, 50), (-14, 8)),
        (3, (55, p.SHAFT_Y, p.MC_EAR_TOP), (-4, 12)),
        (12, (12, p.SHAFT_Y - 6, 50), (-6, 10)),
        (11, (80, p.SHAFT_Y - 7, 46), (-14, -10)),
        (8, (140, p.SHAFT_Y - 3, 43), (-14, -16)),
        (6, (186, p.TR_Y0, 16), (-6, -14)),
        (13, (172, p.SHAFT_Y - 5, 36), (2, -20)),
        (9, (p.BB_XB + 7, p.SHAFT_Y - 9, 40), (14, -12)),
        (10, (p.COLLAR2_X0 + 8, p.SHAFT_Y - 4, 46), (14, -2)),
        (14, (bx, by - 9, bz + 9), (-4, 18)),
        (5, (p.BALL_X + 19, yw - p.CR_T, 75), (10, 14)),
        (4, (p.HD_X1, yw, p.HD_WALL_H), (12, 6)),
    ]:
        balloon(iso, P3, dx, dy, num)
    leader(iso, (p.BALL_X + 8, yw - p.CR_T - p.SAMPLE_T, p.HD_LEDGE_TOP + 27), 14, 22, "시료",
           arrow_tip=False, dot=True)

    sh.notes(264, 150, "주기", [
        "1. 단위 mm, 3각법. 투상도 척도 1:2.",
        "2. 3D 프린트 부품(2~7): PETG 권장, 층 높이 0.2.",
        "    2·3번은 채움 100 %, 나머지는 40 % 이상.",
        "3. 베어링 자리 Ø22.2, 모터 구멍 Ø37.4는 프린터 오차를",
        "    감안한 값. 시험 출력으로 끼워 보고 조정할 것.",
        "4. 축 회전 방향: 축 윗면이 시료 반대쪽(앞)으로.",
        "    반대로 돌리면 공이 끼어 하중이 커짐 (BCT-01).",
        "5. 시료 홀더 위치 D와 하중 설정은 BCT-01 참조.",
        "6. 모터·커플링·칼라는 구입품 기준 예시 치수.",
        "    실물을 재고 3번 클램프 구멍을 맞출 것.",
        "7. M5 볼트는 베이스판 아래에서 너트로 고정",
        "    (고무발 높이 12 이상).",
        "8. 7번 게이지, 15~19번 소품은 그림에서 생략.",
    ], size=7.6, lh=4.5)

    sh.text(14, 106, "부품표", size=10, weight="bold")
    sh.table(14, 103, [("번호", 10, "c"), ("품명", 30, "l"), ("규격 · 치수", 78, "l"), ("수량", 12, "c"),
                       ("구분", 46, "l")], BOM, rh=4.4, size=6.8)
    sh.save(pdf, os.path.join(outdir, "sheet-1_assembly.png"))


# ═══════════════════════════════════════════════════════════
# 2장: 단면도 A-A, 상세 B, 하중 설정
# ═══════════════════════════════════════════════════════════

def sheet2(pdf, outdir):
    sh = Sheet("단면도 · 하중 설정", "BCT-01", "1:1, 2:1", 2)
    yw = YW
    bx, by, bz = p.ball_center()
    y0, z0 = p.SHAFT_Y, p.SHAFT_Z

    # ── 단면 A-A (1:1) ──
    S = View(sh, FRONT, "right", (0, 15, -12), (20, 175), 1.0)
    S.render(section_meshes(p.BALL_X), (0, 15, -12), (250, 152, 90), dpi=DPI, pad=0,
             cut=-p.BALL_X, hatch={"base": 45, "holder": 135, "carrier": 45, "tray": 135, "shaft": 45},
             solid=("sample",))
    S.line3([(0, 17, z0), (0, y0 + 9, z0)], "center")
    S.line3([(0, y0, z0 - 9), (0, y0, z0 + 9)], "center")
    S.center_mark((0, by, bz), p.BALL_D / 2, 2)
    vdim(S, (0, 17, 0), (0, 17, z0), -2)
    vdim(S, (0, yw + p.HD_FOOT_D, 0), (0, yw + p.HD_WALL_T, p.HD_WALL_H), 5)
    leader(S, (0, by + p.BALL_D / 2, bz), 40, 14, "접촉점 = 크레이터 위치", dot=True, arrow_tip=False)
    for num, P3, (dx, dy) in [
        (1, (0, 135, -5), (8, -10)),
        (4, (0, yw + 5, p.HD_WALL_H), (8, 8)),
        (5, (0, yw - 3, 76), (-3, 12)),
        (14, (0, by - 10, bz + 11), (-6, 18)),
        (2, (0, 44, 56), (-12, 10)),
        (3, (0, 52, p.MC_EAR_TOP), (-10, 6)),
        (13, (0, y0 - p.ORING_OUTER_R + 0.5, z0 + 2), (-14, 4)),
        (8, (0, y0 - 2, z0 - 2), (-16, -12)),
        (6, (0, 30, 14), (-10, -10)),
    ]:
        balloon(S, P3, dx, dy, num)
    cx, cy = S.P((0, 74, 54))
    sh.ax.add_patch(Circle((cx, cy), 20, fill=False, lw=0.5, ls=(0, (10, 2, 2, 2)), zorder=6))
    sh.text(cx + 15, cy - 19, "B", size=11, weight="bold", ha="left", box=True, z=8)
    label(sh, 88, 171, "단면 A-A (1:1)")
    sh.text(88, 165, "BCT-00 정면도의 X = 165 평면에서 자른 모습", size=7.2, ha="center", va="top")

    # ── 상세 B (2:1) ──
    B = View(sh, FRONT, "right", (0, 52, 30), (178, 172), 2.0)
    B.circle_uv(y0, z0, p.SHAFT_D / 2, "outline")
    B.circle_uv(y0, z0, p.ORING_OUTER_R, "thin")
    B.circle_uv(by, bz, p.BALL_D / 2, "outline")
    B.center_mark((0, y0, z0), p.SHAFT_D / 2, 2)
    B.center_mark((0, by, bz), p.BALL_D / 2, 1.5)
    ys = yw - p.CR_T
    sx0, sy0 = B.P((0, ys - p.SAMPLE_T, p.HD_LEDGE_TOP + 10))
    sx1, sy1 = B.P((0, ys, p.HD_LEDGE_TOP + 30))
    sh.rect(sx0, sx1, sy0, sy1, "thin", fill="0.15")
    B.line3([(0, ys, 31), (0, ys, 77)], "outline")
    B.line3([(0, yw, 31), (0, yw, 77)], "outline")
    B.line3([(0, ys, 77), (0, yw, 77)], "outline")
    B.line3([(0, y0, z0), (0, y0, 76)], "center")
    B.line3([(0, y0, z0), (0, by, bz)], "thin")
    adim(B, (0, y0, z0), (0, by, bz), -5, text=f"ρ = {p.RHO:.1f}")
    th = math.degrees(p.theta(p.D_REF))
    cxp, cyp = B.P((0, y0, z0))
    from matplotlib.patches import Arc
    sh.ax.add_patch(Arc((cxp, cyp), 44, 44, theta1=90 - th, theta2=90, lw=0.45, color="k", zorder=6))
    sh.text(cxp + 7, cyp + 24, f"θ = {th:.1f}°", size=7.5, ha="left")
    hdim(B, (0, y0, 76), (0, ys - p.SAMPLE_T, p.HD_LEDGE_TOP + 30), 4, text=f"D = {fmt(p.D_REF)}")
    vdim(B, (0, y0, z0), (0, by, bz), -21, text=f"{bz - z0:.1f}")
    dia(B, (0, by, bz), p.BALL_D / 2, 200, "Ø30 쇠구슬", L=12)
    # 접촉점과 회전 방향
    cpx, cpy = B.P((0, ys - p.SAMPLE_T, bz))
    sh.ax.add_patch(Circle((cpx, cpy), 0.9, color="k", zorder=7))
    sh.line([(cpx - 3, cpy + 6), (cpx - 3, cpy - 6)], "thin")
    arrow(sh, (cpx - 3, cpy - 6.5), (0, -1), L=2.4, w=0.8)
    curved_arrow(sh, (cxp, cyp), 16, 200, 300)
    bxp, byp = B.P((0, by, bz))
    curved_arrow(sh, (bxp, byp), 34, 150, 100)
    sh.text(cxp - 14, cyp - 16, "축", size=7.5, ha="right")
    sh.text(bxp - 28, byp + 29, "공", size=7.5, ha="center", va="center")
    leader(B, (0, ys - p.SAMPLE_T, p.HD_LEDGE_TOP + 11), -4, -20, "시료 (두께 t)", dot=True, arrow_tip=False)
    cxx, cyy = B.P((0, ys + p.CR_T / 2, 50))
    sh.text(cxx, cyy, "캐리어 (두께 6)", size=7.2, ha="center", va="center", rot=90)
    leader(B, (0, y0 - p.ORING_OUTER_R * 0.7, z0 - p.ORING_OUTER_R * 0.7), -10, -6, "O링", dot=True,
           arrow_tip=False)
    label(sh, 214, 171, "상세 B (2:1)")
    sh.text(214, 165, "축 윗면 ← (앞쪽), 공 표면은 접촉점에서 ↓", size=7.2, ha="center", va="top")

    # ── 하중 표 ──
    sh.text(262, 281, f"하중 설정표 (공 Ø30, 무게 W = {p.BALL_WEIGHT_N:.2f} N)", size=9.5, weight="bold", va="top")
    rows = []
    for g in p.GG_STEPS:
        D = p.gauge_to_D(g)
        rows.append((fmt(g), fmt(D), f"{math.degrees(p.theta(D)):.1f}", f"{p.load(D):.2f}",
                     f"{p.load(D, 0.2):.2f}"))
    sh.table(262, 274, [("게이지 g", 26, "c"), ("D (t=0.5)", 28, "c"), ("θ (°)", 22, "c"),
                        ("하중 정적 (N)", 32, "c"), ("하중 μ=0.2 (N)", 34, "c")], rows, rh=5.4, size=7.4)
    sh.notes(262, 228, "계산식", [
        "D = g + 4 − t     (t: 시료 두께, 4: 축 반지름)",
        f"θ = asin((D − 15) / ρ),  ρ = {p.RHO:.1f} (축 중심~공 중심)",
        "하중 = W·tanθ / (1 + μ(cosθ + tanθ(1 + sinθ)))",
        "μ = 공과 시료 사이 마찰계수 (연마제에 따라 0.1~0.3)",
        "실제 하중은 정적값보다 10~30 % 작습니다.",
        "같은 실험 안에서는 같은 게이지 단을 쓰면 됩니다.",
        "공 회전수 ≈ 축 회전수 × 0.5",
    ], size=7.6, lh=4.6)
    sh.notes(262, 186, "회전 방향을 지켜야 하는 이유", [
        "축 윗면이 시료 쪽으로 움직이면 마찰력이 공을 축과",
        "시료 사이로 밀어 넣습니다. 그러면 하중이 마찰계수에",
        "따라 크게 변하고 공이 끼일 수 있습니다.",
        "앞쪽으로 돌리면 마찰이 하중을 조금 줄이는 쪽으로",
        "작용해 안정적입니다. 모터 전선 극성으로 바꿉니다.",
    ], size=7.6, lh=4.6)

    sh.notes(14, 155, "설정과 사용 순서", [
        "1. 캐리어 앞면에 시료를 양면테이프로 붙입니다. 측정할 곳을 두 가로 홈 사이(크레이터 높이 띠)에 둡니다.",
        "2. 캐리어 핀을 홀더 소켓에 끼웁니다. 소켓 7개 중 이웃한 두 개를 쓰므로 8 간격으로 5곳에 크레이터를 냅니다.",
        "3. 공을 내려놓은 상태에서 홀더 볼트를 풉니다. 간격 게이지의 원하는 단을 축 표면과 캐리어 앞면 사이",
        "    (O링이 없는 곳)에 끼우고 홀더를 밀착시킨 뒤 볼트를 조입니다.",
        "4. 공을 O링 위에 올려 시료에 기대게 합니다. 연마제(다이아몬드 페이스트 + 희석액)를 공 윗면의",
        "    시료 쪽에 1~2방울 떨어뜨립니다.",
        "5. 모터를 켜고 축 윗면이 앞(시료 반대쪽)으로 도는지 확인합니다. 회전수는 PWM 모듈로 맞춥니다.",
        "6. 정한 시간만큼 돌린 뒤 멈추고, 캐리어를 빼서 세척한 뒤 현미경으로 봅니다.",
        "7. 기판까지 뚫리지 않았으면 캐리어를 같은 소켓에 다시 끼우고 반복합니다.",
        "    공은 이미 생긴 크레이터에 다시 자리 잡습니다.",
        "8. 크레이터마다 게이지 단, 회전수, 시간, 연마제 종류를 기록합니다.",
        "",
        "크레이터 크기 미리 보기: 깊이 h 일 때 크레이터 지름² = 8 × 15 × h",
        "    예) 3층 각 100 nm + 기판 100 nm (h = 0.4 µm) → 지름 약 219 µm",
        "층 두께 = (바깥 지름² − 안쪽 지름²) / (8 × 15)   (지름 µm 를 mm 로 바꿔 계산)",
    ], size=7.6, lh=4.7)
    sh.save(pdf, os.path.join(outdir, "sheet-2_section-and-load.png"))


# ═══════════════════════════════════════════════════════════
# 3장: 베이스판 (P01), 구동축 (P08)
# ═══════════════════════════════════════════════════════════

def sheet3(pdf, outdir):
    sh = Sheet("베이스판 · 구동축", "BCT-02", "1:1", 3,
               material="P01 알루미늄 6061 (또는 아크릴·MDF t10~12) / P08 Ø8 h6 연마봉", qty="P01 1, P08 1")
    T = View(sh, FRONT, "top", (0, 0, 0), (30, 108), 1.0)
    F = View(sh, FRONT, "front", (0, 0, 0), (30, 92), 1.0)
    T.line3([(0, 0, 0), (p.BASE_L, 0, 0), (p.BASE_L, p.BASE_W, 0), (0, p.BASE_W, 0), (0, 0, 0)])
    F.line3([(0, 0, -p.BASE_T), (p.BASE_L, 0, -p.BASE_T), (p.BASE_L, 0, 0), (0, 0, 0), (0, 0, -p.BASE_T)])
    letters = "ABCDEFGH"
    rows = []
    for (x, y, use), L in zip(p.BASE_HOLES, letters):
        T.circle_uv(x, y, p.BOLT_HOLE / 2)
        T.center_mark((x, y, 0), p.BOLT_HOLE / 2, 2)
        px_, py_ = T.P((x, y, 0))
        sh.text(px_ + 4, py_ + 3.2, L, size=8, weight="bold")
        F.line3([(x - p.BOLT_HOLE / 2, 0, -p.BASE_T), (x - p.BOLT_HOLE / 2, 0, 0)], "hidden")
        F.line3([(x + p.BOLT_HOLE / 2, 0, -p.BASE_T), (x + p.BOLT_HOLE / 2, 0, 0)], "hidden")
        rows.append((L, fmt(x), fmt(y), "Ø5.5 관통", use))
    for fx in (p.FOOT_INSET, p.BASE_L - p.FOOT_INSET):
        for fy in (p.FOOT_INSET, p.BASE_W - p.FOOT_INSET):
            T.circle_uv(fx, fy, 10, "hidden")
    leader(T, (p.FOOT_INSET + 7, p.BASE_W - p.FOOT_INSET - 7, 0), 12, -12, "고무발 Ø20 4곳 (아래면, 모서리에서 15)",
           dot=True, arrow_tip=False)
    T.line3([(-4, p.SHAFT_Y, 0), (p.BASE_L + 4, p.SHAFT_Y, 0)], "center")
    sh.text(*T.paper_uv(3, p.SHAFT_Y + 1.5), "축 중심선", size=7, va="bottom")
    # 기준점
    ox_, oy_ = T.P((0, 0, 0))
    arrow(sh, (ox_ + 14, oy_ + 2.5), (1, 0))
    sh.line([(ox_ + 2.5, oy_ + 2.5), (ox_ + 12, oy_ + 2.5)], "thin")
    arrow(sh, (ox_ + 2.5, oy_ + 14), (0, 1))
    sh.line([(ox_ + 2.5, oy_ + 2.5), (ox_ + 2.5, oy_ + 12)], "thin")
    sh.text(ox_ + 15, oy_ + 2.5, "X", size=7.5, va="center")
    sh.text(ox_ + 2.5, oy_ + 15, "Y", size=7.5, ha="center")
    sh.text(ox_ - 2, oy_ - 2, "기준 (0, 0)", size=7.5, ha="right", va="top")
    hdim(T, (0, p.BASE_W, 0), (p.BASE_L, p.BASE_W, 0), 7)
    vdim(T, (p.BASE_L, 0, 0), (p.BASE_L, p.BASE_W, 0), 8)
    vdim(F, (p.BASE_L, 0, -p.BASE_T), (p.BASE_L, 0, 0), 6)
    label(sh, 155, 104.5, "P01 베이스판 평면도 (1:1)")
    label(sh, 155, 76.5, "정면도 (1:1)")
    sh.text(292, 275, "구멍 위치표 (기준: 왼쪽 앞 모서리)", size=9, weight="bold")
    sh.table(292, 271, [("기호", 12, "c"), ("X", 16, "c"), ("Y", 16, "c"), ("구멍", 24, "c"),
                        ("용도", 46, "l")], rows, rh=5.4, size=7.4)
    sh.notes(292, 214, "P01 가공 메모", [
        "1. 알루미늄이면 드릴로 Ø5.5 관통 후 모따기.",
        "2. 아크릴·MDF는 같은 폴더의 DXF로 레이저 가공.",
        "3. 볼트 머리는 위, 너트는 아래 (고무발 12 이상).",
        "4. 모서리 C1, 일반 공차 ±0.3.",
    ], size=7.6, lh=4.6)

    # P08 구동축
    Sx = View(sh, FRONT, "front", (p.SHAFT_X0, 0, p.SHAFT_Z), (40, 45), 1.0)
    r = p.SHAFT_D / 2
    c = 0.5
    Sx.line3([(p.SHAFT_X0 + c, 0, z) for z in ()] or [(p.SHAFT_X0, 0, p.SHAFT_Z - r + c), (p.SHAFT_X0, 0, p.SHAFT_Z + r - c),
                                                        (p.SHAFT_X0 + c, 0, p.SHAFT_Z + r), (p.SHAFT_X1 - c, 0, p.SHAFT_Z + r),
                                                        (p.SHAFT_X1, 0, p.SHAFT_Z + r - c), (p.SHAFT_X1, 0, p.SHAFT_Z - r + c),
                                                        (p.SHAFT_X1 - c, 0, p.SHAFT_Z - r), (p.SHAFT_X0 + c, 0, p.SHAFT_Z - r),
                                                        (p.SHAFT_X0, 0, p.SHAFT_Z - r + c)])
    Sx.line3([(p.SHAFT_X0 + c, 0, p.SHAFT_Z + r), (p.SHAFT_X0 + c, 0, p.SHAFT_Z - r)], "thin")
    Sx.line3([(p.SHAFT_X1 - c, 0, p.SHAFT_Z + r), (p.SHAFT_X1 - c, 0, p.SHAFT_Z - r)], "thin")
    Sx.line3([(p.SHAFT_X0 - 4, 0, p.SHAFT_Z), (p.SHAFT_X1 + 4, 0, p.SHAFT_Z)], "center")
    hdim(Sx, (p.SHAFT_X0, 0, p.SHAFT_Z - r), (p.SHAFT_X1, 0, p.SHAFT_Z - r), -6)
    vdim(Sx, (p.SHAFT_X0, 0, p.SHAFT_Z - r), (p.SHAFT_X0, 0, p.SHAFT_Z + r), -6, text="Ø8 h6")
    leader(Sx, (p.SHAFT_X1, 0, p.SHAFT_Z + r - c), 6, 8, "양 끝 C0.5")
    for i, (xx, name) in enumerate([(p.CPL_X0 + p.CPL_L, "커플링 끝"), (p.COLLAR1_X0, "칼라"), (p.BB_XA, "베어링 A"),
                                    (p.BALL_X, "공 (O링 ±7)"), (p.BB_XB, "베어링 B"), (p.COLLAR2_X0, "칼라")]):
        px_, py_ = Sx.P((xx, 0, p.SHAFT_Z + r))
        h = 6 if i % 2 == 0 else 11
        sh.line([(px_, py_ + 1), (px_, py_ + h)], "thin")
        sh.text(px_, py_ + h + 1, name, size=6.6, ha="center")
    label(sh, 115, 30, "P08 구동축 (1:1)  ·  위쪽 표시는 조립 위치 참고")
    sh.save(pdf, os.path.join(outdir, "sheet-3_base-and-shaft.png"))


# ═══════════════════════════════════════════════════════════
# 4장: 베어링 블록 (P02), 모터 클램프 (P03)
# ═══════════════════════════════════════════════════════════

def sheet4(pdf, outdir):
    sh = Sheet("베어링 블록 · 모터 클램프", "BCT-03", "1:1", 4, material="PETG, 채움 100 %",
               qty="P02 2개, P03 1개")
    xa, yc, zc = p.BB_XA, p.SHAFT_Y, p.SHAFT_Z
    bb = mesh("bb", lambda: M.bearing_block(xa, "left"))
    ref = (xa, yc, 0)
    F = View(sh, AXIAL, "front", ref, (78, 150), 1.0)
    T = View(sh, AXIAL, "top", ref, (78, 236), 1.0)
    R = View(sh, AXIAL, "right", ref, (150, 150), 1.0)
    lo = (xa - 8, yc - 37, -1)
    hi = (xa + 8, yc + 37, p.BB_H + 1)
    for V in (F, T, R):
        V.render(bb, lo, hi, dpi=DPI, pad=1)
    x0, x1 = xa - p.BB_T / 2, xa + p.BB_T / 2
    sd, td = p.BB_SEAT_D / 2, p.BB_THRU_D / 2
    xs = x0 + p.BB_SEAT_DEPTH
    # 숨은선: 우측면도 (X-Z)
    for zz in (zc - sd, zc + sd):
        R.line3([(x0, 0, zz), (xs, 0, zz)], "hidden")
    for zz in (zc - td, zc + td):
        R.line3([(xs, 0, zz), (x1, 0, zz)], "hidden")
    R.line3([(xs, 0, zc - sd), (xs, 0, zc - td)], "hidden")
    R.line3([(xs, 0, zc + td), (xs, 0, zc + sd)], "hidden")
    for xx in (xa - p.BOLT_HOLE / 2, xa + p.BOLT_HOLE / 2):
        R.line3([(xx, 0, 0), (xx, 0, p.BB_FLANGE_T)], "hidden")
    R.line3([(x0 - 3, 0, zc), (x1 + 3, 0, zc)], "center")
    # 숨은선: 평면도
    for yy in (yc - sd, yc + sd):
        T.line3([(x0, yy, 0), (xs, yy, 0)], "hidden")
    for yy in (yc - td, yc + td):
        T.line3([(xs, yy, 0), (x1, yy, 0)], "hidden")
    T.line3([(xs, yc - sd, 0), (xs, yc - td, 0)], "hidden")
    T.line3([(xs, yc + td, 0), (xs, yc + sd, 0)], "hidden")
    for dy in (-p.BB_HOLE_DY, p.BB_HOLE_DY):
        T.center_mark((xa, yc + dy, 0), p.BOLT_HOLE / 2, 1.5)
    F.center_mark((xa, yc, zc), sd, 3)
    F.line3([(xa, yc - 36 - 3, zc), (xa, yc + 36 + 3, zc)], "center")
    # 치수
    fl, bw = p.BB_FLANGE_W / 2, p.BB_BODY_W / 2
    hdim(F, (xa, yc + fl, 0), (xa, yc - fl, 0), -7)
    hdim(F, (xa, yc + bw, p.BB_H), (xa, yc - bw, p.BB_H), 6)
    vdim(F, (xa, yc - fl, 0), (xa, yc - bw, p.BB_H), 6)
    vdim(F, (xa, yc + fl, 0), (xa, yc, zc), -6)
    vdim(F, (xa, yc + fl, 0), (xa, yc + fl, p.BB_FLANGE_T), -14, outside=True)
    dia(F, (xa, yc, zc), sd, 50, "Ø22.2 깊이 7 (608ZZ 압입)", L=26)
    dia(F, (xa, yc, zc), td, 228, "Ø16 관통", L=18)
    hdim(T, (x1, yc + p.BB_HOLE_DY, 0), (x1, yc - p.BB_HOLE_DY, 0), 6, text="58")
    for dy in (-p.BB_HOLE_DY, p.BB_HOLE_DY):
        T.line3([(xa, yc + dy, 0), (x1 + 1, yc + dy, 0)], "center")
    leader(T, (xa, yc - p.BB_HOLE_DY + 1.9, 0), 14, 8, "2×Ø5.5 관통")
    hdim(R, (x0, 0, 0), (x1, 0, 0), -7)
    hdim(R, (x0, 0, p.BB_H), (xs, 0, p.BB_H), 6, outside=True)
    label(sh, 78, 133, "P02 정면도 (축 방향)")
    label(sh, 78, 228.5, "평면도")
    label(sh, 150, 133, "우측면도")
    sh.notes(14, 118, "P02 베어링 블록 (2개)", [
        "1. 출력 방향: 자리 면(Ø22.2 쪽)이 위로 오게 눕혀 출력.",
        "    구멍이 둥글게 나와 베어링이 정확히 들어갑니다.",
        "2. Ø22.2는 시험 출력 후 조정 (헐거우면 −0.1, 빡빡하면 +0.1).",
        "3. 블록 B는 같은 부품을 180° 돌려 자리 면이 바깥(오른쪽)을 향하게 조립.",
        "4. 축 칼라와 베어링 사이에 심 와셔(8×12×0.5)를 넣어",
        "    칼라가 베어링 안쪽 링에만 닿게 합니다.",
    ], size=7.6, lh=4.6)

    # ── P03 모터 클램프 ──
    xm = (p.MC_X0 + p.MC_X1) / 2
    mc = mesh("mc", M.motor_clamp)
    ref = (xm, yc, 0)
    F2 = View(sh, AXIAL, "front", ref, (290, 150), 1.0)
    T2 = View(sh, AXIAL, "top", ref, (290, 253), 1.0)
    R2 = View(sh, AXIAL, "right", ref, (372, 150), 1.0)
    lo = (p.MC_X0 - 1, yc - 38, -1)
    hi = (p.MC_X1 + 1, yc + 38, p.MC_EAR_TOP + 1)
    for V in (F2, T2, R2):
        V.render(mc, lo, hi, dpi=DPI, pad=1)
    F2.center_mark((xm, yc, zc), p.MC_BORE / 2, 3)
    F2.line3([(xm, yc + p.MC_EAR_W / 2 + 2, p.MC_SCREW_Z), (xm, yc - p.MC_EAR_W / 2 - 2, p.MC_SCREW_Z)], "center")
    for zz in (p.MC_SCREW_Z - p.MC_SCREW_D / 2, p.MC_SCREW_Z + p.MC_SCREW_D / 2):
        F2.line3([(xm, yc + p.MC_EAR_W / 2, zz), (xm, yc + p.MC_SLIT / 2, zz)], "hidden")
        F2.line3([(xm, yc - p.MC_SLIT / 2, zz), (xm, yc - p.MC_EAR_W / 2, zz)], "hidden")
    for dy in (-p.MC_HOLE_DY, p.MC_HOLE_DY):
        T2.center_mark((xm, yc + dy, 0), p.BOLT_HOLE / 2, 1.5)
        for xx in (xm - p.BOLT_HOLE / 2, xm + p.BOLT_HOLE / 2):
            R2.line3([(xx, 0, 0), (xx, 0, p.MC_FOOT_T)], "hidden")
    for zz in (zc - p.MC_BORE / 2, zc + p.MC_BORE / 2):
        R2.line3([(p.MC_X0, 0, zz), (p.MC_X1, 0, zz)], "hidden")
    R2.line3([(p.MC_X0 - 3, 0, zc), (p.MC_X1 + 3, 0, zc)], "center")
    R2.center_mark((xm, 0, p.MC_SCREW_Z), p.MC_SCREW_D / 2, 1.5)
    fw, bw = p.MC_FOOT_W / 2, p.MC_BODY_W / 2
    hdim(F2, (xm, yc + fw, 0), (xm, yc - fw, 0), -7)
    hdim(F2, (xm, yc + bw, p.MC_FOOT_T), (xm, yc - bw, p.MC_FOOT_T), -21)
    hdim(F2, (xm, yc + p.MC_EAR_W / 2, p.MC_EAR_TOP), (xm, yc - p.MC_EAR_W / 2, p.MC_EAR_TOP), 5)
    vdim(F2, (xm, yc - fw, 0), (xm, yc - p.MC_EAR_W / 2, p.MC_EAR_TOP), 6)
    vdim(F2, (xm, yc - fw, 0), (xm, yc - bw, p.MC_H), 14)
    vdim(F2, (xm, yc + fw, 0), (xm, yc, zc), -6)
    vdim(F2, (xm, yc + fw, 0), (xm, yc + fw, p.MC_FOOT_T), -14, outside=True)
    dia(F2, (xm, yc, zc), p.MC_BORE / 2, 40, "Ø37.4", L=10)
    leader(F2, (xm, yc + p.MC_SLIT / 2, p.MC_EAR_TOP - 2), -14, 10, "슬릿 2")
    hdim(T2, (p.MC_X1, yc + p.MC_HOLE_DY, 0), (p.MC_X1, yc - p.MC_HOLE_DY, 0), 6, text="62")
    for dy in (-p.MC_HOLE_DY, p.MC_HOLE_DY):
        T2.line3([(xm, yc + dy, 0), (p.MC_X1 + 1, yc + dy, 0)], "center")
    leader(T2, (xm, yc - p.MC_HOLE_DY + 1.9, 0), 16, 9, "2×Ø5.5 관통")
    hdim(R2, (p.MC_X0, 0, 0), (p.MC_X1, 0, 0), -7)
    vdim(R2, (p.MC_X1, 0, 0), (p.MC_X1, 0, p.MC_SCREW_Z), 6)
    leader(R2, (xm - 1.2, 0, p.MC_SCREW_Z + 1.2), -8, 10, "Ø3.4 관통 (M3 조임)")
    label(sh, 290, 133, "P03 정면도 (축 방향)")
    label(sh, 290, 240, "평면도")
    label(sh, 372, 133, "우측면도")
    sh.notes(232, 118, "P03 모터 클램프 (1개)", [
        "1. 출력 방향: 축 방향 면을 바닥에 눕혀 출력 (구멍이 둥글게).",
        "2. 모터 기어박스 지름을 재고 구멍 = 실측 + 0.4 로 조정.",
        "3. 기어박스 부분을 물리고 M3 볼트로 슬릿을 조입니다.",
        "4. 모터 축 중심 높이 40이 베어링 블록과 같아야 합니다.",
    ], size=7.6, lh=4.6)
    sh.save(pdf, os.path.join(outdir, "sheet-4_bearing-block-and-clamp.png"))


# ═══════════════════════════════════════════════════════════
# 5장: 시료 홀더 (P04)
# ═══════════════════════════════════════════════════════════

def sheet5(pdf, outdir):
    sh = Sheet("시료 홀더", "BCT-04", "1:1", 5, material="PETG, 채움 40 % 이상, 벽 4줄", qty="1개")
    yw = YW
    hd = mesh("hd", M.holder)
    ref = (p.HD_X0, yw, 0)
    F = View(sh, FRONT, "front", ref, (52, 100), 1.0)
    T = View(sh, FRONT, "top", ref, (52, 208), 1.0)
    R = View(sh, FRONT, "right", ref, (178, 100), 1.0)
    lo = (p.HD_X0 - 1, yw - p.HD_LEDGE_D - 1, -1)
    hi = (p.HD_X1 + 1, yw + p.HD_FOOT_D + 1, p.HD_WALL_H + 1)
    for V in (F, T, R):
        V.render(hd, lo, hi, dpi=DPI, pad=1)
    X0, X1 = p.HD_X0, p.HD_X1
    pins = M.pin_x_positions()
    g = p.HD_GUSSET
    # 숨은선 (우측면도): 핀 소켓, 장공
    for zz in (p.HD_PIN_Z - p.HD_PIN_HOLE / 2, p.HD_PIN_Z + p.HD_PIN_HOLE / 2):
        R.line3([(0, yw, zz), (0, yw + p.HD_PIN_DEPTH, zz)], "hidden")
    R.line3([(0, yw + p.HD_PIN_DEPTH, p.HD_PIN_Z - p.HD_PIN_HOLE / 2),
             (0, yw + p.HD_PIN_DEPTH, p.HD_PIN_Z + p.HD_PIN_HOLE / 2)], "hidden")
    for yy in (yw + p.HD_SLOT_U0 - p.HD_SLOT_W / 2, yw + p.HD_SLOT_U1 + p.HD_SLOT_W / 2):
        R.line3([(0, yy, 0), (0, yy, p.HD_FOOT_T)], "hidden")
    # 숨은선 (정면도): 보강 리브
    F.line3([(g["x0"], 0, g["z0"]), (g["x0"], 0, g["z1"])], "hidden")
    F.line3([(g["x1"], 0, g["z0"]), (g["x1"], 0, g["z1"])], "hidden")
    for x in pins:
        F.line3([(x, 0, p.HD_PIN_Z - 3), (x, 0, p.HD_WALL_H + 2)], "center")
        F.line3([(x - 3, 0, p.HD_PIN_Z), (x + 3, 0, p.HD_PIN_Z)], "center")
    for xs in p.HD_SLOT_X:
        T.line3([(xs, yw + p.HD_SLOT_U0 - 5, 0), (xs, yw + p.HD_SLOT_U1 + 5, 0)], "center")
    # 정면도 치수
    hdim(F, (X0, 0, 0), (X1, 0, 0), -7)
    vdim(F, (X0, 0, 0), (X0, 0, p.HD_WALL_H), -7)
    hdim(F, (X0, 0, p.HD_WALL_H), (pins[0], 0, p.HD_WALL_H + 2), 4, outside=True)
    hdim(F, (pins[0], 0, p.HD_WALL_H + 2), (pins[-1], 0, p.HD_WALL_H + 2), 2, text="6×8 = 48")
    vdim(F, (X1, 0, 0), (pins[-1], 0, p.HD_PIN_Z), 7)
    vdim(F, (X1, 0, 0), (X1, 0, p.HD_LEDGE_TOP), 16)
    leader(F, (pins[2] + 1.1, 0, p.HD_PIN_Z - 1.1), 8, -20, "7×Ø3.2 깊이 5 (핀 소켓)")
    # 우측면도 치수
    hdim(R, (0, yw, 0), (0, yw + p.HD_FOOT_D, 0), -7)
    hdim(R, (0, yw, p.HD_WALL_H), (0, yw + p.HD_WALL_T, p.HD_WALL_H), 5)
    hdim(R, (0, yw - p.HD_LEDGE_D, p.HD_LEDGE_TOP), (0, yw, p.HD_LEDGE_TOP), 10, outside=True)
    vdim(R, (0, yw + p.HD_FOOT_D, 0), (0, yw + p.HD_FOOT_D, p.HD_FOOT_T), 6, outside=True)
    vdim(R, (0, yw - p.HD_LEDGE_D, p.HD_LEDGE_TOP - p.HD_LEDGE_FRONT_H), (0, yw - p.HD_LEDGE_D, p.HD_LEDGE_TOP),
         -6, outside=True)
    leader(R, (0, yw - p.HD_LEDGE_D / 2, p.HD_LEDGE_TOP - p.HD_LEDGE_FRONT_H - p.HD_LEDGE_D / 2 + 0.5), -3, -16,
           "45° 모따기")
    leader(R, (0, yw + 14, 30), 14, 16, "보강 리브: 두께 8, 높이 45, 길이 15")
    # 평면도 치수
    hdim(T, (X0, yw + p.HD_FOOT_D, 0), (p.HD_SLOT_X[0], yw + p.HD_FOOT_D, 0), 6, outside=True)
    hdim(T, (p.HD_SLOT_X[0], yw + p.HD_FOOT_D, 0), (p.HD_SLOT_X[1], yw + p.HD_FOOT_D, 0), 6)
    vdim(T, (X1, yw, 0), (p.HD_SLOT_X[1], yw + p.HD_SLOT_U0, 0), 8)
    vdim(T, (X1, yw, 0), (p.HD_SLOT_X[1], yw + p.HD_SLOT_U1, 0), 17)
    leader(T, (p.HD_SLOT_X[0] - p.HD_SLOT_W / 2, yw + 35, 0), -8, 4, "장공 ×2")
    label(sh, 90, 85, "정면도 (시료 쪽에서 봄)")
    label(sh, 90, 198, "평면도")
    label(sh, 205, 85, "우측면도")

    IsoView(sh, hd, (262, 405, 150, 268), azim=-60, elev=24, colors={"hd": M.COLORS["holder"]})
    label(sh, 333, 278, "등각도 (척도 없음)")
    sh.notes(244, 128, "P04 메모", [
        "1. 출력 방향: 발판을 아래로. 받침턱은 45° 모따기라 서포트가 필요 없습니다.",
        "2. 핀 소켓 Ø3.2는 출력 후 Ø3.2 드릴로 한 번 다듬습니다.",
        "3. 장공(폭 5.5) 중심은 벽 앞면에서 30~41 → 홀더를 앞뒤로 11 움직여",
        "    D = 17~28 을 맞춥니다.",
        "4. 받침턱 윗면(높이 37)이 캐리어 아랫면 기준입니다.",
        "5. 볼트 구멍(베이스판 G, H)은 Y = 124.5 위치입니다.",
    ], size=7.4, lh=4.6)
    sh.save(pdf, os.path.join(outdir, "sheet-5_sample-holder.png"))


# ═══════════════════════════════════════════════════════════
# 6장: 캐리어 (P05), 연마제 받침 (P06), 간격 게이지 (P07)
# ═══════════════════════════════════════════════════════════

def sheet6(pdf, outdir):
    sh = Sheet("캐리어 · 받침 · 게이지", "BCT-05", "2:1, 1:1", 6, material="PETG (P07은 PLA 가능)",
               qty="P05 3개, P06 1개, P07 1개")
    yw = YW
    xc = p.BALL_X
    zb = p.HD_LEDGE_TOP
    ys0 = yw - p.CR_T
    cr = mesh("cr", M.carrier)
    ref = (xc - p.CR_W / 2, ys0, zb)
    s = 2.0
    F = View(sh, FRONT, "front", ref, (40, 170), s)
    T = View(sh, FRONT, "top", ref, (40, 264), s)
    R = View(sh, FRONT, "right", ref, (150, 170), s)
    lo = (xc - p.CR_W / 2 - 0.5, ys0 - 0.5, zb - 0.5)
    hi = (xc + p.CR_W / 2 + 0.5, yw + 0.5, zb + p.CR_H + 0.5)
    for V in (F, T, R):
        V.render(cr, lo, hi, dpi=DPI, pad=0.5)
    pz = zb + p.CR_PIN_Z
    for dx in (-p.CR_PIN_DX, p.CR_PIN_DX):
        F.circle_uv(xc + dx, pz, p.CR_PIN_HOLE / 2, "hidden")
        F.center_mark((xc + dx, 0, pz), p.CR_PIN_HOLE / 2, 1)
        for xx in (xc + dx - p.CR_PIN_HOLE / 2, xc + dx + p.CR_PIN_HOLE / 2):
            T.line3([(xx, yw - p.CR_PIN_DEPTH, 0), (xx, yw, 0)], "hidden")
    for zz in (pz - p.CR_PIN_HOLE / 2, pz + p.CR_PIN_HOLE / 2):
        R.line3([(0, yw - p.CR_PIN_DEPTH, zz), (0, yw, zz)], "hidden")
    R.line3([(0, yw - p.CR_PIN_DEPTH, pz - p.CR_PIN_HOLE / 2), (0, yw - p.CR_PIN_DEPTH, pz + p.CR_PIN_HOLE / 2)],
            "hidden")
    x0c, x1c = xc - p.CR_W / 2, xc + p.CR_W / 2
    hdim(F, (x0c, 0, zb), (x1c, 0, zb), -7)
    vdim(F, (x0c, 0, zb), (x0c, 0, zb + p.CR_H), -7)
    vdim(F, (x1c, 0, zb), (xc + p.CR_PIN_DX, 0, pz), 7)
    vdim(F, (x1c, 0, zb), (x1c, 0, zb + p.CR_BAND[0]), 16)
    vdim(F, (x1c, 0, zb), (x1c, 0, zb + p.CR_BAND[1]), 25)
    leader(F, (xc + p.CR_PIN_DX + 1.1, 0, pz - 1.1), 3, -40, "2×Ø3 깊이 4\n간격 16 (뒷면)")
    leader(F, (xc - 15, 0, zb + p.CR_BAND[1]), -10, 41, "홈 3곳")
    hdim(R, (0, ys0, zb), (0, yw, zb), -7)
    label(sh, 80, 157, "P05 시료 캐리어 정면도 (2:1)")
    label(sh, 80, 261, "평면도 (2:1)")
    label(sh, 156, 157, "우측면도")
    sh.text(156, 151, "(왼쪽 면이 앞면)", size=7.2, ha="center", va="top")
    sh.notes(14, 140, "P05 메모 (3개 출력)", [
        "1. 출력 방향: 앞면(홈 있는 면)을 바닥에 붙여 출력 → 시료 면이 평평합니다.",
        "2. 평행핀 Ø3×8 두 개를 뒷면 구멍에 4 압입 (4 돌출).",
        "3. 홈 3곳은 폭 0.8, 깊이 0.4. 두 가로 홈 사이(아랫면에서 18~24)가",
        "    크레이터가 생기는 높이입니다.",
        "4. 시료는 얇은 양면테이프로 붙이고, 측정 후 아세톤으로 떼어 냅니다.",
    ], size=7.4, lh=4.6)

    # ── P06 연마제 받침 (1:1) ──
    tr = mesh("tr", M.tray)
    ref = (p.TR_X0, p.TR_Y0, 0)
    F2 = View(sh, FRONT, "front", ref, (200, 178), 1.0)
    T2 = View(sh, FRONT, "top", ref, (200, 212), 1.0)
    lo, hi = (p.TR_X0 - 1, p.TR_Y0 - 1, -1), (p.TR_X1 + 1, p.TR_Y1 + 1, p.TR_H + 1)
    for V in (F2, T2):
        V.render(tr, lo, hi, dpi=DPI, pad=1)
    w = p.TR_WALL
    F2.line3([(p.TR_X0 + w, 0, p.TR_H), (p.TR_X0 + w, 0, w), (p.TR_X1 - w, 0, w), (p.TR_X1 - w, 0, p.TR_H)], "hidden")
    hdim(F2, (p.TR_X0, 0, 0), (p.TR_X1, 0, 0), -7)
    vdim(F2, (p.TR_X0, 0, 0), (p.TR_X0, 0, p.TR_H), -7)
    vdim(T2, (p.TR_X1, p.TR_Y0, 0), (p.TR_X1, p.TR_Y1, 0), 7)
    leader(T2, (p.TR_X0 + w / 2, p.TR_Y1 - 12, 0), -8, 10, "벽·바닥 두께 2")
    label(sh, 225, 163, "P06 연마제 받침 (1:1)")
    sh.text(225, 157, "정면도 · 평면도", size=7.2, ha="center", va="top")

    # ── P07 간격 게이지 (1:1) ──
    gg = mesh("gg", M.gauge)
    n = len(p.GG_STEPS)
    L = n * p.GG_STEP_L
    ref = (0, 0, 0)
    T3 = View(sh, FRONT, "top", ref, (282, 212), 1.0)
    F3 = View(sh, FRONT, "front", ref, (282, 196), 1.0)
    lo, hi = (-1, -1, -1), (L + 1, max(p.GG_STEPS) + 1, p.GG_T + 1)
    for V in (T3, F3):
        V.render(gg, lo, hi, dpi=DPI, pad=1)
    for i, gv in enumerate(p.GG_STEPS):
        x, y = T3.P((i * p.GG_STEP_L + p.GG_STEP_L / 2, gv / 2, 0))
        sh.text(x, y, fmt(gv), size=8, ha="center", va="center", weight="bold")
    hdim(F3, (0, 0, 0), (L, 0, 0), -6, text=f"{n}×10 = {fmt(L)}")
    vdim(F3, (L, 0, 0), (L, 0, p.GG_T), 6, outside=True)
    vdim(T3, (L, 0, 0), (L, p.GG_STEPS[-1], 0), 7)
    vdim(T3, (0, 0, 0), (0, p.GG_STEPS[0], 0), -6)
    label(sh, 312, 182, "P07 간격 게이지 (1:1)")
    sh.text(312, 176, "평면도 · 정면도 (단 폭 = g, 2씩 증가)", size=7.2, ha="center", va="top")

    IsoView(sh, cr + tr, (345, 408, 208, 282), azim=-120, elev=30, colors={"cr": (0.98, 0.8, 0.3),
                                                                            "tr": (0.55, 0.8, 0.55)})
    sh.notes(200, 140, "P06 · P07 메모", [
        "1. 받침은 축 아래 베어링 블록 사이에 그냥 놓습니다 (고정 없음).",
        "2. 게이지 각 단 윗면에 g 값(14~24)을 펜이나 각인으로 표시합니다.",
        "3. 게이지 사용: 공을 뺀 상태에서 축 표면과 캐리어 앞면 사이에",
        "    끼우고 홀더를 밀착 → D = g + 4 − t (BCT-01 하중 표).",
        "4. 게이지는 정확도가 중요하므로 출력 후 캘리퍼스로 확인합니다.",
    ], size=7.4, lh=4.6)
    sh.save(pdf, os.path.join(outdir, "sheet-6_carrier-tray-gauge.png"))


SHEETS = [sheet1, sheet2, sheet3, sheet4, sheet5, sheet6]


def main(outdir, only=None):
    os.makedirs(outdir, exist_ok=True)
    pdf_path = os.path.join(outdir, "ball-crater-tester_drawings.pdf")
    sheets = SHEETS if not only else [SHEETS[i - 1] for i in only]
    if only:
        for fn in sheets:
            fn(None, outdir)
            print("done", fn.__name__, flush=True)
        return None
    with PdfPages(pdf_path) as pdf:
        d = pdf.infodict()
        d["Title"] = "볼 크레이터 두께 측정기 도면"
        for fn in sheets:
            fn(pdf, outdir)
            print("done", fn.__name__, flush=True)
    return pdf_path


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "drawings")
    only = [int(a) for a in sys.argv[2:]] or None
    print(main(out, only))
