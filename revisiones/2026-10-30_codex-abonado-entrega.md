Creé únicamente [scripts/cargar_abonado.sh](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/cargar_abonado.sh).

- Valida IMSI y claves; envía K/OPc por stdin y hace upsert por IMSI. Configura AMF `8000`, SST `1` sin SD y DNN `Metodos1`, IPv4 sin IP estática. Informa IMSI y cantidades modificadas/insertadas.
- Esquema tomado de `open5gs-dbctl`, líneas **551–614**, adaptando DNN y tipo de sesión.
- Verificado: sintaxis con `bash -n`. No ejecuté el script, Docker ni sudo; tampoco accedí a secretos.
- Sin confirmar: funcionamiento contra MongoDB real, disponibilidad de `mongosh` y coincidencia de claves con la SIM.
