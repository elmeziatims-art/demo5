#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detection SOUND de references circulaires via projection (feuille,colonne).
Tout cycle cellule reel se projette en cycle colonne => si le graphe colonne est
acyclique, il n'y a AUCUN circulaire. Les SCC residuels sont inspectes (faux
positifs par decalage de lignes, ex: K33 lit K15:K28)."""
import zipfile,re
from xml.sax.saxutils import unescape

F="DESIGN3_OP.xlsm"
z=zipfile.ZipFile(F)
wb=z.read("xl/workbook.xml").decode("utf8")
rels=z.read("xl/_rels/workbook.xml.rels").decode("utf8")
rid2tgt={}
for rel in re.findall(r'<Relationship\b[^>]*/>',rels):
    rid=re.search(r'Id="(rId\d+)"',rel); tgt=re.search(r'Target="([^"]+)"',rel)
    if rid and tgt:
        t=rid2tgt[rid.group(1)]=tgt.group(1)
name2part={}
for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"',wb):
    nm,rid=m.group(1),m.group(2)
    t=rid2tgt.get(rid,"")
    if t and not t.startswith("/"): t="xl/"+t
    elif t: t=t[1:]
    name2part[nm]=t
SHEETS=[s for s in name2part if name2part[s]]

# noms definis -> (sheet,col) set
names={}
for m in re.finditer(r'<definedName name="([^"]+)"[^>]*>([^<]*)</definedName>',wb):
    nm,ref=m.group(1),unescape(m.group(2))
    names[nm]=ref

def col_letters(a1_range):
    """extrait les lettres de colonne d'une reference (cellule/plage/colonne entiere)"""
    cols=set()
    for part in a1_range.split(":"):
        mm=re.match(r'\$?([A-Za-z]{1,3})',part.strip())
        if mm: cols.add(mm.group(1).upper())
    return cols

def refs_of(formula,cur_sheet):
    """retourne un set de noeuds (sheet,col) references par la formule"""
    out=set()
    f=formula
    # retire les chaines litterales
    f=re.sub(r'"(?:[^"]|"")*"',' ',f)
    # remplace noms definis par leur cible
    for nm,tgt in names.items():
        if re.search(r'(?<![A-Za-z0-9_])'+re.escape(nm)+r'(?![A-Za-z0-9_])',f):
            f2=tgt
            sh=cur_sheet
            mm=re.match(r"^'?([^'!]+)'?!(.*)$",f2)
            if mm: sh=mm.group(1); body=mm.group(2)
            else: body=f2
            for c in col_letters(body): out.add((sh,c))
    # retire les tokens de noms pour ne pas les reparser
    for nm in names: f=re.sub(r'(?<![A-Za-z0-9_])'+re.escape(nm)+r'(?![A-Za-z0-9_])',' ',f)
    # refs avec feuille : Sheet!... ou 'Sheet Name'!...
    for m in re.finditer(r"(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_]*))!(\$?[A-Za-z]{1,3}\$?\d*(?::\$?[A-Za-z]{1,3}\$?\d*)?)",f):
        sh=m.group(1) or m.group(2); rng=m.group(3)
        for c in col_letters(rng): out.add((sh,c))
    # retire les refs qualifiees deja traitees
    f=re.sub(r"(?:'[^']+'|[A-Za-z_][A-Za-z0-9_]*)!\$?[A-Za-z]{1,3}\$?\d*(?::\$?[A-Za-z]{1,3}\$?\d*)?",' ',f)
    # refs locales (meme feuille) : A1, A1:B2, A:A
    for m in re.finditer(r'(?<![A-Za-z0-9_!])(\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?|\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3})(?![A-Za-z0-9_(])',f):
        rng=m.group(1)
        # filtre les faux positifs type "LOG","IF" deja enleves ; garde A1 etc.
        if not re.search(r'\d',rng) and ':' not in rng: continue
        for c in col_letters(rng): out.add((cur_sheet,c))
    return out

# construit le graphe colonne + collecte formules par noeud (pour inspection)
edges={}   # (sheet,col) -> set (sheet,col)
node_formulas={}  # (sheet,col) -> list (ref, formula)
FUNCS=set("IF IFERROR SUM SUMIFS SUMPRODUCT INDEX MATCH AND OR NOT ROUND ABS MAX MIN AVERAGE COUNT COUNTIFS TEXT VALUE LEFT RIGHT MID LEN CONCATENATE".split())
for sh in SHEETS:
    xml=z.read(name2part[sh]).decode("utf8")
    for m in re.finditer(r'<c r="([A-Z]+)(\d+)"[^>]*>(.*?)</c>',xml,re.S):
        col,row,body=m.group(1),m.group(2),m.group(3)
        fm=re.search(r'<f[^>]*>(.*?)</f>',body,re.S)
        if not fm: continue
        formula=unescape(fm.group(1))
        src=(sh,col)
        node_formulas.setdefault(src,[]).append((col+row,formula))
        tgt=refs_of(formula,sh)
        # ne garde que les noeuds qui existent comme feuille
        tgt={(s,c) for (s,c) in tgt if s in name2part}
        edges.setdefault(src,set()).update(tgt)

# Tarjan SCC
import sys
sys.setrecursionlimit(100000)
index={}; low={}; onstack={}; stack=[]; idx=[0]; sccs=[]
def strongconnect(v):
    index[v]=idx[0]; low[v]=idx[0]; idx[0]+=1; stack.append(v); onstack[v]=True
    for w in edges.get(v,()):
        if w not in index:
            strongconnect(w); low[v]=min(low[v],low[w])
        elif onstack.get(w):
            low[v]=min(low[v],index[w])
    if low[v]==index[v]:
        comp=[]
        while True:
            w=stack.pop(); onstack[w]=False; comp.append(w)
            if w==v: break
        sccs.append(comp)
allnodes=set(edges)|{w for s in edges.values() for w in s}
for v in allnodes:
    if v not in index: strongconnect(v)

# rapporte SCC non triviaux (taille>1) ou self-loops
print("Noeuds colonne:",len(allnodes),"| aretes:",sum(len(s) for s in edges.values()))
problem=[]
for comp in sccs:
    if len(comp)>1:
        problem.append(comp)
    elif len(comp)==1 and comp[0] in edges.get(comp[0],()):
        problem.append(comp)  # self-loop
if not problem:
    print("\n*** AUCUN cycle au niveau colonne => AUCUN circulaire (preuve). ***")
else:
    print("\n!!! %d SCC/self-loop a inspecter :"%len(problem))
    for comp in problem:
        print("\n--- SCC:",comp)
        for node in comp:
            for ref,f in node_formulas.get(node,[])[:3]:
                # montre seulement les formules qui referencent un autre membre du SCC
                tg=refs_of(f,node[0])
                if any((s,c) in comp for (s,c) in tg):
                    print("   %s!%s = %s"%(node[0],ref,f[:150]))
                    break
