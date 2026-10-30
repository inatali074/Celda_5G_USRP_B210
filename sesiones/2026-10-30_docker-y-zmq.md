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

## Celda real con la B210 (dentro de la jaula)
Celda n78 TDD, 3525 MHz, 20 MHz, TX 70, en Docker sin `privileged`. Radio estable.

| Teléfono | SIM | Resultado |
| :--- | :--- | :--- |
| Redmi Note 14 5G | SIM 1 | Una sola vez (14:25): RACH, 5G-AKA y `Registration complete`. Sin sesión PDU. No se pudo repetir |
| Motorola Edge 30 Neo | SIM 1 | Sin ningún PRACH |
| Motorola Edge 30 Neo | Chip comercial | RACH hasta el AMF; rechazo 95 esperado |

Conclusión: la celda funciona por radio; el problema es cómo el teléfono trata la SIM de laboratorio. La causa del docx (falta de DF_5GS) queda refutada, y su afirmación de que la SIM 3 tenía NG-RAN no coincide con el chip.

## Para retomar
**Sesión de Claude Code:** `5e913986-b7d2-4ab8-871f-853670d77def` (`claude --resume 5e913986-b7d2-4ab8-871f-853670d77def`, desde esta carpeta).

1. Conseguir una PC con Windows y grabar en la SIM 3 NG-RAN (`0800`) en las tres listas, reescribiendo K y OPc; cargar su abonado con `scripts/cargar_abonado.sh 722999000000003`.
2. Probar con la celda. Si no alcanza, pasar a PLMN 001/01.
3. Con un registro estable: sesión PDU, IP y navegación; después DFT-s-OFDM y NEA2 por separado y las mediciones.
4. Revisar los 9 underflows del log `2026-10-30_motorola_sim1_y_chip.log`.

Para arrancar: conectar la B210 y el lector, `docker compose up -d --no-build mongodb open5gs`, y `docker compose --profile radio up -d --no-build --no-deps gnb-radio` (transmite: confirmar cada vez). Las imágenes y la base quedan guardadas. Los archivos temporales de la sesión pueden perderse al reiniciar la PC; nada imprescindible depende de ellos.
