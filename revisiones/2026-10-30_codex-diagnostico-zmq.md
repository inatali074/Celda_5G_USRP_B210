**El código ubica el freno antes del cell search, en el arranque o circulación de muestras ZMQ. No encontré una opción SA faltante que explique el síntoma.** Sí encontré un problema independiente con el MNC de tres dígitos. Con los datos disponibles no puedo atribuir el bloqueo a una línea concreta sin observar los hilos o el log del radio.

No modifiqué archivos ni ejecuté Docker. Las referencias siguientes son relativas a los árboles `ocudu/` y `s4g/` que indicaste.

**Lo verificado: quién espera a quién**

1. **srsUE pide muestras antes de buscar una celda.** Al abrir el receptor crea el hilo RX (`s4g/lib/src/phy/rf/rf_zmq_imp_rx.c:197`). Ese hilo envía inmediatamente un REQ de un byte y espera la respuesta con muestras (`:40–57`). El primer REQ **no depende de NAS, PLMN, cell search ni RACH**.

2. **El gNB también inicia pedidos de muestras al arrancar su radio.** `ocudu/lib/radio/zmq/radio_session_zmq_impl.cpp:173` inicia RX y después TX. RX agenda `run_async()` (`radio_zmq_rx_channel.cpp:268–282`), que envía el REQ cuando no tiene respuesta pendiente (`:206–210`). Ese pedido va al puerto **2001 del UE**.

3. **srsUE genera ceros de UL incluso estando en IDLE.** Su PHY intenta recibir muestras en IDLE (`s4g/srsue/src/phy/sync_sa.cc:225–238`). Dentro de esa recepción, antes de leer DL, alinea el transmisor con `rf_zmq_tx_align()` (`s4g/lib/src/phy/rf/rf_zmq_imp.c:716–719`). El TX espera el REQ del gNB y responde con muestras, incluidos ceros (`rf_zmq_imp_tx.c:107–142`).

4. **El gNB responde al REQ de DL cuando dispone de muestras.** Recibe el pedido en `ocudu/lib/radio/zmq/radio_zmq_tx_channel.cpp:116–127`; si el buffer está vacío conserva la espera (`:150–162`). La recepción del gNB también alinea su TX antes de consumir UL (`radio_zmq_rx_stream.cpp:75–84`).

5. **NAS necesita que termine una recepción para avanzar.** `slot_sync::recv_callback()` primero llama a `radio->rx_now()` y después a `run_stack_tti()` (`s4g/srsue/src/phy/nr/slot_sync.cc:90–115`). El stack llama a `nas_5g.run_tti()` (`srsue/src/stack/ue_stack_lte.cc:515–535`).

   `switch_on()` solamente cambia el estado a `plmn_search` (`nas_5g.cc:1084–1088`). Recién `run_tti()` lanza el registro (`:114–134`), que solicita conexión RRC (`:294–300`) y dispara cell search (`rrc_nr_procedures.cc:208–215`, `:375–388`).

Esto explica por qué **un bloqueo de muestras puede dejar como último mensaje “NAS5G Switching on”**. TCP `ESTABLISHED` acredita la conexión, pero no acredita respuestas con IQ.

**Hallazgos y límites**

| Severidad | Archivo y línea | Qué falla y corrección propuesta |
|---|---|---|
| **Bloqueante, causa exacta pendiente** | `s4g/srsue/src/phy/nr/slot_sync.cc:98` | Si `rx_now()` no termina, no llegan ticks al stack y NAS no inicia RRC. El síntoma es compatible con esa espera. Falta determinar si espera el REQ de UL, muestras DL o un hilo del gNB que no arrancó. Primero instrumentar; no hay todavía un arreglo funcional demostrado. |
| **Importante** | `config/gnb/gnb_zmq.yml:43`; `config/srsue/ue.conf:43` | Los logs están dirigidos a archivos internos. El silencio en stdout después de N2 no prueba que el radio esté detenido. Propuesta mínima: llevar temporalmente el log del gNB a stdout y habilitar debug de radio. |
| **Importante, posterior al bloqueo actual** | `s4g/srsue/src/stack/upper/usim.cc:291–307`; `config/srsue/ue.conf:24` | La USIM software deduce **MNC de dos dígitos para MCC 722**: interpreta `722/99`, aunque el gNB anuncia `722/999`. La autenticación usa ese PLMN para construir el serving network name (`nas_5g.cc:859`, `:882–889`). Requiere corregir explícitamente esa deducción en srsUE o decidir un PLMN de prueba coherente en todos los componentes. No cambiaría solo el gNB. |

El problema `722/99` **no explica la ausencia del primer cell search**: en SA, RRC marca directamente `plmn_is_selected = true` (`s4g/srsue/src/stack/rrc_nr/rrc_nr.cc:92–94`), antes de la comprobación de `setup_request_proc` (`rrc_nr_procedures.cc:192–195`).

**Configuración y arranque que pude descartar**

- **SA ya está seleccionado:** `rat.eutra.nof_carriers = 0` entra en PHY NR SA y establece `args.stack.sa_mode = true` (`s4g/srsue/src/ue.cc:97–123`). La tasa fija requerida también está configurada (`:284–287`).
- `[rrc] release = 15` está presente. No encontré fundamento para agregar `ue_category` o `nas.force_imsi_attach` como solución a esta espera. Esta última opción pertenece a `args.stack.nas`, y la preparación SA copia algoritmos y APN hacia NAS5G (`ue.cc:290–295`).
- Los extremos ZMQ están cruzados correctamente: gNB TX 2000 → UE RX; UE TX 2001 → gNB RX.
- **El radio arranca automáticamente:** el programa inicia el DU (`ocudu/apps/gnb/gnb.cpp:629`); el controlador SDR inicia radio y lower PHY (`lib/ru/sdr/ru_controller_sdr_impl.cpp:66–78`). No aparece un paso de teclado para habilitarlo.
- **Tiempo real:** fallar al asignar prioridad produce una advertencia y el hilo continúa (`ocudu/lib/support/executors/unique_thread.cpp:16–25`, `:274–283`). No demuestra esta causa. Tampoco corresponde empezar cambiando privilegios, governor o buffers.
- ZMQ fuerza ejecución lower PHY secuencial (`ocudu/apps/units/flexible_o_du/split_8/helpers/ru_sdr_config_translator.cpp:256–260`); no propondría cambiar arbitrariamente su perfil.

**Cambio mínimo y siguiente experimento propuesto**

Para una corrida breve, exclusivamente ZMQ, propondría cambiar **solo observabilidad del gNB**:

```yaml
log:
  filename: stdout
  all_level: info
  radio_level: debug
```

`radio_level` existe en esta versión (`ocudu/apps/units/flexible_o_du/split_8/helpers/ru_sdr_config_cli11_schema.cpp:167`).

El experimento debería registrar, por separado, estas cuatro transacciones:

| Puerto | Pedido | Respuesta esperada |
|---|---|---|
| 2000 | REQ del UE | IQ DL del gNB |
| 2001 | REQ del gNB | IQ UL/ceros del UE |

En el log del gNB buscaría `Socket sent request`, `Socket received request`, `Socket sent … samples` y `Waiting for data/request` (`radio_zmq_rx_channel.cpp:101`, `:215`; `radio_zmq_tx_channel.cpp:126`, `:183`).

Si vuelve a quedar detenido, **la siguiente evidencia decisiva es una captura de stacks de todos los hilos de ambos procesos, dentro de sus contenedores**:

- UE en `rf_zmq_tx_align()` → revisar si el gNB realmente envió su REQ a 2001.
- UE en `rf_zmq_rx_baseband()` → revisar si el gNB recibió el REQ a 2000 y produjo muestras.
- gNB antes de `radio->start()` o dentro de su espera de arranque → revisar el inicio del DU y el ejecutor `radio`.

**Hipótesis principal:** el intercambio inicial no se completa y deja sin reloj al stack del UE. **Todavía no está verificado qué lado lo interrumpe.** Agregar opciones NAS/RRC o volver a cambiar el orden de arranque no resolvería esa incertidumbre.
