import zipfile,re
SRC="Alloc_2_CALC_v3.xlsx"; OUT="Alloc_2_CALC_v4.xlsx"
zin=zipfile.ZipFile(SRC)
wb=zin.read("xl/workbook.xml").decode("utf8");rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
n2f={m.group(1):("xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wb) if m.group(2) in id2f}
F4=n2f["ALLOC"]; x=zin.read(F4).decode("utf8")

# 1) sélecteur version : ligne 12 (label B12 + valeur C12=V01), inseree avant la ligne 14
row12=('<row r="12" spans="2:13" x14ac:dyDescent="0.45">'
       '<c r="B12" s="128" t="inlineStr"><is><t>Version budget restituée (2027)</t></is></c>'
       '<c r="C12" s="129" t="inlineStr"><is><t>V01</t></is></c></row>')
x=re.sub(r'(<row r="14")',row12+r'\1',x,count=1)

# 2) validation liste sur C12
x=x.replace('<dataValidations count="1">','<dataValidations count="2">')
x=x.replace('</dataValidations>',
    '<dataValidation type="list" sqref="C12"><formula1>"V01,V02,V03"</formula1></dataValidation></dataValidations>')

# 3) tableau : critere exercice "2026" -> cle EXVER "2027|"&$C$12
x,n=re.subn(r'_CALC_ALLOC!\$A\$1:\$A\$349,"2026"',
            r'_CALC_ALLOC!$AS$1:$AS$349,"2027|"&amp;$C$12',x)

mod={F4:x.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,mod.get(it.filename,zin.read(it.filename)))
zout.close()
print("OK -> %s | criteres bascules sur version=%d"%(OUT,n))
