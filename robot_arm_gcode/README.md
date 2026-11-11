# 4축 로봇 팔 — Bambu Lab P2S용 G-code

`robot_arm_3d.zip`의 판 묶음 STL(`plate1~3`)을 Bambu Studio 02.09.01.70으로 슬라이스한 파일입니다.
`plate3_control_box`는 메인 만능기판 크기를 120×80으로 바꾼 버전(`robot_arm_3d_1.zip`)으로 다시 슬라이스했습니다. `plate1`, `plate2`는 두 버전의 STL이 같습니다.
Bambu Studio의 **플레이트 슬라이스 파일 내보내기**와 같은 형식(`.gcode.3mf`)이라 USB에 넣어 P2S에서 바로 출력할 수 있습니다.

## 파일

| 파일 | 들어 있는 부품 | 예상 시간 | 필라멘트 | 높이 |
| --- | --- | --- | --- | --- |
| `plate1_arm_parts.gcode.3mf` | P0 시험편, P4, P5, P6a, P6b, P9 ×2 | 1시간 16분 | 28.7 g | 34.4 mm |
| `plate2_base.gcode.3mf` | P1, P2, P3 | 2시간 28분 | 102.5 g | 44.6 mm |
| `plate3_control_box.gcode.3mf` | P7, P8 | 3시간 34분 | 145.1 g | 52.4 mm |

합계는 약 7시간 18분, 필라멘트 약 276 g입니다. 예상 시간에는 출력 전 준비 동작이 포함되어 있습니다.

## 슬라이스 설정 (센터 규칙: 기본설정 그대로)

- 프린터: Bambu Lab P2S 0.4 nozzle
- 공정: 0.20mm Standard @BBL P2S (레이어 0.2 mm, 벽 2겹, 채움 15%)
- 필라멘트: Bambu PLA Basic @BBL P2S (노즐 220 °C, 베드 55 °C)
- 판: Textured PEI Plate (P2S 기본 판)
- 서포트 없음, 자동 방향 맞춤 없음. STL이 이미 출력 방향으로 저장되어 있어 위치와 방향을 그대로 썼습니다.

## 출력 방법

1. `.gcode.3mf` 파일을 본인 USB에 복사합니다.
2. P2S에 USB를 꽂고 화면에서 파일을 골라 출력합니다.
3. 프린터 화면에 미리보기 그림은 나오지 않습니다. 명령줄로 슬라이스해서 그림을 넣지 못했기 때문이고, 출력에는 영향이 없습니다.

## 주의

- 프린터에 끼운 판이 Textured PEI가 아니면 베드 온도가 맞지 않습니다. 이때는 센터 PC의 Bambu Studio에서 판 종류를 바꾸고 다시 슬라이스하세요.
- `plate3_control_box`는 원본 README대로 메인 기판 납땜 배치와 LCD·조이스틱 실측을 확인한 뒤 출력하세요.
- `params.py`를 고쳐 STL을 다시 만들었다면 이 G-code는 쓰지 말고 새 STL로 다시 슬라이스해야 합니다.
