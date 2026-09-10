#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend _CALC_ALLOC VERSION-AWARE : les 3 versions 2027 (V01/V02/V03) coexistent
   dans Allocation2, mais les agregats sommaient par exercice seul -> ils melangeaient
   les versions. On ajoute une cle combinee EXVER = exercice|version (colonne AS) et
   on bascule TOUS les agregats sur cette cle. Les pools viennent de la vue (deja par
   version) -> inchanges. Chirurgical : seul _CALC_ALLOC (sheet13) modifie."""
import zipfile,re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else "Alloc_2_CALC_v2.xlsx"
OUT=sys.argv[2] if len(sys.argv)>2 else "Alloc_2_CALC_v3.xlsx"
NMAX=349
zin=zipfile.ZipFile(SRC)
wb=zin.read("xl/workbook.xml").decode("utf8");rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
n2f={m.group(1):("xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wb) if m.group(2) in id2f}
F13=n2f["_CALC_ALLOC"]
x=zin.read(F13).decode("utf8")

# 1) basculer les agregats sur la cle combinee AS (exercice|version)
x,n=re.subn(r'\$A\$1:\$A\$349,\$A(\d+)',r'$AS$1:$AS$349,$AS\1',x)

# 2) colonne AS = EXVER = exercice & "|" & version(Allocation2!B)
#    en-tete AS1 avant AT1
x=re.sub(r'(<c r="AT1")',
         r'<c r="AS1" t="inlineStr"><is><t>EXVER</t></is></c>\1',x,count=1)
#    formule AS{r} inseree avant </row> pour chaque ligne de donnees
def add_as(m):
    r=int(m.group(1)); body=m.group(2)
    f='IF($A%d="","",$A%d&amp;"|"&amp;Allocation2!B%d)'%(r,r,r)
    cell='<c r="AS%d"><f>%s</f></c>'%(r,f)
    return m.group(0)[:m.group(0).rfind('</row>')]+cell+'</row>'
x=re.sub(r'<row r="(\d+)"[^>]*>(.*?)</row>',
         lambda m:(add_as(m) if 2<=int(m.group(1))<=NMAX else m.group(0)),x,flags=re.S)

mod={F13:x.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,mod.get(it.filename,zin.read(it.filename)))
zout.close()
print("OK -> %s | agregats bascules sur EXVER=%d | colonne AS ajoutee"%(OUT,n))
