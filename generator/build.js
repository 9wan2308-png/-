// 편집 가능한 한국어 PPT 템플릿 생성 스크립트 (1단계: pptxgenjs)
// 레이아웃 배경/장식 도형, 슬라이드의 자유 도형·차트·표·아이콘을 만든다.
// 개체 틀(placeholder)은 postprocess.py 가 layout_spec.json 을 읽어 직접 넣는다.
const fs = require('fs');
const path = require('path');
const pptxgen = require('pptxgenjs');
const React = require('react');
const ReactDOMServer = require('react-dom/server');
const sharp = require('sharp');
const fi = require('react-icons/fi');

const OUT_DIR = process.argv[2] || '.';
const W = 13.333;
const H = 7.5;
const MX = 0.6;
const CW = W - 2 * MX;

// 테마와 무관한 중립색 (설명 글, 구분선)
const GRAY = '5E6E75';
const GRAY_L = '7C8A90';
const LINE = 'D5DEE0';
const BAR_GRAY = 'B9C6CA';

const pres = new pptxgen();
pres.layout = 'LAYOUT_WIDE';
pres.title = '편집 가능한 프레젠테이션 템플릿';
pres.subject = '프레젠테이션 템플릿';
pres.author = '';
pres.company = '';

const spec = { layouts: {}, slides: [] };

// ---------- helpers ----------
const grp = (group, member) => `GRP::${group}::${member}`;

// pptxgenjs text margin order is [left, right, bottom, top] in points
const pad = (l, t, r, b) => [l * 72, r * 72, b * 72, t * 72];

async function icon(name, color = '#FFFFFF') {
  let svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fi[name], { size: 256, color }));
  svg = svg.replace(/currentColor/g, color);
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return 'image/png;base64,' + buf.toString('base64');
}

function oval(x, y, d, fill, extra = {}) {
  return { text: { text: '', options: { shape: pres.shapes.OVAL, x, y, w: d, h: d, fill, ...extra } } };
}
function ring(x, y, d, color, width, transparency = 0) {
  return { text: { text: '', options: { shape: pres.shapes.OVAL, x, y, w: d, h: d, line: { color, width, transparency } } } };
}

function defLayout(name, { bg, objects = [], ph = [], num = false }) {
  pres.defineSlideMaster({ title: name, background: { color: bg }, objects });
  spec.layouts[name] = { ph, num };
}

// placeholder paragraph spec helpers (consumed by postprocess.py)
const P = (text, o = {}) => ({ runs: [{ t: text }], ...o });
const PB = (lead, rest, o = {}) => ({ runs: [{ t: lead, b: true }, { t: rest }], ...o });

function addSlide(layout, ph = {}, notes = '') {
  const slide = pres.addSlide({ masterName: layout });
  spec.slides.push({ layout, ph });
  if (notes) slide.addNotes(notes);
  return slide;
}

function text(slide, str, o) {
  slide.addText(str, { isTextBox: true, margin: 0, lang: 'ko-KR', valign: 'top', ...o });
}

// ---------- layout geometry ----------
const TITLE = { key: 'title', type: 'title', x: 0.95, y: 0.42, w: 11.78, h: 0.9, anchor: 'ctr',
  lvl1: { sz: 30, b: true, color: 'tx2' }, prompt: '제목을 입력하세요' };
const titleDot = () => oval(MX, 0.77, 0.2, { color: 'accent2' });

// ---------- layouts ----------
function defineLayouts() {
  defLayout('표지', {
    bg: 'tx2',
    objects: [
      oval(8.55, -1.35, 6.1, { color: 'accent1' }),
      ring(8.05, -1.85, 7.1, 'FFFFFF', 1.25, 55),
      oval(8.7, 3.8, 2.8, { color: 'accent2' }),
      oval(12.3, 5.55, 0.9, { color: 'accent3' }),
    ],
    ph: [
      { key: 'label', type: 'body', idx: 13, x: 0.8, y: 1.55, w: 7.3, h: 0.5, anchor: 'b',
        lvl1: { sz: 14, b: true, color: 'accent3', spc: 100 }, prompt: '발표 구분 (예: 2026 PRESENTATION)' },
      { key: 'title', type: 'title', x: 0.8, y: 2.15, w: 7.3, h: 2.0, anchor: 't',
        lvl1: { sz: 44, b: true, color: 'bg1', lnSpc: 100 }, prompt: '발표 제목을 입력하세요' },
      { key: 'sub', type: 'body', idx: 14, x: 0.8, y: 4.3, w: 7.3, h: 0.9, anchor: 't',
        lvl1: { sz: 20, color: 'bg2' }, prompt: '부제목을 입력하세요' },
      { key: 'meta', type: 'body', idx: 15, x: 0.8, y: 6.15, w: 7.3, h: 0.55, anchor: 'b',
        lvl1: { sz: 13, color: 'bg2' }, prompt: '발표자  |  소속  |  날짜' },
    ],
  });

  defLayout('목차', {
    bg: 'bg1',
    objects: [
      { rect: { x: 0, y: 0, w: 4.6, h: H, fill: { color: 'tx2' } } },
      oval(-1.3, 4.9, 3.6, { color: 'accent1' }),
      ring(-1.75, 4.45, 4.5, 'FFFFFF', 1.25, 60),
      oval(2.7, 6.0, 0.7, { color: 'accent2' }),
    ],
    ph: [
      { key: 'label', type: 'body', idx: 13, x: 0.8, y: 1.2, w: 3.4, h: 0.5, anchor: 'b',
        lvl1: { sz: 14, b: true, color: 'accent3', spc: 100 }, prompt: 'CONTENTS' },
      { key: 'title', type: 'title', x: 0.8, y: 1.75, w: 3.4, h: 1.0, anchor: 't',
        lvl1: { sz: 40, b: true, color: 'bg1' }, prompt: '목차' },
    ],
  });

  defLayout('섹션 구분', {
    bg: 'tx2',
    objects: [
      oval(8.65, 1.0, 5.5, { color: 'accent1' }),
      ring(8.2, 0.55, 6.4, 'FFFFFF', 1.25, 60),
      oval(8.3, 5.2, 1.0, { color: 'accent2' }),
      oval(12.55, 0.7, 0.45, { color: 'accent3' }),
    ],
    ph: [
      { key: 'num', type: 'body', idx: 13, x: 0.8, y: 1.45, w: 4.0, h: 1.35, anchor: 'b',
        lvl1: { sz: 66, b: true, color: 'accent2' }, prompt: '01' },
      { key: 'title', type: 'title', x: 0.8, y: 2.95, w: 7.3, h: 1.3, anchor: 't',
        lvl1: { sz: 40, b: true, color: 'bg1', lnSpc: 100 }, prompt: '섹션 제목을 입력하세요' },
      { key: 'desc', type: 'body', idx: 14, x: 0.8, y: 4.35, w: 7.0, h: 1.3, anchor: 't',
        lvl1: { sz: 16, color: 'bg2', lnSpc: 130 }, prompt: '섹션에서 다룰 내용을 간단히 소개하세요' },
    ],
  });

  defLayout('제목 및 내용', {
    bg: 'bg1',
    objects: [titleDot()],
    num: true,
    ph: [
      TITLE,
      { key: 'body', type: 'body', idx: 13, x: MX, y: 1.6, w: CW, h: 5.1, anchor: 't',
        lvl1: { sz: 20, color: 'tx1', bullets: true, spcBef: 18, lnSpc: 110 },
        lvl2: { sz: 16, color: GRAY, bullets: true, spcBef: 6, lnSpc: 110 },
        prompt: '내용을 입력하세요' },
    ],
  });

  defLayout('제목만', { bg: 'bg1', objects: [titleDot()], num: true, ph: [TITLE] });

  const card = (x) => ({ text: { text: '', options: { shape: pres.shapes.ROUNDED_RECTANGLE, x, y: 1.6, w: 5.8, h: 5.1, rectRadius: 0.12, fill: { color: 'bg2' } } } });
  const colPh = (x, i) => [
    { key: i ? 'rhead' : 'lhead', type: 'body', idx: 13 + i * 2, x, y: 1.95, w: 5.1, h: 0.65, anchor: 'ctr',
      lvl1: { sz: 20, b: true, color: 'tx2' }, prompt: '소제목을 입력하세요' },
    { key: i ? 'rbody' : 'lbody', type: 'body', idx: 14 + i * 2, x, y: 2.75, w: 5.1, h: 3.65, anchor: 't',
      lvl1: { sz: 16, color: 'tx1', bullets: true, spcBef: 14, lnSpc: 110 },
      lvl2: { sz: 14, color: GRAY, bullets: true, spcBef: 4 }, prompt: '내용을 입력하세요' },
  ];
  defLayout('비교 (2단)', {
    bg: 'bg1',
    objects: [titleDot(), card(MX), card(6.933)],
    num: true,
    ph: [TITLE, ...colPh(0.95, 0), ...colPh(7.283, 1)],
  });

  defLayout('사진 + 내용', {
    bg: 'bg1',
    objects: [
      { rect: { x: 0, y: 0, w: 6.2, h: H, fill: { color: 'bg2' } } },
      oval(0.9, 1.3, 3.6, { color: 'accent1', transparency: 82 }),
      oval(2.9, 3.7, 2.4, { color: 'accent2', transparency: 82 }),
      oval(4.55, 1.55, 0.7, { color: 'accent3', transparency: 55 }),
      oval(6.8, 0.77, 0.2, { color: 'accent2' }),
    ],
    num: true,
    ph: [
      { key: 'photo', type: 'pic', idx: 13, x: 0, y: 0, w: 6.2, h: H, anchor: 't', ins: [0.3, 0.4, 0.3, 0.3],
        lvl1: { sz: 14, color: GRAY, algn: 'ctr' }, prompt: '아이콘을 클릭해 사진을 넣으세요' },
      { key: 'title', type: 'title', x: 7.15, y: 0.42, w: 5.58, h: 0.9, anchor: 'ctr',
        lvl1: { sz: 30, b: true, color: 'tx2' }, prompt: '제목을 입력하세요' },
      { key: 'body', type: 'body', idx: 14, x: 6.8, y: 1.75, w: 5.93, h: 4.95, anchor: 't',
        lvl1: { sz: 16, color: 'tx1', bullets: true, spcBef: 10, lnSpc: 115 },
        lvl2: { sz: 14, color: GRAY, bullets: true, spcBef: 4 }, prompt: '내용을 입력하세요' },
    ],
  });

  defLayout('핵심 메시지', {
    bg: 'accent1',
    objects: [
      { text: { text: '“', options: { x: 0.95, y: 0.35, w: 2.0, h: 2.2, fontSize: 200, bold: true, color: 'FFFFFF', transparency: 30, margin: 0, valign: 'top' } } },
      oval(9.4, 3.9, 5.2, { color: 'tx2', transparency: 75 }),
      ring(10.6, -1.3, 3.4, 'FFFFFF', 1.25, 50),
      oval(9.05, 4.95, 0.55, { color: 'accent3' }),
    ],
    ph: [
      { key: 'msg', type: 'title', x: 1.2, y: 2.25, w: 9.9, h: 2.5, anchor: 't',
        lvl1: { sz: 32, b: true, color: 'bg1', lnSpc: 120 }, prompt: '가장 전하고 싶은 메시지를 입력하세요' },
      { key: 'cap', type: 'body', idx: 14, x: 1.2, y: 5.0, w: 7.6, h: 0.6, anchor: 't',
        lvl1: { sz: 16, color: 'bg1' }, prompt: '출처 또는 덧붙일 설명' },
    ],
  });

  defLayout('마무리', {
    bg: 'tx2',
    objects: [
      oval(-1.6, 4.3, 4.6, { color: 'accent1' }),
      ring(-2.1, 3.8, 5.6, 'FFFFFF', 1.25, 60),
      oval(11.25, -0.95, 2.6, { color: 'accent2' }),
      oval(10.65, 1.35, 0.6, { color: 'accent3' }),
    ],
    ph: [
      { key: 'title', type: 'title', x: 1.5, y: 2.2, w: 10.33, h: 1.4, anchor: 'b',
        lvl1: { sz: 54, b: true, color: 'bg1', algn: 'ctr' }, prompt: '감사합니다' },
      { key: 'sub', type: 'body', idx: 13, x: 1.5, y: 3.8, w: 10.33, h: 0.7, anchor: 't',
        lvl1: { sz: 20, color: 'bg2', algn: 'ctr' }, prompt: '마무리 인사나 요약을 입력하세요' },
      { key: 'contact', type: 'body', idx: 14, x: 1.5, y: 4.65, w: 10.33, h: 0.55, anchor: 't',
        lvl1: { sz: 14, color: 'accent3', algn: 'ctr' }, prompt: '연락처 (이메일 · 전화)' },
    ],
  });
}

// ---------- slides ----------
async function buildSlides() {
  const ic = {};
  for (const n of ['FiTarget', 'FiTrendingUp', 'FiUsers', 'FiArrowRight', 'FiEdit3', 'FiPlusSquare', 'FiCopy',
    'FiDroplet', 'FiBarChart2', 'FiImage', 'FiMessageCircle']) ic[n] = await icon(n);

  // 1. 표지
  addSlide('표지', {
    label: [P('2026 PRESENTATION')],
    title: [P('프레젠테이션 제목을\n입력하세요')],
    sub: [P('발표의 핵심 내용을 한 문장으로 요약해 주세요')],
    meta: [P('발표자 이름   |   소속   |   2026. 09. 29')],
  }, '표지입니다. 글자를 클릭해 바로 수정하세요.\n배경의 원 도형은 [보기] → [슬라이드 마스터]에서 바꿀 수 있습니다.');

  // 2. 목차
  const s2 = addSlide('목차', { label: [P('CONTENTS')], title: [P('목차')] },
    '항목을 추가하려면 항목 하나를 클릭해 그룹을 선택한 뒤 복사(Ctrl+C)·붙여넣기(Ctrl+V) 하세요.');
  const agenda = [
    ['배경 및 목적', '발표를 준비하게 된 배경과 목표를 소개합니다'],
    ['현황 분석', '현재 상황과 주요 데이터를 살펴봅니다'],
    ['실행 전략', '핵심 전략과 구체적인 실행 계획을 제시합니다'],
    ['기대 효과', '예상 성과와 앞으로의 과제를 정리합니다'],
  ];
  agenda.forEach(([t, d], i) => {
    const y = 1.2 + i * 1.4;
    const g = `목차 항목 ${i + 1}`;
    text(s2, String(i + 1).padStart(2, '0'), { x: 5.4, y: y - 0.06, w: 1.0, h: 0.6, fontSize: 30, bold: true, color: 'accent2', objectName: grp(g, '번호') });
    text(s2, t, { x: 6.55, y, w: 6.18, h: 0.45, fontSize: 20, bold: true, color: 'tx2', objectName: grp(g, '제목') });
    text(s2, d, { x: 6.55, y: y + 0.5, w: 6.18, h: 0.4, fontSize: 14, color: GRAY, objectName: grp(g, '설명') });
    if (i < agenda.length - 1) s2.addShape(pres.shapes.LINE, { x: 5.4, y: y + 1.17, w: 7.33, h: 0, line: { color: LINE, width: 0.75 }, objectName: grp(g, '구분선') });
  });

  // 3. 섹션 구분
  addSlide('섹션 구분', {
    num: [P('01')],
    title: [P('배경 및 목적')],
    desc: [P('이 섹션에서 다룰 내용을 한두 문장으로 간단히 소개해 주세요.')],
  }, '섹션을 시작할 때 쓰는 슬라이드입니다. 번호와 제목만 바꿔서 여러 번 복제해 쓰세요 (Ctrl+D).');

  // 4. 제목 및 내용
  const s4 = addSlide('제목 및 내용', {
    title: [P('추진 배경')],
    body: [
      PB('변화하는 환경  ', '고객의 요구가 빠르게 다양해지고 있습니다'),
      P('최근 1년 사이 문의 유형이 두 배 이상 늘었습니다', { lvl: 1 }),
      PB('해결할 문제  ', '기존 방식으로는 대응 속도에 한계가 있습니다'),
      P('한 건을 처리하는 데 평균 3일 이상 걸립니다', { lvl: 1 }),
      PB('발표 목표  ', '새로운 실행 방안을 공유하고 의견을 모읍니다'),
      P('논의한 내용을 바탕으로 다음 달 실행안을 확정합니다', { lvl: 1 }),
    ],
  }, '기본 글머리 기호 슬라이드입니다. Tab 키로 들여쓰면 하위 항목, Shift+Tab 으로 다시 내어쓰기 됩니다.');
  {
    const g = '핵심 메시지 상자';
    s4.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: MX, y: 5.5, w: CW, h: 1.05, rectRadius: 0.12, fill: { color: 'bg2' }, objectName: grp(g, '배경') });
    s4.addShape(pres.shapes.OVAL, { x: 0.95, y: 5.72, w: 0.6, h: 0.6, fill: { color: 'accent2' }, objectName: grp(g, '아이콘 원') });
    s4.addImage({ data: ic.FiMessageCircle, x: 1.1, y: 5.87, w: 0.3, h: 0.3, altText: '말풍선 아이콘', objectName: grp(g, '아이콘') });
    s4.addText([
      { text: '핵심 메시지  ', options: { bold: true, color: 'accent2' } },
      { text: '빠르게 변하는 환경에 맞춰 일하는 방식도 함께 바뀌어야 합니다.', options: { bold: true, color: 'tx2' } },
    ], { x: 1.8, y: 5.5, w: 10.6, h: 1.05, fontSize: 17, valign: 'middle', margin: 0, isTextBox: true, lang: 'ko-KR', objectName: grp(g, '내용') });
  }

  // 5. 핵심 포인트 (카드 3개)
  const s5 = addSlide('제목만', { title: [P('핵심 포인트 세 가지')] },
    '카드 하나를 클릭하면 그룹 전체가 선택됩니다. 한 번 더 클릭하면 안쪽 글자나 도형을 따로 고칠 수 있습니다.');
  const cards = [
    ['FiTarget', 'accent1', '명확한 목표', '달성하려는 목표를 구체적인 숫자와 기한으로 제시하세요.'],
    ['FiTrendingUp', 'accent2', '데이터 기반 분석', '현재 상황을 객관적인 데이터로 보여 주면 설득력이 높아집니다.'],
    ['FiUsers', 'tx2', '함께하는 실행', '누가, 언제, 무엇을 할지 역할을 나누어 실행력을 높이세요.'],
  ];
  const cw3 = (CW - 2 * 0.35) / 3;
  cards.forEach(([ico, col, t, d], i) => {
    const x = MX + i * (cw3 + 0.35);
    const y = 1.75;
    const g = `카드 ${i + 1}`;
    s5.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw3, h: 4.0, rectRadius: 0.12, fill: { color: 'bg2' }, objectName: grp(g, '배경') });
    text(s5, String(i + 1).padStart(2, '0'), { x: x + cw3 - 1.45, y: y + 0.4, w: 1.1, h: 0.75, fontSize: 36, bold: true, color: 'tx2', transparency: 78, align: 'right', objectName: grp(g, '번호') });
    s5.addShape(pres.shapes.OVAL, { x: x + 0.45, y: y + 0.5, w: 0.95, h: 0.95, fill: { color: col }, objectName: grp(g, '아이콘 원') });
    s5.addImage({ data: ic[ico], x: x + 0.68, y: y + 0.73, w: 0.49, h: 0.49, altText: `${t} 아이콘`, objectName: grp(g, '아이콘') });
    text(s5, t, { x: x + 0.45, y: y + 1.85, w: cw3 - 0.9, h: 0.55, fontSize: 22, bold: true, color: 'tx2', objectName: grp(g, '제목') });
    text(s5, d, { x: x + 0.45, y: y + 2.55, w: cw3 - 0.9, h: 1.3, fontSize: 16, color: GRAY, lineSpacingMultiple: 1.35, objectName: grp(g, '설명') });
  });

  // 6. 비교 (2단)
  const s6 = addSlide('비교 (2단)', {
    title: [P('현재와 개선 방향')],
    lhead: [P('현재 상황')],
    lbody: [P('반복 업무를 대부분 수작업으로 처리'), P('부서 간 정보 공유가 늦고 흩어져 있음'), P('성과를 판단할 명확한 기준이 없음'), P('고객 문의가 여러 채널로 흩어져 들어옴')],
    rhead: [P('개선 방향')],
    rbody: [P('반복 업무 자동화로 처리 시간 단축'), P('공유 플랫폼에서 실시간으로 협업'), P('핵심 지표(KPI)로 성과를 투명하게 관리'), P('문의 창구를 하나로 모아 빠르게 응대')],
  }, '양쪽 소제목과 내용을 바꿔 두 가지를 비교하세요. 가운데 화살표는 필요 없으면 지워도 됩니다.');
  s6.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.933, y: 1.6, w: 5.8, h: 5.1, rectRadius: 0.12, line: { color: 'accent1', width: 1.5 }, objectName: '강조 테두리' });
  const side = (x, label, tagFill, value, valueColor, g) => {
    s6.addText(label, { shape: pres.shapes.ROUNDED_RECTANGLE, x, y: 1.4, w: 1.15, h: 0.4, rectRadius: 0.2, fill: { color: tagFill }, color: 'FFFFFF', fontSize: 11, bold: true, align: 'center', valign: 'middle', margin: 0, charSpacing: 1, objectName: `${g} 태그` });
    s6.addShape(pres.shapes.LINE, { x, y: 5.3, w: 5.1, h: 0, line: { color: LINE, width: 1 }, objectName: grp(`${g} 지표`, '구분선') });
    text(s6, '평균 처리 시간', { x, y: 5.55, w: 2.6, h: 0.75, fontSize: 15, color: GRAY, valign: 'middle', objectName: grp(`${g} 지표`, '항목') });
    text(s6, value, { x: x + 2.5, y: 5.5, w: 2.6, h: 0.85, fontSize: 34, bold: true, color: valueColor, align: 'right', valign: 'middle', objectName: grp(`${g} 지표`, '값') });
  };
  side(0.95, 'AS-IS', GRAY_L, '3일', GRAY_L, '왼쪽');
  side(7.283, 'TO-BE', 'accent1', '1일', 'accent1', '오른쪽');
  s6.addShape(pres.shapes.OVAL, { x: 6.29, y: 3.78, w: 0.75, h: 0.75, fill: { color: 'accent2' }, line: { color: 'FFFFFF', width: 3 }, objectName: grp('가운데 화살표', '원') });
  s6.addImage({ data: ic.FiArrowRight, x: 6.475, y: 3.965, w: 0.38, h: 0.38, altText: '화살표 아이콘', objectName: grp('가운데 화살표', '아이콘') });

  // 7. 핵심 수치
  const s7 = addSlide('제목만', { title: [P('숫자로 보는 성과')] },
    '숫자와 설명만 바꿔 쓰세요. 원 테두리 색은 도형을 선택한 뒤 [도형 서식] → [도형 윤곽선]에서 바꿀 수 있습니다.');
  const stats = [
    ['87%', 'accent1', '고객 만족도', '전년보다 12%p 오른 만족도 점수'],
    ['2.4배', 'accent2', '매출 성장', '최근 3년 동안의 매출 증가 규모'],
    ['120+', 'accent3', '협력 기관', '전국 주요 도시의 협력 기관 수'],
  ];
  stats.forEach(([n, col, l, d], i) => {
    const cx = MX + CW / 6 + i * (CW / 3);
    const g = `수치 ${i + 1}`;
    s7.addText(n, { shape: pres.shapes.OVAL, x: cx - 1.25, y: 1.75, w: 2.5, h: 2.5, fill: { color: 'bg2' }, line: { color: col, width: 6 }, fontSize: 40, bold: true, color: 'tx2', align: 'center', valign: 'middle', margin: 0, lang: 'ko-KR', objectName: grp(g, '숫자') });
    text(s7, l, { x: cx - 1.8, y: 4.55, w: 3.6, h: 0.5, fontSize: 20, bold: true, color: 'tx2', align: 'center', objectName: grp(g, '항목') });
    text(s7, d, { x: cx - 1.8, y: 5.1, w: 3.6, h: 0.8, fontSize: 14, color: GRAY, align: 'center', objectName: grp(g, '설명') });
  });
  text(s7, '출처: 2026년 내부 성과 보고서 (예시 수치)', { x: MX, y: 6.55, w: 8, h: 0.3, fontSize: 11, color: GRAY_L, objectName: '출처' });

  // 8. 차트
  const s8 = addSlide('제목만', { title: [P('분기별 실적 추이')] },
    '차트를 마우스 오른쪽 버튼으로 클릭 → [데이터 편집]을 누르면 숫자를 바꿀 수 있습니다. 막대 색은 테마 색을 따라 바뀝니다.');
  const cats = ['1분기', '2분기', '3분기', '4분기'];
  s8.addChart(pres.charts.BAR, [
    { name: '목표', labels: cats, values: [120, 135, 150, 170] },
    { name: '실적', labels: cats, values: [110, 131, 158, 185] },
  ], {
    x: MX, y: 1.75, w: 7.55, h: 4.95, barDir: 'col', barGrouping: 'clustered', barGapWidthPct: 70,
    chartColors: [BAR_GRAY, 'accent1'],
    showValue: true, dataLabelPosition: 'outEnd', dataLabelFontSize: 12, dataLabelColor: GRAY, dataLabelFontFace: '+mn-lt',
    catAxisLabelColor: 'tx1', catAxisLabelFontSize: 14, catAxisLabelFontFace: '+mn-lt', catAxisLineShow: true, catAxisLineColor: LINE,
    valAxisHidden: true, valAxisMinVal: 0, valAxisMaxVal: 210, valGridLine: { style: 'none' }, catGridLine: { style: 'none' },
    showLegend: true, legendPos: 't', legendFontSize: 12, legendColor: GRAY,
    objectName: '실적 차트',
  });
  text(s8, '단위: 백만 원', { x: 5.75, y: 1.45, w: 2.4, h: 0.3, fontSize: 11, color: GRAY_L, align: 'right', objectName: '단위' });
  {
    const x = 8.55, y = 1.55, w = W - MX - 8.55;
    s8.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 5.15, rectRadius: 0.12, fill: { color: 'bg2' }, objectName: grp('분석 상자', '배경') });
    text(s8, '주요 분석', { x: x + 0.4, y: y + 0.35, w: w - 0.8, h: 0.5, fontSize: 20, bold: true, color: 'tx2', objectName: grp('분석 상자', '제목') });
    const pts = ['3분기부터 목표를 넘어섰습니다', '4분기 실적은 목표보다 약 9% 높습니다', '내년에는 신규 고객 확보에 집중합니다'];
    pts.forEach((p, i) => {
      const yy = y + 1.2 + i * 1.2;
      s8.addText(String(i + 1), { shape: pres.shapes.OVAL, x: x + 0.4, y: yy, w: 0.46, h: 0.46, fill: { color: 'accent1' }, color: 'FFFFFF', fontSize: 13, bold: true, align: 'center', valign: 'middle', margin: 0, objectName: grp('분석 상자', `번호 ${i + 1}`) });
      text(s8, p, { x: x + 1.05, y: yy - 0.02, w: w - 1.4, h: 0.85, fontSize: 15, color: 'tx1', lineSpacingMultiple: 1.2, objectName: grp('분석 상자', `내용 ${i + 1}`) });
    });
  }

  // 9. 표
  const s9 = addSlide('제목만', { title: [P('세부 실행 계획')] },
    '표 안을 클릭해 바로 수정하세요. 행이나 열은 [레이아웃] 탭(표 선택 시 표시)에서 추가·삭제할 수 있습니다.');
  const hdr = ['단계', '주요 내용', '담당', '기간', '상태'].map((t) => ({ text: t, options: { bold: true, color: 'FFFFFF', fill: { color: 'tx2' } } }));
  const status = { '완료': 'accent1', '진행 중': 'accent2', '예정': GRAY_L };
  const rows = [
    ['1단계', '현황 조사 및 문제 정의', '기획팀', '10월 1주 ~ 2주', '완료'],
    ['2단계', '개선안 설계 및 검토', '전략팀', '10월 3주 ~ 11월 2주', '진행 중'],
    ['3단계', '시범 운영 및 의견 반영', '운영팀', '11월 3주 ~ 12월', '예정'],
    ['4단계', '전체 확대 및 성과 점검', '전 부서', '2027년 1월', '예정'],
  ].map((r) => r.map((t, j) => ({
    text: j === 4 ? `● ${t}` : t,
    options: {
      bold: j === 0 || j === 4,
      color: j === 0 ? 'tx2' : j === 4 ? status[t] : 'tx1',
      border: [{ type: 'none' }, { type: 'none' }, { pt: 0.75, color: LINE }, { type: 'none' }],
    },
  })));
  s9.addTable([hdr, ...rows], {
    x: MX, y: 1.7, w: CW, colW: [1.45, 4.35, 1.75, 2.85, CW - 1.45 - 4.35 - 1.75 - 2.85],
    rowH: [0.65, 0.9, 0.9, 0.9, 0.9], fontSize: 15, valign: 'middle', margin: [0.08, 0.2, 0.08, 0.2],
    lang: 'ko-KR', objectName: '실행 계획 표',
  });
  {
    const y = 6.3;
    const items = [['완료', 'accent1'], ['진행 중', 'accent2'], ['예정', GRAY_L]];
    let x = MX;
    items.forEach(([t, c]) => {
      s9.addShape(pres.shapes.OVAL, { x, y: y + 0.09, w: 0.16, h: 0.16, fill: { color: c }, objectName: grp('범례', `${t} 점`) });
      text(s9, t, { x: x + 0.26, y, w: 1.0, h: 0.34, fontSize: 12, color: GRAY, valign: 'middle', objectName: grp('범례', `${t} 글자`) });
      x += 1.35;
    });
  }

  // 10. 타임라인
  const s10 = addSlide('제목만', { title: [P('추진 일정')] },
    '단계를 늘리려면 단계 그룹 하나를 복사해 붙여 넣고 간격을 맞추세요. 채워진 원은 완료, 빈 원은 예정된 단계입니다.');
  const steps = [
    ['2026. 10', '현황 조사', '문제를 정의하고 개선 목표를 확정합니다', true],
    ['2026. 11', '개선안 설계', '해결 방안을 설계하고 검토 의견을 반영합니다', true],
    ['2026. 12', '시범 운영', '일부 부서에 먼저 적용해 효과를 검증합니다', false],
    ['2027. 01', '전체 확대', '성과를 점검하고 전 부서로 확대합니다', false],
  ];
  const bw = 2.85, gap = (CW - 4 * bw) / 3, ly = 3.15, cy = 3.85;
  const cxs = steps.map((_, i) => MX + bw / 2 + i * (bw + gap));
  s10.addShape(pres.shapes.LINE, { x: cxs[0], y: ly, w: cxs[3] - cxs[0], h: 0, line: { color: LINE, width: 3 }, objectName: '타임라인 선' });
  s10.addShape(pres.shapes.LINE, { x: cxs[0], y: ly, w: cxs[1] - cxs[0] + 1.3, h: 0, line: { color: 'accent1', width: 3 }, objectName: '진행 선' });
  steps.forEach(([d, t, desc, done], i) => {
    const cx = cxs[i];
    const g = `단계 ${i + 1}`;
    text(s10, d, { x: cx - bw / 2, y: 2.2, w: bw, h: 0.45, fontSize: 17, bold: true, color: 'accent2', align: 'center', objectName: grp(g, '날짜') });
    if (i === 1) s10.addShape(pres.shapes.OVAL, { x: cx - 0.34, y: ly - 0.34, w: 0.68, h: 0.68, fill: { color: 'accent1', transparency: 75 }, objectName: grp(g, '현재 표시') });
    s10.addShape(pres.shapes.OVAL, { x: cx - 0.19, y: ly - 0.19, w: 0.38, h: 0.38,
      fill: { color: done ? 'accent1' : 'FFFFFF' }, line: { color: 'accent1', width: 2.5 }, objectName: grp(g, '점') });
    s10.addShape(pres.shapes.ISOSCELES_TRIANGLE, { x: cx - 0.17, y: cy - 0.15, w: 0.34, h: 0.16, fill: { color: 'bg2' }, objectName: grp(g, '말풍선 꼭지') });
    s10.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: cx - bw / 2, y: cy, w: bw, h: 2.2, rectRadius: 0.12, fill: { color: 'bg2' }, objectName: grp(g, '배경') });
    text(s10, t, { x: cx - bw / 2 + 0.25, y: cy + 0.4, w: bw - 0.5, h: 0.5, fontSize: 20, bold: true, color: 'tx2', align: 'center', objectName: grp(g, '제목') });
    text(s10, desc, { x: cx - bw / 2 + 0.3, y: cy + 1.05, w: bw - 0.6, h: 1.05, fontSize: 15, color: GRAY, align: 'center', lineSpacingMultiple: 1.3, objectName: grp(g, '설명') });
  });

  // 11. 사진 + 내용
  const s11 = addSlide('사진 + 내용', {
    title: [P('현장 사례 소개')],
    body: [
      P('지난 3개월 동안 A 지점에서 새로운 방식을 먼저 적용해 보았습니다.', { bullet: 'none' }),
      P('고객 대기 시간이 절반 가까이 줄었습니다'),
      P('직원 만족도 조사에서 가장 높은 점수를 받았습니다'),
      P('다음 분기부터 다른 지점으로 확대할 예정입니다'),
    ],
  }, '왼쪽 사진 영역 가운데의 그림 아이콘을 클릭하거나, 사진 파일을 영역 위로 끌어다 놓으세요.\n사진은 영역 크기에 맞게 자동으로 잘리며, [그림 서식] → [자르기]로 보이는 부분을 조정할 수 있습니다.');
  [['고객 대기 시간', '-48%', 'accent2'], ['직원 만족도', '4.8점', 'accent1']].forEach(([l, v, c], i) => {
    const x = 6.9 + i * 2.99, y = 5.2, w = 2.84;
    const g = `지표 ${i + 1}`;
    s11.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.4, rectRadius: 0.12, fill: { color: 'bg2' }, objectName: grp(g, '배경') });
    text(s11, l, { x: x + 0.3, y: y + 0.22, w: w - 0.6, h: 0.35, fontSize: 13, color: GRAY, objectName: grp(g, '항목') });
    text(s11, v, { x: x + 0.3, y: y + 0.58, w: w - 0.6, h: 0.65, fontSize: 30, bold: true, color: c, objectName: grp(g, '값') });
  });

  // 12. 핵심 메시지
  addSlide('핵심 메시지', {
    msg: [P('좋은 발표는 청중이 기억할\n단 하나의 메시지에서 시작됩니다.')],
    cap: [P('— 발표에서 가장 강조하고 싶은 한 문장을 적어 보세요')],
  }, '강조하고 싶은 문장이나 인용문을 넣는 슬라이드입니다.');

  // 13. 마무리
  addSlide('마무리', {
    title: [P('감사합니다')],
    sub: [P('질문이나 의견이 있으시면 편하게 말씀해 주세요.')],
    contact: [P('name@example.com   ·   010-0000-0000')],
  }, '마지막 인사 슬라이드입니다. 연락처를 본인 정보로 바꿔 주세요.');

  // 14. 사용 가이드 (숨김 슬라이드)
  const s14 = addSlide('제목만', { title: [P('이 템플릿 사용법')] },
    '이 슬라이드는 숨김 처리되어 슬라이드 쇼에는 나오지 않습니다. 필요 없으면 삭제하세요.\n레이아웃 자체의 디자인(배경, 원 도형, 글자 위치)은 [보기] → [슬라이드 마스터]에서 수정합니다.');
  s14.hidden = true;
  const guide = [
    ['FiEdit3', '글자 수정', '글자를 클릭한 뒤 바로 입력하세요. 서식은 그대로 유지됩니다.'],
    ['FiPlusSquare', '새 슬라이드', '[홈] → [새 슬라이드] ▾ 에서 원하는 레이아웃을 고르세요.'],
    ['FiCopy', '슬라이드 복제', '슬라이드를 선택하고 Ctrl + D 를 누르면 그대로 복제됩니다.'],
    ['FiDroplet', '색·글꼴 바꾸기', '[디자인] → [적용] 그룹 ▾ → [색] 또는 [글꼴]을 고르세요.'],
    ['FiBarChart2', '차트 수정', '차트를 마우스 오른쪽 버튼으로 클릭 → [데이터 편집]'],
    ['FiImage', '사진 넣기', '사진 영역의 그림 아이콘을 클릭하거나 사진을 끌어다 놓으세요.'],
  ];
  guide.forEach(([ico, t, d], i) => {
    const c = i % 3, r = Math.floor(i / 3);
    const x = MX + c * (cw3 + 0.35), y = 1.6 + r * 2.5;
    const g = `안내 ${i + 1}`;
    s14.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: cw3, h: 2.2, rectRadius: 0.12, fill: { color: 'bg2' }, objectName: grp(g, '배경') });
    s14.addShape(pres.shapes.OVAL, { x: x + 0.35, y: y + 0.35, w: 0.64, h: 0.64, fill: { color: 'accent1' }, objectName: grp(g, '아이콘 원') });
    s14.addImage({ data: ic[ico], x: x + 0.51, y: y + 0.51, w: 0.32, h: 0.32, altText: `${t} 아이콘`, objectName: grp(g, '아이콘') });
    text(s14, t, { x: x + 1.15, y: y + 0.35, w: cw3 - 1.45, h: 0.64, fontSize: 17, bold: true, color: 'tx2', valign: 'middle', objectName: grp(g, '제목') });
    text(s14, d, { x: x + 0.35, y: y + 1.2, w: cw3 - 0.7, h: 0.9, fontSize: 14, color: GRAY, lineSpacingMultiple: 1.2, objectName: grp(g, '설명') });
  });
  text(s14, '※ 이 슬라이드는 숨김 상태라 발표할 때는 보이지 않습니다. 필요 없으면 삭제하세요.', { x: MX, y: 6.6, w: 10, h: 0.3, fontSize: 11, color: GRAY_L, objectName: '안내 문구' });
}

(async () => {
  defineLayouts();
  await buildSlides();
  fs.writeFileSync(path.join(OUT_DIR, 'layout_spec.json'), JSON.stringify(spec, null, 1));
  const f = await pres.writeFile({ fileName: path.join(OUT_DIR, 'stage1.pptx') });
  console.log('wrote', f);
})();
