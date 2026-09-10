#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mise en page CHIRURGICALE d'un .xlsm Design Tagetik.
Ne touche QUE styles.xml + l'onglet cad. Rezip fidele: reutilise les ZipInfo
d'origine (create_version/system, date, ordre) -> Excel n'a rien a 'reparer'."""
import zipfile,re

SRC="TGK_DESIGN.xlsm"; OUT="CAD_SAAD_FORMATE.xlsm"
zin=zipfile.ZipFile(SRC)

# ---- 1) styles.xml : +1 fill (navy), +1 font (blanc gras), +1 cellXf ----
s=zin.read("xl/styles.xml").decode("utf8")

def bump(tag):
    global s
    m=re.search(r'(<%s count=")(\d+)(")'%tag,s)
    n=int(m.group(2))
    s=s[:m.start()]+m.group(1)+str(n+1)+m.group(3)+s[m.end():]
    return n  # ancien compte = index du nouvel element

fill_idx=bump("fills")
s=s.replace('</fills>','<fill><patternFill patternType="solid"><fgColor rgb="FF1F3864"/><bgColor indexed="64"/></patternFill></fill></fills>',1)
font_idx=bump("fonts")
s=s.replace('</fonts>','<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font></fonts>',1)
xf_idx=bump("cellXfs")
s=s.replace('</cellXfs>','<xf numFmtId="0" fontId="%d" fillId="%d" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs>'%(font_idx,fill_idx),1)

# verif coherence count == enfants
def check(tag,child):
    blk=re.search(r'<%s [^>]*>(.*?)</%s>'%(tag,tag),s,re.S).group(1)
    dec=int(re.search(r'<%s count="(\d+)"'%tag,s).group(1))
    act=blk.count("<%s"%child)
    assert dec==act,"MISMATCH %s dec=%d act=%d"%(tag,dec,act)
    return dec,act
for t,c in [("fills","fill"),("fonts","font"),("cellXfs","xf")]:
    print(t,check(t,c))

# ---- 2) onglet cad (sheet2.xml) : appliquer le style navy a 3 cellules ----
sh=zin.read("xl/worksheets/sheet2.xml").decode("utf8")
for cell in ("I8","H9","H10"):
    # <c r="I8" s="1" ...> ou <c r="I8" ...> -> forcer s=xf_idx
    def repl(m):
        attrs=m.group(1)
        if ' s="' in attrs: attrs=re.sub(r' s="\d+"',' s="%d"'%xf_idx,attrs)
        else: attrs=attrs+' s="%d"'%xf_idx
        return '<c r="%s"'%cell+attrs
    sh=re.sub(r'<c r="%s"([^>]*)'%cell,repl,sh,count=1)

# ---- 3) rezip fidele : reutiliser les ZipInfo d'origine ----
mods={"xl/styles.xml":s.encode("utf8"),"xl/worksheets/sheet2.xml":sh.encode("utf8")}
with zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED) as zout:
    for zi in zin.infolist():                      # ordre + metadata d'origine
        data=mods.get(zi.filename, zin.read(zi.filename))
        # ZipInfo neuf clone pour eviter effets de bord, garde metadata cle
        ni=zipfile.ZipInfo(zi.filename,date_time=zi.date_time)
        ni.compress_type=zi.compress_type
        ni.create_system=zi.create_system          # 0 (Windows) comme l'origine
        ni.create_version=zi.create_version         # 45
        ni.extract_version=zi.extract_version
        ni.external_attr=zi.external_attr
        ni.internal_attr=zi.internal_attr
        ni.flag_bits=zi.flag_bits
        zout.writestr(ni,data)
print("OK ->",OUT)
