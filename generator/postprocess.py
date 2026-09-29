#!/usr/bin/env python3
"""2단계: pptxgenjs 결과물을 '편집하기 좋은 템플릿'으로 다듬는다.

- 테마 색/글꼴을 교체 (디자인 > 적용 > 색/글꼴 로 전체 변경 가능)
- 슬라이드 마스터의 텍스트 스타일(제목, 글머리 기호 수준)을 정의
- 레이아웃에 실제 개체 틀(제목/텍스트/그림/슬라이드 번호)을 넣고,
  슬라이드의 개체 틀은 서식을 상속하도록 깨끗하게 채움
- 카드 등 관련 도형을 그룹으로 묶고, 도형 ID 중복을 정리
- 언어 태그를 한국어로 지정

usage: postprocess.py stage1.pptx layout_spec.json out.pptx
"""
import json
import re
import sys
import zipfile

from lxml import etree

SRC, SPEC, OUT = sys.argv[1:4]

NS_A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS_P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
NS_R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS = {'a': NS_A, 'p': NS_P, 'r': NS_R}
SCHEME = {'tx1', 'tx2', 'bg1', 'bg2', 'accent1', 'accent2', 'accent3', 'accent4', 'accent5', 'accent6'}

GRAY_L = '7C8A90'
SLDNUM_IDX = 12
FLD_ID = '{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}'
LANG = 'lang="ko-KR" altLang="en-US"'

THEME_NAME = '편집용 템플릿'
FONT = '맑은 고딕'
COLORS = [('dk1', '1F2A30'), ('lt1', 'FFFFFF'), ('dk2', '264653'), ('lt2', 'EAF2F0'),
          ('accent1', '2A9D8F'), ('accent2', 'E76F51'), ('accent3', 'E9C46A'), ('accent4', 'F4A261'),
          ('accent5', '5B8A9A'), ('accent6', '8AB17D'), ('hlink', '2A9D8F'), ('folHlink', '5B8A9A')]


def emu(v):
    return int(round(v * 914400))


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def fill(c, alpha=None):
    tag = 'schemeClr' if c in SCHEME else 'srgbClr'
    inner = f'<a:alpha val="{alpha}"/>' if alpha is not None else ''
    return f'<a:solidFill><a:{tag} val="{c}">{inner}</a:{tag}></a:solidFill>'


def frag(xml):
    root = etree.fromstring(f'<root xmlns:a="{NS_A}" xmlns:p="{NS_P}" xmlns:r="{NS_R}">{xml}</root>'.encode())
    return list(root)


def parse(data):
    return etree.fromstring(data, etree.XMLParser(remove_blank_text=False))


def serialize(root):
    etree.cleanup_namespaces(root)
    body = etree.tostring(root, encoding='UTF-8').decode('utf-8')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\r\n' + body).encode('utf-8')


# ---------------------------------------------------------------- theme
def fix_theme(xml):
    clr = ''.join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in COLORS)
    xml = re.sub(r'<a:clrScheme name="[^"]*">.*?</a:clrScheme>',
                 f'<a:clrScheme name="{THEME_NAME}">{clr}</a:clrScheme>', xml, flags=re.S)
    fonts = f'<a:latin typeface="{FONT}"/><a:ea typeface="{FONT}"/><a:cs typeface=""/><a:font script="Hang" typeface="{FONT}"/>'
    xml = re.sub(r'<a:fontScheme name="[^"]*">.*?</a:fontScheme>',
                 f'<a:fontScheme name="{FONT}"><a:majorFont>{fonts}</a:majorFont><a:minorFont>{fonts}</a:minorFont></a:fontScheme>',
                 xml, flags=re.S)
    xml = xml.replace('name="Office Theme"', f'name="{THEME_NAME}"')
    return xml


# ---------------------------------------------------------------- master
def body_lvl(n, marL, indent, sz, bu, spc_bef, color='tx1', bu_clr='accent1'):
    return (f'<a:lvl{n}pPr marL="{marL}" indent="{indent}" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
            f'<a:lnSpc><a:spcPct val="110000"/></a:lnSpc><a:spcBef><a:spcPts val="{spc_bef * 100}"/></a:spcBef>'
            f'<a:buClr><a:schemeClr val="{bu_clr}"/></a:buClr><a:buFont typeface="Arial" panose="020B0604020202020204" pitchFamily="34" charset="0"/>'
            f'<a:buChar char="{bu}"/><a:defRPr sz="{sz * 100}" kern="1200">{fill(color)}'
            '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl' + f'{n}pPr>')


def other_lvl(n):
    return (f'<a:lvl{n}pPr marL="{(n - 1) * 457200}" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
            f'<a:defRPr sz="1800" kern="1200">{fill("tx1")}<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl{n}pPr>')


TX_STYLES = (
    '<p:txStyles><p:titleStyle>'
    '<a:lvl1pPr algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1">'
    '<a:lnSpc><a:spcPct val="100000"/></a:lnSpc><a:spcBef><a:spcPct val="0"/></a:spcBef><a:buNone/>'
    f'<a:defRPr sz="3000" b="1" kern="1200">{fill("tx2")}<a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/><a:cs typeface="+mj-cs"/></a:defRPr>'
    '</a:lvl1pPr></p:titleStyle><p:bodyStyle>'
    + body_lvl(1, 285750, -285750, 18, '•', 12)
    + body_lvl(2, 685800, -228600, 16, '–', 4, bu_clr='tx2')
    + body_lvl(3, 1085850, -228600, 14, '•', 4, bu_clr='tx2')
    + ''.join(body_lvl(n, 1085850 + (n - 3) * 400050, -228600, 14, '–' if n % 2 == 0 else '•', 4, bu_clr='tx2') for n in range(4, 10))
    + '</p:bodyStyle><p:otherStyle><a:defPPr><a:defRPr lang="ko-KR"/></a:defPPr>'
    + ''.join(other_lvl(n) for n in range(1, 10))
    + '</p:otherStyle></p:txStyles>'
)


def sldnum_lst():
    return f'<a:lstStyle><a:lvl1pPr algn="r"><a:defRPr sz="1100">{fill(GRAY_L)}</a:defRPr></a:lvl1pPr></a:lstStyle>'


def master_cSld():
    def sp(id_, name, ph, x, y, w, h, body, anchor, lst='<a:lstStyle/>'):
        return (f'<p:sp><p:nvSpPr><p:cNvPr id="{id_}" name="{name}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
                f'<p:nvPr><p:ph {ph}/></p:nvPr></p:nvSpPr><p:spPr><a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/>'
                f'<a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
                f'<p:txBody><a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0" anchor="{anchor}">'
                f'<a:normAutofit/></a:bodyPr>{lst}{body}</p:txBody></p:sp>')

    def para(t, lvl=0):
        ppr = f'<a:pPr lvl="{lvl}"/>' if lvl else ''
        return f'<a:p>{ppr}<a:r><a:rPr {LANG}/><a:t>{t}</a:t></a:r></a:p>'

    levels = ['마스터 텍스트 스타일을 편집하려면 클릭', '둘째 수준', '셋째 수준', '넷째 수준', '다섯째 수준']
    return ('<p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>'
            '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
            '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
            + sp(2, '제목 개체 틀 1', 'type="title"', 0.95, 0.42, 11.78, 0.9, para('마스터 제목 스타일 편집'), 'ctr')
            + sp(3, '텍스트 개체 틀 2', 'type="body" idx="1"', 0.6, 1.6, 12.133, 5.1,
                 ''.join(para(t, i) for i, t in enumerate(levels)), 't')
            + sp(4, '슬라이드 번호 개체 틀 3', 'type="sldNum" sz="quarter" idx="4"', 11.73, 6.9, 1.0, 0.35,
                 f'<a:p><a:fld id="{FLD_ID}" type="slidenum"><a:rPr {LANG}/><a:t>‹#›</a:t></a:fld><a:endParaRPr {LANG}/></a:p>',
                 'ctr', sldnum_lst())
            + '</p:spTree></p:cSld>')


def fix_master(xml):
    xml = re.sub(r'<p:cSld>.*?</p:cSld>', lambda m: master_cSld(), xml, count=1, flags=re.S)
    xml = re.sub(r'<p:txStyles>.*?</p:txStyles>', lambda m: TX_STYLES, xml, count=1, flags=re.S)
    xml = xml.replace('<p:hf sldNum="0" hdr="0" ftr="0" dt="0"/>', '<p:hf hdr="0" ftr="0" dt="0"/>')
    # '빈 화면'(pptxgenjs 기본 레이아웃)을 새 슬라이드 목록의 맨 뒤로
    m = re.search(r'<p:sldLayoutIdLst>(<p:sldLayoutId [^>]*/>)(.*?)</p:sldLayoutIdLst>', xml, flags=re.S)
    xml = xml[:m.start()] + f'<p:sldLayoutIdLst>{m.group(2)}{m.group(1)}</p:sldLayoutIdLst>' + xml[m.end():]
    return xml


# ---------------------------------------------------------------- placeholders
PH_NAMES = {'title': '제목', 'body': '텍스트 개체 틀', 'pic': '그림 개체 틀', 'sldNum': '슬라이드 번호 개체 틀'}


def ph_attr(ph):
    t = ph['type']
    a = [f'type="{t}"']
    if t == 'sldNum':
        a.append('sz="quarter"')
    if t != 'title':
        a.append(f'idx="{ph["idx"]}"')
    return a


def lvl_ppr(n, st):
    attrs, inner = [], ''
    if st.get('algn'):
        attrs.append(f'algn="{st["algn"]}"')
    if not st.get('bullets'):
        attrs += ['marL="0"', 'indent="0"']
    if st.get('lnSpc'):
        inner += f'<a:lnSpc><a:spcPct val="{st["lnSpc"] * 1000}"/></a:lnSpc>'
    if 'spcBef' in st:
        inner += f'<a:spcBef><a:spcPts val="{st["spcBef"] * 100}"/></a:spcBef>'
    if not st.get('bullets'):
        inner += '<a:buNone/>'
    r = [f'sz="{st["sz"] * 100}"']
    if 'b' in st:
        r.append(f'b="{1 if st["b"] else 0}"')
    if st.get('spc'):
        r.append(f'spc="{st["spc"]}"')
    col = fill(st['color']) if st.get('color') else ''
    return f'<a:lvl{n}pPr {" ".join(attrs)}>{inner}<a:defRPr {" ".join(r)}>{col}</a:defRPr></a:lvl{n}pPr>'


def layout_ph(ph):
    ins = ph.get('ins')
    ins_attr = (f' lIns="{emu(ins[0])}" tIns="{emu(ins[1])}" rIns="{emu(ins[2])}" bIns="{emu(ins[3])}"' if ins else '')
    if ph.get('lvl2'):
        lst = lvl_ppr(1, ph['lvl1']) + lvl_ppr(2, ph['lvl2'])
    else:
        # 글머리 없는 개체 틀은 Tab 으로 수준이 바뀌어도 같은 모양을 유지
        lst = ''.join(lvl_ppr(n, ph['lvl1']) for n in (1, 2, 3))
    attrs = ph_attr(ph) + ['hasCustomPrompt="1"']
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="0" name="{PH_NAMES[ph["type"]]}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph {" ".join(attrs)}/></p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(ph["x"])}" y="{emu(ph["y"])}"/><a:ext cx="{emu(ph["w"])}" cy="{emu(ph["h"])}"/></a:xfrm></p:spPr>'
            f'<p:txBody><a:bodyPr{ins_attr} anchor="{ph.get("anchor", "t")}"><a:normAutofit/></a:bodyPr><a:lstStyle>{lst}</a:lstStyle>'
            f'<a:p><a:r><a:rPr {LANG} dirty="0"/><a:t>{esc(ph["prompt"])}</a:t></a:r><a:endParaRPr {LANG} dirty="0"/></a:p></p:txBody></p:sp>')


def layout_sldnum():
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="0" name="{PH_NAMES["sldNum"]}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="sldNum" sz="quarter" idx="{SLDNUM_IDX}"/></p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{emu(11.73)}" y="{emu(6.9)}"/><a:ext cx="{emu(1.0)}" cy="{emu(0.35)}"/></a:xfrm></p:spPr>'
            f'<p:txBody><a:bodyPr anchor="ctr"/>{sldnum_lst()}<a:p><a:fld id="{FLD_ID}" type="slidenum"><a:rPr {LANG}/><a:t>‹#›</a:t></a:fld>'
            f'<a:endParaRPr {LANG}/></a:p></p:txBody></p:sp>')


def para_xml(p):
    ppr_attrs = []
    if p.get('lvl'):
        ppr_attrs.append(f'lvl="{p["lvl"]}"')
    ppr_inner = ''
    if p.get('bullet') == 'none':
        ppr_attrs += ['marL="0"', 'indent="0"']
        ppr_inner = '<a:buNone/>'
    ppr = ''
    if ppr_attrs or ppr_inner:
        ppr = f'<a:pPr {" ".join(ppr_attrs)}>{ppr_inner}</a:pPr>' if ppr_inner else f'<a:pPr {" ".join(ppr_attrs)}/>'
    runs = ''
    for r in p['runs']:
        b = ' b="1"' if r.get('b') else ''
        col = fill(r['color']) if r.get('color') else ''
        lines = r['t'].split('\n')
        for i, line in enumerate(lines):
            if i:
                runs += f'<a:br><a:rPr {LANG}{b} dirty="0"/></a:br>'
            space = ' xml:space="preserve"' if line != line.strip() else ''
            runs += f'<a:r><a:rPr {LANG}{b} dirty="0">{col}</a:rPr><a:t{space}>{esc(line)}</a:t></a:r>'
    return f'<a:p>{ppr}{runs}<a:endParaRPr {LANG} dirty="0"/></a:p>'


def slide_ph(ph, paras):
    body = ''.join(para_xml(p) for p in paras) if paras else f'<a:p><a:endParaRPr {LANG} dirty="0"/></a:p>'
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="0" name="{PH_NAMES[ph["type"]]}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph {" ".join(ph_attr(ph))}/></p:nvPr></p:nvSpPr><p:spPr/>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/>{body}</p:txBody></p:sp>')


def slide_sldnum(n):
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="0" name="{PH_NAMES["sldNum"]}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            f'<p:nvPr><p:ph type="sldNum" sz="quarter" idx="{SLDNUM_IDX}"/></p:nvPr></p:nvSpPr><p:spPr/>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:fld id="{FLD_ID}" type="slidenum"><a:rPr {LANG}/><a:t>{n}</a:t></a:fld>'
            f'<a:endParaRPr {LANG}/></a:p></p:txBody></p:sp>')


# ---------------------------------------------------------------- tree utilities
def sp_tree(root):
    return root.find('p:cSld/p:spTree', NS)


def first_shape_index(tree):
    for i, el in enumerate(tree):
        if etree.QName(el).localname not in ('nvGrpSpPr', 'grpSpPr'):
            return i
    return len(tree)


def group_shapes(tree):
    groups = {}
    order = []
    for el in list(tree):
        c = el.find('.//p:cNvPr', NS)
        if c is None:
            continue
        name = c.get('name', '')
        if name.startswith('GRP::'):
            _, g, member = name.split('::', 2)
            c.set('name', member)
            if g not in groups:
                groups[g] = []
                order.append(g)
            groups[g].append(el)
    for g in order:
        els = groups[g]
        boxes = []
        for el in els:
            xfrm = el.find('p:spPr/a:xfrm', NS)
            off, ext = xfrm.find('a:off', NS), xfrm.find('a:ext', NS)
            x, y = int(off.get('x')), int(off.get('y'))
            boxes.append((x, y, x + int(ext.get('cx')), y + int(ext.get('cy'))))
        x0, y0 = min(b[0] for b in boxes), min(b[1] for b in boxes)
        x1, y1 = max(b[2] for b in boxes), max(b[3] for b in boxes)
        grp = frag(f'<p:grpSp><p:nvGrpSpPr><p:cNvPr id="0" name="{esc(g)}"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
                   f'<p:grpSpPr><a:xfrm><a:off x="{x0}" y="{y0}"/><a:ext cx="{x1 - x0}" cy="{y1 - y0}"/>'
                   f'<a:chOff x="{x0}" y="{y0}"/><a:chExt cx="{x1 - x0}" cy="{y1 - y0}"/></a:xfrm></p:grpSpPr></p:grpSp>')[0]
        tree.insert(tree.index(els[0]), grp)
        for el in els:
            grp.append(el)


def renumber(tree):
    for i, c in enumerate(tree.iter(f'{{{NS_P}}}cNvPr'), start=1):
        c.set('id', str(i))
        if i > 1 and c.get('name', '').startswith(tuple(PH_NAMES.values())):
            c.set('name', f'{c.get("name").rstrip("0123456789 ")} {i - 1}')


def fix_lang(xml):
    xml = re.sub(r'lang="en-US"(?! altLang)', LANG, xml)
    return xml.replace('<c:lang val="en-US"/>', '<c:lang val="ko-KR"/>')


def fix_notes(xml):
    def split(m):
        lines = m.group(2).split('\n')
        return ''.join(f'<a:p><a:r><a:rPr {LANG} dirty="0"/><a:t>{ln}</a:t></a:r></a:p>' for ln in lines)
    return re.sub(r'<a:p><a:r><a:rPr (lang="[^"]*"[^>]*?) dirty="0"/><a:t>([^<]*\n[^<]*)</a:t></a:r><a:endParaRPr[^>]*/></a:p>', split, xml)


def fix_chart(xml):
    xml = xml.replace('<a:latin typeface="+mn-lt"/>', '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/>')
    return xml


# ---------------------------------------------------------------- main
def main():
    spec = json.load(open(SPEC, encoding='utf-8'))
    zin = zipfile.ZipFile(SRC)
    files = {n: zin.read(n) for n in zin.namelist()}
    order = zin.namelist()

    files['ppt/theme/theme1.xml'] = fix_theme(files['ppt/theme/theme1.xml'].decode()).encode()
    files['ppt/slideMasters/slideMaster1.xml'] = fix_master(files['ppt/slideMasters/slideMaster1.xml'].decode()).encode()

    # layouts
    layout_name = {}
    for n in sorted(k for k in files if re.match(r'ppt/slideLayouts/slideLayout\d+\.xml$', k)):
        root = parse(files[n])
        csld = root.find('p:cSld', NS)
        name = csld.get('name')
        if name == 'DEFAULT':
            name = '빈 화면'
            csld.set('name', name)
            lspec = {'ph': [], 'num': True}
        else:
            lspec = spec['layouts'][name]
        layout_name[n.split('/')[-1]] = name
        tree = sp_tree(root)
        for ph in lspec['ph']:
            tree.extend(frag(layout_ph(ph)))
        if lspec['num']:
            tree.extend(frag(layout_sldnum()))
        renumber(tree)
        files[n] = serialize(root)
    spec['layouts']['빈 화면'] = {'ph': [], 'num': True}

    # slides
    for i, sspec in enumerate(spec['slides'], start=1):
        n = f'ppt/slides/slide{i}.xml'
        rels = files[f'ppt/slides/_rels/slide{i}.xml.rels'].decode()
        lay_file = re.search(r'Target="\.\./slideLayouts/(slideLayout\d+\.xml)"', rels).group(1)
        assert layout_name[lay_file] == sspec['layout'], (i, layout_name[lay_file], sspec['layout'])
        lspec = spec['layouts'][sspec['layout']]
        root = parse(files[n])
        csld = root.find('p:cSld', NS)
        csld.attrib.pop('name', None)
        tree = sp_tree(root)
        pos = first_shape_index(tree)
        for ph in lspec['ph']:
            el = frag(slide_ph(ph, sspec['ph'].get(ph['key'])))[0]
            tree.insert(pos, el)
            pos += 1
        missing = set(sspec['ph']) - {p['key'] for p in lspec['ph']}
        assert not missing, (i, missing)
        if lspec['num']:
            tree.extend(frag(slide_sldnum(i)))
        group_shapes(tree)
        renumber(tree)
        files[n] = serialize(root)

    for n in list(files):
        if re.match(r'ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$', n) or re.match(r'ppt/charts/chart\d+\.xml$', n):
            x = fix_lang(files[n].decode())
            if n.startswith('ppt/notesSlides/'):
                x = fix_notes(x)
            if n.startswith('ppt/charts/'):
                x = fix_chart(x)
            files[n] = x.encode()

    hidden = sum(b' show="0"' in files[f'ppt/slides/slide{i}.xml'] for i in range(1, len(spec['slides']) + 1))
    app = files['docProps/app.xml'].decode()
    app = re.sub(r'<HiddenSlides>\d+</HiddenSlides>', f'<HiddenSlides>{hidden}</HiddenSlides>', app)
    app = app.replace('<vt:lpstr>Calibri</vt:lpstr>', f'<vt:lpstr>{FONT}</vt:lpstr>')
    app = app.replace('<vt:lpstr>Office Theme</vt:lpstr>', f'<vt:lpstr>{THEME_NAME}</vt:lpstr>')
    files['docProps/app.xml'] = app.encode()

    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
        names = ['[Content_Types].xml'] + [n for n in order if n != '[Content_Types].xml']
        for n in names:
            z.writestr(n, files[n])
    print('wrote', OUT)


if __name__ == '__main__':
    main()
