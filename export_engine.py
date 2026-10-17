import csv,io,json,zipfile
def csv_bytes(rows,fields):
 s=io.StringIO();w=csv.DictWriter(s,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows);return s.getvalue().encode('utf-8-sig')
def json_bytes(v):return json.dumps(v,ensure_ascii=False,indent=2).encode('utf-8')
def backup_zip(path,datasets):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  for n,v in datasets.items():z.writestr(n+'.json',json_bytes(v))
