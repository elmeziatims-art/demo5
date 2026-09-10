import zipfile,re
SRC="nav41.xlsx"; OUT="Alloc_2_CALC_fix.xlsx"
CMAP={'C':'A','D':'B','E':'C','F':'D','G':'E','H':'F','I':'G','K':'I',
      'V':'AI','W':'AJ','X':'AK','Y':'AL','Z':'AM','AA':'AN','AC':'AR'}
def mc(c): return CMAP.get(c,c)
zin=zipfile.ZipFile(SRC)
wb=zin.read("xl/workbook.xml").decode("utf8")
rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
name2f={m.group(1):("xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wb) if m.group(2) in id2f}
allocf=name2f["ALLOC"]
x4=zin.read(allocf).decode("utf8")
# 1) plages : Allocation2!$C$1:$C$175  (les 2 colonnes remappees)
def rrange(m):
    g=m.groups() # (d1,c1,r1,d2,c2,r2)
    if g[1] not in CMAP and g[4] not in CMAP: return m.group(0)
    return "_CALC_ALLOC!%s%s%s:%s%s%s"%(g[0],mc(g[1]),g[2],g[3],mc(g[4]),g[5])
x4n,n1=re.subn(r'Allocation2!(\$?)([A-Z]{1,2})(\$?\d+):(\$?)([A-Z]{1,2})(\$?\d+)',rrange,x4)
# 2) refs simples restantes : Allocation2!$C$1
def rsingle(m):
    if m.group(2) not in CMAP: return m.group(0)
    return "_CALC_ALLOC!%s%s%s"%(m.group(1),mc(m.group(2)),m.group(3))
x4n,n2=re.subn(r'Allocation2!(\$?)([A-Z]{1,2})(\$?\d+)',rsingle,x4n)
wb2=re.sub(r'<calcPr calcId="(\d+)"',r'<calcPr calcId="\1" fullCalcOnLoad="1"',wb,count=1) if "fullCalcOnLoad" not in wb else wb
mod={allocf:x4n.encode("utf8"),"xl/workbook.xml":wb2.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,mod.get(it.filename,zin.read(it.filename)))
zout.close()
print("OK -> %s | plages=%d refs-simples=%d | Allocation2 restant=%d"%(OUT,n1,n2,x4n.count("Allocation2!")))
