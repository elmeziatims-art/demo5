#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inline les 51 zones nommees -> references directes DANS LES FORMULES uniquement.
Perf Tagetik web : le recalcul ne resout plus les noms. Chirurgical : briques
Tagetik + definedNames (ancrage dimensions) conserves byte-identiques."""
import zipfile,re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else "DESIGN_REF_v2.xlsm"
OUT=sys.argv[2] if len(sys.argv)>2 else "DESIGN_REF_v3.xlsm"
zin=zipfile.ZipFile(SRC)
wbxml=zin.read("xl/workbook.xml").decode("utf8")
name2ref={}
for attrs,val in re.findall(r'<definedName ([^>]*)>(.*?)</definedName>',wbxml,re.S):
    nm=re.search(r'name="([^"]+)"',attrs).group(1); name2ref[nm]=val.strip()
names_sorted=sorted(name2ref,key=len,reverse=True)
NAMEPAT=re.compile(r'\b(?:'+'|'.join(re.escape(n) for n in names_sorted)+r')\b')
def inline_text(t): return NAMEPAT.sub(lambda m:name2ref[m.group(0)],t)
# remplace uniquement dans <f>, <formula>, <formula1>, <formula2>
TAGS=re.compile(r'(<(f|formula|formula1|formula2)\b[^>]*>)([^<]*)(</\2>)')
def process(xml):
    return TAGS.sub(lambda m:m.group(1)+inline_text(m.group(3))+m.group(4),xml)
count_before=count_after=0
mod={}
for it in zin.infolist():
    data=zin.read(it.filename)
    if it.filename.startswith("xl/worksheets/sheet") and it.filename.endswith(".xml"):
        x=data.decode("utf8")
        count_before+=len(NAMEPAT.findall(" ".join(re.findall(r'<f\b[^>]*>([^<]*)</f>',x))))
        x2=process(x)
        count_after+=len(NAMEPAT.findall(" ".join(re.findall(r'<f\b[^>]*>([^<]*)</f>',x2))))
        mod[it.filename]=x2.encode("utf8")
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=mod.get(it.filename, zin.read(it.filename))
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,data)
zout.close()
print(f"usages de noms dans formules : {count_before} -> {count_after}")
print(f"OK -> {OUT}")
