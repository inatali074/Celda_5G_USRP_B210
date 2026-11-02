Encontré **3 errores concretos**:

1. **Importante — [scripts/empaquetar_para_otra_pc.sh:54](scripts/empaquetar_para_otra_pc.sh:54).** Al reutilizar una carpeta destino, `*` incluye el `SHA256SUMS.txt` anterior. La redirección lo trunca y termina calculándose un checksum del propio manifiesto mientras se escribe. El instalador lo rechaza en la línea 37 aunque la copia esté intacta. **Corrección:** exigir un destino vacío y generar el manifiesto con una lista explícita que lo excluya.

2. **Importante — [scripts/empaquetar_para_otra_pc.sh:31](scripts/empaquetar_para_otra_pc.sh:31).** `umask 077` no restringe permisos de archivos existentes. Si el destino ya tiene un `secretos.tar` legible por otros usuarios, la línea 40 lo sobrescribe conservando esos permisos y expone K, OPc y ADM. **Corrección:** rechazar destinos existentes o asegurar directorio `0700` y archivo `0600` antes de escribir secretos. El escenario depende de los permisos previos; no inspeccioné claves.

3. **Menor — [docs/LEVANTAR_EN_OTRA_PC.md:38](docs/LEVANTAR_EN_OTRA_PC.md:38).** Siguiendo los comandos de la guía, la terminal sigue dentro del paquete del pendrive: ejecutar el instalador con `bash` no cambia el directorio del shell padre. Allí no existen `./start.sh` ni `./stop.sh`. **Corrección:** agregar `cd ~/red5g-docker` antes del arranque.

**Verificado:** Compose con `name: 5g` espera `5g-open5gs:latest`, `5g-gnb-radio:latest` y `mongo:6.0`; coinciden con lo exportado. El instalador solo inicia MongoDB: no encontré un camino que transmita durante la instalación ni instalación del núcleo/gNB en el host. La sintaxis Bash pasa.

No ejecuté instalación ni arranque, no edité archivos y no abrí `config/secretos/` ni `*.local.*`. La coincidencia de claves entre SIM y núcleo queda sin verificar.
