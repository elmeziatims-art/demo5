#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RAPPORT_ALLOUE_DEPLIABLE.xlsx — le CHOC de l'allocation, dépliable à tous niveaux.
Marque → Campus → Programme → Année → Modalité, avec la cascade AVANT / APRÈS :
   EBITDA propre (la maille avec SES coûts)  −  quote-part siège  =  EBITDA net
Le Δ = ce que le siège coûte à cette maille. Clé de répartition = EFFECTIF (cadrage).
CA réel par classe (socle CRM, foote à la compta). EBITDA net foote au groupe."""
import csv, glob
from collections import defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

INK="152230"; TEAL="0D7A62"; TEALD="0A5A48"; TEALBG="E2EFEB"; CARD2="F5F7F9"
FAINT="7D8B98"; WHITE="FFFFFF"; OCHRE="B3641C"; OCHRED="8A4A12"; OCHREBG="F6E8D8"
RULE="C8D2DA"; SOFT="51606D"
AR="Arial"
def F(sz=10,b=False,c=INK,it=False): return Font(name=AR,size=sz,bold=b,color=c,italic=it)
def fill(c): return PatternFill("solid",fgColor=c)
RGT=Alignment("right",vertical="center")
def LFT(ind=0): return Alignment("left",vertical="center",indent=ind)
thin=Side(style="thin",color=RULE); med=Side(style="medium",color=RULE)
EUR='#,##0;-#,##0;"-"'; PCT='0.0%'; NUM='#,##0'

YEAR=2026
def bloc(a):
    if a[:1]=='7': return 'CA'
    if a in ('604','6063','621','6231'): return 'DIRECT'
    if a in ('6411','6413','6414','645'): return 'PERSO'
    if a in ('613','615','616','6226','6236','625','626','6281'): return 'STRUCT'
    if a in ('6331','6333','63511'): return 'IMPOT'
    if a=='6811': return 'DOTAT'
    return 'X'
BRAND={'MBWAY':'MBway','ISCOM':'Iscom','IPAC':'Ipac','PIGIER':'Pigier','TUNON':'Tunon'}
BR_ORDER=['MBWAY','ISCOM','IPAC','PIGIER','TUNON']
CITY={'LYO':'Lyon','PAR':'Paris','BOR':'Bordeaux','NAN':'Nantes','MTP':'Montpellier',
      'REN':'Rennes','LIL':'Lille','TLS':'Toulouse'}
MODL={'ALT':'Alternance','INIT':'Initial'}
def campus_label(en): p=en.split('_'); return f"{CITY.get(p[1],p[1])}"

# 1) compta : coût EBITDA propre par campus + pool holding (ex dotations)
comp=glob.glob('/home/user/demo5/eduservices/tgk_data/ext_*/AW_002_000004_000001.csv')[0]
camp_cost=defaultdict(float); hold_pool=0.0
with open(comp,encoding='utf-8') as f:
    rd=csv.reader(f,delimiter=';'); next(rd)
    for row in rd:
        en,acc,ex=row[0],row[1],row[2]
        if acc in ('TEC_EBITDA','TEC_PL') or ex!=str(YEAR): continue
        b=bloc(acc)
        if b in ('CA','DOTAT','X'): continue
        amt=float(row[5].replace(',','.'))
        if en=='GRP': hold_pool+=amt
        else: camp_cost[en]+=amt

# 2) CRM : CA + effectif par classe
crm=glob.glob('/home/user/demo5/eduservices/tgk_data/ext_*/AW_002_000002_000001.csv')[0]
cls=defaultdict(lambda:{'ca':0.0,'eff':0.0})
camp_eff=defaultdict(float); eff_group=0.0
with open(crm,encoding='utf-8') as f:
    rd=csv.reader(f,delimiter=';'); next(rd)
    for row in rd:
        if row[6]!=str(YEAR): continue
        en,prog,an,mod=row[2],row[3],row[4],row[5]
        g=lambda i: float(row[i].replace(',','.'))
        eff=g(12); new=g(10); ca=g(15)*eff+g(16)*new
        k=(en,prog,an,mod)
        cls[k]['ca']+=ca; cls[k]['eff']+=eff
        camp_eff[en]+=eff; eff_group+=eff

# 3) coût par classe, séparé campus (avant) / holding (siège)
def node(): return {'ca':0.0,'eff':0.0,'cc':0.0,'ch':0.0}   # cc=coût campus, ch=coût holding
def add(n,ca,eff,cc,ch): n['ca']+=ca; n['eff']+=eff; n['cc']+=cc; n['ch']+=ch
tree=defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:defaultdict(lambda:defaultdict(node)))))
for (en,prog,an,mod),v in cls.items():
    br=en.split('_')[0]; eff=v['eff']
    cc = camp_cost[en]*(eff/camp_eff[en]) if camp_eff[en] else 0
    ch = hold_pool*(eff/eff_group) if eff_group else 0
    add(tree[br][en][prog][an][mod], v['ca'], eff, cc, ch)
def roll(children):
    n=node()
    for c in children.values():
        cc=c if 'ca' in c else roll(c)
        add(n,cc['ca'],cc['eff'],cc['cc'],cc['ch'])
    return n

wb=openpyxl.Workbook(); ws=wb.active; ws.title="Avant-Après allocation"
ws.sheet_view.showGridLines=False
ws.sheet_properties.outlinePr.summaryBelow=False

ws["A1"]="LE CHOC DE L'ALLOCATION — dépliable à tous les niveaux  ·  2026"; ws["A1"].font=F(15,True,INK)
ws["A2"]="EBITDA propre (avec SES coûts) → on charge la quote-part de siège → EBITDA net. Le Δ = ce que le siège coûte à la maille. Clé = effectif."; ws["A2"].font=F(9,False,TEALD)

hr=4
heads=["Maille","CA","Eff.","EBITDA propre","% pr.","− Q-part siège","EBITDA net","% net","Δ (pt)"]
for j,h in enumerate(heads,1):
    c=ws.cell(hr,j,h); c.font=F(9,True,WHITE); c.fill=fill(TEAL)
    c.alignment=LFT() if j==1 else RGT; c.border=Border(bottom=med)

r=hr+1
def wr(lbl,n,lvl,bold=False,color=INK,bg=None,box=None):
    global r
    ca,eff,cc,ch=n['ca'],n['eff'],n['cc'],n['ch']
    propre=ca-cc; net=propre-ch
    mpr=propre/ca if ca else 0; mnet=net/ca if ca else 0
    dpt=(mnet-mpr)*100
    sz=10 if lvl<=1 else 9
    ws.cell(r,1,lbl).font=F(sz,bold,color); ws.cell(r,1).alignment=LFT(lvl)
    ws.cell(r,2,round(ca)).number_format=EUR; ws.cell(r,2).font=F(sz,bold,color)
    ws.cell(r,3,round(eff)).number_format=NUM; ws.cell(r,3).font=F(sz,bold,color)
    ws.cell(r,4,round(propre)).number_format=EUR; ws.cell(r,4).font=F(sz,bold,INK)
    ws.cell(r,5,mpr).number_format=PCT; ws.cell(r,5).font=F(sz,False,FAINT)
    ws.cell(r,6,-round(ch)).number_format=EUR; ws.cell(r,6).font=F(sz,False,OCHRE)
    negm = mnet<0.05
    cnet = OCHRED if negm else TEALD
    ws.cell(r,7,round(net)).number_format=EUR; ws.cell(r,7).font=F(sz,bold or lvl<=1,cnet)
    ws.cell(r,8,mnet).number_format=PCT; ws.cell(r,8).font=F(sz,bold or lvl<=1,cnet)
    ws.cell(r,9,dpt).number_format='-0.0;-0.0'; ws.cell(r,9).font=F(sz,False,OCHRE)
    for j in range(2,10): ws.cell(r,j).alignment=RGT
    if bg:
        for j in range(1,10): ws.cell(r,j).fill=fill(bg)
    if box:
        for j in range(1,10): ws.cell(r,j).border=box
    if lvl>0:
        ws.row_dimensions[r].outline_level=min(lvl,4); ws.row_dimensions[r].hidden=True
    r+=1

grp=node()
for br in BR_ORDER:
    if br not in tree: continue
    nbr=roll(tree[br]); add(grp,nbr['ca'],nbr['eff'],nbr['cc'],nbr['ch'])
    wr(BRAND[br],nbr,0,bold=True,color=TEALD,bg=TEALBG,box=Border(top=thin,bottom=thin))
    for en in sorted(tree[br]):
        wr(campus_label(en),roll(tree[br][en]),1,bold=True,color=INK)
        for prog in sorted(tree[br][en]):
            wr(prog,roll(tree[br][en][prog]),2,color=SOFT)
            for an in sorted(tree[br][en][prog]):
                wr(an,roll(tree[br][en][prog][an]),3,color=FAINT)
                for mod in sorted(tree[br][en][prog][an]):
                    wr(MODL.get(mod,mod),tree[br][en][prog][an][mod],4,color=FAINT)

wr("GROUPE",grp,0,bold=True,color=TEAL,bg=TEALBG,box=Border(top=med,bottom=med))
r+=1
netg=grp['ca']-grp['cc']-grp['ch']
ws.cell(r,1,f"EBITDA net groupe = {round(netg):,} € (foote compta). EBITDA propre = avant quote-part siège ; le siège pèse {round(grp['ch']):,} € réparti à l'effectif.".replace(',',' ')).font=F(8,False,FAINT,True)
ws.cell(r+1,1,"Lecture : Δ (pt) = combien de points de marge le siège retire à la maille. Rouge = marge nette < 5 % (la maille ne couvre plus son coût chargé).").font=F(8,True,OCHRE,True)

ws.column_dimensions['A'].width=32
for col,w in zip("BCDEFGHI",[13,7,13,7,13,13,7,8]): ws.column_dimensions[col].width=w
ws.freeze_panes="A5"

out="/home/user/demo5/eduservices/tagetik/RAPPORT_ALLOUE_DEPLIABLE.xlsx"
wb.save(out); print("SAVED",out,"| net groupe =",round(netg),"| propre groupe =",round(grp['ca']-grp['cc']),"| siège =",round(grp['ch']))
