#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fusionne les styles d'un classeur 'proto' dans un 'design' :
les styles du design gardent leurs index 0..N ; ceux du proto sont ajoutes
decales. Retourne le styles.xml fusionne + une map index_proto -> index_design
pour les cellXfs. Gere fonts/fills/borders/numFmts(custom)/cellXfs."""
import re

def _section(xml, plural, singular):
    m=re.search(r'<%s count="(\d+)"([^>]*)>(.*?)</%s>'%(plural,plural), xml, re.S)
    if not m:
        m2=re.search(r'<%s count="(\d+)"([^>]*)/>'%plural, xml)
        return (int(m2.group(1)) if m2 else 0), [], (m2.span() if m2 else None), True
    inner=m.group(3)
    elts=re.findall(r'<%s\b[^>]*/>|<%s\b[^>]*>.*?</%s>'%(singular,singular,singular), inner, re.S)
    return int(m.group(1)), elts, m.span(), False

class StyleMerger:
    def __init__(self, design_xml, proto_xml):
        self.d=design_xml
        # sections design
        self.nf_d,_ ,_,_=_section(self.d,"fonts","font")
        self.fi_d,_,_,_=_section(self.d,"fills","fill")
        self.bo_d,_,_,_=_section(self.d,"borders","border")
        self.xf_d,_,_,_=_section(self.d,"cellXfs","xf")
        # design custom numFmts ids
        d_nfids=[int(x) for x in re.findall(r'<numFmt numFmtId="(\d+)"',self.d)]
        self.nfmax_d=max(d_nfids) if d_nfids else 163
        # proto sections
        _,self.pfonts,_,_=_section(proto_xml,"fonts","font")
        _,self.pfills,_,_=_section(proto_xml,"fills","fill")
        _,self.pborders,_,_=_section(proto_xml,"borders","border")
        pnf_c,self.pnumfmts,_,_=_section(proto_xml,"numFmts","numFmt")
        _,self.pxfs,_,_=_section(proto_xml,"cellXfs","xf")
        # map proto custom numFmtId -> nouveau id
        self.nfmap={}
        nid=self.nfmax_d+1
        newnf=[]
        for e in self.pnumfmts:
            oid=int(re.search(r'numFmtId="(\d+)"',e).group(1))
            if oid<164:  # builtin, pas de remap
                continue
            self.nfmap[oid]=nid
            newnf.append(re.sub(r'numFmtId="\d+"','numFmtId="%d"'%nid,e,count=1))
            nid+=1
        self.newnf=newnf

    def map_xf(self, s):  # index cellXf proto -> index cellXf fusionne
        return self.xf_d + int(s)

    def _remap_xf(self,e):
        def rep(attr,off):
            nonlocal e
            m=re.search(r'%s="(\d+)"'%attr,e)
            if m: e=e[:m.start()]+'%s="%d"'%(attr,int(m.group(1))+off)+e[m.end():]
        rep("fontId",self.nf_d); rep("fillId",self.fi_d); rep("borderId",self.bo_d)
        m=re.search(r'numFmtId="(\d+)"',e)
        if m:
            oid=int(m.group(1))
            if oid in self.nfmap: e=e[:m.start()]+'numFmtId="%d"'%self.nfmap[oid]+e[m.end():]
        return e

    def merged(self):
        s=self.d
        def grow(plural,singular,elts,base):
            nonlocal s
            if not elts: return
            add="".join(elts)
            m=re.search(r'(<%s count=")(\d+)(")([^>]*)(>)(.*?)(</%s>)'%(plural,plural),s,re.S)
            if m:
                s=s[:m.start()]+m.group(1)+str(base+len(elts))+m.group(3)+m.group(4)+m.group(5)+m.group(6)+add+m.group(7)+s[m.end():]
            else:
                m2=re.search(r'<%s count="(\d+)"([^>]*)/>'%plural,s)
                block='<%s count="%d"%s>%s</%s>'%(plural,base+len(elts),m2.group(2),add,plural)
                s=s[:m2.start()]+block+s[m2.end():]
        # numFmts (ajouter les nouveaux ; creer la section si absente)
        if self.newnf:
            addnf="".join(self.newnf)
            m=re.search(r'(<numFmts count=")(\d+)(")(>)(.*?)(</numFmts>)',s,re.S)
            if m:
                s=s[:m.start()]+m.group(1)+str(int(m.group(2))+len(self.newnf))+m.group(3)+m.group(4)+m.group(5)+addnf+m.group(6)+s[m.end():]
            else:
                s=re.sub(r'(<styleSheet[^>]*>)',r'\1<numFmts count="%d">%s</numFmts>'%(len(self.newnf),addnf),s,count=1)
        grow("fonts","font",self.pfonts,self.nf_d)
        grow("fills","fill",self.pfills,self.fi_d)
        grow("borders","border",self.pborders,self.bo_d)
        grow("cellXfs","xf",[self._remap_xf(e) for e in self.pxfs],self.xf_d)
        return s
