#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rebranche _CALC_ALLOC sur l'instantane 2027 (option A) :
   - volumes VOL_EFF/CA/VOL_NEW : bascule 2027 -> _CALC_MOTEUR (version active cad!P1),
     sinon (2026) chemin actuel (vue/Socle) inchange.
   - VOL_CLASS : structurel -> Socle col O, exercice 2026 fige (option A).
   - agregats E_/M_/G_ : somme des colonnes propres G/H/I (coherent 2026 & 2027).
   - charges VAC..SIEGE + FRAIS_MARQUE : bascule 2027 -> _CALC_PNL!P (charge projetee,
     version active), sinon Compta inchangee.
   Chirurgical : on ne reecrit QUE les cellules ciblees de sheet13 + fullCalcOnLoad.
   Toutes les briques Tagetik et les autres feuilles restent byte-identiques."""
import zipfile,re,sys

SRC=sys.argv[1] if len(sys.argv)>1 else "TEST3_new.xlsm"
OUT=sys.argv[2] if len(sys.argv)>2 else "TEST3_alloc2027.xlsm"
RMAX=175

def mot(col,r):
    return ("SUMIFS(_CALC_MOTEUR!$%s$1:$%s$%d,"
            "_CALC_MOTEUR!$A$1:$A$%d,$B%d,"
            "_CALC_MOTEUR!$C$1:$C$%d,$D%d,"
            "_CALC_MOTEUR!$D$1:$D$%d,$E%d,"
            "_CALC_MOTEUR!$E$1:$E$%d,$F%d,"
            "_CALC_MOTEUR!$B$1:$B$%d,cad!$P$1)"
            %(col,col,RMAX,RMAX,r,RMAX,r,RMAX,r,RMAX,r,RMAX))

def pnl(ent,acc,r):   # ent = jeton Excel ("$B%d"%r ou '\"GRP\"')
    return ('SUMIFS(_CALC_PNL!$P$1:$P$1347,'
            '_CALC_PNL!$A$1:$A$1347,%s,'
            '_CALC_PNL!$B$1:$B$1347,"%s",'
            '_CALC_PNL!$C$1:$C$1347,"2027",'
            '_CALC_PNL!$D$1:$D$1347,cad!$P$1)'%(ent,acc))

def socleO(r):        # VOL_CLASS structurel 2026 (col O), par cle fine
    return ("SUMIFS(Socle!$O$1:$O$%d,Socle!$C$1:$C$%d,$B%d,Socle!$D$1:$D$%d,$D%d,"
            "Socle!$E$1:$E$%d,$E%d,Socle!$F$1:$F$%d,$F%d,Socle!$G$1:$G$%d,\"2026\")"
            %(RMAX,RMAX,r,RMAX,r,RMAX,r,RMAX,r,RMAX))

def agg(srccol,r,by):  # somme colonne propre srccol par exercice + (entite/marque/rien)
    if by=="E":   return "SUMIFS($%s$1:$%s$%d,$A$1:$A$%d,$A%d,$B$1:$B$%d,$B%d)"%(srccol,srccol,RMAX,RMAX,r,RMAX,r)
    if by=="M":   return "SUMIFS($%s$1:$%s$%d,$A$1:$A$%d,$A%d,$C$1:$C$%d,$C%d)"%(srccol,srccol,RMAX,RMAX,r,RMAX,r)
    return "SUMIFS($%s$1:$%s$%d,$A$1:$A$%d,$A%d)"%(srccol,srccol,RMAX,RMAX,r)  # G (groupe)

STRUCT_ACC=["6413","645","613","615","616","625","63511"]
HOLD_ACC  =["6414","6226","626","6281","6331","6333"]

GUARD=re.compile(r'^IF\((.+?)="","",(.*)\)$',re.S)

def build(col,r,old_inner,guard):
    """Retourne la nouvelle formule (sans balises) pour la cellule col+r."""
    A='$A%d'%r; Ecell='$B%d'%r
    if col=="G": return 'IF(%s="","",IF(%s="2027",%s,%s))'%(guard,A,mot("AF",r),old_inner)
    if col=="I": return 'IF(%s="","",IF(%s="2027",%s,%s))'%(guard,A,mot("AH",r),old_inner)
    if col=="H": return 'IF(%s="","",%s)'%(guard,socleO(r))
    if col=="J": return 'IF(%s="","",IF(%s="2027",%s,%s))'%(guard,A,mot("AE",r),old_inner)
    if col in ("L","M","N"):
        sc={"L":"G","M":"H","N":"I"}[col]; return 'IF(%s="","",%s)'%(A,agg(sc,r,"E"))
    if col in ("Q","R","S"):
        sc={"Q":"G","R":"H","S":"I"}[col]; return 'IF(%s="","",%s)'%(A,agg(sc,r,"M"))
    if col in ("T","U","V"):
        sc={"T":"G","U":"H","V":"I"}[col]; return 'IF(%s="","",%s)'%(A,agg(sc,r,"G"))
    if col=="W": proj=pnl(Ecell,"621",r)
    elif col=="X": proj=pnl(Ecell,"6411",r)
    elif col=="Y": proj="%s+%s"%(pnl(Ecell,"604",r),pnl(Ecell,"6063",r))
    elif col=="Z": proj=pnl(Ecell,"6231",r)
    elif col=="AA": proj="+".join(pnl(Ecell,a,r) for a in STRUCT_ACC)
    elif col=="AB": proj="+".join(pnl('"GRP"',a,r) for a in HOLD_ACC)
    elif col=="AO": proj=pnl('"GRP"',"6236",r)
    else: raise KeyError(col)
    return 'IF(%s="","",IF(%s="2027",%s,%s))'%(guard,A,proj,old_inner)

COLS=["G","H","I","J","L","M","N","Q","R","S","T","U","V","W","X","Y","Z","AA","AB","AO"]

zin=zipfile.ZipFile(SRC)
sheet=zin.read("xl/worksheets/sheet13.xml").decode("utf8")

nchg=0; missing=[]
for r in range(2,RMAX+1):
    for col in COLS:
        pat=re.compile(r'(<c r="%s%d"[^>]*>)(.*?)</c>'%(col,r),re.S)
        mo=pat.search(sheet)
        if not mo: missing.append(col+str(r)); continue
        body=mo.group(2)
        fm=re.search(r'<f[^>]*>(.*?)</f>',body,re.S)
        old=fm.group(1) if fm else ""
        gm=GUARD.match(old)
        if gm: guard,inner=gm.group(1),gm.group(2)
        else:  guard,inner="$A%d"%r, old   # secours (ne devrait pas arriver)
        newf=build(col,r,inner,guard)
        rep=mo.group(1)+"<f>"+newf+"</f></c>"
        sheet=sheet[:mo.start()]+rep+sheet[mo.end():]
        nchg+=1

# forcer le recalcul (on a supprime les <v> caches des cellules modifiees)
wb=zin.read("xl/workbook.xml").decode("utf8")
wb=re.sub(r'<calcPr calcId="(\d+)"/>',
          r'<calcPr calcId="\1" fullCalcOnLoad="1"/>',wb,count=1)

mod={"xl/worksheets/sheet13.xml":sheet.encode("utf8"),
     "xl/workbook.xml":wb.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=mod.get(it.filename, zin.read(it.filename))
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,data)
zout.close()
print("OK -> %s | cellules modifiees=%d | manquantes=%d"%(OUT,nchg,len(missing)))
if missing[:10]: print("  (manquantes ex.:",missing[:10],")")
