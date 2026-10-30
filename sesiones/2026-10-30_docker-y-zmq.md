# Sesión 2026-10-30: Docker y prueba sin radio

## Funciona
- B210 en USB 3.0 (sin transmitir).
- Imágenes de `open5gs`, `srsue`, `gnb-zmq` y `gnb-radio` construidas (gNB: unos 50 min).
- Open5GS v2.8.0 con MongoDB 6 y `scripts/cargar_abonado.sh`.
- Módulo `sctp`: se carga solo, sin sudo.
- N2/NG Setup entre gNB y AMF.

## No funciona
Prueba `gnb-zmq` + `srsue`: las conexiones ZMQ se establecen, pero casi no pasan bytes (unos 100 en 5 s). srsUE queda en `NAS5G Switching on`. Diagnóstico de Codex (`revisiones/2026-10-30_codex-diagnostico-zmq.md`): el stack del UE no recibe ticks porque no se completa el intercambio de muestras; todavía no se sabe qué lado lo frena.

## Riesgos abiertos
- **PLMN:** srsUE deduce MNC de 2 dígitos para MCC 722 (722/99). Según Codex, también lo usa para derivar la autenticación, así que agregar 722/99 al NRF probablemente no alcanza. Alternativa: usar 001/01 solo en esta prueba.
- Fuga corregida: srsUE escribía K y OPc en su log, por recibirlas como argumentos. Ahora las lee de un archivo temporal dentro del contenedor (cambio sin ejecutar todavía).

## Próximo paso propuesto
Una corrida con log de radio del gNB a stdout (`radio_level: debug`) y, si sigue detenido, stacks de hilos. Decidir PLMN de la prueba.

## Pendientes del usuario
Entorno de RF, celulares, SIM y entregable.

## Verificación n78 TDD
El gNB acepta n78, 20 MHz, 30 kHz, 3489,42 MHz por ZMQ sin UE y sin red (`evidencia/01_sincronizacion/2026-10-30_gnb_n78_tdd_config.log`). Solo valida la configuración: sin N2 no hay celda activa.

Pista: esta corrida imprime `==== gNB started ===` y la de n3 con AMF conectado nunca lo imprimió. Hay que mirar si el gNB se bloquea al activar la celda, antes de culpar al UE.

## Última corrida con srsUE (autorizada por el usuario)
Con PLMN 001/01 (`config/open5gs/open5gs-5gc-zmq.yml`, activada con `OPEN5GS_CONFIG=open5gs-5gc-zmq.yml`) el síntoma es igual: unos 90 bytes en 5 s y sin búsqueda de celda. Se descarta el PLMN como causa de este bloqueo.

El gNB completa NG Setup y F1 Setup y activa la celda, pero nunca imprime `gNB started` ni hay actividad de radio. Su radio está en `hrtimer_nanosleep`; el resto de los hilos, en espera. `radio_session_zmq_impl.cpp` limita el log de radio a info, así que `radio_level: debug` no aporta. Falta capturar stacks (requiere `SYS_PTRACE`). No se resolvió.

La corrección de claves funcionó: no aparecen en los logs de srsUE.
