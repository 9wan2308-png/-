"""전체 산출물을 다시 만듭니다: STL, DXF, 등각도 이미지, 도면 PDF/PNG.

사용법:  python build.py
"""
import os

import drawings
import models

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))


def main():
    bad = models.interference_report()
    if bad:
        raise SystemExit(f"부품 간섭 발견: {bad}")
    print("간섭 검사: 이상 없음")
    for k, v in models.clearances().items():
        print(f"  틈새 {k}: {v:.2f} mm")
    for name, ext, vol in models.export_stl(os.path.join(ROOT, "stl")):
        print(f"STL {name}: {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} mm, {vol / 1000:.1f} cm3")
    models.export_dxf(os.path.join(ROOT, "dxf", "P01_base_plate.dxf"))
    print("DXF P01_base_plate.dxf")
    models.render_iso(os.path.join(ROOT, "images", "assembly_iso.png"), size=(1600, 1200))
    print("이미지 assembly_iso.png")
    print(drawings.main(os.path.join(ROOT, "drawings")))


if __name__ == "__main__":
    main()
