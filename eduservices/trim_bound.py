#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perf Tagetik : (1) borne les refs colonne-entiere a l'etendue runtime reelle,
(2) rogne les feuilles moteur calculees par nous a leur cap, en corrigeant les
refs des formules PARTAGEES + la dimension. Chirurgical : briques intactes."""
import zipfile,re,sys
SRC=sys.argv[1] if len(sys.argv)>1 else "DESIGN_REF_v3.xlsm"
OUT=sys.argv[2] if len(sys.argv)>2 else "DESIGN_REF_v4.xlsm"
# caps runtime (derniere ligne a garder, en-tete comprise)
REFCAP={"Socle":175,"Campagne":15,"Compta":675,"Moteur":175,"Allocation":175,
        "PNL":1347,"_CALC_MOTEUR":175,"_CALC_PNL":1347,"_CALC_ALLOC":175}
TRIMCAP={"_CALC_MOTEUR":175,"_CALC_PNL":1347,"_CALC_ALLOC":175,
         "Moteur":175,"PNL":1347,"Allocation":175}
zin=zipfile.ZipFile(SRC)
wbxml=zin.read("xl/workbook.xml").decode("utf8")
rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
sheets=[(m.group(1),"xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wbxml) if m.group(2) in id2f]

# --- bornage refs colonne-entiere (prefixe feuille) ---
def bound_prefixed(txt):
    def rep(m):
        sh,d1,c1,d2,c2=m.group(1),m.group(2),m.group(3),m.group(4),m.group(5)
        cap=REFCAP.get(sh)
        if not cap: return m.group(0)
        return "%s!$%s$1:$%s$%d"%(sh,c1,c2,cap)
    return re.sub(r'([A-Za-z_][A-Za-z0-9_]*)!(\$?)([A-Z]{1,3}):(\$?)([A-Z]{1,3})(?![0-9])',rep,txt)
# --- bornage refs colonne sans prefixe (feuille courante) ---
def bound_noprefix(txt,cap):
    if not cap: return txt
    return re.sub(r'(?<![A-Za-z0-9_!$])(\$?)([A-Z]{1,3}):(\$?)([A-Z]{1,3})(?![0-9])',
                  lambda m:"$%s$1:$%s$%d"%(m.group(2),m.group(4),cap),txt)
FCELL=re.compile(r'(<f\b[^>]*>)([^<]*)(</f>)')
def bound_formulas(xml,curcap):
    def rep(m):
        t=bound_prefixed(m.group(2)); t=bound_noprefix(t,curcap)
        return m.group(1)+t+m.group(3)
    return FCELL.sub(rep,xml)

# --- rognage : refs partages, suppression lignes, dimension ---
def shrink_shared_refs(xml,cap):
    def rep(m):
        pre,r1,n1,r2,n2,post=m.group(1),m.group(2),int(m.group(3)),m.group(4),int(m.group(5)),m.group(6)
        if n1<=cap and n2>cap: n2=cap
        return "%s%s%d:%s%d%s"%(pre,r1,n1,r2,n2,post)
    return re.sub(r'(<f\b[^>]*\bref=")([A-Z]+)(\d+):([A-Z]+)(\d+)("[^>]*>)',rep,xml)
def delete_rows(xml,cap):
    def rep(m):
        return "" if int(m.group(1))>cap else m.group(0)
    return re.sub(r'<row r="(\d+)"(?:[^>]*?/>|[^>]*?>.*?</row>)',rep,xml,flags=re.S)
def fix_dim(xml,cap):
    return re.sub(r'(<dimension ref="[A-Z]+1:[A-Z]+)\d+("/>)',lambda m:m.group(1)+str(cap)+m.group(2),xml,count=1)

mod={}
for name,path in sheets:
    x=zin.read(path).decode("utf8")
    x=bound_formulas(x, REFCAP.get(name))          # bornage (toutes feuilles)
    if name in TRIMCAP:                             # rognage (6 feuilles)
        c=TRIMCAP[name]
        x=shrink_shared_refs(x,c); x=delete_rows(x,c); x=fix_dim(x,c)
    mod[path]=x.encode("utf8")

zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data=mod.get(it.filename, zin.read(it.filename))
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,data)
zout.close()
print("OK ->",OUT)
