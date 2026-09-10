#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rend _CALC_ALLOC AUTONOME : il ne lit plus que le masque Allocation + les cles.
   - Masque : 8 colonnes liees a la vue ajoutees (VOL_NEW + 7 POOLS) en AE..AL,
     en-tetes ligne 1 + placeholder ligne 2 (comme les colonnes A..T de la vue,
     que Tagetik injecte au runtime sur toutes les lignes).
   - _CALC_ALLOC : VOL_NEW(J) et les pools (W,X,Y,Z,AA,AB,AO) lisent AE..AL ;
     agregats E_/M_/G_ (L..V) recalcules sur les colonnes propres G/H/I.
     Plus AUCUNE reference a _CALC_MOTEUR/_CALC_PNL/Compta/Socle/cad.
   => Fichier Alloc separe = Allocation + ALLOC + _CALC_ALLOC (rien d'autre).
   Chirurgical : seuls sheet10 + sheet13 + workbook modifies ; briques intactes."""
import zipfile,re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else "TEST3_new.xlsm"
OUT=sys.argv[2] if len(sys.argv)>2 else "TEST3_alloc_autonome.xlsm"
RMAX=175

# ---- colonnes ajoutees au masque (ordre = fin de la vue) ----
NEWH=[("AE","VOL_NEW"),("AF","POOL_VAC"),("AG","POOL_PERM"),("AH","POOL_ODIR"),
      ("AI","POOL_MKT"),("AJ","POOL_STRUCT"),("AK","POOL_HOLDING"),("AL","POOL_FRAIS_MARQUE")]
# ---- _CALC_ALLOC : cible -> colonne source sur le masque ----
POOLMAP={"J":"AE","W":"AF","X":"AG","Y":"AH","Z":"AI","AA":"AJ","AB":"AK","AO":"AL"}

zin=zipfile.ZipFile(SRC)

# ============ 1) MASQUE (sheet10) : en-tetes + placeholders ============
m10=zin.read("xl/worksheets/sheet10.xml").decode("utf8")
# recuperer le style des en-tetes existants (AC1) et d'une cellule vue (I2)
sm=re.search(r'<c r="AC1"([^>]*)>',m10); hdr_attr=sm.group(1) if sm else ""
def add_cells(xml,row,cells):
    # insere les <c> juste avant </row> de la ligne 'row'
    pat=re.compile(r'(<row r="%d"[^>]*>)(.*?)(</row>)'%row,re.S)
    mo=pat.search(xml)
    body=mo.group(2)+ "".join(cells)
    tag=re.sub(r'spans="(\d+):\d+"',r'spans="\1:38"',mo.group(1))  # elargir jusqu'a AL(38)
    return xml[:mo.start()]+tag+body+mo.group(3)+xml[mo.end():]
hdr_cells=['<c r="%s1"%s t="inlineStr"><is><t>%s</t></is></c>'%(c,hdr_attr,name) for c,name in NEWH]
data_cells=['<c r="%s2"/>'%c for c,_ in NEWH]
m10=add_cells(m10,1,hdr_cells)
m10=add_cells(m10,2,data_cells)

# ============ 2) _CALC_ALLOC (sheet13) : rebranchement ============
sheet=zin.read("xl/worksheets/sheet13.xml").decode("utf8")
def agg(srccol,r,by):
    if by=="E": return "SUMIFS($%s$1:$%s$%d,$A$1:$A$%d,$A%d,$B$1:$B$%d,$B%d)"%(srccol,srccol,RMAX,RMAX,r,RMAX,r)
    if by=="M": return "SUMIFS($%s$1:$%s$%d,$A$1:$A$%d,$A%d,$C$1:$C$%d,$C%d)"%(srccol,srccol,RMAX,RMAX,r,RMAX,r)
    return "SUMIFS($%s$1:$%s$%d,$A$1:$A$%d,$A%d)"%(srccol,srccol,RMAX,RMAX,r)
AGGMAP={"L":("G","E"),"M":("H","E"),"N":("I","E"),
        "Q":("G","M"),"R":("H","M"),"S":("I","M"),
        "T":("G","G"),"U":("H","G"),"V":("I","G")}

def newf(col,r):
    if col in POOLMAP:
        return 'IF($A%d="","",Allocation!%s%d)'%(r,POOLMAP[col],r)
    sc,by=AGGMAP[col]
    return 'IF($A%d="","",%s)'%(r,agg(sc,r,by))

COLS=list(POOLMAP)+list(AGGMAP)
nchg=0
for r in range(2,RMAX+1):
    for col in COLS:
        pat=re.compile(r'(<c r="%s%d"[^>]*>)(.*?)</c>'%(col,r),re.S)
        mo=pat.search(sheet)
        if not mo: continue
        rep=mo.group(1)+"<f>"+newf(col,r)+"</f></c>"
        sheet=sheet[:mo.start()]+rep+sheet[mo.end():]
        nchg+=1

# ============ 3) workbook : fullCalcOnLoad ============
wb=zin.read("xl/workbook.xml").decode("utf8")
wb=re.sub(r'<calcPr calcId="(\d+)"/>',r'<calcPr calcId="\1" fullCalcOnLoad="1"/>',wb,count=1)

mod={"xl/worksheets/sheet10.xml":m10.encode("utf8"),
     "xl/worksheets/sheet13.xml":sheet.encode("utf8"),
     "xl/workbook.xml":wb.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=mod.get(it.filename, zin.read(it.filename))
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,data)
zout.close()
print("OK -> %s | _CALC_ALLOC cellules=%d | masque +%d colonnes"%(OUT,nchg,len(NEWH)))
