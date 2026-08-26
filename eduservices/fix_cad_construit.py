import zipfile,re
SRC="CAD_PIL.xlsm"; OUT="CAD_PIL_fix.xlsm"
zin=zipfile.ZipFile(SRC)
wb=zin.read("xl/workbook.xml").decode("utf8");rels=zin.read("xl/_rels/workbook.xml.rels").decode("utf8")
id2f={m.group(1):m.group(2) for m in re.finditer(r'Id="([^"]+)"[^>]*Target="worksheets/(sheet\d+\.xml)"',rels)}
n2f={m.group(1):("xl/worksheets/"+id2f[m.group(2)]) for m in re.finditer(r'<sheet name="([^"]+)"[^>]*r:id="([^"]+)"',wb) if m.group(2) in id2f}
F=n2f["cad"]; x=zin.read(F).decode("utf8")

reps=[
 # E11 : CA construit
 (r'<c r="E11"[^>]*>.*?</c>',
  '<c r="E11" s="80"><f>SUMIFS(Moteur!$R$1:$R$175,Moteur!$B$1:$B$175,cad!$P$1)</f></c>'),
 # E12 : EBITDA construit
 (r'<c r="E12"[^>]*>.*?</c>',
  '<c r="E12" s="80"><f>SUMIFS(_CALC_PNL!$T$1:$T$1347,_CALC_PNL!$D$1:$D$1347,cad!$P$1,_CALC_PNL!$C$1:$C$1347,"2027")</f></c>'),
 # E14 : Effectif construit
 (r'<c r="E14"[^>]*>(?:<v>.*?</v>)?</c>',
  '<c r="E14" s="80"><f>SUMIFS(Moteur!$P$1:$P$175,Moteur!$B$1:$B$175,cad!$P$1)</f></c>'),
]
for pat,new in reps:
    x,n=re.subn(pat,new,x,count=1)
    assert n==1,"pattern non trouve: "+pat
# fullCalcOnLoad
if "fullCalcOnLoad" not in wb:
    wb=re.sub(r'<calcPr calcId="(\d+)"',r'<calcPr calcId="\1" fullCalcOnLoad="1"',wb,count=1)

mod={F:x.encode("utf8"),"xl/workbook.xml":wb.encode("utf8")}
zout=zipfile.ZipFile(OUT,"w",zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    zi=zipfile.ZipInfo(it.filename,date_time=it.date_time)
    zi.compress_type=it.compress_type; zi.external_attr=it.external_attr
    zi.create_system=it.create_system; zi.internal_attr=it.internal_attr
    zout.writestr(zi,mod.get(it.filename,zin.read(it.filename)))
zout.close()
print("OK -> %s"%OUT)
