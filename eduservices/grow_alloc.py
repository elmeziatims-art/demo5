#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sur le DESIGN Alloc_2_CALC.xlsx (briques Tagetik intactes) :
   1) _CALC_ALLOC agrandi de 175 -> 349 lignes (Allocation2 = 348 lignes runtime,
      dont 2027 au-dela de 175) + bornes de plages internes $175 -> $349.
   2) Tableau ALLOC repointe Allocation2 -> _CALC_ALLOC (bon mapping) + plages $349.
   Chirurgical : seuls sheet13 (_CALC_ALLOC), sheet4 (ALLOC), workbook modifies."""
import zipfile,re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else "Alloc_2_CALC.xlsx"
OUT=sys.argv[2] if len(sys.argv)>2 else "Alloc_2_CALC_v2.xlsx"
NMAX=349

zin=zipfile.ZipFile(SRC)
wb=zin.read("xl/workbook.xml").decode("utf8")
rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
n2f={m.group(1):("xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wb) if m.group(2) in id2f}
F13=n2f["_CALC_ALLOC"]; F4=n2f["ALLOC"]

# ================= 1) _CALC_ALLOC : etendre bornes + cloner lignes =================
x=zin.read(F13).decode("utf8")
# a) bornes de plages $...$1:$...$175 -> $349  ('$175' = uniquement des bornes de plage)
x=x.replace("$175","$349")
# b) template = ligne 2 (masters -> plein, sans cache)
mrow=re.search(r'(<row r="2"[^>]*>)(.*?)(</row>)',x,re.S)
open2,body2=mrow.group(1),mrow.group(2)
def to_plain(cellbody):
    # <f t="shared" ref=".." si="N">TXT</f> -> <f>TXT</f> ; supprime <v>
    cb=re.sub(r'<f t="shared"[^>]*?>(.*?)</f>',r'<f>\1</f>',cellbody,flags=re.S)
    cb=re.sub(r'<f t="shared"[^>]*?/>','',cb)          # instance vide (ne devrait pas exister)
    cb=re.sub(r'<v>.*?</v>','',cb,flags=re.S)
    return cb
body2p=to_plain(body2)

def clone(r):
    # cellules r="COL2" -> r="COL{r}"
    b=re.sub(r'(<c r="[A-Z]{1,2})2"',lambda m:'%s%d"'%(m.group(1),r),body2p)
    # refs relatives ligne 2 -> ligne r  (col majuscule immediat suivie de 2)
    b=re.sub(r'(\$?[A-Z]{1,2})2(?![0-9])',lambda m:'%s%d'%(m.group(1),r),b)
    tag=re.sub(r'r="2"','r="%d"'%r,open2,count=1)
    return tag+b+"</row>"

newrows="".join(clone(r) for r in range(176,NMAX+1))
# inserer avant </sheetData>
x=re.sub(r'</sheetData>',newrows+"</sheetData>",x,count=1)
# dimension
x=re.sub(r'(<dimension ref="A1:[A-Z]+)175"',r'\g<1>%d"'%NMAX,x,count=1)
sheet13=x

# ================= 2) tableau ALLOC : Allocation2 -> _CALC_ALLOC + $349 =================
CMAP={'C':'A','D':'B','E':'C','F':'D','G':'E','H':'F','I':'G','K':'I',
      'V':'AI','W':'AJ','X':'AK','Y':'AL','Z':'AM','AA':'AN','AC':'AR'}
def mc(c): return CMAP.get(c,c)
x4=zin.read(F4).decode("utf8")
# absorbe aussi les variantes botchees / liens externes : [N]Allocation2 / 22 / 222 !
SN=r'(?:\[\d+\])?Allocation2{1,3}!'
def rrange(m):
    d1,c1,r1,d2,c2,r2=m.groups()
    if c1 not in CMAP and c2 not in CMAP: return m.group(0)
    return "_CALC_ALLOC!%s%s%s:%s%s%s"%(d1,mc(c1),r1,d2,mc(c2),r2)
x4=re.sub(SN+r'(\$?)([A-Z]{1,2})(\$?\d+):(\$?)([A-Z]{1,2})(\$?\d+)',rrange,x4)
x4=re.sub(SN+r'(\$?)([A-Z]{1,2})(\$?\d+)',
          lambda m:("_CALC_ALLOC!%s%s%s"%(m.group(1),mc(m.group(2)),m.group(3))) if m.group(2) in CMAP else m.group(0),x4)
# etendre les plages du tableau vers _CALC_ALLOC!...$349
x4=x4.replace("$175","$349")
sheet4=x4

# ================= workbook : fullCalcOnLoad =================
if "fullCalcOnLoad" not in wb:
    wb=re.sub(r'<calcPr calcId="(\d+)"',r'<calcPr calcId="\1" fullCalcOnLoad="1"',wb,count=1)

mod={F13:sheet13.encode("utf8"),F4:sheet4.encode("utf8"),"xl/workbook.xml":wb.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,mod.get(it.filename,zin.read(it.filename)))
zout.close()
print("OK -> %s"%OUT)
