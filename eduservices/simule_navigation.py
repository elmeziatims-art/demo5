#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""simule_navigation.py — remplit le template comme le ferait une navigation.

Ecrit dans COCKPIT_DESIGN.xlsm ce que Tagetik y mettrait au lancement : la
hierarchie dans le tableau, les trois blocs de la zone technique, les filtres.
Les colonnes calculees recoivent la MEME formule que le template, recopiee
ligne a ligne, comme Tagetik le fait.

Sert a voir les defauts avant le client, faute de pouvoir ouvrir Excel ici.
"""
import csv, sys, openpyxl
from collections import defaultdict
from openpyxl.utils import get_column_letter as gl
from socle_reel import construire

NOEUD = sys.argv[1] if len(sys.argv)>1 else "ALL"
OUT   = sys.argv[2] if len(sys.argv)>2 else "COCKPIT_SIMU_ALL.xlsm"
ORDRE = ["Ipac Bachelor Factory","ISCOM","MBway","Pigier","Tunon"]
CODE  = {"Ipac Bachelor Factory":"IPAC","ISCOM":"ISCOM","MBway":"MBWAY","Pigier":"PIGIER","Tunon":"TUNON"}
LIB   = {"IPAC_MTP":"Ipac Bachelor Factory Montpellier","IPAC_NAN":"Ipac Bachelor Factory Nantes",
         "IPAC_REN":"Ipac Bachelor Factory Rennes","ISCOM_LIL":"ISCOM Lille","ISCOM_PAR":"ISCOM Paris",
         "ISCOM_TLS":"ISCOM Toulouse","MBWAY_BOR":"MBway Bordeaux","MBWAY_LYO":"MBway Lyon",
         "MBWAY_NAN":"MBway Nantes","MBWAY_PAR":"MBway Paris","PIGIER_BOR":"Pigier Bordeaux",
         "PIGIER_LYO":"Pigier Lyon","TUNON_LYO":"Tunon Lyon","TUNON_PAR":"Tunon Paris"}
N,P = 2026,2025
C = construire()
if NOEUD!="ALL": C=[c for c in C if CODE[c["marque"]]==NOEUD]
acq=defaultdict(lambda: defaultdict(float))
for r in csv.DictReader(open("data/socle_crm.csv",encoding="utf-8-sig"),delimiter=";"):
    acq[r["ENTITY"]][int(r["EXERCICE"])]+=float(r["DEPENSE_ACQ"].replace(",","."))

wb=openpyxl.load_workbook("COCKPIT_DESIGN.xlsm",keep_vba=True); ws=wb["2"]

# ------------------------------------------------------------ les filtres
ws.cell(5,4,"Forecast 2026"); ws.cell(5,9,"V_FINAL")
ws.cell(5,12,"EDUSERVICES" if NOEUD=="ALL" else NOEUD)

# ------------------------------------------------------------ le tableau
# D CA · F EBITDA · H Part · K Inscrits · N EFF · O PLACES · P EFF_ALT
# Q EBITDA_N1 · R CA_N1 · S SPEND · T SPEND_N1 · V PLACES_N1 · W INSCR_N1 · X EFF_N1
FEUILLE=lambda c: dict(D=c["ca"][N], F=c["eb"][N], K=c["inscrits"][N],
    N=c["eff"][N], O=c["places"][N], P=c["mix_alt"][N]*c["eff"][N],
    Q=c["eb"][P], R=c["ca"][P], S=acq[c["ent"]][N], T=acq[c["ent"]][P],
    V=c["places"][P], W=c["inscrits"][P], X=c["eff"][P])
EB_TOT=sum(x["eb"][N] for x in construire())
def calc(r):    # les colonnes que le template calcule, recopiees telles quelles
    return {"E":'=IFERROR((D{0}-R{0})/R{0},"")'.format(r), "G":'=IFERROR((F{0}-Q{0})/Q{0},"")'.format(r),
            "I":'=IFERROR(F{0}/D{0},"")'.format(r),        "J":'=IFERROR((I{0}-U{0})*100,"")'.format(r),
            "L":'=IFERROR(N{0}/O{0},"")'.format(r),        "M":'=IFERROR(P{0}/N{0},"")'.format(r),
            "U":'=IFERROR(Q{0}/R{0},"")'.format(r),        "Y":'=IFERROR((K{0}-W{0})/W{0},"")'.format(r)}
SOMMABLES="DFHKNOPQRSTVWX"
lignes=[]; r=38
racine=r; lignes.append((r,2,"EDUSERVICES",None)); r+=1
for m in ORDRE:
    g=[c for c in C if c["marque"]==m]
    if not g: continue
    tete=r; lignes.append((r,3,m,None)); r+=1
    for c in sorted(g,key=lambda x:LIB[x["ent"]]):
        lignes.append((r,4,LIB[c["ent"]],c)); r+=1
    lignes[[i for i,l in enumerate(lignes) if l[0]==tete][0]]=(tete,3,m,(tete+1,r-1))
lignes[0]=(racine,2,"EDUSERVICES",(racine+1,r-1))
for ligne,niv,lib,src in lignes:
    ws.cell(ligne,2,niv); ws.cell(ligne,3,lib)
    if niv==4:
        v=FEUILLE(src); v["H"]=src["eb"][N]/EB_TOT
        for k,x in v.items(): ws.cell(ligne,openpyxl.utils.column_index_from_string(k),x)
    else:
        a,b=src
        enfants=[l for l in lignes if l[0]>=a and l[0]<=b and l[1]==niv+1]
        for k in SOMMABLES:
            ws.cell(ligne,openpyxl.utils.column_index_from_string(k),
                    "=SUBTOTAL(9,{0}{1}:{0}{2})".format(k,a,b))
    for k,f in calc(ligne).items():
        ws.cell(ligne,openpyxl.utils.column_index_from_string(k),f)
DERNIERE=r-1
for rr in range(DERNIERE+1,58):          # Tagetik nettoie ce qu'il ne remplit pas
    for c in range(2,26): ws.cell(rr,c).value=None

# ------------------------------------------------- la zone technique
TOUS=construire()
def eff_pont(sel):
    p_=n_=v=pr=co=0
    for c in sel:
        ep,en=c["eff"][P],c["eff"][N]
        cap,can=c["ca"][P]/ep,c["ca"][N]/en
        cvp,cvn=c["cvar"][P]/ep,c["cvar"][N]/en
        v+=(en-ep)*(cap-cvp); pr+=(can-cap)*en
        co+=-(cvn-cvp)*en-(c["cdir"][N]-c["cdir"][P])-(c["csiege"][N]-c["csiege"][P])
        p_+=c["eb"][P]; n_+=c["eb"][N]
    return p_,n_,v,pr,co
p_,n_,v,pr,co = eff_pont(C)
PONT=[(1,"EBITDA 2025",0,round(p_),0,0),
      (2,"Activité", round(p_ if v>0 else p_+v),0,round(max(v,0)),round(max(-v,0))),
      (3,"Prix / mix",round(p_+v+pr if pr<0 else p_+v),0,round(max(pr,0)),round(max(-pr,0))),
      (4,"Coûts",     round(n_ if co<0 else p_+v+pr),0,round(max(co,0)),round(max(-co,0))),
      (5,"EBITDA 2026",0,round(n_),0,0)]
for i,ligne in enumerate(PONT,7):
    for j,val in enumerate(ligne,28): ws.cell(i,j,val)

# le bloc de marge bascule d'axe : marques si le perimetre en couvre plusieurs,
# campus sinon. C'est ce qui fait varier son nombre de lignes.
plusieurs = len({c["marque"] for c in C})>1
grp = defaultdict(list)
for c in C: grp[c["marque"] if plusieurs else c["ent"]].append(c)
MARGE=[]
for k in sorted(grp, key=lambda x:(ORDRE.index(x) if plusieurs else x)):
    g=grp[k]; f=lambda a,e: sum(x[a][e] for x in g)
    # ordre de la query reordonnee : libelle, trois marges, ecart, puis detail
    MARGE.append((k if plusieurs else LIB[k],
                  round(f("eb",2024)/f("ca",2024),4), round(f("eb",2025)/f("ca",2025),4),
                  round(f("eb",N)/f("ca",N),4),
                  round(100*(f("eb",N)/f("ca",N)-f("eb",2024)/f("ca",2024)),2),
                  "MARQUE" if plusieurs else "CAMPUS", CODE[k] if plusieurs else k,
                  round(f("ca",2024)),round(f("eb",2024)),round(f("ca",2025)),round(f("eb",2025)),
                  round(f("ca",N)),round(f("eb",N))))
for i,ligne in enumerate(MARGE,7):
    for j,val in enumerate(ligne,35): ws.cell(i,j,val)
for i in range(7+len(MARGE),12):          # Tagetik nettoie le reste du bloc
    for j in range(35,48): ws.cell(i,j).value=None

EX=[2024,2025,N]
dep={e:sum(acq[c["ent"]][e] for c in C) for e in EX}
ins={e:sum(c["inscrits"][e] for c in C) for e in EX}
for i,e in enumerate(EX,7):
    # ordre de la query reordonnee : exercice, deux indices, puis detail
    for j,val in enumerate((str(e),
                            round(100*dep[e]/dep[2024],1),round(100*ins[e]/ins[2024],1),
                            round(dep[e]/ins[e]),
                            round(100*dep[e]/dep[2024]-100*ins[e]/ins[2024],1),
                            round(dep[e]),round(ins[e])),52):
        ws.cell(i,j,val)
for i in range(7+len(EX),12):
    for j in range(52,59): ws.cell(i,j).value=None

wb.save(OUT)
print("%s — noeud %s : %d lignes de tableau (38 a %d), pont 5, marge %d, tension %d"
      %(OUT,NOEUD,DERNIERE-37,DERNIERE,len(MARGE),len(EX)))
