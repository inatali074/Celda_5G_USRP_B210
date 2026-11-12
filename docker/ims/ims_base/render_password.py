import os,pathlib
c=os.environ['COMPONENT_NAME']
p=pathlib.Path('/etc/kamailio_'+c)/(c+'.cfg')
p.write_text(p.read_text().replace(':heslo@', ':'+os.environ['IMS_DB_PASSWORD']+'@'))
p.chmod(0o600)
