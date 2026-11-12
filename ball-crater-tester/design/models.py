"""3D 모델: 3D 프린트 부품(STL), 베이스판(DXF), 조립 확인(간섭 검사)과 등각 투상 이미지를 만듭니다."""
import math
import os

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

import params as p

SEG = 96

# ── 기본 도형 ────────────────────────────────────────────────


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def _xf(m, rows):
    return m.transform(np.array(rows, dtype=float))


def cyl_x(x0, x1, y, z, r, seg=SEG):
    # (a, b, t) -> (t + x0, a + y, b + z)
    return _xf(Manifold.cylinder(x1 - x0, r, r, seg), [[0, 0, 1, x0], [1, 0, 0, y], [0, 1, 0, z]])


def cyl_y(y0, y1, x, z, r, seg=SEG):
    # (a, b, t) -> (b + x, t + y0, a + z)
    return _xf(Manifold.cylinder(y1 - y0, r, r, seg), [[0, 1, 0, x], [0, 0, 1, y0], [1, 0, 0, z]])


def cyl_z(z0, z1, x, y, r, seg=SEG):
    return Manifold.cylinder(z1 - z0, r, r, seg).translate([x, y, z0])


def prism_x(poly_yz, x0, x1):
    """(y, z) 다각형을 X 방향으로 x0~x1 만큼 뽑아냅니다."""
    cs = CrossSection([poly_yz])
    return _xf(Manifold.extrude(cs, x1 - x0), [[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def slot_y(x, y0, y1, w, z0, z1):
    r = w / 2
    return cyl_z(z0, z1, x, y0, r) + cyl_z(z0, z1, x, y1, r) + box(x - r, x + r, y0, y1, z0, z1)


def torus_x(x, y, z, R, r):
    t = Manifold.revolve(CrossSection.circle(r, 48).translate((R, 0)), SEG)
    return _xf(t, [[0, 0, 1, x], [1, 0, 0, y], [0, 1, 0, z]])


# ── 제작 부품 ───────────────────────────────────────────────


def base_plate():
    m = box(0, p.BASE_L, 0, p.BASE_W, -p.BASE_T, 0)
    for x, y, _ in p.BASE_HOLES:
        m -= cyl_z(-p.BASE_T - 1, 1, x, y, p.BOLT_HOLE / 2)
    return m


def bearing_block(xc, seat_side="left"):
    x0, x1 = xc - p.BB_T / 2, xc + p.BB_T / 2
    yc = p.SHAFT_Y
    m = box(x0, x1, yc - p.BB_BODY_W / 2, yc + p.BB_BODY_W / 2, 0, p.BB_H)
    m += box(x0, x1, yc - p.BB_FLANGE_W / 2, yc + p.BB_FLANGE_W / 2, 0, p.BB_FLANGE_T)
    m -= cyl_x(x0 - 1, x1 + 1, yc, p.SHAFT_Z, p.BB_THRU_D / 2)
    if seat_side == "left":
        m -= cyl_x(x0 - 1, x0 + p.BB_SEAT_DEPTH, yc, p.SHAFT_Z, p.BB_SEAT_D / 2)
    else:
        m -= cyl_x(x1 - p.BB_SEAT_DEPTH, x1 + 1, yc, p.SHAFT_Z, p.BB_SEAT_D / 2)
    for dy in (-p.BB_HOLE_DY, p.BB_HOLE_DY):
        m -= cyl_z(-1, p.BB_FLANGE_T + 1, xc, yc + dy, p.BOLT_HOLE / 2)
    return m


def motor_clamp():
    yc, xc = p.SHAFT_Y, (p.MC_X0 + p.MC_X1) / 2
    m = box(p.MC_X0, p.MC_X1, yc - p.MC_BODY_W / 2, yc + p.MC_BODY_W / 2, 0, p.MC_H)
    m += box(p.MC_X0, p.MC_X1, yc - p.MC_FOOT_W / 2, yc + p.MC_FOOT_W / 2, 0, p.MC_FOOT_T)
    m += box(p.MC_X0, p.MC_X1, yc - p.MC_EAR_W / 2, yc + p.MC_EAR_W / 2, p.MC_H - 1, p.MC_EAR_TOP)
    m -= cyl_x(p.MC_X0 - 1, p.MC_X1 + 1, yc, p.SHAFT_Z, p.MC_BORE / 2)
    m -= box(p.MC_X0 - 1, p.MC_X1 + 1, yc - p.MC_SLIT / 2, yc + p.MC_SLIT / 2, p.SHAFT_Z, p.MC_EAR_TOP + 1)
    m -= cyl_y(yc - p.MC_EAR_W / 2 - 1, yc + p.MC_EAR_W / 2 + 1, xc, p.MC_SCREW_Z, p.MC_SCREW_D / 2)
    for dy in (-p.MC_HOLE_DY, p.MC_HOLE_DY):
        m -= cyl_z(-1, p.MC_FOOT_T + 1, xc, yc + dy, p.BOLT_HOLE / 2)
    return m


def pin_x_positions():
    n = p.HD_PIN_N
    return [p.BALL_X + (k - (n - 1) / 2) * p.HD_PIN_PITCH for k in range(n)]


def holder(D=p.D_REF):
    yw = p.wall_y(D)
    X0, X1 = p.HD_X0, p.HD_X1
    m = box(X0, X1, yw, yw + p.HD_WALL_T, 0, p.HD_WALL_H)
    m += box(X0, X1, yw, yw + p.HD_FOOT_D, 0, p.HD_FOOT_T)
    lt, ld, lf = p.HD_LEDGE_TOP, p.HD_LEDGE_D, p.HD_LEDGE_FRONT_H
    ledge = [(yw - ld, lt - lf), (yw + 0.5, lt - lf - ld - 0.5), (yw + 0.5, lt), (yw - ld, lt)]
    m += prism_x(ledge, X0, X1)
    g = p.HD_GUSSET
    m += prism_x([(yw + g["u0"] - 0.5, g["z0"] - 0.5), (yw + g["u1"], g["z0"] - 0.5),
                  (yw + g["u0"] - 0.5, g["z1"])], g["x0"], g["x1"])
    for xs in p.HD_SLOT_X:
        m -= slot_y(xs, yw + p.HD_SLOT_U0, yw + p.HD_SLOT_U1, p.HD_SLOT_W, -1, p.HD_FOOT_T + 1)
    for x in pin_x_positions():
        m -= cyl_y(yw - 1, yw + p.HD_PIN_DEPTH, x, p.HD_PIN_Z, p.HD_PIN_HOLE / 2, 48)
    return m


def carrier(D=p.D_REF, xc=p.BALL_X):
    yw = p.wall_y(D)
    y0, y1 = yw - p.CR_T, yw
    z0 = p.HD_LEDGE_TOP
    m = box(xc - p.CR_W / 2, xc + p.CR_W / 2, y0, y1, z0, z0 + p.CR_H)
    for dx in (-p.CR_PIN_DX, p.CR_PIN_DX):
        m -= cyl_y(y1 - p.CR_PIN_DEPTH, y1 + 1, xc + dx, z0 + p.CR_PIN_Z, p.CR_PIN_HOLE / 2, 48)
    gw, gd = p.CR_GROOVE_W, p.CR_GROOVE_DEPTH
    m -= box(xc - gw / 2, xc + gw / 2, y0 - 1, y0 + gd, z0 - 1, z0 + p.CR_H + 1)
    for zb in p.CR_BAND:
        m -= box(xc - p.CR_W / 2 - 1, xc + p.CR_W / 2 + 1, y0 - 1, y0 + gd, z0 + zb - gw / 2, z0 + zb + gw / 2)
    return m


def pins(D=p.D_REF, xc=p.BALL_X):
    yw = p.wall_y(D)
    out = None
    for dx in (-p.CR_PIN_DX, p.CR_PIN_DX):
        c = cyl_y(yw - p.CR_PIN_DEPTH, yw - p.CR_PIN_DEPTH + p.PIN_L, xc + dx,
                  p.HD_LEDGE_TOP + p.CR_PIN_Z, p.PIN_D / 2 - 0.01, 32)
        out = c if out is None else out + c
    return out


def tray():
    m = box(p.TR_X0, p.TR_X1, p.TR_Y0, p.TR_Y1, 0, p.TR_H)
    w = p.TR_WALL
    m -= box(p.TR_X0 + w, p.TR_X1 - w, p.TR_Y0 + w, p.TR_Y1 - w, w, p.TR_H + 1)
    return m


def gauge():
    m = None
    for i, g in enumerate(p.GG_STEPS):
        b = box(i * p.GG_STEP_L - (0.01 if i else 0), (i + 1) * p.GG_STEP_L, 0, g, 0, p.GG_T)
        m = b if m is None else m + b
    return m


# ── 구입 부품 (조립 확인과 그림용) ──────────────────────────


def purchased(D=p.D_REF):
    y, z = p.SHAFT_Y, p.SHAFT_Z
    parts = {}
    parts["shaft"] = cyl_x(p.SHAFT_X0, p.SHAFT_X1, y, z, p.SHAFT_D / 2)
    b = None
    for xs in (p.BB_XA - p.BB_T / 2, p.BB_XB + p.BB_T / 2 - p.BRG_W):
        ring = cyl_x(xs, xs + p.BRG_W, y, z, p.BRG_OD / 2 - 0.01) - cyl_x(xs - 1, xs + p.BRG_W + 1, y, z, p.BRG_ID / 2 + 0.01)
        b = ring if b is None else b + ring
    parts["bearings"] = b
    c = None
    for xs in (p.COLLAR1_X0, p.COLLAR2_X0):
        ring = cyl_x(xs, xs + p.COLLAR_W, y, z, p.COLLAR_OD / 2) - cyl_x(xs - 1, xs + p.COLLAR_W + 1, y, z, p.SHAFT_D / 2 + 0.01)
        c = ring if c is None else c + ring
    parts["collars"] = c
    parts["coupling"] = (cyl_x(p.CPL_X0, p.CPL_X0 + p.CPL_L, y, z, p.CPL_D / 2)
                         - cyl_x(p.CPL_X0 - 1, p.CPL_X0 + p.CPL_L + 1, y, z, p.SHAFT_D / 2 + 0.01))
    fx = p.MOTOR_FACE_X
    parts["motor"] = (cyl_x(fx - p.GEAR_L, fx, y, z, p.GEAR_D / 2 - 0.01)
                      + cyl_x(fx - p.GEAR_L - p.CAN_L, fx - p.GEAR_L + 0.01, y, z, p.CAN_D / 2)
                      + cyl_x(fx - 0.01, fx + p.MSHAFT_L, y, z, p.MSHAFT_D / 2))
    o = None
    for dx in (-p.ORING_PITCH / 2, p.ORING_PITCH / 2):
        t = torus_x(p.BALL_X + dx, y, z, p.ORING_TUBE_R, p.ORING_CS_S / 2 - 0.005)
        o = t if o is None else o + t
    parts["orings"] = o
    bx, by, bz = p.ball_center(D)
    parts["ball"] = Manifold.sphere(p.BALL_D / 2 - 0.005, 128).translate([bx, by, bz])
    yw = p.wall_y(D)
    parts["sample"] = box(p.BALL_X - 10, p.BALL_X + 10, yw - p.CR_T - p.SAMPLE_T, yw - p.CR_T,
                          p.HD_LEDGE_TOP + 10, p.HD_LEDGE_TOP + 30)
    parts["pins"] = pins(D)
    return parts


def made(D=p.D_REF):
    return {
        "base": base_plate(),
        "block_a": bearing_block(p.BB_XA, "left"),
        "block_b": bearing_block(p.BB_XB, "right"),
        "clamp": motor_clamp(),
        "holder": holder(D),
        "carrier": carrier(D),
        "tray": tray(),
    }


def assembly(D=p.D_REF):
    a = made(D)
    a.update(purchased(D))
    return a


# ── 내보내기 ────────────────────────────────────────────────


def to_trimesh(m):
    mesh = m.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                           faces=np.asarray(mesh.tri_verts), process=True)


def _place_on_bed(tm):
    lo, hi = tm.bounds
    tm.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])
    return tm


def _rot(tm, rows):
    M = np.eye(4)
    M[:3, :3] = np.array(rows, dtype=float)
    tm.apply_transform(M)
    return tm


def export_stl(outdir):
    os.makedirs(outdir, exist_ok=True)
    items = {
        # 파일명: (모델, 출력 방향 회전)
        "P02_bearing_block_x2.stl": (bearing_block(p.BB_XA, "left"), [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),
        "P03_motor_clamp.stl": (motor_clamp(), [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]),
        "P04_sample_holder.stl": (holder(), None),
        "P05_sample_carrier.stl": (carrier(), [[1, 0, 0], [0, 0, -1], [0, 1, 0]]),
        "P06_drip_tray.stl": (tray(), None),
        "P07_gap_gauge.stl": (gauge(), None),
    }
    out = []
    for name, (m, rot) in items.items():
        tm = to_trimesh(m)
        if rot is not None:
            _rot(tm, rot)
        _place_on_bed(tm)
        assert tm.is_watertight, name
        path = os.path.join(outdir, name)
        tm.export(path)
        out.append((name, tm.extents, tm.volume))
    return out


def export_dxf(path):
    import ezdxf
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    doc.layers.add("CUT", color=1)
    doc.layers.add("NOTE", color=5)
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0), (p.BASE_L, 0), (p.BASE_L, p.BASE_W), (0, p.BASE_W)],
                       close=True, dxfattribs={"layer": "CUT"})
    for x, y, _ in p.BASE_HOLES:
        msp.add_circle((x, y), p.BOLT_HOLE / 2, dxfattribs={"layer": "CUT"})
    msp.add_text("P01 BASE PLATE 250x160 t10, 8 x D5.5 THRU", height=4,
                 dxfattribs={"layer": "NOTE"}).set_placement((0, -10))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    doc.saveas(path)


# ── 간섭 검사 ───────────────────────────────────────────────

# 서로 닿거나 끼워지는 것이 정상인 쌍
_ALLOWED = {
    frozenset(x) for x in [
        ("shaft", "bearings"), ("shaft", "collars"), ("shaft", "coupling"), ("motor", "coupling"),
        ("shaft", "orings"), ("bearings", "block_a"), ("bearings", "block_b"),
        ("pins", "carrier"), ("pins", "holder"), ("sample", "carrier"),
        ("carrier", "holder"), ("ball", "orings"), ("ball", "sample"), ("motor", "clamp"),
        ("block_a", "base"), ("block_b", "base"), ("clamp", "base"), ("holder", "base"), ("tray", "base"),
    ]
}


def interference_report(D=p.D_REF, tol=0.05):
    a = assembly(D)
    names = list(a)
    bad = []
    for i, n1 in enumerate(names):
        for n2 in names[i + 1:]:
            if frozenset((n1, n2)) in _ALLOWED:
                continue
            v = (a[n1] ^ a[n2]).volume()
            if v > tol:
                bad.append((n1, n2, v))
    return bad


def clearances(D=p.D_REF):
    a = assembly(D)
    pairs = [("ball", "shaft"), ("ball", "holder"), ("ball", "carrier"), ("ball", "tray"),
             ("orings", "tray"), ("holder", "block_a"), ("holder", "block_b"), ("tray", "block_a")]
    return {f"{x}-{y}": a[x].min_gap(a[y], 30) for x, y in pairs}


# ── 등각 투상 렌더 (z-버퍼) ─────────────────────────────────

COLORS = {
    "base": (0.70, 0.72, 0.75), "block_a": (0.30, 0.55, 0.85), "block_b": (0.30, 0.55, 0.85),
    "clamp": (0.30, 0.55, 0.85), "holder": (0.95, 0.60, 0.20), "carrier": (0.98, 0.80, 0.30),
    "tray": (0.55, 0.80, 0.55), "shaft": (0.80, 0.80, 0.82), "bearings": (0.55, 0.55, 0.58),
    "collars": (0.60, 0.60, 0.62), "coupling": (0.75, 0.76, 0.78), "motor": (0.25, 0.25, 0.28),
    "orings": (0.12, 0.12, 0.12), "ball": (0.85, 0.86, 0.90), "sample": (0.45, 0.30, 0.60),
    "pins": (0.6, 0.6, 0.6),
}


def render_iso(path, D=p.D_REF, size=(1800, 1350), azim=-55, elev=28, margin=0.06):
    a = assembly(D)
    az, el = math.radians(azim), math.radians(elev)
    # 카메라: 보는 사람은 (방위각 az, 고도 el) 방향에 있음. 시선 d, 화면 오른쪽 r, 화면 위 u (정투상)
    d = -np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    up = np.array([0, 0, 1.0])
    r = np.cross(d, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, d)
    light = -d * 0.6 + u * 0.6 + r * 0.3
    light /= np.linalg.norm(light)

    meshes = [(n, to_trimesh(m)) for n, m in a.items()]
    allv = np.vstack([tm.vertices for _, tm in meshes])
    sx, sy = allv @ r, allv @ u
    W, H = size
    span = max((sx.max() - sx.min()) / (W * (1 - 2 * margin)), (sy.max() - sy.min()) / (H * (1 - 2 * margin)))
    cx, cy = (sx.max() + sx.min()) / 2, (sy.max() + sy.min()) / 2

    zbuf = np.full((H, W), np.inf)
    img = np.ones((H, W, 3))
    ids = np.full((H, W), -1)
    nbuf = np.zeros((H, W, 3))
    for pid, (name, tm) in enumerate(meshes):
        V = tm.vertices
        px = (V @ r - cx) / span + W / 2
        py = H / 2 - (V @ u - cy) / span
        pz = V @ d
        col = np.array(COLORS.get(name, (0.7, 0.7, 0.7)))
        fn = tm.face_normals
        for f, n in zip(tm.faces, fn):
            if n @ d > 0:          # 뒷면은 건너뜀
                continue
            x, y, zz = px[f], py[f], pz[f]
            x0, x1 = int(max(0, math.floor(x.min()))), int(min(W - 1, math.ceil(x.max())))
            y0, y1 = int(max(0, math.floor(y.min()))), int(min(H - 1, math.ceil(y.max())))
            if x1 < x0 or y1 < y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
            if abs(den) < 1e-12:
                continue
            w0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
            w1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            depth = w0 * zz[0] + w1 * zz[1] + w2 * zz[2]
            sub = zbuf[y0:y1 + 1, x0:x1 + 1]
            upd = inside & (depth < sub)
            if not upd.any():
                continue
            sub[upd] = depth[upd]
            shade = 0.35 + 0.65 * max(0.0, float(n @ light))
            img[y0:y1 + 1, x0:x1 + 1][upd] = np.clip(col * shade, 0, 1)
            ids[y0:y1 + 1, x0:x1 + 1][upd] = pid
            nbuf[y0:y1 + 1, x0:x1 + 1][upd] = n
    # 윤곽선: 부품 경계, 깊이 불연속, 면 방향이 크게 바뀌는 곳
    edge = np.zeros((H, W), bool)
    for ax in (0, 1):
        a1 = np.roll(ids, 1, axis=ax)
        edge |= ids != a1
        z1 = np.roll(zbuf, 1, axis=ax)
        fin = np.isfinite(zbuf) & np.isfinite(z1)
        dz = np.zeros_like(zbuf)
        dz[fin] = np.abs(zbuf[fin] - z1[fin])
        edge |= dz > 2.0
        n1 = np.roll(nbuf, 1, axis=ax)
        edge |= (ids >= 0) & ((nbuf * n1).sum(-1) < 0.8)
    img[edge] = img[edge] * 0.25
    import matplotlib.image as mpimg
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mpimg.imsave(path, img)
    return path


if __name__ == "__main__":
    print("interference:", interference_report())
    for k, v in clearances().items():
        print(f"  gap {k}: {v:.2f} mm")
