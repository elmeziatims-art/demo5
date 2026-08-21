#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Moteur de chirurgie OOXML pour Design Tagetik.
Ne regenere QUE <sheetData> + l'attribut dimension d'une feuille ; tout le reste
du XML (dont <customProperties> Tagetik) reste byte-a-byte. Les autres parties du
zip (customProperty*.bin, customXml, webextensions, _TGK_HIDDEN) sont recopiees
telles quelles. Chaines en inline-string -> sharedStrings.xml jamais touche."""
import zipfile,re
from xml.sax.saxutils import escape

def col2num(col):
    n=0
    for ch in col: n=n*26+(ord(ch)-64)
    return n
def num2col(n):
    s=""
    while n>0: n,r=divmod(n-1,26); s=chr(65+r)+s
    return s
def split_ref(ref):
    m=re.match(r'([A-Z]+)(\d+)',ref); return m.group(1),int(m.group(2))

class Sheet:
    def __init__(self,xml):
        self.xml=xml
        m=re.search(r'<sheetData>(.*?)</sheetData>',xml,re.S)
        if m is None:
            m=re.search(r'<sheetData/>',xml); self.sd_start,self.sd_end,body=m.start(),m.end(),""
        else:
            self.sd_start,self.sd_end,body=m.start(),m.end(),m.group(1)
        # parse rows -> {rownum: {colnum: full <c ...>...</c> or <c .../>}}
        self.rows={}
        self.rowattrs={}
        for rm in re.finditer(r'<row r="(\d+)"([^>]*?)(?:/>|>(.*?)</row>)',body,re.S):
            rn=int(rm.group(1)); self.rowattrs[rn]=rm.group(2)
            inner=rm.group(3) if rm.group(3) is not None else ""
            cells={}
            for cm in re.finditer(r'<c r="([A-Z]+)(\d+)"([^>]*?)(?:/>|>(.*?)</c>)',inner,re.S):
                col=cm.group(1); attrs=cm.group(3); content=cm.group(4)
                cells[col2num(col)]=(attrs,content)
            self.rows[rn]=cells
    def _set(self,ref,attrs,content):
        col,rn=split_ref(ref); cn=col2num(col)
        self.rows.setdefault(rn,{})[cn]=(attrs,content)
        self.rowattrs.setdefault(rn,"")
    def set_formula(self,ref,formula,s=None):
        a=' s="%d"'%s if s is not None else ''
        self._set(ref,a,'<f>%s</f>'%escape(formula))
    def set_number(self,ref,val,s=None):
        a=' s="%d"'%s if s is not None else ''
        self._set(ref,a,'<v>%s</v>'%val)
    def set_text(self,ref,text,s=None):
        a=(' s="%d"'%s if s is not None else '')+' t="inlineStr"'
        self._set(ref,a,'<is><t xml:space="preserve">%s</t></is>'%escape(str(text)))
    def render(self):
        # rebuild sheetData
        parts=[]
        maxc=1;maxr=1;minc=16384;minr=1048576
        for rn in sorted(self.rows):
            cells=self.rows[rn]
            if not cells and not self.rowattrs.get(rn): continue
            cs=[]
            for cn in sorted(cells):
                attrs,content=cells[cn]; ref=num2col(cn)+str(rn)
                if content is None or content=="":
                    cs.append('<c r="%s"%s/>'%(ref,attrs))
                else:
                    cs.append('<c r="%s"%s>%s</c>'%(ref,attrs,content))
                maxc=max(maxc,cn);minc=min(minc,cn)
            ra=self.rowattrs.get(rn,"")
            parts.append('<row r="%d"%s>%s</row>'%(rn,ra,"".join(cs)))
            maxr=max(maxr,rn);minr=min(minr,rn)
        sd="<sheetData>"+"".join(parts)+"</sheetData>"
        xml=self.xml[:self.sd_start]+sd+self.xml[self.sd_end:]
        # update dimension
        if self.rows:
            newdim="%s%d:%s%d"%(num2col(minc),minr,num2col(maxc),maxr)
            xml=re.sub(r'<dimension ref="[^"]+"/>','<dimension ref="%s"/>'%newdim,xml,count=1)
        return xml

class Book:
    def __init__(self,src):
        self.src=src; self.zin=zipfile.ZipFile(src)
        self.wbxml=self.zin.read("xl/workbook.xml").decode("utf8")
        rels=self.zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
        ridmap=dict(re.findall(r'Id="(rId\d+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels))
        self.name2xml={n:ridmap[r] for n,r in re.findall(r'<sheet name="([^"]+)"[^>]*r:id="(rId\d+)"',self.wbxml)}
        self.mods={}
    def sheet(self,name):
        xf="xl/worksheets/"+self.name2xml[name]
        if xf not in self.mods: self.mods[xf]=Sheet(self.zin.read(xf).decode("utf8"))
        return self.mods[xf]
    def add_names(self,defs):  # dict name->refers (A1 style, sheet-qualified)
        block="".join('<definedName name="%s">%s</definedName>'%(n,escape(r)) for n,r in defs.items())
        if "<definedNames>" in self.wbxml:
            self.wbxml=re.sub(r'</definedNames>',block+'</definedNames>',self.wbxml,count=1)
        else:
            # inserer apres </sheets>
            self.wbxml=re.sub(r'(</sheets>)',r'\1<definedNames>'+block+'</definedNames>',self.wbxml,count=1)
    def set_fullcalc(self):
        if "<calcPr" in self.wbxml:
            self.wbxml=re.sub(r'<calcPr[^>]*/>','<calcPr calcId="0" fullCalcOnLoad="1"/>',self.wbxml,count=1)
        else:
            self.wbxml=re.sub(r'(</workbook>)',r'<calcPr calcId="0" fullCalcOnLoad="1"/>\1',self.wbxml,count=1)
    def save(self,out):
        rendered={xf:sh.render() for xf,sh in self.mods.items()}
        rendered["xl/workbook.xml"]=self.wbxml
        with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as zout:
            for zi in self.zin.infolist():
                if zi.filename in rendered: data=rendered[zi.filename].encode("utf8")
                else: data=self.zin.read(zi.filename)
                ni=zipfile.ZipInfo(zi.filename,date_time=zi.date_time)
                ni.compress_type=zi.compress_type; ni.create_system=zi.create_system
                ni.create_version=zi.create_version; ni.extract_version=zi.extract_version
                ni.external_attr=zi.external_attr; ni.internal_attr=zi.internal_attr; ni.flag_bits=zi.flag_bits
                zout.writestr(ni,data)

if __name__=="__main__":
    # TEST mecanisme: injecter une formule triviale dans cad, prouver tagetik intact
    b=Book("DESIGN.xlsm")
    b.sheet("cad").set_formula("H1","1+1")
    b.add_names({"TEST_NAME":"cad!$C$9"})
    b.set_fullcalc()
    b.save("_test.xlsm")
    import xml.dom.minidom as M
    a=zipfile.ZipFile("DESIGN.xlsm"); z=zipfile.ZipFile("_test.xlsm")
    same=sum(1 for n in a.namelist() if a.read(n)==z.read(n))
    mod=[n for n in a.namelist() if a.read(n)!=z.read(n)]
    print("identiques:",same,"/",len(a.namelist())," modifies:",mod)
    tgk=[n for n in a.namelist() if "customProperty" in n or n.startswith("customXml") or n.startswith("xl/webextensions") or "sheet1.xml" in n]
    print("TAGETIK+_TGK_HIDDEN intacts:",all(a.read(n)==z.read(n) for n in tgk),"(%d parts)"%len(tgk))
    for f in ["xl/worksheets/sheet2.xml","xl/workbook.xml"]: M.parseString(z.read(f))
    print("XML bien formes: OK  | testzip:",z.testzip())
    # customProperties element toujours dans cad ?
    print("cad garde <customProperties>:", b"<customProperties" in z.read("xl/worksheets/sheet2.xml"))
