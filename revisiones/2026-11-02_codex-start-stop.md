Encontré **3 problemas concretos**, ordenados por severidad:

1. **Bloqueante — [stop.sh:11](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/stop.sh:11)**. Si falla `compose stop` y `docker inspect` falla, la condición resulta falsa y se omite `docker kill`. Si el `kill` falla, tampoco se controla. En ambos casos se anuncia «La B210 ya no transmite» aunque el gNB podría seguir corriendo. `set -u` no detiene el script por errores de comandos. **Corrección:** comprobar los resultados y verificar que el contenedor esté detenido; si no se puede comprobar, terminar con error sin afirmar que cesó la transmisión.

2. **Importante — [scripts/panel.sh:74](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/panel.sh:74)**. `docker attach` conecta la entrada al gNB: un Ctrl-C accidental en métricas puede detenerlo. `--detach-keys=ctrl-q` agrega una secuencia de desconexión, pero no neutraliza Ctrl-C. **Corrección:** interceptar ese carácter antes de enviarlo al contenedor o mostrar métricas por un canal de lectura. El aviso de la línea 71 no evita el accidente.

3. **Importante — [scripts/anonimizar.sed:3](/home/nacho/Escritorio/Comunicaciones%20Moviles/5G/scripts/anonimizar.sed:3), también línea 4**. Las excepciones operan sobre **toda la línea**: si contiene un SUCI/IMSI de laboratorio, quedan sin anonimizar los identificadores de terceros del mismo tipo presentes allí. Lo reproduje con datos sintéticos. El filtro se usa para guardar el log del núcleo en `stop.sh:30`. **Corrección:** decidir la excepción por cada identificador, no por línea.

Verifiqué además que la confirmación precede al arranque del gNB en `start.sh`; no encontré accesos a variables sin definir que hagan abortar `stop.sh` con `set -u`, ni comandos inválidos en `red5g.screenrc` para GNU Screen 4.09.01. No encontré problemas dentro del alcance pedido en `ping_ue.py`.

La revisión fue estática, con pruebas del filtro sobre texto sintético: no ejecuté los scripts operativos, no abrí secretos ni archivos `*.local.*` y no edité nada.
