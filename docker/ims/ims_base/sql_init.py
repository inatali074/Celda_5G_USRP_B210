import os,re,subprocess,pathlib
c=os.environ['COMPONENT_NAME']
p=os.environ['IMS_DB_PASSWORD']
if not re.fullmatch(r'[A-Za-z0-9_]{16,}',p) or p.startswith('CAMBIAR'): raise SystemExit('Cambiar IMS_DB_PASSWORD: 16+ caracteres alfanuméricos/_')
pathlib.Path('/root/.my.cnf').write_text('[client]\nhost=10.53.2.17\nuser='+c+'\npassword='+p+'\n')
base='/usr/local/src/kamailio/'
files={'icscf':['misc/examples/ims/icscf/icscf.sql'],'scscf':['utils/kamctl/mysql/'+x+'-create.sql' for x in ['standard','presence','ims_usrloc_scscf','ims_dialog','ims_charging']],'pcscf':['utils/kamctl/mysql/'+x+'-create.sql' for x in ['standard','presence','ims_usrloc_pcscf','ims_dialog']]}
r=subprocess.run(['mysql','-N',c,'-e','SHOW TABLES'],check=True,capture_output=True)
tables=r.stdout.decode().split()
if tables and 'ims_schema_ready' not in tables:
 raise SystemExit('Esquema CSCF incompleto: revisar SQL antes de continuar; no se borra la base.')
if not tables:
 for f in files[c]:
  with open(base+f) as src: subprocess.run(['mysql',c],stdin=src,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 subprocess.run(['mysql',c,'-e','CREATE TABLE ims_schema_ready (id INT PRIMARY KEY)'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
