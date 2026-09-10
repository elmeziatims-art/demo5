#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebranche _CALC_ALLOC sur l'onglet template Tagetik 'Allocation2' (VERSION en B,
   donc mapping decale de +1) et ajoute les 8 colonnes POOL a la fin de Allocation2
   (X->AE, contigues a A->W => une seule matrice liee a la vue).
   Chirurgical : seuls sheet5 (Allocation2) + sheet13 (_CALC_ALLOC) + workbook."""
import zipfile,re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else "Alloc_2.xlsx"
OUT=sys.argv[2] if len(sys.argv)>2 else "Alloc_2_CALC.xlsx"

# ancien Allocation -> nouveau Allocation2 (colonnes)
CMAP={'C':'D','D':'E','E':'F','F':'G','G':'H','H':'I','I':'J','J':'K','K':'L',
      'AE':'X','AF':'Y','AG':'Z','AH':'AA','AI':'AB','AJ':'AC','AK':'AD','AL':'AE'}
POOLH=[('X','VOL_NEW'),('Y','POOL_VAC'),('Z','POOL_PERM'),('AA','POOL_ODIR'),
       ('AB','POOL_MKT'),('AC','POOL_STRUCT'),('AD','POOL_HOLDING'),('AE','POOL_FRAIS_MARQUE')]

zin=zipfile.ZipFile(SRC)

# ---------- 1) _CALC_ALLOC : Allocation!<col> -> Allocation2!<newcol> ----------
x13=zin.read("xl/worksheets/sheet13.xml").decode("utf8")
def remap(m):
    col=m.group(1)
    if col not in CMAP: return m.group(0)        # laisse tel quel si non mappe
    return 'Allocation2!%s%s'%(CMAP[col],m.group(2))
x13n,ncnt=re.subn(r'(?<![A-Za-z0-9_])Allocation!([A-Z]{1,2})(\d+)',remap,x13)

# ---------- 2) Allocation2 : en-tetes X..AE (l.1) + placeholders (l.2) ----------
x5=zin.read("xl/worksheets/sheet5.xml").decode("utf8")
def rebuild_tail(x,row,newcells,spans_to=31):
    mo=re.search(r'(<row r="%d"[^>]*>)(.*?)(</row>)'%row,x,re.S)
    open_tag,body,close=mo.group(1),mo.group(2),mo.group(3)
    cm=re.search(r'<c r="W%d"[^>]*?(?:/>|>.*?</c>)'%row,body,re.S)   # garde jusqu'a W
    newbody=body[:cm.end()]+"".join(newcells)
    open_tag=re.sub(r'spans="(\d+):\d+"',r'spans="\1:%d"'%spans_to,open_tag)
    return x[:mo.start()]+open_tag+newbody+close+x[mo.end():]
hdr=['<c r="%s1" s="6" t="inlineStr"><is><t>%s</t></is></c>'%(c,n) for c,n in POOLH]
dat=['<c r="%s2" s="6"/>'%c for c,_ in POOLH]
x5=rebuild_tail(x5,1,hdr)
x5=rebuild_tail(x5,2,dat)
x5=re.sub(r'(<dimension ref="A1:)[A-Z]+(\d+"/>)',r'\1AE\2',x5,count=1)

# ---------- 3) workbook : fullCalcOnLoad ----------
wb=zin.read("xl/workbook.xml").decode("utf8")
if "fullCalcOnLoad" not in wb:
    wb=re.sub(r'<calcPr calcId="(\d+)"',r'<calcPr calcId="\1" fullCalcOnLoad="1"',wb,count=1)

mod={"xl/worksheets/sheet13.xml":x13n.encode("utf8"),
     "xl/worksheets/sheet5.xml":x5.encode("utf8"),
     "xl/workbook.xml":wb.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=mod.get(it.filename, zin.read(it.filename))
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,data)
zout.close()
print("OK -> %s | _CALC_ALLOC refs remappees=%d | Allocation2 +8 colonnes POOL"%(OUT,ncnt))
