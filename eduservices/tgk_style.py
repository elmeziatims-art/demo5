#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""StyleBank : ajoute des styles (police/fond/bordure/format/alignement) a un
styles.xml EXISTANT sans toucher aux index 0..N deja utilises par les autres
onglets. Retourne des index cellXf (attribut s=) a poser via tgk_surgery."""
import re

def _esc_attr(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

class StyleBank:
    def __init__(self, xml):
        self.xml = xml
        def cnt(tag):
            m = re.search(r'<%s count="(\d+)"' % tag, xml)
            return int(m.group(1)) if m else 0
        self.font_base   = cnt("fonts")
        self.fill_base   = cnt("fills")
        self.border_base = cnt("borders")
        self.xf_base     = cnt("cellXfs")
        ids = [int(i) for i in re.findall(r'<numFmt numFmtId="(\d+)"', xml)]
        self.next_nf = max([163] + ids) + 1
        m = re.search(r'<dxfs count="(\d+)"', xml)
        self.dxf_base = int(m.group(1)) if m else 0
        self.nf, self.fo, self.fl, self.bo, self.xf_, self.dx = [], [], [], [], [], []
        self._c = {}

    def dxf(self, color=None, bold=False, fill=None):
        """format differentiel (conditionalFormatting). Retourne un dxfId."""
        k = ("dx", color, bold, fill)
        if k in self._c: return self._c[k]
        parts = ['<dxf>']
        if color or bold:
            parts.append('<font>%s%s</font>' % ('<b/>' if bold else '',
                         ('<color rgb="FF%s"/>' % color) if color else ''))
        if fill:
            parts.append('<fill><patternFill><bgColor rgb="FF%s"/></patternFill></fill>' % fill)
        parts.append('</dxf>')
        i = self.dxf_base + len(self.dx); self.dx.append(''.join(parts)); self._c[k] = i; return i

    def font(self, sz=10, bold=False, italic=False, color="1C2733"):
        k = ("fo", sz, bold, italic, color)
        if k in self._c: return self._c[k]
        x = '<font>%s%s<sz val="%s"/><color rgb="FF%s"/><name val="Arial"/><family val="2"/></font>' % (
            '<b/>' if bold else '', '<i/>' if italic else '', sz, color)
        i = self.font_base + len(self.fo); self.fo.append(x); self._c[k] = i; return i

    def fill(self, rgb):
        if rgb is None: return 0
        k = ("fl", rgb)
        if k in self._c: return self._c[k]
        x = '<fill><patternFill patternType="solid"><fgColor rgb="FF%s"/><bgColor indexed="64"/></patternFill></fill>' % rgb
        i = self.fill_base + len(self.fl); self.fl.append(x); self._c[k] = i; return i

    def border(self, top=None, bottom=None, left=None, right=None):
        """chaque cote = (rgb, style) ou None. style: thin/medium/thick."""
        k = ("bo", top, bottom, left, right)
        if k in self._c: return self._c[k]
        def sd(name, spec):
            if not spec: return '<%s/>' % name
            rgb, style = spec
            return '<%s style="%s"><color rgb="FF%s"/></%s>' % (name, style, rgb, name)
        x = '<border>%s%s%s%s<diagonal/></border>' % (sd("left", left), sd("right", right), sd("top", top), sd("bottom", bottom))
        i = self.border_base + len(self.bo); self.bo.append(x); self._c[k] = i; return i

    def numfmt(self, code):
        k = ("nf", code)
        if k in self._c: return self._c[k]
        nid = self.next_nf; self.next_nf += 1
        self.nf.append('<numFmt numFmtId="%d" formatCode="%s"/>' % (nid, _esc_attr(code)))
        self._c[k] = nid; return nid

    def xf(self, font=0, fill=0, border=0, numfmt=None, halign=None, valign=None, wrap=False, indent=0):
        k = ("xf", font, fill, border, numfmt, halign, valign, wrap, indent)
        if k in self._c: return self._c[k]
        al = ''; applyAl = ''
        if halign or valign or wrap or indent:
            a = []
            if halign: a.append('horizontal="%s"' % halign)
            if valign: a.append('vertical="%s"' % valign)
            if wrap: a.append('wrapText="1"')
            if indent: a.append('indent="%d"' % indent)
            al = '<alignment %s/>' % ' '.join(a); applyAl = ' applyAlignment="1"'
        x = ('<xf numFmtId="%d" fontId="%d" fillId="%d" borderId="%d" xfId="0"'
             ' applyFont="1" applyFill="1" applyBorder="1"%s%s>%s</xf>') % (
            numfmt or 0, font, fill, border,
            (' applyNumberFormat="1"' if numfmt else ''), applyAl, al)
        i = self.xf_base + len(self.xf_); self.xf_.append(x); self._c[k] = i; return i

    def render(self):
        xml = self.xml
        if self.nf:
            if '<numFmts' in xml:
                xml = re.sub(r'(<numFmts count=")(\d+)(")',
                             lambda m: m.group(1) + str(int(m.group(2)) + len(self.nf)) + m.group(3), xml, count=1)
                xml = xml.replace('</numFmts>', ''.join(self.nf) + '</numFmts>', 1)
            else:
                blk = '<numFmts count="%d">%s</numFmts>' % (len(self.nf), ''.join(self.nf))
                xml = re.sub(r'(<styleSheet[^>]*>)', lambda m: m.group(1) + blk, xml, count=1)
        for tag, items in (("fonts", self.fo), ("fills", self.fl), ("borders", self.bo), ("cellXfs", self.xf_)):
            if not items: continue
            xml = re.sub(r'(<%s count=")(\d+)(")' % tag,
                         lambda m: m.group(1) + str(int(m.group(2)) + len(items)) + m.group(3), xml, count=1)
            xml = xml.replace('</%s>' % tag, ''.join(items) + '</%s>' % tag, 1)
        if self.dx:
            if '<dxfs' in xml:
                xml = re.sub(r'(<dxfs count=")(\d+)(")',
                             lambda m: m.group(1) + str(int(m.group(2)) + len(self.dx)) + m.group(3), xml, count=1)
                if '</dxfs>' in xml:
                    xml = xml.replace('</dxfs>', ''.join(self.dx) + '</dxfs>', 1)
                else:  # <dxfs count="0"/>
                    xml = re.sub(r'<dxfs count="\d+"/>', '<dxfs count="%d">%s</dxfs>' % (self.dxf_base + len(self.dx), ''.join(self.dx)), xml, count=1)
            else:  # inserer <dxfs> apres </cellStyles> (ordre schema)
                blk = '<dxfs count="%d">%s</dxfs>' % (len(self.dx), ''.join(self.dx))
                if '</cellStyles>' in xml: xml = xml.replace('</cellStyles>', '</cellStyles>' + blk, 1)
                else: xml = xml.replace('</cellXfs>', '</cellXfs>' + blk, 1)
        return xml
