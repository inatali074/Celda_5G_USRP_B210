Creé únicamente:

- `docker-compose.yml`
- `docker/gnb/Dockerfile`
- `docker/open5gs/Dockerfile`
- `docker/open5gs/entrypoint.sh`
- `docker/srsue/Dockerfile`

Falta crear:

- `config/open5gs/open5gs-5gc.yml`: núcleo, MongoDB y direcciones N2/N3.
- `config/open5gs/network.env`: `UE_SUBNET` y `OGSTUN_ADDRESS`, coherentes con el YAML.
- `config/gnb/gnb_b210.yml`
- `config/gnb/gnb_zmq.yml`
- `config/srsue/ue.conf`, con referencias a los archivos privados necesarios bajo `/run/secretos`.

Validé sintaxis YAML, sintaxis del entrypoint y restricciones del compose: sin perfiles solo quedan MongoDB y Open5GS; ningún servicio publica puertos.

Quedaron sin confirmar mediante build: los instaladores internos de OCUDU, su opción `ENABLE_ZEROMQ`, las imágenes B210 y la disponibilidad de `5gc` en Open5GS v2.8.0. Agregué comprobaciones que detienen la construcción ante esas ausencias. También falta comprobar superposición de subredes y acceso USB restringido.

No ejecuté Docker ni usé la USRP.
