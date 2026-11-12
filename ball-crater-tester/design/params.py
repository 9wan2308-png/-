"""볼 크레이터 두께 측정기: 모든 치수(mm)를 이 파일 한 곳에서 관리합니다.

치수를 바꾸려면 이 파일만 고친 뒤 build.sh 를 다시 실행하세요.
도면(PDF/PNG), 3D 프린트용 STL, 베이스판 DXF 가 모두 같은 값으로 다시 만들어집니다.

조립 좌표계
  X : 구동축 방향 (모터 쪽이 0, 오른쪽이 +)
  Y : 앞(0) → 뒤(시료 홀더 쪽이 +)
  Z : 위. 베이스판 윗면이 Z = 0
"""
import math

# ── 베이스판 (P01) ────────────────────────────────────────────
BASE_L, BASE_W, BASE_T = 250.0, 160.0, 10.0
BOLT_HOLE = 5.5          # M5 볼트 관통 구멍
FOOT_INSET = 15.0        # 고무발 위치 (모서리에서)

# ── 구동축 ────────────────────────────────────────────────────
SHAFT_Y, SHAFT_Z = 60.0, 40.0      # 축 중심 위치 (Z = 축 높이 H)
SHAFT_D = 8.0
SHAFT_X0, SHAFT_X1 = 83.0, 233.0   # 길이 150

# ── 쇠구슬과 O링 ─────────────────────────────────────────────
BALL_D = 30.0
BALL_X = 165.0                      # 공(=크레이터)이 놓이는 X 위치
BALL_DENSITY = 7.81                 # 크롬강 g/cm3
ORING_ID, ORING_CS = 7.0, 3.0       # NBR O링 내경 x 굵기
ORING_PITCH = 14.0                  # O링 두 개의 중심 간격


def _stretched_cs():
    """8mm 축에 늘려 끼운 O링의 실제 굵기 (부피 일정 가정)."""
    cs = ORING_CS
    for _ in range(30):
        cs = ORING_CS * math.sqrt((ORING_ID + ORING_CS) / (SHAFT_D + cs))
    return cs


ORING_CS_S = _stretched_cs()
ORING_TUBE_R = SHAFT_D / 2 + ORING_CS_S / 2     # O링 단면 중심의 반지름
ORING_OUTER_R = SHAFT_D / 2 + ORING_CS_S        # O링 바깥 반지름
# 축 중심 ~ 공 중심 거리 (공이 O링 두 개 위에 얹힐 때)
RHO = ORING_TUBE_R + math.sqrt((BALL_D / 2 + ORING_CS_S / 2) ** 2 - (ORING_PITCH / 2) ** 2)
BALL_MASS_G = BALL_DENSITY * (4 / 3) * math.pi * (BALL_D / 20) ** 3
BALL_WEIGHT_N = BALL_MASS_G / 1000 * 9.81

# ── 베어링 블록 (P02, 2개) ───────────────────────────────────
BRG_ID, BRG_OD, BRG_W = 8.0, 22.0, 7.0          # 608ZZ
BB_T = 14.0              # X 방향 두께
BB_BODY_W = 40.0         # 몸통 폭 (Y)
BB_H = 58.0              # 높이
BB_FLANGE_W, BB_FLANGE_T = 72.0, 8.0
BB_HOLE_DY = 29.0        # 고정 구멍: 축 중심에서 ±29
BB_SEAT_D, BB_SEAT_DEPTH = 22.2, 7.0             # 베어링 압입 자리
BB_THRU_D = 16.0
BB_XA, BB_XB = 115.0, 215.0                      # 블록 A, B 중심 X

# ── 구입 부품 위치 ───────────────────────────────────────────
COLLAR_OD, COLLAR_W = 16.0, 8.0
COLLAR1_X0, COLLAR2_X0 = 99.0, 223.0
CPL_D, CPL_L, CPL_X0 = 19.0, 25.0, 70.0          # 커플링 6x8 (D19 L25)
MOTOR_FACE_X = 67.5
GEAR_D, GEAR_L = 37.0, 25.0                      # JGB37-520 기어박스
CAN_D, CAN_L = 35.0, 35.0
MSHAFT_D, MSHAFT_L = 6.0, 15.0

# ── 모터 클램프 (P03) ────────────────────────────────────────
MC_X0, MC_X1 = 45.0, 65.0
MC_BODY_W = 50.0
MC_H = 64.0
MC_BORE = 37.4
MC_FOOT_W, MC_FOOT_T = 74.0, 6.0
MC_HOLE_DY = 31.0
MC_EAR_W, MC_EAR_TOP = 18.0, 74.0
MC_SLIT = 2.0
MC_SCREW_Z, MC_SCREW_D = 69.0, 3.4

# ── 시료 홀더 (P04) ──────────────────────────────────────────
HD_X0, HD_X1 = 127.0, 203.0
HD_WALL_T, HD_WALL_H = 10.0, 85.0
HD_FOOT_D, HD_FOOT_T = 55.0, 8.0
HD_SLOT_X = (137.0, 193.0)
HD_SLOT_U0, HD_SLOT_U1 = 30.0, 41.0   # 벽 앞면에서 잰 장공 중심 범위 (이동량 11)
HD_SLOT_W = 5.5
HD_LEDGE_D = 6.0          # 받침턱 돌출 (= 캐리어 두께)
HD_LEDGE_TOP = 37.0       # 받침턱 윗면 높이 = 캐리어 아랫면
HD_LEDGE_FRONT_H = 3.0
HD_PIN_Z = 70.0
HD_PIN_PITCH, HD_PIN_N = 8.0, 7
HD_PIN_HOLE, HD_PIN_DEPTH = 3.2, 5.0
HD_GUSSET = dict(x0=161.0, x1=169.0, u0=10.0, u1=25.0, z0=8.0, z1=45.0)

# ── 시료 캐리어 (P05) ────────────────────────────────────────
CR_W, CR_H, CR_T = 40.0, 40.0, 6.0
CR_PIN_DX = 8.0           # 핀: 중심에서 ±8
CR_PIN_Z = 33.0           # 핀: 캐리어 아랫면에서
CR_PIN_HOLE, CR_PIN_DEPTH = 3.0, 4.0
CR_GROOVE_W, CR_GROOVE_DEPTH = 0.8, 0.4
CR_BAND = (18.0, 24.0)    # 크레이터가 생기는 높이 띠 (캐리어 아랫면에서)
PIN_D, PIN_L = 3.0, 8.0

# ── 연마제 받침 (P06) ────────────────────────────────────────
TR_X0, TR_X1 = 140.0, 190.0
TR_Y0, TR_Y1 = 28.0, 80.0
TR_H, TR_WALL = 22.0, 2.0

# ── 간격 게이지 (P07) ────────────────────────────────────────
GG_STEPS = [14.0, 16.0, 18.0, 20.0, 22.0, 24.0]
GG_STEP_L, GG_T = 10.0, 6.0

# ── 하중 설정 ────────────────────────────────────────────────
SAMPLE_T = 0.5            # 기준 시료 두께 (웨이퍼 조각)
D_REF = 23.0              # 도면에 그린 기준 설정
D_MIN, D_MAX = 17.0, 28.0


def wall_y(D, ts=SAMPLE_T):
    """축 중심~시료면 거리 D 일 때 홀더 벽 앞면의 Y 위치."""
    return SHAFT_Y + D + ts + CR_T


HD_BASE_HOLE_Y = wall_y(D_MIN) + HD_SLOT_U1      # = 124.5

BASE_HOLES = [
    # (X, Y, 용도)
    (55.0, SHAFT_Y - MC_HOLE_DY, "모터 클램프"),
    (55.0, SHAFT_Y + MC_HOLE_DY, "모터 클램프"),
    (BB_XA, SHAFT_Y - BB_HOLE_DY, "베어링 블록 A"),
    (BB_XA, SHAFT_Y + BB_HOLE_DY, "베어링 블록 A"),
    (BB_XB, SHAFT_Y - BB_HOLE_DY, "베어링 블록 B"),
    (BB_XB, SHAFT_Y + BB_HOLE_DY, "베어링 블록 B"),
    (HD_SLOT_X[0], HD_BASE_HOLE_Y, "시료 홀더"),
    (HD_SLOT_X[1], HD_BASE_HOLE_Y, "시료 홀더"),
]


def theta(D):
    """공 중심이 축 바로 위에서 시료 쪽으로 기운 각도 (rad)."""
    return math.asin((D - BALL_D / 2) / RHO)


def ball_center(D=D_REF):
    th = theta(D)
    return BALL_X, SHAFT_Y + RHO * math.sin(th), SHAFT_Z + RHO * math.cos(th)


def load(D, mu=0.0):
    """시료를 누르는 힘 (N). mu = 공-시료 마찰계수 (0 이면 정적값)."""
    th = theta(D)
    t = math.tan(th)
    return BALL_WEIGHT_N * t / (1 + mu * (math.cos(th) + t * (1 + math.sin(th))))


def gauge_to_D(g, ts=SAMPLE_T):
    """간격 게이지 단(g) → 축 중심~시료면 거리 D."""
    return g + SHAFT_D / 2 - ts
