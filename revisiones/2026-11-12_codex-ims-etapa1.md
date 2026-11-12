Implementé los archivos de la etapa 1:

- `docker/ims/` y `config/ims/`: seis servicios, configuraciones y licencia.
- `docker-compose.yml`: perfil `ims`, red e IPs, sin puertos IMS publicados.
- `config/open5gs/open5gs-5gc-ims.yml` y entrypoint: DNN `ims`, `ogstun2` opcional, sin NAT.
- Cargadores IMS y verificador nuevos; `cargar_abonado.sh` ahora preserva otras sesiones.
- `start.sh` y `stop.sh`: integración de IMS antes del gNB y del apagado del núcleo.

Pasaron sintaxis Bash/Python, parseo YAML/XML y pruebas simuladas de idempotencia y preservación de SQN.

Para probar, seguí [docker/ims/README.md](docker/ims/README.md): preparar credenciales MySQL, construir imágenes —incluida Open5GS—, validar sin radio, cargar 003/1003 y 004/1004, y finalmente comprobar PDU `ims` y REGISTER 200 OK.

No ejecuté Docker, builds, sudo, git ni accedí a secretos. Quedan pendientes las pruebas reales de SQL, Diameter, IPsec y registro con los teléfonos.
