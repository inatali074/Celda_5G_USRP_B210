"""Se ejecuta dentro de ims-pyhss; entrada sensible sólo por stdin."""
import json,sys,urllib.request,urllib.error

def api(method,path,data=None):
    body=None if data is None else json.dumps(data).encode()
    req=urllib.request.Request('http://127.0.0.1:8080/'+path,data=body,
        headers={'Content-Type':'application/json'},method=method)
    with urllib.request.urlopen(req,timeout=15) as r:
        return json.load(r)

def find(kind,key,value):
    page=0
    while True:
        rows=api('GET',f'{kind}/list?page={page}&page_size=100')
        if not isinstance(rows,list): raise ValueError()
        matches=[r for r in rows if str(r.get(key))==value]
        if len(matches)>1: raise ValueError()
        if matches: return matches[0]
        if len(rows)<100: return None
        page+=1

def ensure(kind,key,value,payload,update=False):
    row=find(kind,key,value)
    if row:
        ident=row[kind+'_id']
        if update: api('PATCH',f'{kind}/{ident}',payload)
    else:
        row=api('PUT',kind+'/',payload)
        ident=row[kind+'_id']
    if not isinstance(ident,int): raise ValueError()
    return ident

def main():
    x=json.load(sys.stdin); imsi=x['imsi']; msisdn=x['msisdn']
    data=ensure('apn','apn','Metodos1',{'apn':'Metodos1','apn_ambr_dl':0,'apn_ambr_ul':0})
    ims=ensure('apn','apn','ims',{'apn':'ims','apn_ambr_dl':0,'apn_ambr_ul':0})
    # No PATCH de AUC: nunca reescribir SQN ni material de autenticación existente.
    auc=ensure('auc','imsi',imsi,{'imsi':imsi,'ki':x['ki'],'opc':x['opc'],'amf':'8000','sqn':0})
    old=find('subscriber','imsi',imsi)
    apns=set((old or {}).get('apn_list','').split(','))-{''}
    apns.update([str(data),str(ims)])
    sub=ensure('subscriber','imsi',imsi,{'imsi':imsi,'enabled':True,'auc_id':auc,
        'default_apn':(old or {}).get('default_apn',data),'apn_list':','.join(sorted(apns)),
        'msisdn':msisdn,'ue_ambr_dl':0,'ue_ambr_ul':0},True)
    ims_sub=ensure('ims_subscriber','imsi',imsi,{'imsi':imsi,'msisdn':msisdn,
        'msisdn_list':json.dumps([msisdn]),'ifc_path':'default_ifc.xml'},True)
    print(f'IMSI {imsi}: APN IDs {data},{ims}; AUC ID {auc}; subscriber ID {sub}; IMS ID {ims_sub}; OK')

if __name__=='__main__':
    try: main()
    except Exception:
        print('Error de aprovisionamiento PyHSS (detalle sensible omitido).',file=sys.stderr)
        sys.exit(1)
