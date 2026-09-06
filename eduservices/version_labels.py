import zipfile,re
SRC="Alloc_2_CALC_v4.xlsx"; OUT="Alloc_2_CALC_v5.xlsx"
zin=zipfile.ZipFile(SRC)
wb=zin.read("xl/workbook.xml").decode("utf8");rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
n2f={m.group(1):("xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wb) if m.group(2) in id2f}
F4=n2f["ALLOC"]; x=zin.read(F4).decode("utf8")

# 1) C12 : valeur "V01" -> "Cadrage" + ajout D12 (code) juste apres
x=x.replace(
 '<c r="C12" s="129" t="inlineStr"><is><t>V01</t></is></c>',
 '<c r="C12" s="129" t="inlineStr"><is><t>Cadrage</t></is></c>'
 '<c r="D12"><f>IF($C$12="Optimiste","V02",IF($C$12="Prudent","V03","V01"))</f></c>')

# 2) validation liste : libelles parlants
x=x.replace('<formula1>"V01,V02,V03"</formula1>','<formula1>"Cadrage,Optimiste,Prudent"</formula1>')

# 3) tableau : lit le code D12 au lieu de C12
x,n=re.subn(r'"2027\|"&amp;\$C\$12',r'"2027|"&amp;$D$12',x)

mod={F4:x.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,mod.get(it.filename,zin.read(it.filename)))
zout.close()
print("OK -> %s | criteres relies a D12=%d"%(OUT,n))
