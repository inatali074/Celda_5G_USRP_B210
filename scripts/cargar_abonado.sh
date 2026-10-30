#!/bin/bash
set +x
set -eu
set -o pipefail
set +a

error() {
    printf 'Error: %s\n' "$1" >&2
    exit 1
}

[[ $# -eq 1 ]] || error 'Uso: scripts/cargar_abonado.sh <IMSI>'
[[ $1 =~ ^[0-9]{15}$ ]] || error 'El IMSI debe tener exactamente 15 dígitos.'
imsi=$1
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

command -v docker >/dev/null 2>&1 || error 'No se encontró Docker.'
if ! servicios=$(docker compose -f "$raiz/docker-compose.yml" ps --status running --services 2>/dev/null); then
    error 'No se pudo consultar Compose; verificá Docker y los permisos de acceso.'
fi
[[ $'\n'${servicios}$'\n' == *$'\nmongodb\n'* ]] || error 'El servicio mongodb del compose no está corriendo.'

# El código es fijo en argv; los datos sensibles viajan únicamente por stdin.
# Se ocultan los diagnósticos de mongosh porque podrían incluir datos del documento.
if ! resultado=$(docker compose -f "$raiz/docker-compose.yml" exec -T mongodb mongosh --quiet --norc open5gs --eval '
try {
    const input = JSON.parse(require("fs").readFileSync(0, "utf8"));
    if (!/^[0-9]{15}$/.test(input.imsi) ||
        !/^[0-9a-fA-F]{32}$/.test(input.k) ||
        !/^[0-9a-fA-F]{32}$/.test(input.opc)) quit(2);
    const subscribers = db.getSiblingDB("open5gs").subscribers;
    const previous = subscribers.findOne({imsi: input.imsi},
        {_id: 1, "slice._id": 1, "slice.session._id": 1});
    const slice = previous?.slice?.[0];
    const ambr = () => ({
        downlink: {value: NumberInt(1000000000), unit: NumberInt(0)},
        uplink: {value: NumberInt(1000000000), unit: NumberInt(0)}
    });
    const result = subscribers.updateOne({imsi: input.imsi}, {
        $set: {
            schema_version: NumberInt(1),
            slice: [{
                sst: NumberInt(1), default_indicator: true,
                session: [{
                    name: "Metodos1", type: NumberInt(1),
                    qos: {index: NumberInt(9), arp: {
                        priority_level: NumberInt(8),
                        pre_emption_capability: NumberInt(1),
                        pre_emption_vulnerability: NumberInt(2)
                    }},
                    ambr: ambr(), pcc_rule: [],
                    _id: slice?.session?.[0]?._id ?? new ObjectId()
                }],
                _id: slice?._id ?? new ObjectId()
            }],
            "security.k": input.k, "security.op": null,
            "security.opc": input.opc, "security.amf": "8000",
            ambr: ambr(), access_restriction_data: 32,
            network_access_mode: 0, subscriber_status: 0,
            operator_determined_barring: 0, subscribed_rau_tau_timer: 12
        },
        $setOnInsert: {
            _id: new ObjectId(), imsi: input.imsi,
            msisdn: [], imeisv: [], mme_host: [], mm_realm: [],
            purge_flag: [], __v: 0
        }
    }, {upsert: true});
    if (!result.acknowledged) quit(3);
    print(`IMSI ${input.imsi}: modificados=${result.modifiedCount}, insertados=${result.upsertedCount}`);
} catch (_) {
    quit(1);
}
' 2>/dev/null <<EOF
{"imsi":"$imsi","k":"$USIM_K","opc":"$USIM_OPC"}
EOF
); then
    error 'Falló el upsert; verificá que mongodb siga corriendo, que mongosh esté disponible y que la base permita escritura.'
fi
unset USIM_K USIM_OPC
salida_re="^IMSI ${imsi}: modificados=[01], insertados=[01]$"
[[ $resultado =~ $salida_re ]] || error 'MongoDB devolvió una respuesta inesperada; verificá el resultado antes de reintentar.'
printf '%s\n' "$resultado"
