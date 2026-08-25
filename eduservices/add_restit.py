#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bloc 'Charges indirectes allouees' sur ALLOC (E5:M10) : montant groupe (live,
ligne 95) + % cout complet + explication. Chirurgical, rien deplace, sans fusion."""
from tgk_surgery import Book
from tgk_style import StyleBank
b=Book("TEST3_fix.xlsm")
sb=StyleBank(b.styles_xml())
NAVY="1F3864"; GREY="3B3B3B"; HDRBG="E8F0FB"; HTX="15406E"
NF_EUR=sb.numfmt('#,##0" €";-#,##0" €";"–"'); NF_PCT=sb.numfmt('0.0%;-0.0%;"–"')
XTIT=sb.xf(font=sb.font(11,True,False,NAVY),fill=sb.fill(HDRBG),halign="centerContinuous",valign="center")
XTITf=sb.xf(fill=sb.fill(HDRBG),halign="centerContinuous")
XHDR=sb.xf(font=sb.font(9,True,False,HTX),fill=sb.fill(HDRBG),halign="center",valign="center",wrap=True)
XHDRl=sb.xf(font=sb.font(9,True,False,HTX),fill=sb.fill(HDRBG),halign="centerContinuous",valign="center",wrap=True)
XNAME=sb.xf(font=sb.font(11,True,False,NAVY),halign="left",valign="center")
XEUR=sb.xf(font=sb.font(11,False,False,NAVY),numfmt=NF_EUR,halign="right",valign="center")
XPCT=sb.xf(font=sb.font(11,False,False,GREY),numfmt=NF_PCT,halign="right",valign="center")
XEXP=sb.xf(font=sb.font(10,False,True,GREY),halign="left",valign="center")
al=b.sheet("ALLOC")
def T(r,t,s): al.set_text(r,t,s=s)
def F(r,f,s): al.set_formula(r,f,s=s)
# titre (bande E5:M5)
T("E5","Charges indirectes allouées au coût complet",XTIT)
for c in "FGHIJKLM": al.put_cell(c+"5",' s="%d"'%XTITf,None)
# entetes (ligne 6, retour a la ligne) + bande H6:M6 pour l'explication
T("E6","Charge",XHDR); T("F6","Montant groupe",XHDR); T("G6","% coût complet",XHDR)
T("H6","Comment elle est allouée",XHDRl)
for c in "IJKLM": al.put_cell(c+"6",' s="%d"'%XHDRl,None)
al.rowattrs[6]=' ht="30" customHeight="1"'; al.rows.setdefault(6,{})
# 4 charges (7-10) : total ligne 95 + cle cout complet ; explication en debordement (I-M vides)
CH=[("ODIR","G","Coûts directs hors enseignement (pédagogie, vie étudiante, frais spécifiques)."),
    ("STRUCT","H","Structure du campus (loyers, IT, admin locale), répartie sur ses classes."),
    ("Frais marque","I","Publicité de la marque, répartie sur les campus au prorata de l'effectif."),
    ("Holding","J","Siège & fonctions centrales, allouées aux marques au prorata du CA.")]
for i,(name,col,expl) in enumerate(CH):
    r=7+i
    T("E%d"%r,name,XNAME); F("F%d"%r,"%s95"%col,XEUR)
    F("G%d"%r,"IFERROR(%s95/$K$95,0)"%col,XPCT); T("H%d"%r,expl,XEXP)
b.set_styles(sb.render())
b.save("TEST3_restit.xlsm")
print("OK -> TEST3_restit.xlsm")
