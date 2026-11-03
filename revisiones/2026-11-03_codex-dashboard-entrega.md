Implementado. **No construí imágenes, no inicié contenedores ni usé sudo o la USRP.**

Archivos creados en `docker/dashboard/`:

- `Dockerfile` y `requirements.txt`: Python 3.12, ping, iperf3 y dependencias fijadas.
- `app.py`: backend asyncio, métricas, logs, contadores, ping e iperf3.
- `index.html`: página con tablas, gráficos, eventos, herramientas y JSON crudo.
- `README.md`: uso, limitaciones, fuentes y procedimiento de prueba.

Diff resumido de los archivos modificados:

| Archivo | Cambio |
|---|---|
| `docker-compose.yml` | Servicio `dashboard` sin perfil, namespace compartido con Open5GS, publicación exclusiva en `127.0.0.1:8080`, volúmenes de logs y únicamente `NET_RAW` para ping. |
| Las dos configuraciones gNB indicadas | Agregados `remote_control` y métricas JSON con periodicidad de 1000 ms y scheduler por celda/UE. Ningún otro parámetro cambiado. |
| Ambos YAML de Open5GS | Agregado `logger.file.path: /var/log/open5gs/core.log`. |
| `start.sh` | Incluye dashboard al levantar el núcleo e imprime la URL. |
| `stop.sh` | Detiene también dashboard; conserva el guardado actual de logs. |

Para el gNB elegí compartir `/tmp`: un wrapper vacía solamente `gnb.log` y hace `exec` del binario con los argumentos originales. Conserva stdin y señales, y `stop.sh` mantiene su ruta de copia. Los montajes del dashboard son de solo lectura.

**Verificaciones realizadas:** `py_compile`, `bash -n`, YAML mediante PyYAML y `git diff --check`, todas correctas. También pasaron pruebas locales del extractor, BLER, validación de destinos, mapa IMSI/IP y seguimiento de logs con append, truncado y rotación.

Verifiqué `logger.file.path` y el agregado del archivo sin quitar el logger predeterminado en [Open5GS v2.8.0, ogs-init.c](https://github.com/open5gs/open5gs/blob/v2.8.0/lib/app/ogs-init.c). **No pude verificar independientemente la anidación de OCUDU:** GitLab falló; quedó implementada según el relevamiento de Claude. Falta validarla con fuente/binario y probar el sistema en Docker.

Riesgos y límites:

- Los UE pueden acceder a `10.45.0.1:8080`; no hay autenticación.
- Ping, iperf3 y procesamiento de métricas agregan carga y pueden alterar mediciones.
- Los logs crecen sin rotación automática.
- Chart.js 4.4.1 requiere acceso al CDN.
- No se relacionan RNTI e IMSI sin evidencia explícita; unidades desconocidas se muestran crudas.

Para construir y probar, ejecutá desde la raíz:

```bash
docker compose build dashboard

OPEN5GS_CONFIG=open5gs-5gc-zmq.yml \
  docker compose up -d --no-build mongodb open5gs dashboard
```

Abrí **http://localhost:8080**: comprobá que funcione sin gNB, probá ping e iniciá el servidor iperf3. Recrear Open5GS puede interrumpir sesiones existentes.

Después de validar las claves OCUDU, para una corrida RF autorizada:

```bash
./start.sh gnb_b210_00101_csiper_ppm0_kos.yml
# Al terminar:
./stop.sh
```

**`start.sh` transmite inmediatamente.** El README detalla la alternativa n3 y las pruebas desde el teléfono contra `10.45.0.1:5201`, normales y con `-R`.
