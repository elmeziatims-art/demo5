#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detecteur de cycles au niveau CELLULE (miroir exact du graphe Excel).
- noeuds = cellules FORMULE (les statiques sont des puits, jamais dans un cycle)
- plages/colonnes entieres etendues UNIQUEMENT aux cellules peuplees (pas de
  lignes fantomes) => pas d'OOM
- Tarjan iteratif => lineaire. Rapporte tout SCC>1 ou auto-reference => circulaire.
"""
import zipfile,re,sys
from xml.sax.saxutils import unescape
F=sys.argv[1] if len(sys.argv)>1 else "DESIGN3_OP.xlsm"
z=zipfile.ZipFile(F)
wb=z.read("xl/workbook.xml").decode("utf8")
rels=z.read("xl/_rels/workbook.xml.rels").decode("utf8")
rid2tgt={m.group(1):m.group(2) for m in (re.search(r'Id="(rId\d+)"[^>]*Target="([^"]+)"',r) for r in re.findall(r'<Relationship\b[^>]*/>',rels)) if m}
name2part={}
for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"',wb):
    t=rid2tgt.get(m.group(2),"")
    if t and not t.startswith("/"): t="xl/"+t
    elif t: t=t[1:]
    name2part[m.group(1)]=t
SHEETS=[s for s in name2part if name2part[s]]

def colnum(letters):
    n=0
    for ch in letters.upper(): n=n*26+(ord(ch)-64)
    return n

# 1) parse : formules + index des cellules-formule par (sheet,colnum)
formula_of={}                 # (sheet,col,row) -> formule
fcells_by_sc={}               # (sheet,colnum) -> sorted set rows qui sont des formules
for sh in SHEETS:
    xml=z.read(name2part[sh]).decode("utf8")
    for m in re.finditer(r'<c r="([A-Z]+)(\d+)"[^>]*>(.*?)</c>',xml,re.S):
        col,row,body=m.group(1),int(m.group(2)),m.group(3)
        fm=re.search(r'<f[^>]*>(.*?)</f>',body,re.S)
        if fm and fm.group(1):
            node=(sh,col,row); formula_of[node]=unescape(fm.group(1))
            fcells_by_sc.setdefault((sh,colnum(col)),[]).append(row)
for k in fcells_by_sc: fcells_by_sc[k].sort()

# noms definis -> liste de (sheet,colnum_lo,colnum_hi,row_lo,row_hi)
def parse_ref_target(sheet,body):
    outs=[]
    for part in [body]:
        for seg in [part]:
            for rng in [seg]:
                mm=re.findall(r'\$?([A-Za-z]{1,3})\$?(\d+)?',rng)
    return outs
names={}
for m in re.finditer(r'<definedName name="([^"]+)"[^>]*>([^<]*)</definedName>',wb):
    nm,ref=m.group(1),unescape(m.group(2))
    names[nm]=ref

INF=10**9
def range_to_cells(sheet,rng):
    """retourne liste de cellules-formule existantes couvertes par la ref rng sur sheet"""
    res=[]
    ends=rng.split(":")
    def parse_end(e):
        mm=re.match(r'\$?([A-Za-z]{1,3})\$?(\d*)$',e.strip())
        if not mm: return None
        return colnum(mm.group(1)), (int(mm.group(2)) if mm.group(2) else None)
    a=parse_end(ends[0])
    if a is None: return res
    if len(ends)==1:
        c0,r0=a; c1,r1=a
    else:
        b=parse_end(ends[1])
        if b is None: return res
        c0,r0=a; c1,r1=b
    clo,chi=min(c0,c1),max(c0,c1)
    rlo=1 if (r0 is None or r1 is None) else min(r0,r1)
    rhi=INF if (r0 is None or r1 is None) else max(r0,r1)
    for cc in range(clo,chi+1):
        rows=fcells_by_sc.get((sheet,cc))
        if not rows: continue
        # colonne lettre
        letters=""
        n=cc
        while n: n,rem=divmod(n-1,26); letters=chr(65+rem)+letters
        for r in rows:
            if rlo<=r<=rhi: res.append((sheet,letters,r))
    return res

def resolve_name(sheet,tgt):
    mm=re.match(r"^'?([^'!]+)'?!(.*)$",tgt)
    sh=sheet; body=tgt
    if mm: sh=mm.group(1); body=mm.group(2)
    return range_to_cells(sh,body)

RE_QUAL=re.compile(r"(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_.]*))!(\$?[A-Za-z]{1,3}\$?\d*(?::\$?[A-Za-z]{1,3}\$?\d*)?)")
RE_LOCAL=re.compile(r'(?<![A-Za-z0-9_!:])(\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?|\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3})(?![A-Za-z0-9_(])')

def deps(node):
    sheet,col,row=node
    f=formula_of[node]
    f=re.sub(r'"(?:[^"]|"")*"',' ',f)   # retire chaines
    targets=[]
    # noms definis
    for nm,tgt in names.items():
        if re.search(r'(?<![A-Za-z0-9_])'+re.escape(nm)+r'(?![A-Za-z0-9_])',f):
            targets+=resolve_name(sheet,tgt)
            f=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(nm)+r'(?![A-Za-z0-9_])',' ',f)
    # refs qualifiees Sheet!...
    for m in RE_QUAL.finditer(f):
        sh=m.group(1) or m.group(2); rng=m.group(3)
        if sh in name2part: targets+=range_to_cells(sh,rng)
    f=RE_QUAL.sub(' ',f)
    # refs locales
    for m in RE_LOCAL.finditer(f):
        rng=m.group(1)
        if not re.search(r'\d',rng) and ':' not in rng: continue
        targets+=range_to_cells(sheet,rng)
    return targets

# 2) Tarjan iteratif sur les cellules-formule
nodes=list(formula_of.keys())
idx={}; low={}; onst={}; st=[]; counter=[0]; sccs=[]
sys.setrecursionlimit(10000)
def tarjan(root):
    work=[(root,0,None)]
    it_stack={}
    while work:
        v,pi,dep_iter=work[-1]
        if v not in idx:
            idx[v]=low[v]=counter[0]; counter[0]+=1; st.append(v); onst[v]=True
            it_stack[v]=deps(v)
        recurse=False
        dv=it_stack[v]
        while pi<len(dv):
            w=dv[pi]; pi+=1
            if w not in formula_of:  # cellule statique => puits, ignore
                continue
            if w not in idx:
                work[-1]=(v,pi,None); work.append((w,0,None)); recurse=True; break
            elif onst.get(w):
                low[v]=min(low[v],idx[w])
        if recurse: continue
        work[-1]=(v,pi,None)
        # fin des voisins de v
        if pi>=len(dv):
            if low[v]==idx[v]:
                comp=[]
                while True:
                    w=st.pop(); onst[w]=False; comp.append(w)
                    if w==v: break
                if len(comp)>1 or (comp[0] in deps(comp[0])): sccs.append(comp)
            work.pop()
            if work:
                p=work[-1][0]; low[p]=min(low[p],low[v])
for nd in nodes:
    if nd not in idx: tarjan(nd)

print("Fichier:",F)
print("Cellules-formule:",len(nodes))
real=[c for c in sccs if len(c)>1 or c[0] in deps(c[0])]
if not real:
    print("*** AUCUN cycle cellule => AUCUNE reference circulaire (preuve cell-level). ***")
else:
    print("!!! %d cycle(s) reel(s):"%len(real))
    for comp in real[:20]:
        print("  --- cycle (%d cellules):"%len(comp))
        for nd in comp[:12]:
            print("     %s!%s%d = %s"%(nd[0],nd[1],nd[2],formula_of[nd][:110]))
