#!/bin/bash
set +x
set -eu
set -o pipefail
set +a

error() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

[[ $# -eq 2 ]] || error 'Uso: scripts/cargar_ims.sh <IMSI> <MSISDN>'
[[ $1 =~ ^[0-9]{15}$ ]] || error 'El IMSI debe tener exactamente 15 dígitos.'
imsi=$1
[[ $2 =~ ^[0-9]{4,15}$ ]] || error 'MSISDN inválido.'
msisdn=$2
case "$imsi:$msisdn" in
 001010000000003:1003|001010000000004:1004) ;;
 *) error 'Asignaciones de esta etapa: IMSI …003 / 1003 e IMSI …004 / 1004.' ;;
esac
raiz=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd -- "$raiz"
secretos=$raiz/config/secretos/usim.env
[[ -f $secretos && -r $secretos ]] || error 'Falta config/secretos/usim.env o no se puede leer.'

# No se usa source: el archivo contiene datos y no debe ejecutar comandos.
unset USIM_K USIM_OPC
clave_re='^[[:space:]]*(export[[:space:]]+)?(USIM_K|USIM_OPC)[[:space:]]*=(.*)$'
valor_re="^[[:space:]]*([[:xdigit:]]{32}|\"[[:xdigit:]]{32}\"|'[[:xdigit:]]{32}')[[:space:]]*(#.*)?$"
while IFS= read -r linea || [[ -n $linea ]]; do
    linea=${linea%$'\r'}
    if [[ $linea =~ $clave_re ]]; then
        nombre=${BASH_REMATCH[2]}
        valor=${BASH_REMATCH[3]}
        [[ $valor =~ $valor_re ]] || error "${nombre} debe contener exactamente 32 caracteres hexadecimales."
        valor=${BASH_REMATCH[1]}
        valor=${valor#\"}; valor=${valor%\"}
        valor=${valor#\'}; valor=${valor%\'}
        [[ ! -v $nombre ]] || error "${nombre} está repetida en usim.env."
        printf -v "$nombre" '%s' "$valor"
    fi
done < "$secretos"
unset linea valor nombre
[[ ${USIM_K:-} =~ ^[[:xdigit:]]{32}$ ]] || error 'Falta USIM_K válida en usim.env.'
[[ ${USIM_OPC:-} =~ ^[[:xdigit:]]{32}$ ]] || error 'Falta USIM_OPC válida en usim.env.'

# Las claves viajan por stdin, nunca por argv, compose environment ni archivos.
if ! docker compose --profile ims exec -T ims-pyhss python3 /opt/provisionar_ims.py 2>/dev/null <<EOF
{"imsi":"$imsi","msisdn":"$msisdn","ki":"$USIM_K","opc":"$USIM_OPC"}
EOF
then
 error 'Falló PyHSS. No se muestran cuerpos de API. Revisá disponibilidad y reintentá; no se resetea SQN.'
fi
unset USIM_K USIM_OPC
if ! docker compose exec -T mongodb mongosh --quiet --norc open5gs --eval '
try {
 const x=JSON.parse(require("fs").readFileSync(0,"utf8"));
 const col=db.getSiblingDB("open5gs").subscribers;
 const sub=col.findOne({imsi:x.imsi});
 if (!sub) quit(2);
 const slices=sub.slice ?? [];
 const slice=slices.find(s=>s.sst===1 && !s.sd);
 if (!slice) quit(3);
 const old=(slice.session ?? []).find(s=>s.name==="ims");
 const session={...(old ?? {}),name:"ims",type:NumberInt(1),
  qos:{index:NumberInt(5),arp:{priority_level:NumberInt(1),
   pre_emption_capability:NumberInt(1),pre_emption_vulnerability:NumberInt(1)}},
  ambr:{downlink:{value:NumberInt(3850),unit:NumberInt(1)},uplink:{value:NumberInt(1530),unit:NumberInt(1)}},
  pcc_rule:old?.pcc_rule ?? [],_id:old?._id ?? new ObjectId()};
 slice.session=(slice.session ?? []).filter(s=>s.name!=="ims"); slice.session.push(session);
 const result=col.updateOne({_id:sub._id},{$set:{slice:slices},$addToSet:{msisdn:x.msisdn}});
 if(!result.acknowledged) quit(4);
 print("IMSI "+x.imsi+": MongoDB ims y MSISDN actualizados");
} catch (_) { quit(1); }
' 2>/dev/null <<EOF
{"imsi":"$imsi","msisdn":"$msisdn"}
EOF
then
 error 'Falló MongoDB: primero cargá el abonado 5G con SST 1. PyHSS puede haber quedado cargado; reintentar es seguro.'
fi
