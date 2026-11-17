# Evidencia 09: "UL processor is busy" (corrida del 2026-11-13, P-004)

Corrida: n78 TDD (opción 1 del menú, `gnb_b210_00101_n78_cpofdm.yml`), en tachoPC (4 hilos), con volcado IQ y log en `info`. El log va de 13:04:22 a 16:09:37 UTC.

La traba de las 12:35:50 UTC no quedó registrada. El gNB se reinició a las 13:04, y el log nuevo pisó al anterior.

## Archivos
- `gnb_inicio_ul_busy.log`: la configuración de hilos, el primer PRACH y las primeras 40 fallas. No contiene identidades.
- `ul_busy_por_slot.txt`: cantidad de fallas según el slot de la trama.
- `ul_busy_por_minuto.txt`: por minuto, las fallas, los slots volcados al archivo IQ, los PUSCH, los PRACH detectados, las fallas de RF y los pedidos tardíos.

## Qué muestran los datos
1. **La falla nunca se va.** Empieza 0,19 s después del primer PRACH (13:04:58), a los 36 s del arranque. Desde ahí sigue hasta el final: 329 440 fallas en 3 horas.
   - Antes de la primera falla no hay avisos de tiempo real. Los 6 `underflow` previos fueron a las 13:04:34, durante el arranque.
2. **La tasa crece durante la corrida.** Arranca en ~700 por minuto y llega a ~5800 por minuto a las 16:04. Sube por escalones, y algunos coinciden con ráfagas de fallas de RF (por ejemplo a las 15:42:58), pero otros no.
3. **No depende del volcado IQ ni del tráfico.** Hay minutos con 10 PUSCH y 10 slots volcados, y aun así con 738 fallas (13:48). La correlación por minuto entre las fallas y los slots volcados es de 0,32. **Se descarta el volcado IQ como causa principal**, aunque puede sumar carga.
4. **Aparece a intervalos regulares, incluso sin tráfico.** Al principio hay una falla cada 80 a 100 ms, como si una de las entradas de un conjunto fijo de procesadores quedara ocupada para siempre y se la volviera a pedir cada cierta cantidad de slots.
5. **Se concentra en el slot 19**, el de la ocasión de PRACH (`prach-ConfigurationIndex` 159, formato B4, una por trama). Ahí cae el 49 % de las fallas (160 300). El slot 8 suma el 26 %.
   - Al principio se leyó como apoyo a la hipótesis del 2026-11-04 (el slot del PRACH sería el más pesado). El código lo explica de otra forma: ver la conclusión.
6. **Se procesa con un solo hilo.** El pool `main_pool` se instanció con **1 worker**, porque tachoPC tiene 4 hilos. Ese pool procesa la capa física superior y las capas de arriba (`gnb expert_execution threads main_pool --help`). Pasó lo mismo en todas las corridas guardadas en tachoPC.

## Qué dice el código de OCUDU (commit e0db566, el de la imagen)
Leído el 2026-11-17, de un clon parcial de `gitlab.com/ocudu/ocudu`.

1. **Dónde se genera la falla:** `lib/fapi_adaptor/phy/p7/fapi_to_phy_fastpath_translator.cpp:503-507`.
   - Por cada `UL_TTI.request` que trae PDUs, se pide un repositorio de PDU al pool de procesadores de subida.
   - Si el procesador que toca no está libre, el repositorio vuelve inválido. Se registra "UL processor is busy" y **se descarta todo el pedido de ese slot**: PUSCH, PUCCH y PRACH.
2. **Cómo se elige el procesador:** por turno (*round-robin*), no según el número de slot.
   - El contador avanza en 1 en cada pedido y vuelve a 0 al llegar al tamaño del pool (`lib/phy/upper/processor_pool_helpers.h:43-55`).
   - El pool tiene **un procesador por slot de la trama: 20 en n78** (`apps/units/flexible_o_du/o_du_low/du_low_config_translator.cpp:178-180,195`, "reusing uplink processors every 10 ms").
3. **Cuándo un procesador queda libre:** cuando su máquina de estados (`lib/phy/upper/uplink_processor_fsm.h`) vuelve al estado *idle*. Para eso tiene que pasar una de estas cosas:
   - recibir los 14 símbolos del slot y terminar todos sus PDU;
   - descartarse en el estado "esperando el primer símbolo" (`discard_slot`, `uplink_processor_impl.cpp:527-540`).

   **No hay ningún tiempo límite.** Si queda en el estado "recibiendo" o "esperando que terminen los PDU", nada lo libera. Entonces `start_new_slot` falla para siempre (`uplink_processor_impl.cpp:90-102`).
4. **Cómo puede quedar a mitad de un slot.** Cuando la PHY inferior detecta un salto en las marcas de tiempo de las muestras (muestras perdidas), se realinea a la subtrama siguiente sin avisar a la PHY superior (`lib/phy/lower/processors/uplink/uplink_processor_impl.cpp:163-171` → `process_alignment`).
   - Los símbolos que faltaban de ese slot no llegan nunca, y el procesador queda para siempre en "recibiendo".
   - Lo mismo pasa si llega un pedido tarde, a mitad de un slot.
   - **Esta parte es inferida:** lo que muestra el código es que no hay recuperación, pero no vi en el log cuál fue la perturbación que la disparó.
5. **El volcado IQ escribe en su propio hilo** (`lib/phy/upper/rx_resource_grid_printer_backend.h:33`), así que no frena la PHY. Igual compite por la CPU.
6. **`main_pool`** (`apps/services/worker_manager/worker_manager.cpp:268-299`):
   - Por defecto calcula antenas DL + UL + celdas + 2 = 5 hilos, pero deja 3 CPU libres.
   - Con 4 CPU queda en **1 hilo**; en la PC de Santi, con 12, en 5.
   - `nof_threads` se puede subir hasta la cantidad de CPU.

## Conclusión
**Es una pérdida de procesadores sin recuperación, no una sobrecarga sostenida.**
- Cada procesador que queda trabado produce un "busy" cada 20 pedidos de subida.
- Al principio había ~2 pedidos por trama: el PRACH en el slot 19 y los PUCCH de los slots 7 y 8 cada 2 tramas. Eso da una falla cada 10 tramas, que es justo lo observado (950.19 → 960.19 → 970.19).
- Con tráfico hay más pedidos y la tasa sube. Cada nueva perturbación traba otro procesador y la tasa sube un escalón.
- Que la mayoría caiga en el slot 19 se explica porque es el slot con más pedidos (hay PRACH en todas las tramas). **Ya no hace falta la hipótesis de la carga del PRACH** (`zero_correlation_zone`).
- Solo se recupera reiniciando el gNB.
- Cuando se traban muchos procesadores, se pierde una gran parte de los pedidos de subida (PUSCH, PUCCH con ACK y CSI). Eso es lo que se vio como "el plano de datos muere" el 12/11 y el 13/11.

## Qué hacer
1. **Reducir lo que provoca pérdida de muestras o pedidos tardíos.** En tachoPC:
   - el volcado IQ y el log en `info` suman carga (el log de esta corrida pesa 715 MB), pero por decisión del usuario (2026-11-17) se mantiene la opción 1 del menú como está;
   - mantener el governor en `performance` y cerrar los otros programas.
2. ~~Probar `expert_execution: threads: main_pool: nof_threads: 2` en tachoPC, en una prueba A/B/A.~~ Descartado por falta de tiempo (decisión del usuario, 2026-11-17).
3. **Mientras tanto:** si aparece "UL processor is busy", reiniciar el gNB antes de medir.
